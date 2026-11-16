"""Consultas do Administrador contra a v1 (add-acompanhamento-administrador, tarefa 2.4).

Usa o cenário sintético da fila (fila/teste_criar_cenario: dois médicos, duas fichas Vermelhas de Cardiologia e
tokens de Recepção e Administrador). No fim, fila/teste_encerrar_cenario com finalizar_pendentes fecha as fichas
do cenário, mesmo se o teste parar no meio.
"""

import json
import os
import secrets
import shutil
import ssl
import subprocess
import time
import unittest
from pathlib import Path

import httpx
from dotenv import dotenv_values

RAIZ = Path(__file__).resolve().parents[2]
PERFIL = os.getenv("XANO_TEST_PROFILE", "ps-impacta")
URL = os.getenv("XANO_CADASTROS_API_URL") or dotenv_values(RAIZ / "frontend/.env").get("XANO_CADASTROS_API_URL")


def cpf(numero: int) -> str:
    digitos = [int(c) for c in str(numero).zfill(9)]
    for tamanho in (9, 10):
        verificador = sum(valor * (tamanho + 1 - indice) for indice, valor in enumerate(digitos)) * 10 % 11
        digitos.append(0 if verificador == 10 else verificador)
    return "".join(map(str, digitos))


def funcao(nome: str, entrada: dict) -> dict:
    comando = [shutil.which("xano") or "xano", "function", "run", nome, "--json", "-", "--branch", "v1", "-p", PERFIL, "-o", "json"]
    for tentativa in range(6):
        # Plano gratuito: 25 requisições a cada 20 s no CLI; ao bater no limite, espera a janela e tenta de novo.
        time.sleep(3 if tentativa == 0 else 21)
        processo = subprocess.run(comando, input=json.dumps(entrada), text=True, capture_output=True, timeout=60, check=False)
        if processo.returncode == 0 or "requests per 20 seconds" not in processo.stderr:
            break
    if processo.returncode:
        raise AssertionError(processo.stderr or processo.stdout)
    return json.loads(processo.stdout)


class AcompanhamentoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not URL:
            raise unittest.SkipTest("Configure XANO_CADASTROS_API_URL")
        cls.marcador = str(time.time_ns() // 1_000_000)
        base = int(cls.marcador[-8:]) + 20_000_000
        criado = funcao("fila/teste_criar_cenario", {"marcador": cls.marcador, "senha": secrets.token_urlsafe(20),
                                                     "cpf_um": cpf(base), "cpf_dois": cpf(base + 1)})
        assert criado["status"] == "ok", criado
        cls.cenario = criado["result"]
        cls.http = httpx.Client(timeout=20, verify=ssl.create_default_context())

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "http"):
            cls.http.close()
        if hasattr(cls, "cenario"):
            encerrado = funcao("fila/teste_encerrar_cenario", {"marcador": cls.marcador, "finalizar_pendentes": True})
            assert encerrado["status"] == "ok", encerrado

    def get(self, caminho: str, token: str, **params):
        time.sleep(2.5)
        resposta = self.http.get(URL + caminho, headers={"Authorization": "Bearer " + self.cenario[token]}, params=params)
        if resposta.status_code == 429:
            time.sleep(21)
            resposta = self.http.get(URL + caminho, headers={"Authorization": "Bearer " + self.cenario[token]}, params=params)
        return resposta

    def test_consultas_do_administrador(self):
        c = self.cenario
        caminhos = ["/admin/fila-geral", f"/admin/fichas/{c['ficha_um']}", "/admin/equipe", "/admin/auditoria"]

        with self.subTest("só o Administrador consulta"):
            for caminho in caminhos:
                self.assertIn(self.get(caminho, "token_recepcao").status_code, (401, 403), caminho)
                self.assertIn(self.get(caminho, "token_um").status_code, (401, 403), caminho)

        with self.subTest("fila geral com as fichas do cenário na ordem da regra"):
            fila = self.get("/admin/fila-geral", "token_admin")
            self.assertEqual(fila.status_code, 200, fila.text)
            # O cenário cria uma ficha Vermelha (V-CAR-) e uma Amarela (A-CAR-), ambas de Cardiologia.
            do_cenario = {f["id"]: f for f in fila.json() if f["id"] in (c["ficha_um"], c["ficha_dois"])}
            self.assertEqual(set(do_cenario), {c["ficha_um"], c["ficha_dois"]})
            self.assertTrue(all(f["status"] == "AGUARDANDO" for f in do_cenario.values()))
            self.assertEqual({f["cor"] for f in do_cenario.values()}, {"VERMELHA", "AMARELA"})
            # Na regra da fila, a Vermelha vem antes da Amarela da mesma especialidade.
            vermelha = next(f for f in do_cenario.values() if f["cor"] == "VERMELHA")
            amarela = next(f for f in do_cenario.values() if f["cor"] == "AMARELA")
            self.assertLess(vermelha["posicao"], amarela["posicao"])
            do_cenario = list(do_cenario.values())
            self.assertTrue(all(isinstance(f["posicao"], int) and f["posicao"] >= 1 for f in do_cenario), do_cenario)
            self.assertTrue(all("nome" not in f and "cpf" not in f for f in fila.json()))

        with self.subTest("filtros de cor e status"):
            azuis = self.get("/admin/fila-geral", "token_admin", cor="AZUL").json()
            self.assertTrue(all(f["cor"] == "AZUL" for f in azuis))
            self.assertFalse({c["ficha_um"], c["ficha_dois"]} & {f["id"] for f in azuis})
            chamadas = self.get("/admin/fila-geral", "token_admin", status="CHAMADO").json()
            self.assertTrue(all(f["status"] == "CHAMADO" for f in chamadas))

        with self.subTest("detalhe da ficha só leitura"):
            detalhe = self.get(f"/admin/fichas/{c['ficha_um']}", "token_admin")
            self.assertEqual(detalhe.status_code, 200, detalhe.text)
            corpo = detalhe.json()
            self.assertEqual((corpo["id"], corpo["status"]), (c["ficha_um"], "AGUARDANDO"))
            self.assertIn(corpo["senha"], corpo["senhas"])
            self.assertIsInstance(corpo["chamadas"], list)
            self.assertIsInstance(corpo["historico"], list)
            self.assertEqual(self.get("/admin/fichas/999999999", "token_admin").status_code, 404)

        with self.subTest("equipe com filtro por perfil"):
            medicos = self.get("/admin/equipe", "token_admin", perfil="MEDICO")
            self.assertEqual(medicos.status_code, 200, medicos.text)
            self.assertTrue(all(p["perfil"] == "MEDICO" for p in medicos.json()["equipe"]))


if __name__ == "__main__":
    unittest.main()

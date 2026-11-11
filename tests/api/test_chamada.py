"""Integração da chamada médica na v1, sempre com pacientes e médicos fictícios."""

import concurrent.futures
import json
import os
import secrets
import subprocess
import time
import unittest
from pathlib import Path

import httpx
from dotenv import dotenv_values


PERFIL = os.getenv("XANO_TEST_PROFILE", "ps-impacta")
RAIZ = Path(__file__).resolve().parents[2]
URL = os.getenv("XANO_FILA_API_URL") or dotenv_values(RAIZ / "frontend/.env").get("XANO_FILA_API_URL")


def cpf(numero: int) -> str:
    digitos = [int(c) for c in str(numero).zfill(9)]
    for tamanho in (9, 10):
        verificador = sum(valor * (tamanho + 1 - indice) for indice, valor in enumerate(digitos)) * 10 % 11
        digitos.append(0 if verificador == 10 else verificador)
    return "".join(map(str, digitos))


def funcao(nome: str, entrada: dict, *, esperar: bool = True) -> dict:
    if esperar:
        time.sleep(2.5)  # Xano Free: a instância limita as chamadas também pelo CLI.
    processo = subprocess.run(
        ["xano", "function", "run", nome, "--json", "-", "--branch", "v1", "-p", PERFIL, "-o", "json"],
        input=json.dumps(entrada), text=True, capture_output=True, timeout=40, check=False,
    )
    if processo.returncode:
        raise AssertionError(processo.stderr or processo.stdout)
    return json.loads(processo.stdout)


class ChamadaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not URL:
            raise unittest.SkipTest("Configure XANO_FILA_API_URL para a integração da chamada")
        cls.marcador = str(time.time_ns() // 1_000_000)
        base = int(cls.marcador[-8:]) + 10_000_000
        criado = funcao("fila/teste_criar_cenario", {
            "marcador": cls.marcador,
            "senha": secrets.token_urlsafe(20),
            "cpf_um": cpf(base), "cpf_dois": cpf(base + 1),
        })
        assert criado["status"] == "ok", criado
        cls.cenario = criado["result"]
        c = cls.cenario
        ajustado = funcao("fila/teste_ajustar_cenario", {
            "marcador": cls.marcador, "medico_um": c["medico_um"], "medico_dois": c["medico_dois"],
            "ficha_dois": c["ficha_dois"], "vinculo_neu": c["vinculos"][1], "vinculo_cli": c["vinculos"][2],
        })
        assert ajustado["status"] == "ok", ajustado
        cls.http = httpx.Client(timeout=10)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "http"):
            cls.http.close()
        if hasattr(cls, "cenario"):
            encerrado = funcao("fila/teste_encerrar_cenario", {"marcador": cls.marcador})
            assert encerrado["status"] == "ok", encerrado

    def requisitar(self, metodo: str, caminho: str, token: str, **kwargs):
        time.sleep(2.5)
        resposta = self.http.request(metodo, URL + caminho, headers={"Authorization": "Bearer " + self.cenario[token]}, **kwargs)
        if resposta.status_code == 429:
            time.sleep(21)
            resposta = self.http.request(metodo, URL + caminho, headers={"Authorization": "Bearer " + self.cenario[token]}, **kwargs)
        return resposta

    def adiantar(self, ficha: int):
        resposta = funcao("fila/teste_adiantar_chamada", {"ficha_id": ficha, "marcador": self.marcador})
        self.assertEqual(resposta["status"], "ok", resposta)

    def agir(self, usuario: int, ficha: int, acao: str):
        resposta = funcao("fila/agir_chamada", {"usuario_id": usuario, "ficha_id": ficha, "acao": acao})
        self.assertEqual(resposta["status"], "ok", resposta)
        return resposta["result"]

    def test_fluxo_concorrente_e_oportunidades(self):
        c = self.cenario
        for token in ("token_recepcao", "token_admin"):
            with self.subTest(perfil=token):
                self.assertEqual(self.requisitar("POST", "/medico/chamar-proximo", token, json={}).status_code, 403)
                self.assertEqual(self.requisitar("GET", "/medico/filas", token).status_code, 403)
                self.assertEqual(self.requisitar("GET", f"/fichas/{c['ficha_um']}/impressao", token).status_code, 403)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            chamadas = list(pool.map(lambda uid: funcao("fila/chamar_proximo", {"usuario_id": uid}, esperar=False), (c["usuario_um"], c["usuario_dois"])))
        self.assertEqual([item["status"] for item in chamadas], ["ok", "ok"])
        fichas = [item["result"]["ficha"]["id"] for item in chamadas]
        self.assertEqual(set(fichas), {c["ficha_um"], c["ficha_dois"]})
        ficha_um, ficha_dois = fichas
        impressao_inicial = self.requisitar("GET", f"/fichas/{ficha_um}/impressao", "token_um")
        self.assertEqual(impressao_inicial.status_code, 200, impressao_inicial.text)
        ficha_inicial = impressao_inicial.json()["ficha"]

        pendente = funcao("fila/chamar_proximo", {"usuario_id": c["usuario_um"]})
        self.assertIn("FICHA_PENDENTE", pendente["exception"]["message"])
        self.assertEqual(self.requisitar("POST", "/medico/chamar-proximo", "token_um", json={"ficha_id": ficha_dois}).status_code, 400)
        self.assertEqual(self.requisitar("GET", f"/fichas/{ficha_um}/impressao", "token_dois").status_code, 403)
        self.assertEqual(self.requisitar("POST", f"/medico/fichas/{ficha_um}/acao", "token_dois", json={"acao": "COMPARECEU"}).status_code, 403)

        cedo = self.requisitar("POST", f"/medico/fichas/{ficha_um}/acao", "token_um", json={"acao": "REPETIR"})
        self.assertEqual(cedo.status_code, 400)
        self.assertIn("AGUARDE_INTERVALO:", cedo.json()["message"])
        self.adiantar(ficha_um)
        self.assertEqual(self.agir(c["usuario_um"], ficha_um, "REPETIR")["tentativa"], 2)
        self.adiantar(ficha_um)
        retorno = self.agir(c["usuario_um"], ficha_um, "REPETIR")
        self.assertEqual((retorno["status"], retorno["oportunidade"], retorno["tentativa"]), ("AGUARDANDO", 2, 0))
        segunda = funcao("fila/chamar_proximo", {"usuario_id": c["usuario_um"]})
        self.assertEqual(segunda["status"], "ok", segunda)
        self.assertEqual(segunda["result"]["ficha"]["id"], ficha_um)
        impresso = self.requisitar("GET", f"/fichas/{ficha_um}/impressao", "token_um")
        self.assertEqual(impresso.status_code, 200, impresso.text)
        ficha_reentrada = impresso.json()["ficha"]
        self.assertEqual(ficha_reentrada["senha"], ficha_inicial["senha"])
        self.assertEqual(ficha_reentrada["especialidade"], ficha_inicial["especialidade"])
        self.assertEqual(ficha_reentrada["chegada_em"], ficha_inicial["chegada_em"])
        tentativas = [(e["oportunidade"], e["tentativa"]) for e in impresso.json()["historico"] if e["tipo"] == "CHAMADA"]
        self.assertEqual(tentativas, [(1, 1), (1, 2), (1, 3), (2, 1)])
        self.adiantar(ficha_um)
        self.agir(c["usuario_um"], ficha_um, "REPETIR")
        self.adiantar(ficha_um)
        final = self.agir(c["usuario_um"], ficha_um, "REPETIR")
        self.assertEqual((final["status"], final["oportunidade"], final["tentativa"]), ("DESISTENCIA", 2, 3))
        self.assertEqual(self.requisitar("GET", f"/fichas/{ficha_um}/impressao", "token_um").status_code, 403)

        compareceu = self.agir(c["usuario_dois"], ficha_dois, "COMPARECEU")
        self.assertEqual(compareceu["status"], "ATENDIDO")
        self.assertEqual(self.requisitar("GET", f"/fichas/{ficha_dois}/impressao", "token_dois").status_code, 200)


if __name__ == "__main__":
    unittest.main()

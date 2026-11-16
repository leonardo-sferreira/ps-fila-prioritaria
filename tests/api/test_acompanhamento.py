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
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import dotenv_values

RAIZ = Path(__file__).resolve().parents[2]
PERFIL = os.getenv("XANO_TEST_PROFILE", "ps-impacta")
URL = os.getenv("XANO_CADASTROS_API_URL") or dotenv_values(RAIZ / "frontend/.env").get("XANO_CADASTROS_API_URL")
URL_AUTH = os.getenv("XANO_AUTH_API_URL") or dotenv_values(RAIZ / "frontend/.env").get("XANO_AUTH_API_URL")


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

    def requisitar(self, metodo: str, base: str, caminho: str, token: str, **params):
        time.sleep(2.5)
        cabecalho = {"Authorization": "Bearer " + self.cenario[token]}
        resposta = self.http.request(metodo, base + caminho, headers=cabecalho, params=params or None)
        if resposta.status_code == 429:
            time.sleep(21)
            resposta = self.http.request(metodo, base + caminho, headers=cabecalho, params=params or None)
        return resposta

    def get(self, caminho: str, token: str, **params):
        return self.requisitar("GET", URL, caminho, token, **params)

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

    def test_fluxo_reflete_no_acompanhamento(self):
        """Roda depois de test_consultas_do_administrador (ordem alfabética), porque muda o cenário."""
        c = self.cenario
        hoje = datetime.now(timezone(timedelta(hours=-3))).date()  # Brasília, sem horário de verão

        with self.subTest("me/status devolve o status da própria sessão (7.4)"):
            proprio = self.requisitar("GET", URL_AUTH, "/me/status", "token_um")
            self.assertEqual((proprio.status_code, proprio.json()), (200, {"status": "DISPONIVEL"}), proprio.text)
            self.assertIn(self.requisitar("GET", URL_AUTH, "/me/status", "token_admin").status_code, (401, 403))
            # A Recepção do cenário não tem sessão aberta: o endpoint pede novo login.
            self.assertEqual(self.requisitar("GET", URL_AUTH, "/me/status", "token_recepcao").status_code, 401)

        with self.subTest("detalhe mostra o ajuste de cor com justificativa"):
            ajuste = funcao("fila/teste_marcar_ajuste", {"ficha_id": c["ficha_dois"], "usuario_id": c["usuario_recepcao"], "marcador": self.marcador})
            self.assertEqual(ajuste["status"], "ok", ajuste)
            corpo = self.get(f"/admin/fichas/{c['ficha_dois']}", "token_admin").json()
            self.assertEqual((corpo["cor"], corpo["cor_calculada"], corpo["justificativa_ajuste"]), ("AMARELA", "AZUL", "Teste: ajuste sintético"))
            alteracao = [h for h in corpo["historico"] if h["tipo_evento"] == "PRIORIDADE_ALTERADA"]
            self.assertEqual(len(alteracao), 1, corpo["historico"])
            self.assertNotIn(alteracao[0]["usuario"], ("Sistema", "—"))
            self.assertEqual(alteracao[0]["justificativa"], "Teste: ajuste sintético")

        with self.subTest("ficha chamada duas vezes aparece com médico e tentativa"):
            chamada = funcao("fila/chamar_proximo", {"usuario_id": c["usuario_um"]})
            self.assertEqual(chamada["status"], "ok", chamada)
            ficha = chamada["result"]["ficha"]["id"]
            self.assertIn(ficha, (c["ficha_um"], c["ficha_dois"]))
            if ficha == c["ficha_um"]:
                self.assertEqual(funcao("fila/teste_adiantar_chamada", {"ficha_id": ficha, "marcador": self.marcador})["status"], "ok")
                repetida = funcao("fila/agir_chamada", {"usuario_id": c["usuario_um"], "ficha_id": ficha, "acao": "REPETIR"})
                self.assertEqual(repetida["result"]["tentativa"], 2, repetida)
            esperado = 2 if ficha == c["ficha_um"] else 1
            chamadas = self.get("/admin/fila-geral", "token_admin", status="CHAMADO").json()
            linha = next((f for f in chamadas if f["id"] == ficha), None)
            self.assertIsNotNone(linha, chamadas)
            self.assertEqual(linha["tentativa"], esperado)
            self.assertTrue(linha["medico"])
            detalhe = self.get(f"/admin/fichas/{ficha}", "token_admin").json()
            self.assertEqual([(ch["tipo"], ch["tentativa"]) for ch in detalhe["chamadas"]], [("CHAMADA", n) for n in range(1, esperado + 1)])
            self.assertTrue(all(ch["medico"] not in ("—", None) for ch in detalhe["chamadas"]))

        with self.subTest("sessão encerrada sai da equipe e entra na auditoria"):
            antes = {p["usuario_id"] for p in self.get("/admin/equipe", "token_admin").json()["equipe"]}
            self.assertIn(c["usuario_dois"], antes)
            self.assertEqual(self.requisitar("POST", URL_AUTH, "/auth/logout", "token_dois").status_code, 200)
            depois = {p["usuario_id"] for p in self.get("/admin/equipe", "token_admin").json()["equipe"]}
            self.assertNotIn(c["usuario_dois"], depois)
            acessos = self.get("/admin/auditoria", "token_admin", origem="SESSAO", usuario_id=c["usuario_dois"]).json()["itens"]
            self.assertEqual(sorted(e["tipo_evento"] for e in acessos), ["LOGIN", "LOGOUT"], acessos)

        with self.subTest("auditoria ordenada, paginada e filtrada"):
            pagina = self.get("/admin/auditoria", "token_admin")
            self.assertEqual(pagina.status_code, 200, pagina.text)
            corpo = pagina.json()
            self.assertEqual((corpo["pagina"], corpo["por_pagina"], corpo["de"], corpo["ate"]), (1, 50, hoje.isoformat(), hoje.isoformat()))
            momentos = [e["em"] for e in corpo["itens"]]
            self.assertEqual(momentos, sorted(momentos, reverse=True))
            self.assertLessEqual(len(corpo["itens"]), 50)
            self.assertEqual(len(corpo["itens"]), min(corpo["total"], 50))
            if corpo["total"] > 50:
                segunda = self.get("/admin/auditoria", "token_admin", pagina=2).json()
                self.assertEqual(len(segunda["itens"]), min(corpo["total"] - 50, 50))
                self.assertLessEqual(segunda["itens"][0]["em"], momentos[-1])
            chamadas = self.get("/admin/auditoria", "token_admin", origem="CHAMADA", usuario_id=c["usuario_um"]).json()["itens"]
            self.assertTrue(chamadas)
            self.assertTrue(all(e["origem"] == "CHAMADA" and e["usuario_id"] == c["usuario_um"] for e in chamadas))
            ontem = (hoje - timedelta(days=1)).isoformat()
            passado = self.get("/admin/auditoria", "token_admin", data_inicio=ontem, data_fim=ontem, usuario_id=c["usuario_um"]).json()
            self.assertEqual(passado["total"], 0, passado)
            longo = self.get("/admin/auditoria", "token_admin", data_inicio=(hoje - timedelta(days=40)).isoformat(), data_fim=hoje.isoformat())
            self.assertEqual(longo.status_code, 400, longo.text)


if __name__ == "__main__":
    unittest.main()

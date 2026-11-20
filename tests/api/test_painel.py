"""Painel público contra a v1 (add-painel-publico, tarefa 1.2).

Usa o cenário sintético da fila (fila/teste_criar_cenario: duas fichas de Cardiologia, V-CAR-<marcador> Vermelha e
A-CAR-<marcador> Amarela, e dois médicos). O painel é consultado sem token. No fim, fila/teste_encerrar_cenario com
finalizar_pendentes fecha as fichas do cenário, mesmo se o teste parar no meio.

Fora daqui: o tamanho da previsão (8 e 3 elegíveis) é coberto pelos testes nativos de fila/prever_fila, e o ticket
da triagem não é chamado aqui para não mexer na fila real da pré-triagem; o teste confere só o formato dele.
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
URL = os.getenv("XANO_FILA_API_URL") or dotenv_values(RAIZ / "frontend/.env").get("XANO_FILA_API_URL")
PROIBIDAS = {"nome", "cpf", "nascimento", "data_nascimento", "telefone", "sintomas", "sintoma", "sinais", "pa_sistolica", "fc", "fr",
             "temperatura", "spo2", "glicemia", "paciente", "paciente_id", "medico", "medico_id", "observacao", "escore_risco", "email"}


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


def chaves(valor) -> set[str]:
    """Todas as chaves de objetos em qualquer nível da resposta."""
    if isinstance(valor, dict):
        return set(valor) | {c for v in valor.values() for c in chaves(v)}
    if isinstance(valor, list):
        return {c for v in valor for c in chaves(v)}
    return set()


class PainelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not URL:
            raise unittest.SkipTest("Configure XANO_FILA_API_URL")
        cls.marcador = str(time.time_ns() // 1_000_000)
        base = int(cls.marcador[-8:]) + 30_000_000
        criado = funcao("fila/teste_criar_cenario", {"marcador": cls.marcador, "senha": secrets.token_urlsafe(20),
                                                     "cpf_um": cpf(base), "cpf_dois": cpf(base + 1)})
        assert criado["status"] == "ok", criado
        cls.cenario = criado["result"]
        cls.vermelha, cls.amarela = "V-CAR-" + cls.marcador, "A-CAR-" + cls.marcador
        cls.http = httpx.Client(timeout=20, verify=ssl.create_default_context())

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "http"):
            cls.http.close()
        if hasattr(cls, "cenario"):
            encerrado = funcao("fila/teste_encerrar_cenario", {"marcador": cls.marcador, "finalizar_pendentes": True})
            assert encerrado["status"] == "ok", encerrado

    def painel(self, **params):
        time.sleep(2.5)
        resposta = self.http.get(URL + "/painel", params=params or None)
        if resposta.status_code == 429:
            time.sleep(21)
            resposta = self.http.get(URL + "/painel", params=params or None)
        return resposta

    def previsao(self, corpo: dict, sigla: str) -> list[str]:
        return [s["senha"] for p in corpo["previsoes"] if p["sigla"] == sigla for s in p["senhas"]]

    def agir(self, ficha: int, acao: str) -> dict:
        resposta = funcao("fila/agir_chamada", {"usuario_id": self.cenario["usuario_um"], "ficha_id": ficha, "acao": acao})
        self.assertEqual(resposta["status"], "ok", resposta)
        return resposta["result"]

    def repetir(self, ficha: int) -> dict:
        self.assertEqual(funcao("fila/teste_adiantar_chamada", {"ficha_id": ficha, "marcador": self.marcador})["status"], "ok")
        return self.agir(ficha, "REPETIR")

    def test_painel_publico(self):
        c = self.cenario

        with self.subTest("sem token, sem dado pessoal e com o formato do design"):
            resposta = self.painel()
            self.assertEqual(resposta.status_code, 200, resposta.text)
            corpo = resposta.json()
            self.assertEqual(set(corpo), {"atual", "ultimas", "triagem", "previsoes", "gerado_em"})
            self.assertFalse(chaves(corpo) & PROIBIDAS, chaves(corpo) & PROIBIDAS)
            self.assertLessEqual(len(corpo["ultimas"]), 4)
            if corpo["triagem"] is not None:
                self.assertEqual(set(corpo["triagem"]), {"ticket_id", "tipo", "numero", "tentativa", "chamado_em"})

        with self.subTest("filtro por especialidade"):
            so_car = self.painel(especialidades="car").json()
            self.assertEqual([p["sigla"] for p in so_car["previsoes"]], ["CAR"])
            self.assertTrue(so_car["atual"] is None or so_car["atual"]["sigla"] == "CAR")
            self.assertTrue(all(u["sigla"] == "CAR" for u in so_car["ultimas"]))
            self.assertEqual(self.painel(especialidades="XYZ").status_code, 400)

        with self.subTest("Vermelha na frente da Amarela na previsão"):
            prevista = self.previsao(so_car, "CAR")
            self.assertIn(self.vermelha, prevista)
            self.assertIn(self.amarela, prevista)
            self.assertLess(prevista.index(self.vermelha), prevista.index(self.amarela))
            cores = {s["senha"]: s["cor"] for p in so_car["previsoes"] for s in p["senhas"]}
            if all(cores[s] != "VERMELHA" for s in prevista if s != self.vermelha):
                self.assertEqual(prevista[0], self.vermelha)

        with self.subTest("a chamada é a primeira prevista da especialidade (CA11) e vira a atual"):
            antes = self.painel().json()
            chamada = funcao("fila/chamar_proximo", {"usuario_id": c["usuario_um"]})
            self.assertEqual(chamada["status"], "ok", chamada)
            senha = chamada["result"]["ficha"]["senha"]
            sigla = senha.split("-")[1]
            self.assertEqual(self.previsao(antes, sigla)[0], senha)
            depois = self.painel().json()
            self.assertEqual((depois["atual"]["senha"], depois["atual"]["tentativa"]), (senha, 1))
            self.assertNotIn(senha, self.previsao(depois, sigla))
            self.assertNotIn(senha, [u["senha"] for u in depois["ultimas"]])
            self.ficha_chamada, self.chamada_id = chamada["result"]["ficha"]["id"], depois["atual"]["chamada_id"]

        with self.subTest("repetição volta ao destaque como 2ª chamada"):
            self.assertEqual(self.repetir(self.ficha_chamada)["tentativa"], 2)
            repetida = self.painel().json()["atual"]
            self.assertEqual((repetida["senha"], repetida["tentativa"]), (senha, 2))
            self.assertNotEqual(repetida["chamada_id"], self.chamada_id)

        if self.ficha_chamada == c["ficha_um"]:
            with self.subTest("desistência sai da previsão"):
                # Esgota a 1ª oportunidade (volta à fila), chama de novo e esgota a 2ª: DESISTENCIA.
                self.assertEqual(self.repetir(self.ficha_chamada)["status"], "AGUARDANDO")
                self.assertIn(self.vermelha, self.previsao(self.painel(especialidades="CAR").json(), "CAR"))
                segunda = funcao("fila/chamar_proximo", {"usuario_id": c["usuario_um"]})
                self.assertEqual(segunda["result"]["ficha"]["id"], self.ficha_chamada, segunda)
                self.repetir(self.ficha_chamada)
                self.assertEqual(self.repetir(self.ficha_chamada)["status"], "DESISTENCIA")
                final = self.painel(especialidades="CAR").json()
                self.assertNotIn(self.vermelha, self.previsao(final, "CAR"))
                self.assertIn(self.amarela, self.previsao(final, "CAR"))


if __name__ == "__main__":
    unittest.main()

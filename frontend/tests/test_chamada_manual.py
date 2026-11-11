"""Chamada manual na fila de pré-triagem (change chamada-manual-pre-triagem): contagem por chamada, limite e ações."""
import asyncio
import inspect
import unittest
from unittest.mock import patch

from ps_fila_prioritaria.comum import _timestamp_segundos
from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.fila_pre_triagem import FilaTicketsState

AGORA = 1_794_155_600_000  # ms, como o Xano devolve


class Resposta:
    status_code = 200
    is_success = True

    def __init__(self, dados):
        self.dados = dados

    def json(self):
        return self.dados


class EstadoFalso:
    _requisitar = FilaTicketsState._requisitar
    carregar = FilaTicketsState.carregar.fn
    acao = FilaTicketsState.acao.fn
    chamar_novamente = FilaTicketsState.chamar_novamente.fn
    nao_compareceu = FilaTicketsState.nao_compareceu.fn

    def __init__(self):
        self.tickets = []
        self.mensagem = ""
        self.erro = False
        self.auth = type("Auth", (), {"token": "token-teste"})()

    async def get_state(self, estado):
        assert estado is AuthState
        return self.auth


def carregar_ticket(tentativas: int, segundos_desde_chamada: int, tentativas_maximas: int = 3) -> dict:
    estado = EstadoFalso()
    corpo = {
        "tickets": [{"id": 7, "tipo": "NORMAL", "numero": 1, "status": "CHAMADO", "tentativas": tentativas,
                     "chamado_em": AGORA - segundos_desde_chamada * 1000}],
        "agora": AGORA,
        "intervalo_segundos": 30,
        "intervalo_repeticao_segundos": 10,
        "tentativas_maximas": tentativas_maximas,
    }
    with patch("ps_fila_prioritaria.api.requisitar", return_value=Resposta(corpo)):
        asyncio.run(estado.carregar())
    return estado.tickets[0]


class TestContagemPorChamada(unittest.TestCase):
    def test_primeira_chamada_espera_30_segundos(self):
        self.assertEqual(carregar_ticket(1, 0)["segundos_restantes"], 30)
        self.assertEqual(carregar_ticket(1, 29)["segundos_restantes"], 1)
        self.assertEqual(carregar_ticket(1, 30)["segundos_restantes"], 0)

    def test_segunda_e_terceira_chamada_esperam_10_segundos(self):
        for tentativas in (2, 3):
            self.assertEqual(carregar_ticket(tentativas, 0)["segundos_restantes"], 10)
            self.assertEqual(carregar_ticket(tentativas, 9)["segundos_restantes"], 1)
            self.assertEqual(carregar_ticket(tentativas, 10)["segundos_restantes"], 0)

    def test_chamar_novamente_some_na_terceira_chamada(self):
        self.assertTrue(carregar_ticket(1, 30)["pode_chamar_novamente"])
        self.assertTrue(carregar_ticket(2, 10)["pode_chamar_novamente"])
        self.assertFalse(carregar_ticket(3, 10)["pode_chamar_novamente"])

    def test_sem_parametros_a_tela_nao_bloqueia_e_o_xano_decide(self):
        estado = EstadoFalso()
        corpo = [{"id": 7, "status": "CHAMADO", "tentativas": 1, "chamado_em": AGORA}]
        with patch("ps_fila_prioritaria.api.requisitar", return_value=Resposta(corpo)):
            asyncio.run(estado.carregar())
        self.assertEqual(estado.tickets[0]["segundos_restantes"], -1)
        self.assertTrue(estado.tickets[0]["pode_chamar_novamente"])


class TestAcoesManuais(unittest.TestCase):
    def _executar(self, metodo: str) -> tuple[EstadoFalso, list]:
        estado = EstadoFalso()
        with patch("ps_fila_prioritaria.api.requisitar", side_effect=[Resposta({}), Resposta([])]) as requisitar:
            asyncio.run(getattr(estado, metodo)(7))
        return estado, requisitar.call_args_list

    def test_chamar_novamente_envia_repetir(self):
        estado, chamadas = self._executar("chamar_novamente")
        self.assertEqual(chamadas[0].args[2], "/tickets/7/acao")
        self.assertEqual(chamadas[0].kwargs["json"], {"acao": "REPETIR"})
        self.assertEqual(estado.mensagem, "Ticket chamado novamente.")

    def test_nao_compareceu_envia_ausencia(self):
        estado, chamadas = self._executar("nao_compareceu")
        self.assertEqual(chamadas[0].kwargs["json"], {"acao": "AUSENCIA"})
        self.assertEqual(estado.mensagem, "Não comparecimento registrado.")

    def test_tela_nunca_avanca_sozinha(self):
        self.assertFalse(hasattr(FilaTicketsState, "atualizar_automaticamente"))
        codigo = inspect.getsource(FilaTicketsState.monitorar.fn)
        self.assertNotIn("acao", codigo.split('"""')[-1])
        self.assertNotIn("AVANCAR", codigo)


class TestDatas(unittest.TestCase):
    def test_datas_xano_sao_convertidas(self):
        self.assertEqual(_timestamp_segundos(1700000000000), 1700000000)
        self.assertEqual(_timestamp_segundos("2023-11-14T22:13:20Z"), 1700000000)
        self.assertIsNone(_timestamp_segundos("invalida"))

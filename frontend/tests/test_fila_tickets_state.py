"""Testes locais do fluxo da interface de pré-triagem."""
import asyncio
import unittest
from unittest.mock import patch

from ps_fila_prioritaria.ps_fila_prioritaria import AuthState, FilaTicketsState, PacienteState


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
    proximo = FilaTicketsState.proximo.fn
    acao = FilaTicketsState.acao.fn
    identificar = FilaTicketsState.identificar.fn

    def __init__(self):
        self.tickets = []
        self.mensagem = ""
        self.erro = False
        self.auth = type("Auth", (), {"token": "token-teste"})()
        self.paciente = type("Paciente", (), {"ticket_id": 0, "_resetar_paciente_atual": lambda self: None})()

    async def get_state(self, estado):
        return self.auth if estado is AuthState else self.paciente


class TestFilaTicketsState(unittest.TestCase):
    def test_chamada_atualiza_lista_com_senha_e_token(self):
        estado = EstadoFalso()
        with patch("ps_fila_prioritaria.ps_fila_prioritaria.api.requisitar", side_effect=[
            Resposta({"id": 7}), Resposta([{"id": 7, "tipo": "PEDIATRICO", "numero": 2}])
        ]) as requisitar:
            asyncio.run(estado.proximo())
        self.assertEqual(estado.tickets[0]["senha_exibida"], "C-002")
        self.assertEqual(requisitar.call_args_list[0].kwargs["token"], "token-teste")
        self.assertEqual(requisitar.call_args_list[1].args[2], "/tickets")

    def test_desistencia_envia_acao_e_recarrega(self):
        estado = EstadoFalso()
        with patch("ps_fila_prioritaria.ps_fila_prioritaria.api.requisitar", side_effect=[Resposta({}), Resposta([])]) as requisitar:
            asyncio.run(estado.acao(7, "DESISTENCIA"))
        self.assertEqual(requisitar.call_args_list[0].kwargs["json"], {"acao": "DESISTENCIA"})
        self.assertEqual(requisitar.call_args_list[0].args[2], "/tickets/7/acao")

    def test_identificacao_preserva_ticket(self):
        estado = EstadoFalso()
        asyncio.run(estado.identificar(7))
        self.assertEqual(estado.paciente.ticket_id, 7)


class TestApresentacaoFila(unittest.TestCase):
    def test_ticket_do_totem_ganha_tipo_cor_e_hora_de_brasilia(self):
        estado = EstadoFalso()
        corpo = {
            "tickets": [
                {"id": 1, "tipo": "PREFERENCIAL", "numero": 4, "status": "AGUARDANDO", "emitido_em": 1794155580000},
                {"id": 2, "tipo": "PEDIATRICO", "numero": 2, "status": "CHAMADO", "emitido_em": 1794153079441, "chamado_em": 1794153886955},
            ],
            "agora": 1794155600000,  # 08/11/2026 16:33:20 UTC
            "intervalo_segundos": 30,
        }
        with patch("ps_fila_prioritaria.ps_fila_prioritaria.api.requisitar", return_value=Resposta(corpo)):
            asyncio.run(estado.carregar())
        preferencial, pediatrico = estado.tickets
        self.assertEqual((preferencial["senha_exibida"], preferencial["nome_tipo"], preferencial["cor_tipo"]), ("P-004", "Preferencial", "#ED8B00"))
        self.assertEqual(preferencial["emitido_hora"], "13:33")  # 16:33 UTC = 13:33 em Brasília (UTC-3)
        self.assertEqual(pediatrico["nome_tipo"], "Pediátrico")
        self.assertEqual(estado.atualizado_em, "13:33:20")

    def test_tipo_desconhecido_nao_quebra_a_tela(self):
        estado = EstadoFalso()
        with patch("ps_fila_prioritaria.ps_fila_prioritaria.api.requisitar", return_value=Resposta([{"id": 1, "numero": 1, "status": "AGUARDANDO"}])):
            asyncio.run(estado.carregar())
        self.assertEqual(estado.tickets[0]["nome_tipo"], "—")
        self.assertEqual(estado.tickets[0]["emitido_hora"], "—")

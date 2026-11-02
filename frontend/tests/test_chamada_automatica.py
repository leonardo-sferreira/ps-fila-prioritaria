"""Casos novos de temporização e confirmação de presença na fila."""
import asyncio
import unittest
from unittest.mock import AsyncMock

from ps_fila_prioritaria.ps_fila_prioritaria import FilaTicketsState, _timestamp_segundos


class TestChamadaAutomatica(unittest.TestCase):
    def _executar_avanco(self, ticket):
        estado = type("Estado", (), {})()
        estado.tickets = [ticket]
        estado.carregar = AsyncMock()
        estado.acao = AsyncMock()
        asyncio.run(FilaTicketsState.atualizar_automaticamente.fn(estado))
        return estado.acao

    def test_avanca_somente_no_prazo_sem_presenca(self):
        self._executar_avanco({"id": 7, "status": "CHAMADO", "presente": False, "segundos_restantes": 0}).assert_awaited_once_with(7, "AVANCAR")
        for mudanca in ({"segundos_restantes": 1}, {"presente": True}, {"status": "AGUARDANDO"}, {"segundos_restantes": -1}):
            ticket = {"id": 7, "status": "CHAMADO", "presente": False, "segundos_restantes": 0}
            ticket.update(mudanca)
            self._executar_avanco(ticket).assert_not_awaited()

    def test_datas_xano_sao_convertidas(self):
        self.assertEqual(_timestamp_segundos(1700000000000), 1700000000)
        self.assertEqual(_timestamp_segundos("2023-11-14T22:13:20Z"), 1700000000)
        self.assertIsNone(_timestamp_segundos("invalida"))

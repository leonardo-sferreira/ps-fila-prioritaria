"""Seletor de status da Recepção/Triagem (add-acompanhamento-administrador, D5)."""

import asyncio
from unittest.mock import patch

from ps_fila_prioritaria.estados import status_equipe as s
from tests.test_cadastros_state import REQUISITAR, Resposta, estado_falso


def _estado(**campos):
    estado = estado_falso(s.StatusEquipeState, **{"status": "DISPONIVEL", "ocupado": False, "mensagem": "", "erro": False, **campos})
    estado._requisitar = lambda metodo, caminho, **kw: s.StatusEquipeState._requisitar(estado, metodo, caminho, **kw)
    return estado


def test_opcoes_nao_incluem_em_atendimento():
    assert [valor for valor, _ in s.OPCOES_STATUS] == ["DISPONIVEL", "PAUSA", "AUSENTE"]
    assert s.NOME_STATUS["EM_ATENDIMENTO"] == "Em atendimento"


def test_carregar_le_o_status_da_sessao():
    estado = _estado(status="")
    with patch(REQUISITAR, return_value=Resposta(200, {"perfil": "RECEPCAO_TRIAGEM", "status_operacional": "PAUSA"})):
        asyncio.run(s.StatusEquipeState.carregar.fn(estado))
    assert estado.status == "PAUSA"


def test_definir_envia_patch_e_atualiza():
    estado = _estado()
    chamadas = []

    def requisitar(metodo, _variavel, caminho, **kw):
        chamadas.append((metodo, caminho, kw.get("json")))
        return Resposta(200, {"status": "AUSENTE"})

    with patch(REQUISITAR, side_effect=requisitar):
        asyncio.run(s.StatusEquipeState.definir.fn(estado, "AUSENTE"))
    assert chamadas == [("PATCH", "/me/status", {"status": "AUSENTE"})]
    assert estado.status == "AUSENTE" and estado.mensagem == "Status: Ausente." and not estado.ocupado


def test_mesmo_status_nao_chama_a_api():
    estado = _estado(status="PAUSA")
    with patch(REQUISITAR, side_effect=AssertionError("não deve chamar")):
        asyncio.run(s.StatusEquipeState.definir.fn(estado, "PAUSA"))
    assert estado.status == "PAUSA"

"""Regressões da tela pública do Totem (add-totem)."""

import unittest
from unittest.mock import patch

import httpx

from ps_fila_prioritaria.ps_fila_prioritaria import TotemState

REQUISICAO = "ps_fila_prioritaria.api.httpx.request"
AMBIENTE = {"XANO_TRIAGEM_API_URL": "https://triagem.test", "TOTEM_CHAVE": "chave-de-teste"}


class Resposta:
    def __init__(self, status_code: int, corpo: object):
        self.status_code = status_code
        self._corpo = corpo

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> object:
        return self._corpo


class EstadoFalso:
    """Permite testar os handlers sem uma sessão Reflex em execução."""

    emitir = TotemState.emitir.fn
    concluir = TotemState.concluir.fn

    def __init__(self) -> None:
        self.emitindo = False
        self.codigo = ""
        self.tipo_emitido = ""
        self.erro = ""


def _emitir(estado: EstadoFalso, tipo: str, **mock) -> object:
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(REQUISICAO, **mock) as requisicao:
        list(estado.emitir(tipo))
    return requisicao


def test_emissao_mostra_o_codigo_e_manda_a_chave_so_ao_backend() -> None:
    estado = EstadoFalso()
    requisicao = _emitir(estado, "PREFERENCIAL", return_value=Resposta(200, {"tipo": "PREFERENCIAL", "numero": 7, "codigo": "P-007"}))
    assert requisicao.call_args.args[:2] == ("POST", "https://triagem.test/totem/tickets")
    assert requisicao.call_args.kwargs["json"] == {"chave_dispositivo": "chave-de-teste", "tipo": "PREFERENCIAL"}
    assert estado.codigo == "P-007"
    assert estado.tipo_emitido == "PREFERENCIAL"
    assert not estado.emitindo and estado.erro == ""
    # A chave não fica em nenhuma variável do estado (o estado é sincronizado com o navegador).
    assert "chave-de-teste" not in vars(estado).values()


def test_falha_da_api_mostra_erro_sem_tentar_de_novo() -> None:
    for resposta in (Resposta(401, {"message": "Dispositivo não autorizado."}), Resposta(500, {"message": "x"})):
        estado = EstadoFalso()
        requisicao = _emitir(estado, "NORMAL", return_value=resposta)
        assert requisicao.call_count == 1
        assert estado.erro == "Não foi possível emitir o ticket."
        assert estado.codigo == "" and not estado.emitindo


def test_sem_conexao_mostra_erro_sem_tentar_de_novo() -> None:
    estado = EstadoFalso()
    requisicao = _emitir(estado, "PEDIATRICO", side_effect=httpx.ConnectError("offline"))
    assert requisicao.call_count == 1
    assert estado.erro == "Não foi possível emitir o ticket."


def test_concluir_volta_para_a_escolha() -> None:
    estado = EstadoFalso()
    estado.codigo, estado.tipo_emitido, estado.erro = "N-001", "NORMAL", "x"
    estado.concluir()
    assert estado.codigo == estado.tipo_emitido == estado.erro == ""


class TestTotemState(unittest.TestCase):
    """Compatível tanto com unittest quanto com pytest."""

    def test_emissao(self) -> None:
        test_emissao_mostra_o_codigo_e_manda_a_chave_so_ao_backend()

    def test_falha(self) -> None:
        test_falha_da_api_mostra_erro_sem_tentar_de_novo()

    def test_sem_conexao(self) -> None:
        test_sem_conexao_mostra_erro_sem_tentar_de_novo()

    def test_concluir(self) -> None:
        test_concluir_volta_para_a_escolha()

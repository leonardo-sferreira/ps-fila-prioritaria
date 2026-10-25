"""Regressões de estado do login, da guarda de rota e do logout."""

import unittest
from unittest.mock import patch

import httpx

from ps_fila_prioritaria.ps_fila_prioritaria import AuthState

REQUISICAO = "ps_fila_prioritaria.api.httpx.request"
REDIRECT = "ps_fila_prioritaria.ps_fila_prioritaria.rx.redirect"
AMBIENTE = {"XANO_AUTH_API_URL": "https://auth.test"}


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

    _encerrar_sessao_local = AuthState._encerrar_sessao_local
    _validar_sessao = AuthState._validar_sessao
    entrar = AuthState.entrar.fn
    verificar_sessao = AuthState.verificar_sessao.fn
    ir_para_inicio = AuthState.ir_para_inicio.fn
    sair = AuthState.sair.fn

    def __init__(self, token: str = "") -> None:
        self.token = token
        self.nome = ""
        self.perfil = ""
        self.entrando = False
        self.mensagem = ""


def _executar_login(estado: EstadoFalso, resposta: Resposta) -> list[object]:
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(REQUISICAO, return_value=resposta) as requisicao, patch(
        REDIRECT, side_effect=lambda rota: f"redirect:{rota}"
    ):
        eventos = [evento for evento in estado.entrar({"email": "ana@ps.com.br", "senha": "segredo123"}) if evento]
    assert requisicao.call_args.args[:2] == ("POST", "https://auth.test/auth/login")
    assert requisicao.call_args.kwargs["json"] == {"email": "ana@ps.com.br", "senha": "segredo123"}
    return eventos


def test_login_valido_guarda_token_e_vai_para_a_area_do_perfil() -> None:
    for perfil, rota in (("RECEPCAO_TRIAGEM", "/recepcao"), ("MEDICO", "/medico"), ("ADMINISTRADOR", "/admin")):
        estado = EstadoFalso()
        eventos = _executar_login(estado, Resposta(200, {"token": "tok", "nome": "Ana", "perfil": perfil}))
        assert estado.token == "tok"
        assert estado.nome == "Ana"
        assert estado.perfil == perfil
        assert not estado.entrando
        assert eventos == [f"redirect:{rota}"]


def test_login_recusado_mostra_mensagem_da_api_e_nao_guarda_token() -> None:
    estado = EstadoFalso()
    eventos = _executar_login(estado, Resposta(401, {"message": "E-mail ou senha inválidos"}))
    assert estado.token == ""
    assert estado.mensagem == "E-mail ou senha inválidos"
    assert not estado.entrando
    assert eventos == []


def test_login_sem_configuracao_avisa_e_nao_chama_api() -> None:
    estado = EstadoFalso()
    with patch.dict("os.environ", {"XANO_AUTH_API_URL": ""}, clear=False), patch(REQUISICAO) as requisicao:
        list(estado.entrar({"email": "a@b.c", "senha": "x"}))
    requisicao.assert_not_called()
    assert "XANO_AUTH_API_URL" in estado.mensagem
    assert not estado.entrando


def test_guarda_sem_token_vai_para_o_login_sem_chamar_api() -> None:
    estado = EstadoFalso()
    with patch(REQUISICAO) as requisicao, patch(REDIRECT, side_effect=lambda rota: rota):
        assert estado.verificar_sessao("RECEPCAO_TRIAGEM") == "/login"
    requisicao.assert_not_called()


def test_guarda_com_token_expirado_limpa_sessao_e_avisa() -> None:
    estado = EstadoFalso(token="vencido")
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(
        REQUISICAO, return_value=Resposta(401, {"message": "Invalid token."})
    ) as requisicao, patch(REDIRECT, side_effect=lambda rota: rota):
        assert estado.verificar_sessao("MEDICO") == "/login"
    assert requisicao.call_args.kwargs["headers"] == {"Authorization": "Bearer vencido"}
    assert estado.token == ""
    assert estado.perfil == ""
    assert estado.mensagem == "Sua sessão expirou. Faça login novamente."


def test_guarda_com_perfil_errado_redireciona_para_a_propria_area() -> None:
    estado = EstadoFalso(token="tok")
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(
        REQUISICAO, return_value=Resposta(200, {"id": 1, "nome": "Bia", "perfil": "MEDICO"})
    ), patch(REDIRECT, side_effect=lambda rota: rota):
        assert estado.verificar_sessao("RECEPCAO_TRIAGEM") == "/medico"
    assert estado.perfil == "MEDICO"


def test_guarda_com_perfil_certo_libera_a_pagina() -> None:
    estado = EstadoFalso(token="tok")
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(
        REQUISICAO, return_value=Resposta(200, {"id": 1, "nome": "Ana", "perfil": "RECEPCAO_TRIAGEM"})
    ):
        assert estado.verificar_sessao("RECEPCAO_TRIAGEM") is None
    assert estado.nome == "Ana"


def test_raiz_leva_usuario_logado_para_a_sua_area() -> None:
    estado = EstadoFalso(token="tok")
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(
        REQUISICAO, return_value=Resposta(200, {"id": 1, "nome": "Caio", "perfil": "ADMINISTRADOR"})
    ), patch(REDIRECT, side_effect=lambda rota: rota):
        assert estado.ir_para_inicio() == "/admin"


def test_sair_encerra_sessao_na_api_e_descarta_token() -> None:
    estado = EstadoFalso(token="tok")
    estado.nome = "Ana"
    estado.perfil = "RECEPCAO_TRIAGEM"
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(
        REQUISICAO, return_value=Resposta(200, {"encerrada": True})
    ) as requisicao, patch(REDIRECT, side_effect=lambda rota: rota):
        assert estado.sair() == "/login"
    assert requisicao.call_args.args[:2] == ("POST", "https://auth.test/auth/logout")
    assert estado.token == ""
    assert estado.nome == ""
    assert estado.perfil == ""


def test_sair_descarta_token_mesmo_sem_conexao() -> None:
    estado = EstadoFalso(token="tok")
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(
        REQUISICAO, side_effect=httpx.ConnectError("offline")
    ), patch(REDIRECT, side_effect=lambda rota: rota):
        assert estado.sair() == "/login"
    assert estado.token == ""


class TestAuthState(unittest.TestCase):
    """Compatível tanto com unittest quanto com pytest."""

    def test_login_valido(self) -> None:
        test_login_valido_guarda_token_e_vai_para_a_area_do_perfil()

    def test_login_recusado(self) -> None:
        test_login_recusado_mostra_mensagem_da_api_e_nao_guarda_token()

    def test_login_sem_configuracao(self) -> None:
        test_login_sem_configuracao_avisa_e_nao_chama_api()

    def test_guarda_sem_token(self) -> None:
        test_guarda_sem_token_vai_para_o_login_sem_chamar_api()

    def test_guarda_token_expirado(self) -> None:
        test_guarda_com_token_expirado_limpa_sessao_e_avisa()

    def test_guarda_perfil_errado(self) -> None:
        test_guarda_com_perfil_errado_redireciona_para_a_propria_area()

    def test_guarda_perfil_certo(self) -> None:
        test_guarda_com_perfil_certo_libera_a_pagina()

    def test_raiz(self) -> None:
        test_raiz_leva_usuario_logado_para_a_sua_area()

    def test_sair(self) -> None:
        test_sair_encerra_sessao_na_api_e_descarta_token()

    def test_sair_sem_conexao(self) -> None:
        test_sair_descarta_token_mesmo_sem_conexao()

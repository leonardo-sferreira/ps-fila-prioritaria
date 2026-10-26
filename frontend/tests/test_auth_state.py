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
    _postar = AuthState._postar
    _aguardar_reenvio = AuthState._aguardar_reenvio
    entrar = AuthState.entrar.fn
    verificar_codigo = AuthState.verificar_codigo.fn
    reenviar_codigo = AuthState.reenviar_codigo.fn
    exigir_login_pendente = AuthState.exigir_login_pendente.fn
    voltar_ao_login = AuthState.voltar_ao_login.fn
    verificar_sessao = AuthState.verificar_sessao.fn
    ir_para_inicio = AuthState.ir_para_inicio.fn
    _sair = AuthState._sair
    sair = AuthState.sair.fn
    sair_por_inatividade = AuthState.sair_por_inatividade.fn

    def __init__(self, token: str = "") -> None:
        self.token = token
        self.nome = ""
        self.perfil = ""
        self.entrando = False
        self.mensagem = ""
        self.aviso = ""
        self.email_pendente = ""
        self.segundos_reenvio = 0
        self.inatividade_segundos = 0


def _executar(estado: EstadoFalso, handler, resposta: Resposta, *args: object) -> tuple[list[object], object]:
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(REQUISICAO, return_value=resposta) as requisicao, patch(
        REDIRECT, side_effect=lambda rota: f"redirect:{rota}"
    ):
        eventos = [evento for evento in handler(estado, *args) if evento]
    return eventos, requisicao


def _executar_login(estado: EstadoFalso, resposta: Resposta) -> list[object]:
    eventos, requisicao = _executar(estado, EstadoFalso.entrar, resposta, {"email": " Ana@PS.com.br ", "senha": "segredo123"})
    assert requisicao.call_args.args[:2] == ("POST", "https://auth.test/auth/login")
    assert requisicao.call_args.kwargs["json"] == {"email": "ana@ps.com.br", "senha": "segredo123"}
    return eventos


def test_senha_correta_vai_para_o_codigo_sem_token_e_sem_guardar_a_senha() -> None:
    estado = EstadoFalso()
    eventos = _executar_login(estado, Resposta(200, {"codigo_enviado": True, "reenvio_em_segundos": 60}))
    assert estado.token == ""
    assert estado.email_pendente == "ana@ps.com.br"
    assert estado.segundos_reenvio == 60
    assert "segredo123" not in vars(estado).values()
    assert not estado.entrando
    assert eventos == ["redirect:/login/codigo", AuthState.contar_reenvio]


def test_login_recusado_mostra_mensagem_da_api_e_nao_guarda_token() -> None:
    estado = EstadoFalso()
    eventos = _executar_login(estado, Resposta(401, {"message": "E-mail ou senha inválidos"}))
    assert estado.token == ""
    assert estado.email_pendente == ""
    assert estado.mensagem == "E-mail ou senha inválidos"
    assert not estado.entrando
    assert eventos == []


def test_codigo_correto_guarda_token_e_vai_para_a_area_do_perfil() -> None:
    for perfil, rota in (("RECEPCAO_TRIAGEM", "/recepcao"), ("MEDICO", "/medico"), ("ADMINISTRADOR", "/admin")):
        estado = EstadoFalso()
        estado.email_pendente = "ana@ps.com.br"
        eventos, requisicao = _executar(
            estado, EstadoFalso.verificar_codigo, Resposta(200, {"token": "tok", "nome": "Ana", "perfil": perfil}), {"codigo": " 123456 "}
        )
        assert requisicao.call_args.args[:2] == ("POST", "https://auth.test/auth/login/verificar")
        assert requisicao.call_args.kwargs["json"] == {"email": "ana@ps.com.br", "codigo": "123456"}
        assert estado.token == "tok"
        assert estado.nome == "Ana"
        assert estado.perfil == perfil
        assert estado.email_pendente == ""
        assert not estado.entrando
        assert eventos == [f"redirect:{rota}"]


def test_codigo_recusado_mostra_mensagem_e_nao_guarda_token() -> None:
    estado = EstadoFalso()
    estado.email_pendente = "ana@ps.com.br"
    eventos, _ = _executar(estado, EstadoFalso.verificar_codigo, Resposta(401, {"message": "Código inválido ou expirado"}), {"codigo": "000000"})
    assert estado.token == ""
    assert estado.email_pendente == "ana@ps.com.br"
    assert estado.mensagem == "Código inválido ou expirado"
    assert not estado.entrando
    assert eventos == []


def test_reenvio_aceito_avisa_e_reinicia_o_contador() -> None:
    estado = EstadoFalso()
    estado.email_pendente = "ana@ps.com.br"
    eventos, requisicao = _executar(estado, EstadoFalso.reenviar_codigo, Resposta(200, {"codigo_enviado": True, "reenvio_em_segundos": 60}))
    assert requisicao.call_args.args[:2] == ("POST", "https://auth.test/auth/login/reenviar")
    assert requisicao.call_args.kwargs["json"] == {"email": "ana@ps.com.br"}
    assert estado.aviso == "Enviamos um novo código para o seu e-mail."
    assert estado.segundos_reenvio == 60
    assert eventos == [AuthState.contar_reenvio]


def test_reenvio_cedo_demais_mostra_o_tempo_que_falta() -> None:
    estado = EstadoFalso()
    estado.email_pendente = "ana@ps.com.br"
    eventos, _ = _executar(estado, EstadoFalso.reenviar_codigo, Resposta(429, {"message": "Aguarde 12 segundos para pedir um novo código."}))
    assert estado.mensagem == "Aguarde 12 segundos para pedir um novo código."
    assert estado.email_pendente == "ana@ps.com.br"
    assert eventos == []


def test_reenvio_sem_login_pendente_volta_ao_login() -> None:
    estado = EstadoFalso()
    estado.email_pendente = "ana@ps.com.br"
    mensagem = "Não foi possível reenviar o código. Faça login novamente."
    eventos, _ = _executar(estado, EstadoFalso.reenviar_codigo, Resposta(403, {"message": mensagem}))
    assert estado.email_pendente == ""
    assert estado.mensagem == mensagem
    assert eventos == ["redirect:/login"]


def test_tela_do_codigo_sem_primeira_etapa_volta_ao_login() -> None:
    estado = EstadoFalso()
    with patch(REDIRECT, side_effect=lambda rota: rota):
        assert estado.exigir_login_pendente() == "/login"
        estado.email_pendente = "ana@ps.com.br"
        assert estado.exigir_login_pendente() is None
        assert estado.voltar_ao_login() == "/login"
    assert estado.email_pendente == ""


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


def test_guarda_guarda_o_tempo_de_inatividade_vindo_do_auth_me() -> None:
    estado = EstadoFalso(token="tok")
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(
        REQUISICAO, return_value=Resposta(200, {"id": 1, "nome": "Ana", "perfil": "RECEPCAO_TRIAGEM", "inatividade_segundos": 3600})
    ):
        assert estado.verificar_sessao("RECEPCAO_TRIAGEM") is None
    assert estado.inatividade_segundos == 3600


def test_saida_por_inatividade_encerra_a_sessao_e_avisa_no_login() -> None:
    estado = EstadoFalso(token="tok")
    estado.nome = "Ana"
    estado.perfil = "RECEPCAO_TRIAGEM"
    estado.inatividade_segundos = 3600
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(
        REQUISICAO, return_value=Resposta(200, {"encerrada": True})
    ) as requisicao, patch(REDIRECT, side_effect=lambda rota: rota):
        assert estado.sair_por_inatividade() == "/login"
    assert requisicao.call_args.args[:2] == ("POST", "https://auth.test/auth/logout")
    assert requisicao.call_args.kwargs["headers"] == {"Authorization": "Bearer tok"}
    assert estado.token == estado.nome == estado.perfil == ""
    assert estado.inatividade_segundos == 0
    assert estado.mensagem == "Sua sessão foi encerrada por inatividade."


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

    def test_senha_correta(self) -> None:
        test_senha_correta_vai_para_o_codigo_sem_token_e_sem_guardar_a_senha()

    def test_codigo_correto(self) -> None:
        test_codigo_correto_guarda_token_e_vai_para_a_area_do_perfil()

    def test_codigo_recusado(self) -> None:
        test_codigo_recusado_mostra_mensagem_e_nao_guarda_token()

    def test_reenvio_aceito(self) -> None:
        test_reenvio_aceito_avisa_e_reinicia_o_contador()

    def test_reenvio_cedo(self) -> None:
        test_reenvio_cedo_demais_mostra_o_tempo_que_falta()

    def test_reenvio_sem_pendente(self) -> None:
        test_reenvio_sem_login_pendente_volta_ao_login()

    def test_tela_do_codigo(self) -> None:
        test_tela_do_codigo_sem_primeira_etapa_volta_ao_login()

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

    def test_tempo_de_inatividade(self) -> None:
        test_guarda_guarda_o_tempo_de_inatividade_vindo_do_auth_me()

    def test_saida_por_inatividade(self) -> None:
        test_saida_por_inatividade_encerra_a_sessao_e_avisa_no_login()

    def test_raiz(self) -> None:
        test_raiz_leva_usuario_logado_para_a_sua_area()

    def test_sair(self) -> None:
        test_sair_encerra_sessao_na_api_e_descarta_token()

    def test_sair_sem_conexao(self) -> None:
        test_sair_descarta_token_mesmo_sem_conexao()

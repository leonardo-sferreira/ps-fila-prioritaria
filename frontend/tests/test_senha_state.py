"""Regressões de estado do fluxo "Esqueci minha senha" (telas A1 a A4)."""

import unittest
from unittest.mock import patch

from ps_fila_prioritaria.ps_fila_prioritaria import SenhaState

REQUISICAO = "ps_fila_prioritaria.api.httpx.request"
REDIRECT = "ps_fila_prioritaria.ps_fila_prioritaria.rx.redirect"
AMBIENTE = {"XANO_AUTH_API_URL": "https://auth.test"}
GENERICA = "Se o e-mail estiver cadastrado, enviamos um código"


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

    _limpar = SenhaState._limpar
    solicitar_codigo = SenhaState.solicitar_codigo.fn
    reenviar_codigo = SenhaState.reenviar_codigo.fn
    verificar_codigo = SenhaState.verificar_codigo.fn
    redefinir = SenhaState.redefinir.fn
    exigir_email = SenhaState.exigir_email.fn
    exigir_codigo = SenhaState.exigir_codigo.fn
    voltar_ao_login = SenhaState.voltar_ao_login.fn

    def __init__(self, email: str = "", codigo: str = "") -> None:
        self.email = email
        self.codigo = codigo
        self.enviando = False
        self.mensagem = ""
        self.aviso = ""
        self.segundos_reenvio = 0


def _executar(estado: EstadoFalso, handler, resposta: Resposta | None, *args: object) -> tuple[list[object], object]:
    with patch.dict("os.environ", AMBIENTE, clear=False), patch(REQUISICAO, return_value=resposta) as requisicao, patch(
        REDIRECT, side_effect=lambda rota: f"redirect:{rota}"
    ):
        eventos = [evento for evento in handler(estado, *args) if evento]
    return eventos, requisicao


def test_solicitar_guarda_o_email_e_vai_para_o_codigo() -> None:
    estado = EstadoFalso()
    eventos, requisicao = _executar(
        estado, EstadoFalso.solicitar_codigo, Resposta(200, {"mensagem": GENERICA, "reenvio_em_segundos": 60}), {"email": " Ana@PS.com.br "}
    )
    assert requisicao.call_args.args[:2] == ("POST", "https://auth.test/auth/senha/solicitar")
    assert requisicao.call_args.kwargs["json"] == {"email": "ana@ps.com.br"}
    assert estado.email == "ana@ps.com.br"
    assert estado.segundos_reenvio == 60
    assert not estado.enviando
    assert eventos == ["redirect:/senha/codigo", SenhaState.contar_reenvio]


def test_solicitar_cedo_demais_fica_na_tela_com_a_mensagem() -> None:
    estado = EstadoFalso()
    eventos, _ = _executar(
        estado, EstadoFalso.solicitar_codigo, Resposta(429, {"message": "Aguarde 30 segundos para pedir um novo código."}), {"email": "a@b.c"}
    )
    assert estado.mensagem == "Aguarde 30 segundos para pedir um novo código."
    assert estado.email == ""
    assert eventos == []


def test_reenvio_avisa_e_reinicia_o_contador() -> None:
    estado = EstadoFalso(email="ana@ps.com.br")
    eventos, requisicao = _executar(estado, EstadoFalso.reenviar_codigo, Resposta(200, {"mensagem": GENERICA, "reenvio_em_segundos": 60}))
    assert requisicao.call_args.kwargs["json"] == {"email": "ana@ps.com.br"}
    assert estado.aviso == "Se o e-mail estiver cadastrado, enviamos um novo código."
    assert estado.segundos_reenvio == 60
    assert eventos == [SenhaState.contar_reenvio]


def test_codigo_correto_guarda_o_codigo_e_vai_para_a_nova_senha() -> None:
    estado = EstadoFalso(email="ana@ps.com.br")
    eventos, requisicao = _executar(estado, EstadoFalso.verificar_codigo, Resposta(200, {"codigo_valido": True}), {"codigo": " 123456 "})
    assert requisicao.call_args.args[:2] == ("POST", "https://auth.test/auth/senha/verificar")
    assert requisicao.call_args.kwargs["json"] == {"email": "ana@ps.com.br", "codigo": "123456"}
    assert estado.codigo == "123456"
    assert eventos == ["redirect:/senha/nova"]


def test_codigo_invalido_mostra_a_mensagem_da_tela_a2b() -> None:
    estado = EstadoFalso(email="ana@ps.com.br")
    eventos, _ = _executar(estado, EstadoFalso.verificar_codigo, Resposta(401, {"message": "Código inválido ou expirado"}), {"codigo": "000000"})
    assert estado.mensagem == "Código inválido ou expirado"
    assert estado.codigo == ""
    assert not estado.enviando
    assert eventos == []


def test_senhas_diferentes_sao_recusadas_sem_chamar_a_api() -> None:
    estado = EstadoFalso(email="ana@ps.com.br", codigo="123456")
    eventos, requisicao = _executar(estado, EstadoFalso.redefinir, None, {"nova_senha": "segredo123", "confirmacao": "segredo124"})
    requisicao.assert_not_called()
    assert estado.mensagem == "As duas senhas devem ser iguais."
    assert eventos == []


def test_nova_senha_valida_limpa_o_fluxo_e_mostra_o_sucesso() -> None:
    estado = EstadoFalso(email="ana@ps.com.br", codigo="123456")
    eventos, requisicao = _executar(
        estado, EstadoFalso.redefinir, Resposta(200, {"senha_redefinida": True}), {"nova_senha": "segredo123", "confirmacao": "segredo123"}
    )
    assert requisicao.call_args.args[:2] == ("POST", "https://auth.test/auth/senha/redefinir")
    assert requisicao.call_args.kwargs["json"] == {"email": "ana@ps.com.br", "codigo": "123456", "nova_senha": "segredo123"}
    assert estado.email == estado.codigo == ""
    assert eventos == ["redirect:/senha/sucesso"]


def test_nova_senha_curta_mostra_a_mensagem_da_api_e_mantem_o_codigo() -> None:
    estado = EstadoFalso(email="ana@ps.com.br", codigo="123456")
    eventos, _ = _executar(
        estado,
        EstadoFalso.redefinir,
        Resposta(400, {"message": "A nova senha deve ter pelo menos 8 caracteres."}),
        {"nova_senha": "1234567", "confirmacao": "1234567"},
    )
    assert estado.mensagem == "A nova senha deve ter pelo menos 8 caracteres."
    assert estado.codigo == "123456"
    assert eventos == []


def test_guardas_das_telas_voltam_para_o_inicio_do_fluxo() -> None:
    with patch(REDIRECT, side_effect=lambda rota: rota):
        assert EstadoFalso().exigir_email() == "/senha"
        assert EstadoFalso(email="ana@ps.com.br").exigir_email() is None
        assert EstadoFalso(email="ana@ps.com.br").exigir_codigo() == "/senha"
        assert EstadoFalso(email="ana@ps.com.br", codigo="123456").exigir_codigo() is None
        estado = EstadoFalso(email="ana@ps.com.br", codigo="123456")
        assert estado.voltar_ao_login() == "/login"
    assert estado.email == estado.codigo == ""


class TestSenhaState(unittest.TestCase):
    """Compatível tanto com unittest quanto com pytest."""

    def test_solicitar(self) -> None:
        test_solicitar_guarda_o_email_e_vai_para_o_codigo()

    def test_solicitar_cedo(self) -> None:
        test_solicitar_cedo_demais_fica_na_tela_com_a_mensagem()

    def test_reenvio(self) -> None:
        test_reenvio_avisa_e_reinicia_o_contador()

    def test_codigo_correto(self) -> None:
        test_codigo_correto_guarda_o_codigo_e_vai_para_a_nova_senha()

    def test_codigo_invalido(self) -> None:
        test_codigo_invalido_mostra_a_mensagem_da_tela_a2b()

    def test_senhas_diferentes(self) -> None:
        test_senhas_diferentes_sao_recusadas_sem_chamar_a_api()

    def test_nova_senha_valida(self) -> None:
        test_nova_senha_valida_limpa_o_fluxo_e_mostra_o_sucesso()

    def test_nova_senha_curta(self) -> None:
        test_nova_senha_curta_mostra_a_mensagem_da_api_e_mantem_o_codigo()

    def test_guardas(self) -> None:
        test_guardas_das_telas_voltam_para_o_inicio_do_fluxo()

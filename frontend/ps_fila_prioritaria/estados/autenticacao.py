"""Estados de login, código de acesso, redefinição de senha e visibilidade da senha."""

from typing import Any

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import (
    _contar_reenvio,
    _mascarar_email,
    _mensagem_erro,
    _postar_publico,
    _segundos_reenvio,
    _texto_reenvio,
)


# Área inicial de cada perfil (design D7).
AREA_POR_PERFIL = {
    "RECEPCAO_TRIAGEM": "/recepcao",
    "MEDICO": "/medico",
    "ADMINISTRADOR": "/admin",
}


class AuthState(rx.State):
    """Sessão da equipe no navegador. A autorização real é feita no Xano (design D3)."""

    token: str = rx.LocalStorage("", name="ps_token")
    nome: str = ""
    perfil: str = ""
    entrando: bool = False
    mensagem: str = ""
    aviso: str = ""
    email_pendente: str = ""
    segundos_reenvio: int = 0
    contando: bool = False
    # Vem do auth/me (INATIVIDADE_SEGUNDOS no Xano); 0 enquanto a sessão não foi conferida.
    inatividade_segundos: int = 0

    def _encerrar_sessao_local(self, mensagem: str = "") -> None:
        self.token = ""
        self.nome = ""
        self.perfil = ""
        self.mensagem = mensagem

    def _validar_sessao(self, perfil_exigido: str) -> rx.event.EventSpec | None:
        """Confere o token com auth/me; devolve o redirecionamento necessário ou None se pode seguir."""
        if not self.token:
            return rx.redirect("/login")
        try:
            resposta = api.requisitar("GET", "XANO_AUTH_API_URL", "/auth/me", token=self.token)
        except api.ConfiguracaoAusente:
            self.mensagem = "Configure XANO_AUTH_API_URL para conectar o login à API do PS."
            return rx.redirect("/login")
        except httpx.RequestError:
            self.mensagem = "Não foi possível conectar à API de autenticação."
            return rx.redirect("/login")

        if resposta.status_code == 401:
            self._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
            return rx.redirect("/login")
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return rx.redirect("/login")

        usuario = resposta.json()
        self.nome = str(usuario.get("nome", ""))
        self.perfil = str(usuario.get("perfil", ""))
        self.inatividade_segundos = int(usuario.get("inatividade_segundos") or 0)
        if perfil_exigido and self.perfil != perfil_exigido:
            return rx.redirect(AREA_POR_PERFIL.get(self.perfil, "/login"))
        return None

    @rx.var
    def email_exibido(self) -> str:
        return _mascarar_email(self.email_pendente)

    @rx.var
    def texto_reenvio(self) -> str:
        return _texto_reenvio(self.segundos_reenvio)

    def _postar(self, caminho: str, corpo: dict[str, Any]) -> httpx.Response | None:
        return _postar_publico(self, caminho, corpo)

    def _aguardar_reenvio(self, resposta: httpx.Response) -> None:
        self.segundos_reenvio = _segundos_reenvio(resposta)

    def entrar(self, dados: dict[str, Any]):
        """Primeira etapa: e-mail e senha. Com sucesso, o código segue por e-mail (design D13)."""
        self.mensagem = ""
        self.entrando = True
        yield
        email = str(dados.get("email", "")).strip().lower()
        resposta = self._postar("/auth/login", {"email": email, "senha": dados.get("senha", "")})
        self.entrando = False
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        # Só o e-mail fica guardado entre as etapas; a senha não.
        self.email_pendente = email
        self.aviso = ""
        self._aguardar_reenvio(resposta)
        yield rx.redirect("/login/codigo")
        yield AuthState.contar_reenvio

    def verificar_codigo(self, dados: dict[str, Any]):
        """Segunda etapa: com o código conferido, guarda o token e leva à área do perfil."""
        self.mensagem = ""
        self.aviso = ""
        self.entrando = True
        yield
        resposta = self._postar("/auth/login/verificar", {"email": self.email_pendente, "codigo": str(dados.get("codigo", "")).strip()})
        self.entrando = False
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        sessao = resposta.json()
        self.token = str(sessao["token"])
        self.nome = str(sessao.get("nome", ""))
        self.perfil = str(sessao.get("perfil", ""))
        self.email_pendente = ""
        self.segundos_reenvio = 0
        yield rx.redirect(AREA_POR_PERFIL.get(self.perfil, "/login"))

    def reenviar_codigo(self):
        self.mensagem = ""
        self.aviso = ""
        resposta = self._postar("/auth/login/reenviar", {"email": self.email_pendente})
        if resposta is None:
            return
        if resposta.status_code == 403:
            # Primeiro passo vencido: volta ao login para informar a senha de novo.
            self.email_pendente = ""
            self.mensagem = _mensagem_erro(resposta)
            yield rx.redirect("/login")
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        self.aviso = "Enviamos um novo código para o seu e-mail."
        self._aguardar_reenvio(resposta)
        yield AuthState.contar_reenvio

    @rx.event(background=True)
    async def contar_reenvio(self):
        await _contar_reenvio(self)

    def exigir_login_pendente(self) -> rx.event.EventSpec | None:
        """Guarda da tela do código: sem a primeira etapa feita, volta ao login."""
        if not self.email_pendente:
            return rx.redirect("/login")
        return None

    def voltar_ao_login(self) -> rx.event.EventSpec:
        self.email_pendente = ""
        self.mensagem = ""
        self.aviso = ""
        return rx.redirect("/login")

    def verificar_sessao(self, perfil_exigido: str = "") -> rx.event.EventSpec | None:
        """Guarda de rota usada no on_load das páginas internas."""
        return self._validar_sessao(perfil_exigido)

    def ir_para_inicio(self) -> rx.event.EventSpec:
        redirecionamento = self._validar_sessao("")
        if redirecionamento is not None:
            return redirecionamento
        return rx.redirect(AREA_POR_PERFIL.get(self.perfil, "/login"))

    def _sair(self, mensagem: str = "") -> rx.event.EventSpec:
        if self.token:
            try:
                api.requisitar("POST", "XANO_AUTH_API_URL", "/auth/logout", token=self.token)
            except (api.ConfiguracaoAusente, httpx.RequestError):
                pass  # O token é descartado mesmo se a API não responder.
        self._encerrar_sessao_local(mensagem)
        self.inatividade_segundos = 0
        return rx.redirect("/login")

    def sair(self) -> rx.event.EventSpec:
        return self._sair()

    def sair_por_inatividade(self) -> rx.event.EventSpec:
        """Chamado pela página /sair/inatividade quando o contador da tela estoura (add-privacidade, D5)."""
        return self._sair("Sua sessão foi encerrada por inatividade.")


class SenhaState(rx.State):
    """"Esqueci minha senha" (telas A1 a A4 do Figma). As regras do código ficam no Xano (design D12)."""

    email: str = ""
    codigo: str = ""
    enviando: bool = False
    mensagem: str = ""
    aviso: str = ""
    segundos_reenvio: int = 0
    contando: bool = False

    @rx.var
    def email_exibido(self) -> str:
        return _mascarar_email(self.email)

    @rx.var
    def texto_reenvio(self) -> str:
        return _texto_reenvio(self.segundos_reenvio)

    def _limpar(self) -> None:
        self.email = ""
        self.codigo = ""
        self.mensagem = ""
        self.aviso = ""

    def iniciar(self) -> None:
        self.mensagem = ""
        self.aviso = ""

    def solicitar_codigo(self, dados: dict[str, Any]):
        """A1: a resposta é a mesma para qualquer e-mail; só usuário ativo recebe o código."""
        self.mensagem = ""
        self.enviando = True
        yield
        email = str(dados.get("email", "")).strip().lower()
        resposta = _postar_publico(self, "/auth/senha/solicitar", {"email": email})
        self.enviando = False
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        self.email = email
        self.codigo = ""
        self.aviso = ""
        self.segundos_reenvio = _segundos_reenvio(resposta)
        yield rx.redirect("/senha/codigo")
        yield SenhaState.contar_reenvio

    def reenviar_codigo(self):
        self.mensagem = ""
        self.aviso = ""
        resposta = _postar_publico(self, "/auth/senha/solicitar", {"email": self.email})
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        self.aviso = "Se o e-mail estiver cadastrado, enviamos um novo código."
        self.segundos_reenvio = _segundos_reenvio(resposta)
        yield SenhaState.contar_reenvio

    @rx.event(background=True)
    async def contar_reenvio(self):
        await _contar_reenvio(self)

    def verificar_codigo(self, dados: dict[str, Any]):
        """A2: confere o código sem usá-lo; o uso definitivo é na troca da senha (A3)."""
        self.mensagem = ""
        self.aviso = ""
        self.enviando = True
        yield
        codigo = str(dados.get("codigo", "")).strip()
        resposta = _postar_publico(self, "/auth/senha/verificar", {"email": self.email, "codigo": codigo})
        self.enviando = False
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)  # A2b
            return

        self.codigo = codigo
        yield rx.redirect("/senha/nova")

    def redefinir(self, dados: dict[str, Any]):
        """A3: a confirmação é só da tela; o mínimo de 8 caracteres é validado no Xano."""
        self.mensagem = ""
        nova_senha = str(dados.get("nova_senha", ""))
        if nova_senha != str(dados.get("confirmacao", "")):
            self.mensagem = "As duas senhas devem ser iguais."
            return
        self.enviando = True
        yield
        resposta = _postar_publico(
            self, "/auth/senha/redefinir", {"email": self.email, "codigo": self.codigo, "nova_senha": nova_senha}
        )
        self.enviando = False
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        self._limpar()
        self.segundos_reenvio = 0
        yield rx.redirect("/senha/sucesso")

    def exigir_email(self) -> rx.event.EventSpec | None:
        """Guarda da tela A2: sem o pedido feito na A1, volta para ela."""
        if not self.email:
            return rx.redirect("/senha")
        return None

    def exigir_codigo(self) -> rx.event.EventSpec | None:
        """Guarda da tela A3: sem o código conferido na A2, volta para a A1."""
        if not self.email or not self.codigo:
            return rx.redirect("/senha")
        return None

    def voltar_ao_login(self) -> rx.event.EventSpec:
        self._limpar()
        return rx.redirect("/login")


class VisibilidadeSenhaState(rx.State):
    """Mostrar/ocultar a senha digitada. Só muda a aparência do campo; o valor continua no formulário."""

    login: bool = False
    nova: bool = False

    def alternar_login(self) -> None:
        self.login = not self.login

    def alternar_nova(self) -> None:
        self.nova = not self.nova

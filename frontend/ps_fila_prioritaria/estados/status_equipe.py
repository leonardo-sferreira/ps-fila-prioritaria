"""Status da própria Recepção/Triagem; persistência e autorização continuam no Xano."""

from contextlib import aclosing

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import _mensagem_erro
from ps_fila_prioritaria.estados.autenticacao import AREA_POR_PERFIL, AuthState

STATUS_RECEPCAO = {"DISPONIVEL": "Disponível", "PAUSA": "Pausa", "AUSENTE": "Ausente"}


class StatusRecepcaoState(rx.State):
    status_operacional: str = ""
    ocupado: bool = False
    erro: bool = False
    mensagem: str = ""

    @rx.var
    def status_exibido(self) -> str:
        return STATUS_RECEPCAO.get(self.status_operacional, "Não consultado")

    async def _executar(self, destino: str | None = None):
        if self.ocupado:
            return
        if destino is not None and destino not in STATUS_RECEPCAO:
            self.erro, self.mensagem = True, "Escolha Disponível, Pausa ou Ausente."
            return
        self.ocupado = True
        self.erro, self.mensagem = False, ""
        try:
            yield  # Publica o carregamento antes de acessar a API.
            auth = await self.get_state(AuthState)
            if not auth.token or auth.perfil != "RECEPCAO_TRIAGEM":
                self.status_operacional = ""
                yield rx.redirect(AREA_POR_PERFIL.get(auth.perfil, "/login") if auth.token else "/login")
                return
            if destino is not None and destino == self.status_operacional:
                return  # Evento duplicado já confirmado; não repetir a escrita.
            if destino is None:
                self.status_operacional = ""
            metodo = "GET" if destino is None else "PATCH"
            argumentos = {} if destino is None else {"json": {"status": destino}}
            try:
                resposta = api.requisitar(metodo, "XANO_AUTH_API_URL", "/me/status", token=auth.token, **argumentos)
            except api.ConfiguracaoAusente:
                self.erro, self.mensagem = True, "A API de autenticação não está configurada para consultar o status."
                return
            except httpx.TimeoutException:
                self.status_operacional = ""
                self.erro, self.mensagem = True, "Tempo de resposta excedido. Status não confirmado; atualize antes de tentar novamente."
                return
            except httpx.RequestError:
                self.status_operacional = ""
                self.erro, self.mensagem = True, "Não foi possível confirmar o status. Confira a conexão e atualize antes de tentar novamente."
                return
            if resposta.status_code == 401:
                self.status_operacional = ""
                auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
                yield rx.redirect("/login")
                return
            if resposta.status_code == 404:
                self.erro, self.mensagem = True, "Consulta de status indisponível. O GET /me/status precisa estar publicado."
                return
            if (200 <= resposta.status_code < 300 and resposta.status_code != 200) or resposta.status_code >= 500:
                self.status_operacional = ""
                self.erro, self.mensagem = True, "Status não confirmado. Atualize antes de tentar novamente."
                return
            if resposta.status_code != 200:
                self.erro, self.mensagem = True, (
                    "Acesso negado ao status da Recepção/Triagem." if resposta.status_code == 403
                    else _mensagem_erro(resposta)
                )
                return
            try:
                corpo = resposta.json()
                if not isinstance(corpo, dict) or not isinstance(corpo.get("status"), str) or corpo["status"] not in STATUS_RECEPCAO:
                    raise ValueError("Confirmação inválida")
                if destino is not None and corpo["status"] != destino:
                    raise ValueError("Status não corresponde ao solicitado")
            except (ValueError, TypeError):
                self.status_operacional = ""
                self.erro, self.mensagem = True, "O serviço retornou um status inesperado. Atualize antes de tentar novamente."
                return
            self.status_operacional = corpo["status"]
            if destino is not None:
                self.mensagem = "Status atualizado para " + STATUS_RECEPCAO[destino] + "."
        finally:
            self.ocupado = False

    async def carregar(self):
        async with aclosing(self._executar()) as eventos:
            async for evento in eventos:
                yield evento

    async def definir_status(self, status: str):
        # EM_ATENDIMENTO é automático no Médico e nunca é uma opção manual.
        if self.ocupado:
            return
        if not isinstance(status, str) or status not in STATUS_RECEPCAO:
            self.erro, self.mensagem = True, "Escolha Disponível, Pausa ou Ausente."
            return
        async with aclosing(self._executar(status)) as eventos:
            async for evento in eventos:
                yield evento

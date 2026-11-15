"""Status operacional da Recepção/Triagem (add-acompanhamento-administrador, D5; spec status-equipe).

A pessoa escolhe Disponível, Pausa ou Ausente; "Em atendimento" não é escolhido à mão. O status atual vem de
auth/me (sessão ativa) e a troca vai para PATCH me/status. As regras ficam no Xano.
"""

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import _mensagem_erro
from ps_fila_prioritaria.estados.autenticacao import AuthState

NOME_STATUS = {"DISPONIVEL": "Disponível", "EM_ATENDIMENTO": "Em atendimento", "PAUSA": "Pausa", "AUSENTE": "Ausente"}
OPCOES_STATUS = [("DISPONIVEL", "Disponível"), ("PAUSA", "Pausa"), ("AUSENTE", "Ausente")]


class StatusEquipeState(rx.State):
    status: str = ""
    ocupado: bool = False
    mensagem: str = ""
    erro: bool = False

    @rx.var
    def status_exibido(self) -> str:
        return NOME_STATUS.get(self.status, "—")

    async def _requisitar(self, metodo: str, caminho: str, **kwargs) -> httpx.Response | None:
        auth = await self.get_state(AuthState)
        try:
            resposta = api.requisitar(metodo, "XANO_AUTH_API_URL", caminho, token=auth.token, **kwargs)
        except (api.ConfiguracaoAusente, httpx.RequestError):
            self.erro, self.mensagem = True, "Não foi possível consultar o status. Confira a conexão."
            return None
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
        return resposta

    async def carregar(self) -> None:
        resposta = await self._requisitar("GET", "/auth/me")
        if resposta is not None and resposta.is_success:
            self.status = str((resposta.json() or {}).get("status_operacional") or "")

    async def definir(self, status: str) -> None:
        if self.ocupado or status == self.status:
            return
        self.ocupado, self.erro, self.mensagem = True, False, ""
        try:
            resposta = await self._requisitar("PATCH", "/me/status", json={"status": status})
            if resposta is None:
                return
            if not resposta.is_success:
                self.erro, self.mensagem = True, _mensagem_erro(resposta)
                return
            self.status = str((resposta.json() or {}).get("status") or status)
            self.mensagem = f"Status: {NOME_STATUS.get(self.status, self.status)}."
        finally:
            self.ocupado = False

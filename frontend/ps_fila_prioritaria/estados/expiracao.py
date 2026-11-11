"""Estado do cartão "Fichas e tickets parados" do Administrador (add-expiracao-24h, D6)."""

from typing import Any

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import _data_hora_brasilia, _mensagem_erro, formatar_ticket
from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.fichas_do_dia import NOME_SITUACAO

NOME_SITUACAO_TICKET = {"AGUARDANDO": "Aguardando", "CHAMADO": "Chamado"}


def _linha_ficha(ficha: dict[str, Any]) -> dict[str, Any]:
    status = str(ficha.get("status") or "")
    return {
        "id": int(ficha.get("id") or 0),
        "identificacao": str(ficha.get("senha") or "Sem senha"),
        "situacao": NOME_SITUACAO.get(status, status or "—"),
        "horario": _data_hora_brasilia(ficha.get("chegada_em")),
    }


def _linha_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    status = str(ticket.get("status") or "")
    return {
        "id": int(ticket.get("id") or 0),
        "identificacao": formatar_ticket(ticket.get("tipo"), ticket.get("numero")),
        "situacao": NOME_SITUACAO_TICKET.get(status, status or "—"),
        "horario": _data_hora_brasilia(ticket.get("emitido_em")),
    }


class ExpiracaoState(rx.State):
    """Prévia e dispensa; o servidor recalcula o que está parado no momento da dispensa (D1)."""

    fichas: list[dict[str, Any]] = []
    tickets: list[dict[str, Any]] = []
    horas: int = 0
    carregando: bool = False
    dispensando: bool = False
    confirmacao_aberta: bool = False
    mensagem: str = ""
    erro: bool = False

    @rx.var
    def total(self) -> int:
        return len(self.fichas) + len(self.tickets)

    @rx.var
    def texto_confirmacao(self) -> str:
        return f"Encerrar {len(self.fichas)} ficha(s) e {len(self.tickets)} ticket(s) como desistência?"

    def set_confirmacao_aberta(self, aberta: bool) -> None:
        self.confirmacao_aberta = bool(aberta)

    async def _requisitar(self, metodo: str) -> dict[str, Any] | None:
        auth = await self.get_state(AuthState)
        try:
            resposta = api.requisitar(metodo, "XANO_TRIAGEM_API_URL", "/expiracao", token=auth.token)
        except (api.ConfiguracaoAusente, httpx.RequestError):
            self.erro = True
            self.mensagem = "Não foi possível conectar à API."
            return None
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
        if not resposta.is_success:
            self.erro = True
            self.mensagem = _mensagem_erro(resposta)
            return None
        corpo = resposta.json()
        return corpo if isinstance(corpo, dict) else {}

    def _aplicar_resposta(self, corpo: dict[str, Any]) -> None:
        self.fichas = [_linha_ficha(ficha) for ficha in (corpo.get("fichas") or [])]
        self.tickets = [_linha_ticket(ticket) for ticket in (corpo.get("tickets") or [])]
        self.horas = int(corpo.get("horas_expiracao") or 0)

    async def carregar(self) -> None:
        """Prévia: só lista o que passou do prazo; em caso de erro mantém a última lista."""
        self.carregando = True
        try:
            corpo = await self._requisitar("GET")
        finally:
            self.carregando = False
        if corpo is None:
            return
        self._aplicar_resposta(corpo)
        self.erro = bool(corpo.get("motivo"))
        self.mensagem = str(corpo.get("motivo") or "")

    async def dispensar(self) -> None:
        """Encerra tudo o que está parado agora e recarrega a prévia."""
        if self.dispensando:
            return
        self.confirmacao_aberta = False
        self.dispensando = True
        try:
            corpo = await self._requisitar("POST")
        finally:
            self.dispensando = False
        if corpo is None:
            return
        if corpo.get("motivo"):
            self.erro = True
            self.mensagem = str(corpo["motivo"])
            return
        encerradas = len(corpo.get("fichas") or [])
        encerrados = len(corpo.get("tickets") or [])
        await self.carregar()
        if not self.erro:
            self.mensagem = f"Dispensados: {encerradas} ficha(s) e {encerrados} ticket(s)."

"""Estado do cartão "Fichas e tickets parados" do Administrador (add-expiracao-24h, D6)."""

from typing import Any

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import _data_hora_brasilia, _mensagem_erro, _timestamp_segundos, formatar_ticket
from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.fichas_do_dia import NOME_SITUACAO

NOME_SITUACAO_TICKET = {"AGUARDANDO": "Aguardando", "CHAMADO": "Chamado"}
TAMANHOS_PAGINA = ["10", "25", "50"]
ORDEM_MAIOR_TEMPO = "Maior tempo parado"
ORDEM_MENOR_TEMPO = "Menor tempo parado"
ORDENS = [ORDEM_MAIOR_TEMPO, ORDEM_MENOR_TEMPO]


def _linha_ficha(ficha: dict[str, Any]) -> dict[str, Any]:
    status = str(ficha.get("status") or "")
    return {
        "id": int(ficha.get("id") or 0),
        "identificacao": str(ficha.get("senha") or "Sem senha"),
        "tipo": "Ficha",
        "situacao": NOME_SITUACAO.get(status, status or "—"),
        "horario": _data_hora_brasilia(ficha.get("chegada_em")),
        "instante": _timestamp_segundos(ficha.get("chegada_em")) or 0,
    }


def _linha_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    status = str(ticket.get("status") or "")
    return {
        "id": int(ticket.get("id") or 0),
        "identificacao": formatar_ticket(ticket.get("tipo"), ticket.get("numero")),
        "tipo": "Ticket",
        "situacao": NOME_SITUACAO_TICKET.get(status, status or "—"),
        "horario": _data_hora_brasilia(ticket.get("emitido_em")),
        "instante": _timestamp_segundos(ticket.get("emitido_em")) or 0,
    }


def total_paginas(total: int, tamanho: int) -> int:
    return max(1, -(-total // tamanho))


def recortar_pagina(itens: list[dict[str, Any]], pagina: int, tamanho: int, ordem: str) -> list[dict[str, Any]]:
    """Ordena pelo tempo parado (maior tempo = mais antigo primeiro) e devolve só a página pedida."""
    ordenados = sorted(itens, key=lambda item: (item["instante"], item["identificacao"]), reverse=ordem == ORDEM_MENOR_TEMPO)
    pagina = min(max(1, pagina), total_paginas(len(itens), tamanho))
    inicio = (pagina - 1) * tamanho
    return ordenados[inicio : inicio + tamanho]


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
    pagina: int = 1
    tamanho_pagina: str = TAMANHOS_PAGINA[0]
    ordem: str = ORDEM_MAIOR_TEMPO

    @rx.var
    def total(self) -> int:
        return len(self.fichas) + len(self.tickets)

    @rx.var
    def total_paginas(self) -> int:
        return total_paginas(self.total, int(self.tamanho_pagina))

    @rx.var
    def itens_pagina(self) -> list[dict[str, Any]]:
        """Fichas e tickets juntos, ordenados pelo tempo parado, recortados na página atual."""
        return recortar_pagina(self.fichas + self.tickets, self.pagina, int(self.tamanho_pagina), self.ordem)

    def set_tamanho_pagina(self, tamanho: str) -> None:
        if tamanho in TAMANHOS_PAGINA:
            self.tamanho_pagina = tamanho
            self.pagina = 1

    def set_ordem(self, ordem: str) -> None:
        if ordem in ORDENS:
            self.ordem = ordem
            self.pagina = 1

    def pagina_anterior(self) -> None:
        self.pagina = max(1, self.pagina - 1)

    def proxima_pagina(self) -> None:
        self.pagina = min(total_paginas(len(self.fichas) + len(self.tickets), int(self.tamanho_pagina)), self.pagina + 1)

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
        self.pagina = 1

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

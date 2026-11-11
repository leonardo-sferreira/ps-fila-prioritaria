"""Estado da fila de pré-triagem (tickets do Totem e chamada manual)."""

import asyncio
from typing import Any

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import _hora_brasilia, _mensagem_erro, _timestamp_segundos, formatar_ticket
from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.pacientes import PacienteState


# Nome e cor de cada tipo na fila de pré-triagem (mesmas cores do Totem, tela 1/2 do Figma).
COR_SECUNDARIA_FILA = "var(--ps-secundaria)"


APARENCIA_TIPO_TICKET = {
    "PEDIATRICO": ("Pediátrico", "#6554C0"),
    "PREFERENCIAL": ("Preferencial", "#ED8B00"),
    "NORMAL": ("Normal", "#1565C0"),
}


class FilaTicketsState(rx.State):
    tickets: list[dict[str, Any]] = []
    atualizado_em: str = ""
    mensagem: str = ""
    erro: bool = False
    monitorando: bool = False

    async def _requisitar(self, metodo: str, caminho: str, **kwargs: Any) -> httpx.Response | None:
        auth = await self.get_state(AuthState)
        try:
            resposta = api.requisitar(metodo, "XANO_TRIAGEM_API_URL", caminho, token=auth.token, **kwargs)
        except (api.ConfiguracaoAusente, httpx.RequestError):
            self.erro = True
            self.mensagem = "Não foi possível conectar à fila de pré-triagem."
            return None
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
        if not resposta.is_success:
            self.erro = True
            self.mensagem = _mensagem_erro(resposta)
            return None
        return resposta

    async def carregar(self) -> None:
        resposta = await self._requisitar("GET", "/tickets")
        if resposta is not None:
            corpo = resposta.json() or {}
            self.tickets = corpo.get("tickets", []) if isinstance(corpo, dict) else corpo
            agora = _timestamp_segundos(corpo.get("agora")) if isinstance(corpo, dict) else None
            parametros = corpo if isinstance(corpo, dict) else {}
            intervalo = int(parametros.get("intervalo_segundos") or 0)
            intervalo_repeticao = int(parametros.get("intervalo_repeticao_segundos") or 0)
            tentativas_maximas = int(parametros.get("tentativas_maximas") or 0)
            for ticket in self.tickets:
                ticket.setdefault("presente", False)
                tentativas = int(ticket.get("tentativas") or 0)
                # Chamada manual (chamada-manual-pre-triagem, D1): 30 s depois da 1ª chamada, 10 s depois das seguintes.
                espera = intervalo if tentativas <= 1 else intervalo_repeticao
                chamado = _timestamp_segundos(ticket.get("chamado_em"))
                ticket["segundos_restantes"] = max(0, int(chamado + espera - agora + 0.999)) if chamado is not None and agora is not None and espera > 0 else -1
                # Sem o limite configurado, a tela oferece o botão e o Xano decide (LIMITE_DE_CHAMADAS).
                ticket["pode_chamar_novamente"] = tentativas_maximas <= 0 or tentativas < tentativas_maximas
                ticket["senha_exibida"] = formatar_ticket(ticket.get("tipo"), ticket.get("numero"))
                ticket["nome_tipo"], ticket["cor_tipo"] = APARENCIA_TIPO_TICKET.get(ticket.get("tipo"), ("—", COR_SECUNDARIA_FILA))
                ticket["emitido_hora"] = _hora_brasilia(ticket.get("emitido_em"))
            self.atualizado_em = _hora_brasilia(corpo.get("agora") if isinstance(corpo, dict) else None, segundos=True)

    @rx.var
    def chamados(self) -> list[dict[str, Any]]:
        return [ticket for ticket in self.tickets if ticket.get("status") == "CHAMADO"]

    @rx.var
    def aguardando(self) -> list[dict[str, Any]]:
        return [ticket for ticket in self.tickets if ticket.get("status") == "AGUARDANDO"]

    @rx.var
    def resumo_tipos(self) -> list[dict[str, Any]]:
        """Quantos tickets de cada tipo aguardam chamada, na ordem do Totem."""
        return [
            {"nome": nome, "cor": cor, "quantidade": sum(1 for t in self.tickets if t.get("status") == "AGUARDANDO" and t.get("tipo") == tipo)}
            for tipo, (nome, cor) in APARENCIA_TIPO_TICKET.items()
        ]

    @rx.event(background=True)
    async def monitorar(self):
        """Só atualiza a tela: recarrega do Xano a cada 10 s e desconta a contagem a cada 1 s. Nunca envia ação."""
        # Import tardio: o módulo principal importa as páginas, que importam este estado.
        from ps_fila_prioritaria.ps_fila_prioritaria import app

        async with self:
            if self.monitorando:
                return
            self.monitorando = True
        try:
            ciclos = 0
            while True:
                await asyncio.sleep(1)
                async with self:
                    conexao = app.event_namespace
                    if (self.router.url.path.rstrip("/") != "/recepcao/fila" or conexao is None
                            or self.router.session.client_token not in conexao.token_to_sid):
                        return
                    ciclos += 1
                    if ciclos % 10 == 0:
                        await self.carregar()
                    else:
                        tickets = [dict(ticket) for ticket in self.tickets]
                        for ticket in tickets:
                            if ticket.get("status") == "CHAMADO" and not ticket.get("presente"):
                                restante = ticket.get("segundos_restantes", -1)
                                if restante > 0:
                                    ticket["segundos_restantes"] = restante - 1
                        self.tickets = tickets
        finally:
            async with self:
                self.monitorando = False

    async def proximo(self) -> None:
        self.erro = False
        self.mensagem = ""
        resposta = await self._requisitar("POST", "/tickets/proximo")
        if resposta is not None:
            self.mensagem = "Ticket chamado."
            await self.carregar()

    async def acao(self, ticket_id: int, acao: str) -> None:
        self.erro = False
        self.mensagem = ""
        resposta = await self._requisitar("POST", f"/tickets/{ticket_id}/acao", json={"acao": acao})
        if resposta is not None:
            self.mensagem = "Operação registrada."
            await self.carregar()

    async def chamar_novamente(self, ticket_id: int) -> None:
        await self.acao(ticket_id, "REPETIR")
        if not self.erro:
            self.mensagem = "Ticket chamado novamente."

    async def nao_compareceu(self, ticket_id: int) -> None:
        await self.acao(ticket_id, "AUSENCIA")
        if not self.erro:
            self.mensagem = "Não comparecimento registrado."

    async def identificar(self, ticket_id: int):
        paciente = await self.get_state(PacienteState)
        paciente._resetar_paciente_atual()
        paciente.ticket_id = ticket_id
        return rx.redirect("/recepcao/pacientes")

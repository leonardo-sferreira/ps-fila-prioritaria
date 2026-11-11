"""Estado da aba "Fichas do dia" da Recepção/Triagem (add-fichas-do-dia)."""

from typing import Any

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import _hora_brasilia, _mensagem_erro
from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.comprovante import NOME_PRIORIDADE
from ps_fila_prioritaria.estados.ficha import _normalizar_texto

NOME_SITUACAO = {
    "EM_TRIAGEM": "Em triagem",
    "AGUARDANDO": "Aguardando",
    "CHAMADO": "Chamada",
    "ATENDIDO": "Atendida",
    "DESISTENCIA": "Desistência",
    "CANCELADO": "Cancelada",
}
SITUACOES_FINAIS = {"ATENDIDO", "DESISTENCIA", "CANCELADO"}
# Opções do filtro: valor e rótulo. As situações finais ficam juntas em "Finalizadas" (D2).
FILTROS_SITUACAO = [
    ("TODAS", "Todas"),
    ("EM_TRIAGEM", "Em triagem"),
    ("AGUARDANDO", "Aguardando"),
    ("CHAMADO", "Chamadas"),
    ("FINALIZADAS", "Finalizadas"),
]


def _linha(ficha: dict[str, Any]) -> dict[str, Any]:
    """Prepara uma ficha da API para a tabela: hora em Brasília e nomes de cor e situação."""
    status = str(ficha.get("status") or "")
    prioridade = str(ficha.get("prioridade_atual") or "")
    return {
        "id": int(ficha.get("id") or 0),
        "status": status,
        "situacao": NOME_SITUACAO.get(status, status or "—"),
        "chegada": _hora_brasilia(ficha.get("chegada_em")),
        "nome": str((ficha.get("paciente") or {}).get("nome") or "—"),
        "senha": str(ficha.get("senha") or ""),
        "prioridade": prioridade,
        "nome_prioridade": NOME_PRIORIDADE.get(prioridade, ""),
        "especialidade": str(ficha.get("especialidade") or ""),
    }


def filtrar_fichas(fichas: list[dict[str, Any]], filtro: str, busca: str) -> list[dict[str, Any]]:
    """Filtra por situação e busca por nome ou senha, sem diferenciar acentos nem maiúsculas."""
    termo = _normalizar_texto(busca or "")
    resultado = []
    for ficha in fichas:
        status = ficha.get("status")
        if filtro == "FINALIZADAS":
            if status not in SITUACOES_FINAIS:
                continue
        elif filtro not in ("", "TODAS") and status != filtro:
            continue
        if termo and termo not in _normalizar_texto(str(ficha.get("nome") or "")) and termo not in _normalizar_texto(str(ficha.get("senha") or "")):
            continue
        resultado.append(ficha)
    return resultado


class FichasDoDiaState(rx.State):
    """Lista só para consulta: a tela nunca altera fichas (D1, D5)."""

    fichas: list[dict[str, Any]] = []
    filtro: str = "TODAS"
    busca: str = ""
    carregando: bool = False
    mensagem: str = ""
    erro: bool = False
    atualizado_em: str = ""

    @rx.var
    def fichas_filtradas(self) -> list[dict[str, Any]]:
        return filtrar_fichas(self.fichas, self.filtro, self.busca)

    def set_filtro(self, valor: str | list[str]) -> None:
        # O seletor segmentado também pode enviar lista (modo múltiplo); aqui é sempre um valor só.
        self.filtro = valor[0] if isinstance(valor, list) and valor else str(valor or "TODAS")

    def set_busca(self, valor: str) -> None:
        self.busca = valor

    async def carregar(self) -> None:
        """Busca a lista no Xano; em caso de erro mantém a última lista e avisa."""
        auth = await self.get_state(AuthState)
        self.carregando = True
        try:
            resposta = api.requisitar("GET", "XANO_TRIAGEM_API_URL", "/fichas", token=auth.token)
        except (api.ConfiguracaoAusente, httpx.RequestError):
            self.erro = True
            self.mensagem = "Não foi possível conectar à lista de fichas."
            return
        finally:
            self.carregando = False
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
        if not resposta.is_success:
            self.erro = True
            self.mensagem = _mensagem_erro(resposta)
            return
        corpo = resposta.json() or {}
        self.fichas = [_linha(ficha) for ficha in (corpo.get("fichas") or [])]
        self.atualizado_em = _hora_brasilia(corpo.get("agora"), segundos=True)
        self.erro = False
        self.mensagem = ""

    def abrir(self, ficha_id: int) -> rx.event.EventSpec:
        return rx.redirect(f"/recepcao/ficha/{ficha_id}")

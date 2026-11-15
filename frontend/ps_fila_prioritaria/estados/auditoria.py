"""Auditoria do Administrador, só leitura (add-acompanhamento-administrador, D2/D4, tarefa 2.3).

O Xano junta alterações, chamadas e entradas/saídas, filtra pelo período (padrão: hoje) e pagina em 50; aqui só se
traduzem os códigos para a tela. Registro sem usuário é da carga automática e aparece como "Sistema".
"""

import json
from datetime import datetime
from typing import Any

import reflex as rx

from ps_fila_prioritaria.comum import FUSO_BRASILIA, _timestamp_segundos
from ps_fila_prioritaria.estados.cadastros import chamar

POR_PAGINA = 50
ORIGENS = [("TODAS", "Tudo"), ("ALTERACAO", "Alterações"), ("CHAMADA", "Chamadas"), ("SESSAO", "Entradas e saídas")]
NOME_ORIGEM = {"ALTERACAO": "Alteração", "CHAMADA": "Chamada", "SESSAO": "Acesso"}
NOME_EVENTO = {
    "CARGA_INICIAL": "Carga inicial",
    "LOGIN": "Entrou no sistema",
    "LOGOUT": "Saiu do sistema",
    "CHAMADA": "Chamou o paciente",
    "COMPARECIMENTO": "Paciente compareceu",
    "DESISTENCIA": "Paciente desistiu",
}


def _rotulo_evento(codigo: str) -> str:
    """Código do evento em texto: os conhecidos pelo nome; os demais (ex.: USUARIO_EDITADO) em minúsculas legíveis."""
    if codigo in NOME_EVENTO:
        return NOME_EVENTO[codigo]
    return codigo.replace("_", " ").capitalize() if codigo else "—"


def _valor(valor: Any) -> str:
    if valor in (None, "", {}, []):
        return "—"
    if isinstance(valor, dict):
        return " · ".join(f"{k}: {'—' if v is None else v}" for k, v in valor.items())
    return json.dumps(valor, ensure_ascii=False) if not isinstance(valor, str) else valor


def linha_auditoria(evento: dict[str, Any]) -> dict[str, Any]:
    segundos = _timestamp_segundos(evento.get("em"))
    quando = datetime.fromtimestamp(segundos, FUSO_BRASILIA).strftime("%d/%m/%Y %H:%M:%S") if segundos is not None else "—"
    entidade = str(evento.get("entidade") or "")
    registro = evento.get("registro_id")
    return {
        "quando": quando,
        "origem": NOME_ORIGEM.get(str(evento.get("origem")), str(evento.get("origem") or "")),
        "evento": _rotulo_evento(str(evento.get("tipo_evento") or "")),
        "alvo": f"{entidade.replace('_', ' ').capitalize()} #{registro}" if registro else entidade.capitalize(),
        "usuario": str(evento.get("usuario") or "—"),
        "sistema": evento.get("usuario_id") is None and str(evento.get("origem")) == "ALTERACAO",
        "anterior": _valor(evento.get("valor_anterior")),
        "novo": _valor(evento.get("valor_novo")),
        "justificativa": str(evento.get("justificativa") or ""),
    }


def parametros_consulta(data_inicio: str, data_fim: str, origem: str, usuario_id: str, pagina: int) -> dict[str, Any]:
    params: dict[str, Any] = {"pagina": max(int(pagina), 1)}
    if data_inicio:
        params["data_inicio"] = data_inicio
    if data_fim:
        params["data_fim"] = data_fim
    if origem and origem != "TODAS":
        params["origem"] = origem
    if usuario_id.isdigit() and usuario_id != "0":
        params["usuario_id"] = int(usuario_id)
    return params


class AuditoriaState(rx.State):
    itens: list[dict[str, Any]] = []
    total: int = 0
    pagina: int = 1
    data_inicio: str = ""
    data_fim: str = ""
    origem: str = "TODAS"
    usuario_id: str = "0"
    opcoes_usuarios: list[dict[str, str]] = []
    carregando: bool = False
    mensagem: str = ""
    erro: bool = False

    @rx.var
    def total_paginas(self) -> int:
        return max((self.total + POR_PAGINA - 1) // POR_PAGINA, 1)

    async def carregar(self) -> None:
        if not self.data_inicio:
            hoje = datetime.now(FUSO_BRASILIA).strftime("%Y-%m-%d")
            self.data_inicio = self.data_fim = hoje
        if not self.opcoes_usuarios:
            ok_u, usuarios = await chamar(self, "GET", "/usuarios")
            if ok_u:
                self.opcoes_usuarios = [{"id": str(u["id"]), "nome": str(u.get("nome") or "")} for u in (usuarios or [])]
        await self._consultar()

    async def _consultar(self) -> None:
        self.carregando = True
        try:
            ok, corpo = await chamar(self, "GET", "/admin/auditoria",
                                     params=parametros_consulta(self.data_inicio, self.data_fim, self.origem, self.usuario_id, self.pagina))
        finally:
            self.carregando = False
        if not ok:
            self.erro, self.mensagem, self.itens, self.total = True, str(corpo), [], 0
            return
        corpo = corpo or {}
        self.itens = [linha_auditoria(e) for e in (corpo.get("itens") or [])]
        self.total = int(corpo.get("total") or 0)
        self.erro, self.mensagem = False, ""

    async def _filtrar(self) -> None:
        self.pagina = 1
        await self._consultar()

    async def set_data_inicio(self, valor: str) -> None:
        self.data_inicio = valor
        if self.data_fim and valor > self.data_fim:
            self.data_fim = valor
        await self._filtrar()

    async def set_data_fim(self, valor: str) -> None:
        self.data_fim = valor
        await self._filtrar()

    async def set_origem(self, valor: str) -> None:
        self.origem = valor
        await self._filtrar()

    async def set_usuario(self, valor: str) -> None:
        self.usuario_id = valor
        await self._filtrar()

    async def pagina_anterior(self) -> None:
        if self.pagina > 1:
            self.pagina -= 1
            await self._consultar()

    async def proxima_pagina(self) -> None:
        if self.pagina < self.total_paginas:
            self.pagina += 1
            await self._consultar()

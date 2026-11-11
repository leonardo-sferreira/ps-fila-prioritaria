"""Página "Fichas do dia" da Recepção/Triagem (add-fichas-do-dia)."""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_BORDA,
    COR_ERRO,
    COR_FUNDO,
    COR_SECUNDARIA,
    COR_TEXTO,
    botao_secundario,
    cabecalho,
    cartao_painel,
    menu_recepcao,
    protegido,
)
from ps_fila_prioritaria.estados.fichas_do_dia import FILTROS_SITUACAO, FichasDoDiaState
from ps_fila_prioritaria.paginas.ficha import CORES_PRIORIDADE

COLUNAS = [
    ("CHEGADA", "80px"),
    ("PACIENTE", None),
    ("SENHA", "120px"),
    ("COR", "110px"),
    ("ESPECIALIDADE", "150px"),
    ("SITUAÇÃO", "120px"),
    ("", "90px"),
]
COR_SITUACAO = {
    "EM_TRIAGEM": "gray",
    "AGUARDANDO": "amber",
    "CHAMADO": "blue",
    "ATENDIDO": "green",
    "DESISTENCIA": "red",
    "CANCELADO": "red",
}


def selo_prioridade(ficha: dict[str, Any]) -> rx.Component:
    return rx.cond(
        ficha["nome_prioridade"] != "",
        rx.hstack(
            rx.box(
                width="10px",
                height="10px",
                border_radius="50%",
                background=rx.match(ficha["prioridade"], *[(codigo, cor) for codigo, _, _, cor in CORES_PRIORIDADE], COR_SECUNDARIA),
            ),
            rx.text(ficha["nome_prioridade"], size="2", color=COR_TEXTO),
            align="center",
            spacing="2",
        ),
        rx.text("—", size="2", color=COR_SECUNDARIA),
    )


def celula(conteudo: rx.Component, largura: str | None) -> rx.Component:
    return rx.box(conteudo, width=largura or "auto", flex="1" if largura is None else "0 0 auto", min_width="0")


def linha_ficha(ficha: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        celula(rx.text(ficha["chegada"], size="2", color=COR_SECUNDARIA), COLUNAS[0][1]),
        celula(rx.text(ficha["nome"], size="2", weight="medium", color=COR_TEXTO, trim="both"), COLUNAS[1][1]),
        celula(rx.text(rx.cond(ficha["senha"] != "", ficha["senha"], "—"), size="2", weight="bold", color=COR_TEXTO), COLUNAS[2][1]),
        celula(selo_prioridade(ficha), COLUNAS[3][1]),
        celula(rx.text(rx.cond(ficha["especialidade"] != "", ficha["especialidade"], "—"), size="2", color=COR_TEXTO), COLUNAS[4][1]),
        celula(
            rx.badge(ficha["situacao"], color_scheme=rx.match(ficha["status"], *COR_SITUACAO.items(), "gray"), size="1"),
            COLUNAS[5][1],
        ),
        celula(botao_secundario("Abrir", on_click=FichasDoDiaState.abrir(ficha["id"])), COLUNAS[6][1]),
        align="center",
        spacing="3",
        width="100%",
        padding="10px 16px",
        border_bottom=f"1px solid {COR_BORDA}",
        _hover={"background": "#F7F9FB"},
    )


def tabela_fichas() -> rx.Component:
    cabecalho_tabela = rx.hstack(
        *[celula(rx.text(rotulo, size="1", weight="medium", color=COR_SECUNDARIA), largura) for rotulo, largura in COLUNAS],
        spacing="3",
        width="100%",
        padding="0 16px 10px",
        border_bottom=f"1px solid {COR_BORDA}",
    )
    return cartao_painel(
        rx.cond(
            FichasDoDiaState.fichas_filtradas.length() == 0,
            rx.text("Nenhuma ficha encontrada para este filtro.", size="2", color=COR_SECUNDARIA, padding="8px 16px"),
            rx.box(
                rx.vstack(cabecalho_tabela, rx.foreach(FichasDoDiaState.fichas_filtradas, linha_ficha), spacing="0", min_width="860px"),
                overflow_x="auto",
                width="100%",
            ),
        ),
        padding="20px 0",
    )


def pagina_fichas_do_dia() -> rx.Component:
    return protegido(
        "RECEPCAO_TRIAGEM",
        rx.box(
            cabecalho("RECEPÇÃO/TRIAGEM — FICHAS DO DIA", "Abra uma ficha para continuar a triagem ou reavaliar quem aguarda"),
            menu_recepcao("/recepcao/fichas"),
            rx.center(
                rx.vstack(
                    rx.flex(
                        rx.segmented_control.root(
                            *[rx.segmented_control.item(rotulo, value=valor) for valor, rotulo in FILTROS_SITUACAO],
                            value=FichasDoDiaState.filtro,
                            on_change=FichasDoDiaState.set_filtro,
                            size="2",
                        ),
                        rx.input(
                            rx.input.slot(rx.icon("search", size=16)),
                            value=FichasDoDiaState.busca,
                            on_change=FichasDoDiaState.set_busca,
                            placeholder="Buscar por nome ou senha",
                            size="2",
                            width=rx.breakpoints(initial="100%", sm="260px"),
                        ),
                        rx.spacer(),
                        botao_secundario("Atualizar", on_click=FichasDoDiaState.carregar, loading=FichasDoDiaState.carregando),
                        align="center",
                        gap="12px",
                        wrap="wrap",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.cond(
                            FichasDoDiaState.mensagem != "",
                            rx.text(FichasDoDiaState.mensagem, size="2", color=COR_ERRO),
                        ),
                        rx.spacer(),
                        rx.cond(
                            FichasDoDiaState.atualizado_em != "",
                            rx.text("Fichas em andamento e finalizadas hoje · atualizado às ", FichasDoDiaState.atualizado_em, size="1", color=COR_SECUNDARIA),
                        ),
                        width="100%",
                    ),
                    tabela_fichas(),
                    # Recarrega a lista a cada 15 s enquanto a aba está aberta; nunca altera fichas (D5).
                    rx.moment(interval=15000, on_change=lambda _: FichasDoDiaState.carregar, display="none"),
                    spacing="4",
                    width="min(100%, 1184px)",
                ),
                padding="28px 16px 40px",
                width="100%",
            ),
            background=COR_FUNDO,
            font_family="Inter, sans-serif",
            min_height="100vh",
            width="100%",
        ),
    )

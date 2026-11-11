"""Tela inicial do Administrador (add-acompanhamento-administrador, D6): o painel do plantão da Recepção/Triagem,
mais indicadores do dia, a equipe logada e o cartão de fichas paradas. Só consulta, exceto a dispensa por prazo."""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_BORDA,
    COR_ERRO,
    COR_FUNDO,
    COR_SECUNDARIA,
    COR_TEXTO,
    cabecalho,
    menu_admin,
    protegido,
)
from ps_fila_prioritaria.estados.equipe import EquipeState
from ps_fila_prioritaria.estados.plantao import PlantaoState
from ps_fila_prioritaria.paginas.areas import cartao_parados
from ps_fila_prioritaria.paginas.plantao import NUMERO, painel, painel_plantao, rotulo


def indicador(item: dict[str, Any]) -> rx.Component:
    return rx.vstack(
        rx.text(item["valor"], font_size="32px", weight="bold", color=COR_TEXTO, style=NUMERO),
        rx.text(item["rotulo"], size="2", weight="medium", color=COR_TEXTO),
        rx.text(item["detalhe"], size="1", color=COR_SECUNDARIA),
        spacing="1",
        padding="4px 12px",
        border_left=f"2px solid {COR_BORDA}",
        width="100%",
    )


def indicadores_do_dia() -> rx.Component:
    return painel(
        rx.vstack(
            rotulo("Indicadores do dia"),
            rx.grid(rx.foreach(PlantaoState.indicadores, indicador), columns=rx.breakpoints(initial="2", md="4"), gap="16px", width="100%"),
            spacing="4",
            width="100%",
        ),
    )


def contagem_status(item: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.box(width="8px", height="8px", background=item["cor"], border_radius="1px", flex_shrink="0"),
        rx.text(item["nome"], size="2", color=COR_SECUNDARIA),
        rx.text(item["quantidade"], size="2", weight="bold", color=COR_TEXTO, style=NUMERO),
        align="center",
        spacing="2",
    )


def linha_pessoa(p: dict[str, Any]) -> rx.Component:
    return rx.grid(
        rx.text(p["nome"], size="2", weight="medium", color=COR_TEXTO, white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
        rx.text(p["perfil_nome"], size="2", color=COR_SECUNDARIA, white_space="nowrap"),
        rx.hstack(
            rx.box(width="8px", height="8px", background=p["cor"], border_radius="1px", flex_shrink="0"),
            rx.text(p["status"], size="2", color=COR_TEXTO, white_space="nowrap"),
            align="center",
            spacing="2",
        ),
        rx.text("desde ", p["login"], size="1", color=COR_SECUNDARIA, text_align="right", white_space="nowrap"),
        grid_template_columns=rx.breakpoints(initial="1fr auto", sm="minmax(0, 1fr) 130px 140px 80px"),
        align_items="center",
        gap="8px 12px",
        padding="8px 0",
        border_bottom=f"1px solid {COR_BORDA}",
        width="100%",
    )


def equipe_agora() -> rx.Component:
    e = EquipeState
    return painel(
        rx.vstack(
            rx.hstack(
                rotulo("Equipe agora"),
                rx.spacer(),
                rx.text(e.medicos_logados.to_string() + " médico(s) · " + e.recepcao_logada.to_string() + " na Recepção/Triagem",
                        size="1", color=COR_SECUNDARIA),
                width="100%",
                align="center",
                wrap="wrap",
            ),
            rx.flex(rx.foreach(e.medicos_por_status, contagem_status), gap="8px 20px", wrap="wrap"),
            rx.cond(e.mensagem != "", rx.text(e.mensagem, size="2", color=COR_ERRO)),
            rx.cond(
                e.pessoas.length() > 0,
                rx.vstack(rx.foreach(e.pessoas, linha_pessoa), spacing="0", width="100%"),
                rx.text("Ninguém com sessão ativa.", size="2", color=COR_SECUNDARIA),
            ),
            spacing="4",
            width="100%",
        ),
    )


def area_admin() -> rx.Component:
    return protegido(
        "ADMINISTRADOR",
        rx.box(
            cabecalho("ADMINISTRADOR", "Área inicial — Administrador"),
            menu_admin("/admin"),
            rx.center(
                rx.vstack(
                    painel_plantao(extras=(indicadores_do_dia(), equipe_agora()), com_links=False),
                    painel(cartao_parados()),
                    # A equipe também se atualiza a cada 30 s, junto com o painel do plantão.
                    rx.moment(interval=30000, on_change=lambda _: EquipeState.carregar, display="none"),
                    spacing="5",
                    width="min(100%, 1184px)",
                ),
                padding="28px 16px 48px",
                width="100%",
            ),
            background=COR_FUNDO,
            font_family="Inter, sans-serif",
            min_height="100vh",
            width="100%",
        ),
    )

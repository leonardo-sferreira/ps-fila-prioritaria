"""Área inicial da Recepção/Triagem: painel do plantão com o que está acontecendo no dia."""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_AZUL,
    COR_BORDA,
    COR_ERRO,
    COR_FUNDO,
    COR_SECUNDARIA,
    COR_SUPERFICIE,
    COR_TEXTO,
    cabecalho,
    menu_recepcao,
    protegido,
)
from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.plantao import PlantaoState

NUMERO = {"font_variant_numeric": "tabular-nums", "letter_spacing": "-0.02em", "line_height": "1"}


def rotulo(texto: Any) -> rx.Component:
    """Rótulo pequeno em caixa alta, como nas fichas impressas: separa as seções sem caixas extras."""
    return rx.text(texto, size="1", weight="bold", color=COR_SECUNDARIA, letter_spacing="0.08em", text_transform="uppercase")


def painel(*filhos: rx.Component, **props: Any) -> rx.Component:
    return rx.box(*filhos, background=COR_SUPERFICIE, border=f"1px solid {COR_BORDA}", border_radius="6px", padding="24px", width="100%", **props)


def segmento_cor(cor: dict[str, Any]) -> rx.Component:
    """Bloco da barra segmentada: largura proporcional; nome e número escritos dentro quando cabem."""
    return rx.cond(
        cor["visivel"],
        rx.tooltip(
            rx.box(
                rx.text(cor["rotulo"], size="1", weight="bold", color=cor["texto"], white_space="nowrap"),
                flex_grow=cor["quantidade"],
                flex_basis="0",
                min_width="10px",
                height="28px",
                background=cor["cor"],
                border_radius="4px",
                display="flex",
                align_items="center",
                padding_left="8px",
                overflow="hidden",
            ),
            content=cor["dica"],
        ),
    )


def legenda_cor(cor: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.box(width="10px", height="10px", background=cor["cor"], border_radius="2px"),
        rx.text(cor["nome"], size="1", color=COR_SECUNDARIA),
        rx.text(cor["quantidade"], size="1", weight="bold", color=COR_TEXTO, style=NUMERO),
        align="center",
        spacing="1",
    )


def linha_espera(titulo: str, item: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(titulo, size="2", color=COR_SECUNDARIA),
        rx.spacer(),
        rx.cond(
            item["texto"] != "",
            rx.hstack(
                rx.text(item["identificacao"], size="2", weight="bold", color=COR_TEXTO, white_space="nowrap"),
                rx.text(item["texto"], size="2", color=COR_TEXTO, white_space="nowrap", style=NUMERO),
                spacing="2",
                align="baseline",
            ),
            rx.text("ninguém esperando", size="2", color=COR_SECUNDARIA),
        ),
        width="100%",
        align="baseline",
        padding="8px 0",
        border_top=f"1px solid {COR_BORDA}",
    )


def bloco_espera() -> rx.Component:
    return painel(
        rx.grid(
            rx.vstack(
                rotulo("Na espera agora"),
                rx.text(PlantaoState.na_espera, font_size="72px", weight="bold", color=COR_TEXTO, style=NUMERO),
                rx.text(
                    PlantaoState.tickets_aguardando.to_string() + " na pré-triagem · " + PlantaoState.fichas_aguardando.to_string() + " na fila médica",
                    size="2",
                    color=COR_SECUNDARIA,
                ),
                spacing="3",
                justify="center",
            ),
            rx.vstack(
                rotulo("Fila médica por cor"),
                rx.cond(
                    PlantaoState.fichas_aguardando > 0,
                    rx.hstack(rx.foreach(PlantaoState.cores, segmento_cor), spacing="0", gap="2px", width="100%"),
                    rx.box(
                        rx.text("Ninguém na fila médica", size="1", color=COR_SECUNDARIA),
                        height="28px",
                        display="flex",
                        align_items="center",
                        padding_left="10px",
                        border=f"1px dashed {COR_BORDA}",
                        border_radius="4px",
                        width="100%",
                    ),
                ),
                rx.hstack(rx.foreach(PlantaoState.cores, legenda_cor), spacing="4", wrap="wrap"),
                rx.box(height="8px"),
                linha_espera("Mais tempo na fila médica", PlantaoState.maior_ficha),
                linha_espera("Mais tempo na pré-triagem", PlantaoState.maior_ticket),
                spacing="2",
                width="100%",
            ),
            columns=rx.breakpoints(initial="1", md="2"),
            gap="32px",
            align_items="center",
        ),
    )


def etapa(item: dict[str, Any], indice: rx.Var) -> rx.Component:
    """Uma etapa do percurso do paciente; a seta à esquerda liga à etapa anterior."""
    return rx.link(
        rx.hstack(
            rx.cond(indice > 0, rx.icon("chevron-right", size=16, color=COR_BORDA, flex_shrink="0")),
            rx.vstack(
                rx.text(item["quantidade"], font_size="36px", weight="bold", color=COR_TEXTO, style=NUMERO),
                rx.text(item["rotulo"], size="2", weight="medium", color=COR_TEXTO),
                rx.text(item["detalhe"], size="1", color=COR_SECUNDARIA),
                spacing="1",
                padding="4px 12px",
                border_left=f"2px solid {COR_BORDA}",
                _hover={"border_left_color": COR_AZUL},
                width="100%",
            ),
            align="center",
            spacing="2",
            width="100%",
        ),
        href=item["rota"],
        underline="none",
        width="100%",
    )


def percurso() -> rx.Component:
    return painel(
        rx.vstack(
            rx.hstack(
                rotulo("Percurso do dia"),
                rx.spacer(),
                rx.text("do Totem à conclusão · toque para abrir", size="1", color=COR_SECUNDARIA),
                width="100%",
                align="center",
            ),
            rx.grid(
                rx.foreach(PlantaoState.etapas, etapa),
                columns=rx.breakpoints(initial="2", sm="3", md="5"),
                gap="16px",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
    )


def linha_especialidade(item: dict[str, Any]) -> rx.Component:
    return rx.grid(
        rx.text(item["nome"], size="2", color=COR_TEXTO, white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
        rx.box(
            rx.box(width=item["largura"], height="100%", background=COR_AZUL, border_radius="0 4px 4px 0"),
            height="8px",
            # Trilho num tom mais claro do mesmo azul (meter), para a barra ler de ponta a ponta.
            background="var(--ps-destaque)",
            width="100%",
        ),
        rx.text(item["quantidade"], size="2", weight="bold", color=COR_TEXTO, text_align="right", style=NUMERO),
        grid_template_columns="minmax(90px, 140px) 1fr 32px",
        align_items="center",
        gap="12px",
        width="100%",
    )


def por_especialidade() -> rx.Component:
    return painel(
        rx.vstack(
            rotulo("Fila médica por especialidade"),
            rx.cond(
                PlantaoState.especialidades.length() > 0,
                rx.vstack(rx.foreach(PlantaoState.especialidades, linha_especialidade), spacing="3", width="100%"),
                rx.text("Nenhuma senha aguardando médico.", size="2", color=COR_SECUNDARIA),
            ),
            spacing="4",
            width="100%",
        ),
        height="100%",
    )


def coluna_hora(item: dict[str, Any]) -> rx.Component:
    return rx.tooltip(
        rx.vstack(
            rx.text(item["valor"], size="1", weight="bold", color=COR_TEXTO, min_height="16px", style=NUMERO),
            rx.box(
                rx.box(
                    height=item["altura"],
                    min_height=item["altura_minima"],
                    background=rx.cond(item["atual"], COR_AZUL, "var(--ps-barra)"),
                    border_radius="4px 4px 0 0",
                    width="100%",
                ),
                height="120px",
                display="flex",
                align_items="flex-end",
                width="100%",
            ),
            rx.text(item["hora"], size="1", color=rx.cond(item["atual"], COR_TEXTO, COR_SECUNDARIA), weight=rx.cond(item["atual"], "bold", "regular")),
            spacing="1",
            align="center",
            flex="1",
            min_width="0",
        ),
        content=item["dica"],
    )


def chegadas_por_hora() -> rx.Component:
    return painel(
        rx.vstack(
            rx.hstack(
                rotulo("Chegadas por hora"),
                rx.spacer(),
                rx.text(PlantaoState.chegadas_hoje.to_string() + " fichas abertas hoje", size="1", color=COR_SECUNDARIA),
                width="100%",
                align="center",
            ),
            rx.box(
                rx.hstack(rx.foreach(PlantaoState.chegadas, coluna_hora), spacing="0", gap="4px", align="end", width="100%"),
                border_bottom=f"1px solid {COR_BORDA}",
                width="100%",
            ),
            rx.text("Hora atual em destaque; passe o mouse para ver cada hora.", size="1", color=COR_SECUNDARIA),
            spacing="3",
            width="100%",
        ),
        height="100%",
    )


def painel_plantao() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rotulo(rx.text("Plantão de hoje · ", AuthState.nome)),
                rx.text(PlantaoState.data_extenso, size="7", weight="bold", color=COR_TEXTO),
                spacing="1",
            ),
            rx.spacer(),
            rx.vstack(
                rx.button(rx.icon("refresh-cw", size=14), "Atualizar", on_click=PlantaoState.carregar, variant="ghost", color_scheme="gray", size="2"),
                rx.cond(PlantaoState.atualizado_em != "", rx.text("atualizado às ", PlantaoState.atualizado_em, size="1", color=COR_SECUNDARIA)),
                spacing="1",
                align="end",
            ),
            width="100%",
            align="end",
            wrap="wrap",
        ),
        rx.cond(PlantaoState.mensagem != "", rx.text(PlantaoState.mensagem, size="2", color=COR_ERRO)),
        bloco_espera(),
        percurso(),
        rx.grid(
            por_especialidade(),
            chegadas_por_hora(),
            columns=rx.breakpoints(initial="1", md="2"),
            gap="20px",
            width="100%",
        ),
        # Atualiza sozinho a cada 30 s enquanto a tela está aberta; só consulta.
        rx.moment(interval=30000, on_change=lambda _: PlantaoState.carregar, display="none"),
        spacing="5",
        width="min(100%, 1184px)",
    )


def area_recepcao() -> rx.Component:
    return protegido(
        "RECEPCAO_TRIAGEM",
        rx.box(
            cabecalho("RECEPÇÃO/TRIAGEM", "Área inicial — Recepção/Triagem"),
            menu_recepcao("/recepcao"),
            rx.center(painel_plantao(), padding="28px 16px 48px", width="100%"),
            background=COR_FUNDO,
            font_family="Inter, sans-serif",
            min_height="100vh",
            width="100%",
        ),
    )

"""Cartão de fichas e tickets parados (add-expiracao-24h), usado na tela inicial do Administrador."""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.componentes import COR_BORDA, COR_ERRO, COR_SECUNDARIA, COR_SUCESSO, COR_TEXTO, botao_secundario
from ps_fila_prioritaria.estados.expiracao import ORDENS, TAMANHOS_PAGINA, ExpiracaoState


def linha_parada(item: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.text(item["identificacao"], size="2", weight="bold", color=COR_TEXTO, width="110px"),
        rx.badge(item["tipo"], color_scheme=rx.cond(item["tipo"] == "Ficha", "blue", "gray"), variant="outline", size="1"),
        rx.badge(item["situacao"], color_scheme="gray", size="1"),
        rx.spacer(),
        rx.text(item["horario"], size="2", color=COR_SECUNDARIA),
        align="center",
        width="100%",
        padding="6px 0",
        border_bottom=f"1px solid {COR_BORDA}",
    )


def controles_lista() -> rx.Component:
    """Ordem e quantidade por página; trocar qualquer um volta à página 1."""
    return rx.hstack(
        rx.select(ORDENS, value=ExpiracaoState.ordem, on_change=ExpiracaoState.set_ordem, size="2"),
        rx.spacer(),
        rx.text("Por página", size="2", color=COR_SECUNDARIA),
        rx.select(TAMANHOS_PAGINA, value=ExpiracaoState.tamanho_pagina, on_change=ExpiracaoState.set_tamanho_pagina, size="2"),
        align="center",
        spacing="2",
        wrap="wrap",
        width="100%",
    )


def paginacao() -> rx.Component:
    return rx.hstack(
        botao_secundario("Anterior", on_click=ExpiracaoState.pagina_anterior, disabled=ExpiracaoState.pagina <= 1),
        rx.text(
            "Página " + ExpiracaoState.pagina.to_string() + " de " + ExpiracaoState.total_paginas.to_string(),
            size="2",
            color=COR_SECUNDARIA,
        ),
        botao_secundario(
            "Próxima", on_click=ExpiracaoState.proxima_pagina, disabled=ExpiracaoState.pagina >= ExpiracaoState.total_paginas
        ),
        justify="center",
        align="center",
        spacing="3",
        width="100%",
    )


def dialogo_dispensa() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Dispensar fichas e tickets parados"),
            rx.alert_dialog.description(
                ExpiracaoState.texto_confirmacao,
                " Cada encerramento fica no histórico em seu nome.",
                size="2",
            ),
            rx.hstack(
                rx.alert_dialog.cancel(botao_secundario("Cancelar")),
                rx.alert_dialog.action(
                    rx.button("Dispensar todos", on_click=ExpiracaoState.dispensar, color_scheme="red", size="3"),
                ),
                justify="end",
                spacing="3",
                margin_top="16px",
            ),
            max_width="460px",
        ),
        open=ExpiracaoState.confirmacao_aberta,
        on_open_change=ExpiracaoState.set_confirmacao_aberta,
    )


def cartao_parados() -> rx.Component:
    """Dispensa por prazo (add-expiracao-24h, D6): prévia do que passou do prazo e dispensa com confirmação."""
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Fichas e tickets parados", weight="bold", size="4", color=COR_TEXTO),
                rx.text(
                    rx.cond(
                        ExpiracaoState.horas > 0,
                        "Sem conclusão há mais de " + ExpiracaoState.horas.to_string() + " horas.",
                        "Sem conclusão além do prazo configurado.",
                    ),
                    size="2",
                    color=COR_SECUNDARIA,
                ),
                spacing="0",
            ),
            rx.spacer(),
            botao_secundario("Atualizar", on_click=ExpiracaoState.carregar, loading=ExpiracaoState.carregando),
            rx.button(
                "Dispensar todos",
                on_click=ExpiracaoState.set_confirmacao_aberta(True),
                disabled=ExpiracaoState.total == 0,
                loading=ExpiracaoState.dispensando,
                color_scheme="red",
                size="3",
            ),
            align="center",
            spacing="3",
            wrap="wrap",
            width="100%",
        ),
        rx.cond(
            ExpiracaoState.mensagem != "",
            rx.text(ExpiracaoState.mensagem, size="2", color=rx.cond(ExpiracaoState.erro, COR_ERRO, COR_SUCESSO)),
        ),
        rx.cond(
            ExpiracaoState.total == 0,
            rx.text("Nenhuma ficha ou ticket parado.", size="2", color=COR_SECUNDARIA),
            rx.vstack(
                controles_lista(),
                rx.vstack(rx.foreach(ExpiracaoState.itens_pagina, linha_parada), spacing="1", width="100%"),
                paginacao(),
                spacing="3",
                width="100%",
            ),
        ),
        dialogo_dispensa(),
        spacing="3",
        width="100%",
    )

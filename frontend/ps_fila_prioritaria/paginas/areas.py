"""Áreas iniciais de cada perfil."""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_AZUL,
    COR_BORDA,
    COR_ERRO,
    COR_FUNDO,
    COR_SECUNDARIA,
    COR_SUCESSO,
    COR_TEXTO,
    botao_secundario,
    cabecalho,
    menu_recepcao,
    protegido,
)
from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.expiracao import ExpiracaoState
from ps_fila_prioritaria.estados.pacientes import PacienteState


def area_inicial(perfil: str, titulo: str, nome_perfil: str, conteudo: rx.Component) -> rx.Component:
    return protegido(
        perfil,
        rx.box(
            cabecalho(titulo, f"Área inicial — {nome_perfil}"),
            *([menu_recepcao("/recepcao")] if perfil == "RECEPCAO_TRIAGEM" else []),
            rx.center(
                rx.vstack(
                    rx.text("Olá, ", AuthState.nome, weight="bold", size="5", color=COR_TEXTO),
                    rx.text(f"Perfil: {nome_perfil}", size="2", color=COR_SECUNDARIA),
                    conteudo,
                    spacing="3",
                    padding="28px 32px",
                    background="white",
                    border=f"1px solid {COR_BORDA}",
                    border_radius="12px",
                    width="min(100%, 772px)",
                ),
                padding="40px 16px",
                width="100%",
            ),
            background=COR_FUNDO,
            font_family="Inter, sans-serif",
            min_height="100vh",
            width="100%",
        ),
    )


def area_recepcao() -> rx.Component:
    return area_inicial(
        "RECEPCAO_TRIAGEM",
        "RECEPÇÃO/TRIAGEM",
        "Recepção/Triagem",
        rx.vstack(
            rx.link(rx.button("Fila de pré-triagem", size="3", background=COR_AZUL), href="/recepcao/fila"),
            rx.button("Identificar paciente sem ticket", size="3", variant="outline", on_click=PacienteState.iniciar_sem_ticket),
            rx.link(rx.button("Fichas do dia", size="3", variant="outline"), href="/recepcao/fichas"),
        ),
    )


def area_medico() -> rx.Component:
    return area_inicial("MEDICO", "MÉDICO", "Médico", rx.text("As funções do Médico ainda estão em construção.", size="2", color=COR_SECUNDARIA))


def linha_parada(item: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.text(item["identificacao"], size="2", weight="bold", color=COR_TEXTO, width="110px"),
        rx.badge(item["situacao"], color_scheme="gray", size="1"),
        rx.spacer(),
        rx.text(item["horario"], size="2", color=COR_SECUNDARIA),
        align="center",
        width="100%",
        padding="6px 0",
        border_bottom=f"1px solid {COR_BORDA}",
    )


def lista_parados(titulo: str, itens: rx.Var) -> rx.Component:
    return rx.cond(
        itens.length() > 0,
        rx.vstack(
            rx.text(titulo, size="1", weight="medium", color=COR_SECUNDARIA),
            rx.foreach(itens, linha_parada),
            spacing="1",
            width="100%",
        ),
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
        rx.divider(),
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
                lista_parados("FICHAS", ExpiracaoState.fichas),
                lista_parados("TICKETS DO TOTEM", ExpiracaoState.tickets),
                spacing="4",
                width="100%",
            ),
        ),
        dialogo_dispensa(),
        spacing="3",
        width="100%",
        padding_top="8px",
    )


def area_admin() -> rx.Component:
    return area_inicial(
        "ADMINISTRADOR",
        "ADMINISTRADOR",
        "Administrador",
        cartao_parados(),
    )

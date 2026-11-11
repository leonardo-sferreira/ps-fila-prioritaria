"""Áreas iniciais de cada perfil."""

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_AZUL,
    COR_BORDA,
    COR_FUNDO,
    COR_SECUNDARIA,
    COR_TEXTO,
    cabecalho,
    menu_recepcao,
    protegido,
)
from ps_fila_prioritaria.estados.autenticacao import AuthState
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
        ),
    )


def area_medico() -> rx.Component:
    return area_inicial("MEDICO", "MÉDICO", "Médico", rx.text("As funções do Médico ainda estão em construção.", size="2", color=COR_SECUNDARIA))


def area_admin() -> rx.Component:
    return area_inicial(
        "ADMINISTRADOR",
        "ADMINISTRADOR",
        "Administrador",
        rx.text("As funções do Administrador ainda estão em construção.", size="2", color=COR_SECUNDARIA),
    )

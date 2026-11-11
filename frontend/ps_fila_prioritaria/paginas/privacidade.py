"""Página do aviso de privacidade."""

import reflex as rx

from ps_fila_prioritaria.componentes import COR_AZUL_BOTAO, COR_BORDA, COR_SUPERFICIE, COR_TEXTO, logo_ps
from ps_fila_prioritaria.comum import ARQUIVO_AVISO_PRIVACIDADE
from ps_fila_prioritaria.paginas.autenticacao import fundo_acesso


def carregar_aviso_privacidade() -> str:
    return ARQUIVO_AVISO_PRIVACIDADE.read_text(encoding="utf-8")


def privacidade() -> rx.Component:
    # Página pública do aviso: não exige login nem mexe na sessão aberta (spec privacidade).
    return fundo_acesso(
        rx.vstack(
            logo_ps(),
            rx.box(rx.markdown(carregar_aviso_privacidade()), color=COR_TEXTO, width="100%"),
            rx.link(rx.button("Voltar ao login", size="3", background=COR_AZUL_BOTAO), href="/login"),
            align="center",
            spacing="4",
            padding="40px 32px",
            background=COR_SUPERFICIE,
            border=f"1px solid {COR_BORDA}",
            border_radius="16px",
            box_shadow="0 2px 8px rgba(18, 60, 107, 0.06)",
            width="min(100%, 760px)",
        )
    )

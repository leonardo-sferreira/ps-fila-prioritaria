"""Página do Totem de autoatendimento."""

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_AZUL_BOTAO,
    COR_BORDA,
    COR_ERRO,
    COR_FUNDO,
    COR_MARINHO,
    COR_SECUNDARIA,
    COR_SUPERFICIE,
    COR_TEXTO,
    cabecalho,
)
from ps_fila_prioritaria.estados.totem import TotemState


# Tipos de ticket do Totem (add-totem D5), na ordem e com as cores da tela 1 do Figma.
TIPOS_TOTEM = [
    ("PEDIATRICO", "C", "Pediátrico", "#6554C0", "Crianças de até 11 anos."),
    ("PREFERENCIAL", "P", "Preferencial", "#ED8B00", "Pessoas com 60 anos ou mais, gestantes e demais pessoas com direito a atendimento preferencial."),
    ("NORMAL", "N", "Normal", "#1565C0", "Todos os demais pacientes."),
]


NOME_TIPO_TOTEM = {tipo: nome for tipo, _, nome, _, _ in TIPOS_TOTEM}


def cartao_tipo_totem(tipo: str, letra: str, nome: str, cor: str, descricao: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.center(rx.text(letra, weight="bold", size="6", color=cor), width="64px", height="64px", border_radius="50%", background=f"{cor}1F"),
            rx.text(nome, weight="bold", size="7", color=COR_TEXTO),
            rx.text(descricao, size="3", color=COR_SECUNDARIA),
            rx.spacer(),
            rx.divider(color=COR_BORDA),
            rx.text("Toque para retirar", weight="bold", size="3", color=cor),
            spacing="3",
            align="start",
            height="100%",
            padding="28px",
        ),
        on_click=TotemState.emitir(tipo),
        cursor="pointer",
        background=COR_SUPERFICIE,
        border=f"1px solid {COR_BORDA}",
        border_top=f"6px solid {cor}",
        border_radius="12px",
        box_shadow="0 2px 8px rgba(18, 60, 107, 0.06)",
        min_height="320px",
        flex="1",
        _hover={"box_shadow": "0 6px 16px rgba(18, 60, 107, 0.14)"},
        aria_label=f"Retirar ticket {nome}",
    )


def aviso_totem() -> rx.Component:
    """Estados da emissão por cima da escolha: emitindo (1a), emitido (1b) e falha (1c)."""
    conteudo = rx.cond(
        TotemState.emitindo,
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Emitindo seu ticket…", weight="bold", size="6", color=COR_TEXTO),
            rx.text("Aguarde um instante.", size="3", color=COR_SECUNDARIA),
            align="center",
            spacing="4",
        ),
        rx.cond(
            TotemState.codigo != "",
            rx.vstack(
                rx.text("SEU TICKET", weight="medium", size="2", color=COR_SECUNDARIA),
                rx.text(TotemState.codigo, weight="bold", font_size="88px", line_height="1", color=COR_MARINHO),
                rx.match(TotemState.tipo_emitido, *[(t, rx.text(n, weight="medium", size="4", color=COR_TEXTO)) for t, n in NOME_TIPO_TOTEM.items()], rx.fragment()),
                rx.text(
                    "Aguarde a chamada da Recepção/Triagem e acompanhe o painel da sala de espera.",
                    size="3",
                    color=COR_SECUNDARIA,
                    text_align="center",
                ),
                rx.button("Concluir", on_click=TotemState.concluir, size="4", background=COR_AZUL_BOTAO, width="100%"),
                align="center",
                spacing="4",
            ),
            rx.vstack(
                rx.center(rx.text("!", weight="bold", size="7", color=COR_ERRO), width="72px", height="72px", border_radius="50%", background=f"{COR_ERRO}1F"),
                rx.text(TotemState.erro, weight="bold", size="6", color=COR_TEXTO, text_align="center"),
                rx.text("Toque em Voltar para tentar de novo ou procure a recepção.", size="3", color=COR_SECUNDARIA, text_align="center"),
                rx.button("Voltar", on_click=TotemState.concluir, size="4", background=COR_AZUL_BOTAO, width="100%"),
                align="center",
                spacing="4",
            ),
        ),
    )
    return rx.cond(
        TotemState.emitindo | (TotemState.codigo != "") | (TotemState.erro != ""),
        rx.center(
            rx.box(conteudo, background=COR_SUPERFICIE, border_radius="16px", padding="40px", width="min(100%, 480px)", box_shadow="0 8px 24px rgba(0, 0, 0, 0.18)"),
            position="fixed",
            inset="0",
            background="rgba(0, 0, 0, 0.45)",
            z_index="10",
            padding="16px",
        ),
    )


def totem() -> rx.Component:
    # Tela 1 do Figma: pública, sem login e sem pedir dado pessoal (spec totem).
    return rx.box(
        cabecalho("TOTEM DE AUTOATENDIMENTO", "", com_sessao=False),
        rx.vstack(
            rx.text("Bem-vindo ao Pronto-Socorro", weight="bold", size="8", color=COR_TEXTO),
            rx.text("Escolha o tipo de atendimento e toque para retirar seu ticket de chegada", size="3", color=COR_SECUNDARIA),
            rx.box(height="12px"),
            rx.flex(*[cartao_tipo_totem(*t) for t in TIPOS_TOTEM], gap="24px", width="100%", direction={"base": "column", "md": "row"}),
            spacing="2",
            padding="48px",
            width="100%",
            max_width="1280px",
            margin="0 auto",
        ),
        rx.center(
            rx.text("Em caso de dúvida, procure a recepção", size="2", color=COR_SECUNDARIA),
            border_top=f"1px solid {COR_BORDA}",
            padding="16px",
            width="100%",
        ),
        aviso_totem(),
        background=COR_FUNDO,
        font_family="Inter, sans-serif",
        min_height="100vh",
        width="100%",
    )

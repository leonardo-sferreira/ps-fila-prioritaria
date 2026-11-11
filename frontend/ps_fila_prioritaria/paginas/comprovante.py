"""Página do comprovante de senha."""

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_AZUL,
    COR_FUNDO,
    COR_SECUNDARIA,
    botao_secundario,
    menu_recepcao,
    protegido,
)
from ps_fila_prioritaria.estados.comprovante import ComprovanteState


def comprovante_senha() -> rx.Component:
    """Comprovante térmico de 80 mm sem dados pessoais nem clínicos (Rev. 2.1, §9)."""
    return rx.box(
        rx.el.style("@page { size: 80mm auto; margin: 4mm; } @media print { .nao-imprimir { display: none !important; } body { background: white !important; } }"),
        menu_recepcao(),
        rx.cond(
            ComprovanteState.mensagem != "",
            rx.callout(ComprovanteState.mensagem, color_scheme="red", margin="16px"),
            rx.vstack(
                rx.text("PRONTO-SOCORRO", size="2", weight="bold", letter_spacing="0.08em"),
                rx.text("SENHA DE ATENDIMENTO", size="1", color=COR_SECUNDARIA),
                rx.text(ComprovanteState.senha, font_size="40px", weight="bold", line_height="1.1", letter_spacing="0.02em"),
                rx.text("Prioridade: ", ComprovanteState.prioridade, size="3", weight="medium"),
                rx.text("Especialidade: ", ComprovanteState.especialidade, size="3"),
                rx.text("Entrada: ", ComprovanteState.entrada, size="2"),
                rx.divider(),
                rx.text(
                    "Acompanhe o painel. Sua senha será chamada até 3 vezes, com intervalo de 30 segundos. "
                    "Sem resposta, ela volta uma única vez ao fim da fila. A ordem segue a prioridade, não a chegada.",
                    size="1",
                    text_align="center",
                ),
                rx.text("Guarde este comprovante.", size="1", weight="bold"),
                spacing="2",
                align="center",
                width="72mm",
                padding="4mm",
                background="white",
                color="black",
                font_family="Inter, sans-serif",
            ),
        ),
        rx.hstack(
            rx.button("Imprimir", on_click=rx.call_script("window.print()"), size="3", background=COR_AZUL),
            rx.link(botao_secundario("Voltar à ficha"), href="/recepcao/ficha/" + ComprovanteState.ficha_id.to_string()),
            rx.link(botao_secundario("Nova identificação"), href="/recepcao"),
            spacing="3",
            wrap="wrap",
            class_name="nao-imprimir",
            padding="16px",
        ),
        background=COR_FUNDO,
        min_height="100vh",
        padding="16px",
    )


def pagina_comprovante() -> rx.Component:
    return protegido("RECEPCAO_TRIAGEM", comprovante_senha())

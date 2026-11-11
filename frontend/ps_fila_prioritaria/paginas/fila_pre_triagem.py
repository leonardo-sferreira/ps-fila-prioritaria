"""Página da fila de pré-triagem."""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_AZUL,
    COR_AZUL_BOTAO,
    COR_BORDA,
    COR_ERRO,
    COR_FUNDO,
    COR_SECUNDARIA,
    COR_SUCESSO,
    COR_SUPERFICIE,
    COR_TEXTO,
    botao_secundario,
    cabecalho,
    cartao_painel,
    menu_recepcao,
    protegido,
)
from ps_fila_prioritaria.estados.fila_pre_triagem import FilaTicketsState


def chip_tipo_ticket(ticket: dict[str, Any]) -> rx.Component:
    """Chip colorido do tipo, como na tela 2 do Figma."""
    return rx.box(
        rx.text(ticket["nome_tipo"], size="2", weight="medium", color=ticket["cor_tipo"]),
        background=ticket["cor_tipo"].to(str) + "1F",
        border_radius="999px",
        padding="3px 14px",
        width="fit-content",
    )


def cartao_chamado(ticket: dict[str, Any]) -> rx.Component:
    """Ticket em chamada: código grande, chamada atual, contagem e ações da Recepção (chamada manual, sem avanço automático)."""
    presente = ticket["presente"].to(bool)
    # Contagem em zero (ou desconhecida, -1) libera os botões; o Xano valida o prazo de qualquer forma.
    aguardando_intervalo = ticket["segundos_restantes"].to(int) > 0
    pode_chamar_novamente = ticket["pode_chamar_novamente"].to(bool)
    return cartao_painel(
        rx.hstack(
            rx.vstack(
                rx.text(rx.cond(presente, "PRESENTE — PRONTO PARA IDENTIFICAR", "CHAMANDO AGORA"), size="1", weight="medium",
                        color=rx.cond(presente, COR_SUCESSO, COR_SECUNDARIA)),
                rx.text(ticket["senha_exibida"], weight="bold", font_size="44px", line_height="1.1", color=ticket["cor_tipo"]),
                rx.hstack(
                    chip_tipo_ticket(ticket),
                    rx.text(ticket["tentativas"], "ª chamada", size="2", color=COR_TEXTO),
                    rx.cond(ticket["oportunidade"].to(int) > 1, rx.text("· 2ª oportunidade", size="2", color=COR_SECUNDARIA)),
                    rx.cond(~presente & aguardando_intervalo,
                            rx.text("· ", rx.cond(pode_chamar_novamente, "Chamar novamente e Não compareceu liberam", "Não compareceu libera"),
                                    " em ", ticket["segundos_restantes"], " s", size="2", color=COR_SECUNDARIA)),
                    align="center",
                    spacing="2",
                    wrap="wrap",
                ),
                spacing="2",
                align="start",
            ),
            rx.spacer(),
            rx.hstack(
                botao_secundario("Desistência", on_click=FilaTicketsState.acao(ticket["id"], "DESISTENCIA")),
                rx.cond(
                    ~presente,
                    rx.hstack(
                        rx.cond(
                            pode_chamar_novamente,
                            botao_secundario("Chamar novamente", on_click=FilaTicketsState.chamar_novamente(ticket["id"]), disabled=aguardando_intervalo),
                        ),
                        botao_secundario("Não compareceu", on_click=FilaTicketsState.nao_compareceu(ticket["id"]), disabled=aguardando_intervalo),
                        spacing="3",
                        wrap="wrap",
                    ),
                ),
                rx.cond(
                    presente,
                    rx.button("Identificar paciente", on_click=FilaTicketsState.identificar(ticket["id"]), size="3", background=COR_AZUL_BOTAO),
                    rx.button("Marcar presente", on_click=FilaTicketsState.acao(ticket["id"], "PRESENTE"), size="3", background=COR_SUCESSO),
                ),
                spacing="3",
                wrap="wrap",
            ),
            align="center",
            spacing="4",
            wrap="wrap",
            width="100%",
        ),
        border_left=rx.cond(presente, f"8px solid {COR_SUCESSO}", f"8px solid {COR_AZUL}"),
        padding="20px 28px",
    )


def linha_ticket_aguardando(ticket: dict[str, Any], indice: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(indice + 1, "º", size="2", color=COR_SECUNDARIA, width="48px"),
        rx.text(ticket["senha_exibida"], weight="bold", size="4", color=ticket["cor_tipo"], width="120px"),
        rx.box(chip_tipo_ticket(ticket), width="180px"),
        rx.text(ticket["emitido_hora"], size="3", color=COR_TEXTO, width="120px"),
        rx.text(rx.cond(ticket["oportunidade"].to(int) > 1, "2ª oportunidade", ""), size="2", color=COR_SECUNDARIA, flex="1"),
        rx.button("Desistência", on_click=FilaTicketsState.acao(ticket["id"], "DESISTENCIA"), variant="ghost", color_scheme="gray", size="2"),
        align="center",
        width="100%",
        padding="12px 16px",
        border_radius="8px",
        background=rx.cond(indice % 2 == 1, COR_FUNDO, "transparent"),
    )


def resumo_tipo(item: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.box(width="10px", height="10px", border_radius="50%", background=item["cor"]),
        rx.text(item["nome"], size="2", color=COR_TEXTO),
        rx.text(item["quantidade"], size="2", weight="bold", color=COR_TEXTO),
        align="center",
        spacing="2",
        padding="6px 14px",
        border=f"1px solid {COR_BORDA}",
        border_radius="999px",
        background=COR_SUPERFICIE,
    )


def pagina_fila_tickets() -> rx.Component:
    cabecalho_tabela = rx.hstack(
        *[rx.text(rotulo, size="1", weight="medium", color=COR_SECUNDARIA, **props) for rotulo, props in (
            ("ORDEM", {"width": "48px"}), ("TICKET", {"width": "120px"}), ("TIPO", {"width": "180px"}),
            ("RETIRADO ÀS", {"width": "120px"}), ("", {"flex": "1"}),
        )],
        width="100%",
        padding="0 16px 10px",
        border_bottom=f"1px solid {COR_BORDA}",
    )
    return protegido(
        "RECEPCAO_TRIAGEM",
        rx.box(
            cabecalho("RECEPÇÃO/TRIAGEM — FILA DE PRÉ-TRIAGEM", "Chame os tickets retirados no Totem e confirme a presença"),
            menu_recepcao("/recepcao/fila"),
            rx.center(
                rx.vstack(
                    rx.hstack(
                        rx.button("Chamar próximo", on_click=FilaTicketsState.proximo, size="3", background=COR_AZUL_BOTAO, min_width="200px"),
                        botao_secundario("Atualizar", on_click=FilaTicketsState.carregar),
                        rx.spacer(),
                        rx.foreach(FilaTicketsState.resumo_tipos, resumo_tipo),
                        align="center",
                        spacing="3",
                        wrap="wrap",
                        width="100%",
                    ),
                    rx.cond(
                        FilaTicketsState.mensagem != "",
                        rx.text(FilaTicketsState.mensagem, size="2", color=rx.cond(FilaTicketsState.erro, COR_ERRO, COR_SUCESSO)),
                    ),
                    rx.cond(
                        FilaTicketsState.chamados.length() > 0,
                        rx.vstack(rx.foreach(FilaTicketsState.chamados, cartao_chamado), spacing="3", width="100%"),
                    ),
                    rx.hstack(
                        rx.text("Aguardando chamada", weight="bold", size="5", color=COR_TEXTO),
                        rx.text("(ordem de chegada; a chamada alterna prioritários e normais)", size="2", color=COR_SECUNDARIA),
                        rx.spacer(),
                        rx.cond(FilaTicketsState.atualizado_em != "",
                                rx.text("Atualizado às ", FilaTicketsState.atualizado_em, size="1", color=COR_SECUNDARIA)),
                        align="baseline",
                        spacing="3",
                        wrap="wrap",
                        width="100%",
                        padding_top="8px",
                    ),
                    cartao_painel(
                        rx.cond(
                            FilaTicketsState.aguardando.length() == 0,
                            rx.text("Nenhum ticket aguardando. Os tickets retirados no Totem aparecem aqui automaticamente.",
                                    size="2", color=COR_SECUNDARIA, padding="8px 16px"),
                            rx.vstack(cabecalho_tabela, rx.foreach(FilaTicketsState.aguardando, linha_ticket_aguardando), spacing="1", width="100%"),
                        ),
                        padding="20px 16px",
                    ),
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

"""Painel público da sala de espera, para TV (add-painel-publico, D4). Sem login e sem nenhuma ação que altere dados.

Layout 16:9: à esquerda a senha atual, grande e na cor da prioridade; à direita a triagem e as últimas chamadas;
embaixo a previsão por especialidade. Fundo escuro fixo e texto grande, legível a alguns metros.
"""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.estados.painel import PainelState

FUNDO = "#0B1626"
CARTAO = "#14243A"
TEXTO = "#FFFFFF"
APAGADO = "#A9B8CC"
COR_PRIORIDADE = {"VERMELHA": "#C62828", "AMARELA": "#ED8B00", "AZUL": "#1565C0"}


def cor_de(cor: Any) -> rx.Var:
    return rx.match(cor, *[(c, hexa) for c, hexa in COR_PRIORIDADE.items()], "#455A64")


def cartao(*filhos: rx.Component, **estilo: Any) -> rx.Component:
    return rx.box(*filhos, background=CARTAO, border_radius="18px", padding="24px 28px", width="100%", **estilo)


def titulo(texto: str) -> rx.Component:
    return rx.text(texto, color=APAGADO, font_size="clamp(14px, 1.4vw, 26px)", font_weight="600", letter_spacing="0.08em",
                   text_transform="uppercase")


def bloco_atual() -> rx.Component:
    a = PainelState.atual
    return rx.box(
        rx.cond(
            a.length() > 0,
            rx.vstack(
                titulo("Senha chamada"),
                rx.text(a["senha"], color=TEXTO, font_size="clamp(64px, 9vw, 190px)", font_weight="800", line_height="1",
                        letter_spacing="0.02em"),
                rx.text(a["destino"], color=TEXTO, font_size="clamp(28px, 3.4vw, 64px)", font_weight="700"),
                rx.hstack(
                    rx.cond(a["tentativa"] != "", rx.text(a["tentativa"], color=TEXTO, font_size="clamp(18px, 2vw, 36px)",
                                                          font_weight="700", background="rgba(0,0,0,0.25)", padding="4px 16px",
                                                          border_radius="999px")),
                    rx.text(a["hora"], color=TEXTO, opacity="0.85", font_size="clamp(18px, 2vw, 36px)"),
                    spacing="4", align="center",
                ),
                spacing="3", justify="center", height="100%",
            ),
            rx.vstack(titulo("Senha chamada"), rx.text("Aguardando chamadas", color=TEXTO, font_size="clamp(28px, 3vw, 56px)",
                                                       font_weight="700"), spacing="3", justify="center", height="100%"),
        ),
        # A key muda a cada novidade e remonta o bloco, o que reinicia a animação de destaque.
        key=PainelState.destaques.to_string(),
        class_name=rx.cond(PainelState.destaques > 0, "ps-painel-destaque", ""),
        background=rx.cond(a.length() > 0, cor_de(a["cor"]), CARTAO),
        border_radius="24px", padding="clamp(24px, 3vw, 56px)", height="100%", width="100%",
    )


def linha_ultima(u: Any) -> rx.Component:
    return rx.hstack(
        rx.box(width="14px", height="14px", border_radius="50%", background=cor_de(u["cor"]), flex_shrink="0"),
        rx.text(u["senha"], color=TEXTO, font_size="clamp(20px, 2.2vw, 40px)", font_weight="700", min_width="40%"),
        rx.text(u["destino"], color=APAGADO, font_size="clamp(14px, 1.4vw, 26px)", flex="1"),
        rx.text(u["hora"], color=APAGADO, font_size="clamp(14px, 1.4vw, 26px)"),
        align="center", spacing="3", width="100%", padding="10px 0", border_bottom="1px solid rgba(255,255,255,0.08)",
    )


def bloco_lateral() -> rx.Component:
    t = PainelState.triagem
    return rx.vstack(
        cartao(
            titulo("Triagem"),
            rx.cond(
                t.length() > 0,
                rx.hstack(
                    rx.text("Senha ", t["ticket"], color=TEXTO, font_size="clamp(28px, 3.4vw, 64px)", font_weight="800"),
                    rx.vstack(rx.cond(t["tentativa"] != "", rx.text(t["tentativa"], color=TEXTO, font_size="clamp(14px, 1.4vw, 26px)",
                                                                    font_weight="700")),
                              rx.text(t["hora"], color=APAGADO, font_size="clamp(14px, 1.4vw, 26px)"), spacing="0"),
                    align="center", spacing="5",
                ),
                rx.text("Nenhum ticket chamado", color=APAGADO, font_size="clamp(18px, 2vw, 34px)"),
            ),
        ),
        cartao(
            titulo("Últimas chamadas"),
            rx.cond(PainelState.ultimas.length() == 0, rx.text("—", color=APAGADO, font_size="clamp(18px, 2vw, 34px)")),
            rx.foreach(PainelState.ultimas, linha_ultima),
            flex="1",
        ),
        spacing="4", height="100%", width="100%",
    )


def coluna_previsao(p: Any) -> rx.Component:
    return rx.box(
        rx.text(p["especialidade"], color=TEXTO, font_size="clamp(16px, 1.6vw, 30px)", font_weight="700", margin_bottom="8px"),
        rx.cond(
            p["senhas"].to(list).length() == 0,
            rx.text("Fila vazia", color=APAGADO, font_size="clamp(14px, 1.3vw, 24px)"),
            rx.vstack(
                rx.foreach(p["senhas"].to(list[dict[str, str]]), lambda s, i: rx.hstack(
                    rx.text(i + 1, "º", color=APAGADO, font_size="clamp(14px, 1.3vw, 24px)", min_width="1.8em"),
                    rx.box(width="12px", height="12px", border_radius="50%", background=cor_de(s["cor"]), flex_shrink="0"),
                    rx.text(s["senha"], color=TEXTO, font_size="clamp(16px, 1.6vw, 30px)", font_weight="600", white_space="nowrap"),
                    align="center", spacing="2")),
                spacing="1",
            ),
        ),
        background=CARTAO, border_radius="14px", padding="16px 20px", min_width="200px", flex="1",
    )


def painel() -> rx.Component:
    return rx.box(
        rx.moment(interval=3000, on_change=lambda _: PainelState.atualizar, display="none"),
        rx.cond(
            ~PainelState.som_ativo,
            rx.button("Toque para ativar o som", on_click=PainelState.ativar_som, position="fixed", top="16px", right="16px",
                      size="3", z_index="10", background="#FFFFFF", color=FUNDO, cursor="pointer"),
        ),
        rx.cond(
            PainelState.reconectando,
            rx.text("Reconectando… mostrando a última informação recebida", position="fixed", bottom="12px", right="16px",
                    color="#FFD54F", font_size="clamp(12px, 1.1vw, 20px)", z_index="10"),
        ),
        rx.cond(PainelState.aviso != "", rx.callout(PainelState.aviso, color_scheme="orange", margin_bottom="16px")),
        rx.grid(
            bloco_atual(),
            bloco_lateral(),
            grid_template_columns=rx.breakpoints(initial="1fr", md="3fr 2fr"),
            gap="20px", width="100%", min_height="58vh",
        ),
        rx.box(
            rx.hstack(titulo("Próximas senhas por especialidade"),
                      rx.text("Previsão sujeita a mudança: pacientes mais graves são chamados antes.", color=APAGADO,
                              font_size="clamp(12px, 1.1vw, 20px)"),
                      justify="between", align="end", wrap="wrap", width="100%", margin_bottom="12px"),
            rx.flex(rx.foreach(PainelState.previsoes, coluna_previsao), gap="14px", wrap="wrap", width="100%"),
            margin_top="20px",
        ),
        background=FUNDO, min_height="100vh", padding="clamp(16px, 2vw, 36px)", font_family="Inter, sans-serif",
    )

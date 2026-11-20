"""Painel público da sala de espera (add-painel-publico; tela 5 do Figma, "Painel público — Chamando o paciente").

Sem login e sem nenhuma ação que altere dados. Cabeçalho padrão com data e hora, cartão "Chamando agora" com a senha
atual, cartão da triagem com o último ticket chamado e a tabela das últimas chamadas. Decisão do PO (20/11/2026): o
painel não mostra a previsão das próximas senhas, só a chamada atual e as que já foram chamadas.
"""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_AZUL,
    COR_BORDA,
    COR_FUNDO,
    COR_HOVER,
    COR_MARINHO,
    COR_SECUNDARIA,
    COR_SUPERFICIE,
    COR_TEXTO,
    cabecalho,
)
from ps_fila_prioritaria.estados.painel import PainelState

# Faixa lateral do cartão na cor clínica da senha (mesmas variáveis do painel do plantão, claro e escuro).
COR_CLINICA = {"VERMELHA": "var(--ps-clinica-vermelha)", "AMARELA": "var(--ps-clinica-amarela)", "AZUL": "var(--ps-clinica-azul)"}
SOMBRA = "0 2px 8px rgba(18, 60, 107, 0.08)"


def cor_clinica(cor: Any) -> rx.Var:
    return rx.match(cor, *COR_CLINICA.items(), COR_AZUL)


def rotulo(texto: Any) -> rx.Component:
    return rx.text(texto, size="2", weight="medium", color=COR_SECUNDARIA, text_transform="uppercase", letter_spacing="0.04em")


def cartao_atual() -> rx.Component:
    a = PainelState.atual
    return rx.box(
        rx.cond(
            a.length() > 0,
            rx.vstack(
                rotulo("Chamando agora"),
                rx.text(a["senha"], weight="bold", font_size="clamp(56px, 7vw, 120px)", line_height="1.05", color=COR_MARINHO),
                rx.text("Dirija-se à ", a["destino"], " · ", a["tentativa"], size="5", color=COR_TEXTO),
                spacing="3",
            ),
            rx.vstack(rotulo("Chamando agora"), rx.text("Aguardando a próxima chamada", size="6", weight="medium", color=COR_SECUNDARIA),
                      spacing="3"),
        ),
        # A key muda a cada chamada nova ou repetida e remonta o cartão, o que reinicia o destaque.
        key=PainelState.destaques.to_string(),
        class_name=rx.cond(PainelState.destaques > 0, "ps-painel-destaque", ""),
        background=COR_SUPERFICIE,
        border=f"1px solid {COR_BORDA}",
        border_left=rx.cond(a.length() > 0, "8px solid " + cor_clinica(a["cor"]).to(str), f"8px solid {COR_BORDA}"),
        border_radius="16px",
        box_shadow=SOMBRA,
        padding="32px 48px",
        width="100%",
        min_height="200px",
        display="flex",
        align_items="center",
    )


def cartao_triagem() -> rx.Component:
    t = PainelState.triagem
    return rx.center(
        rx.vstack(
            rx.box(width="8px", height="8px", border_radius="50%", background=COR_AZUL),
            rx.text("Triagem · Ticket chamado", size="1", weight="bold", color=COR_SECUNDARIA, text_transform="uppercase"),
            rx.cond(
                t.length() > 0,
                rx.fragment(
                    rx.text(t["ticket"], weight="bold", font_size="clamp(36px, 4vw, 64px)", line_height="1.1", color=COR_MARINHO),
                    rx.text(t["tentativa"], size="2", color=COR_TEXTO),
                ),
                rx.text("—", weight="bold", font_size="clamp(36px, 4vw, 64px)", line_height="1.1", color=COR_SECUNDARIA),
            ),
            rx.text("Dirija-se à Recepção/Triagem", size="2", color=COR_SECUNDARIA),
            align="center",
            spacing="2",
        ),
        background=COR_SUPERFICIE,
        border=f"1px solid {COR_BORDA}",
        border_radius="16px",
        box_shadow=SOMBRA,
        padding="24px",
        width="100%",
        min_height="200px",
    )


COLUNAS = [("Senha", "30%"), ("Especialidade", "30%"), ("Sala", "20%"), ("Horário", "20%")]


def linha_ultima(u: Any, i: Any) -> rx.Component:
    return rx.hstack(
        rx.text(u["senha"], size="4", weight="bold", color=COR_TEXTO, width="30%"),
        rx.text(u["especialidade"], size="3", color=COR_TEXTO, width="30%"),
        rx.text(u["sala"], size="3", color=COR_TEXTO, width="20%"),
        rx.text(u["hora"], size="3", color=COR_TEXTO, width="20%"),
        padding="14px 24px",
        width="100%",
        align="center",
        background=rx.cond(i % 2 == 1, COR_HOVER, "transparent"),
        border_radius="8px",
    )


def tabela_ultimas() -> rx.Component:
    return rx.vstack(
        rx.text("Últimas chamadas", size="4", weight="bold", color=COR_TEXTO),
        rx.box(
            rx.hstack(*[rx.text(nome, size="1", weight="bold", color=COR_SECUNDARIA, text_transform="uppercase", width=largura)
                        for nome, largura in COLUNAS],
                      padding="14px 24px", width="100%", border_bottom=f"1px solid {COR_BORDA}"),
            rx.cond(
                PainelState.ultimas.length() == 0,
                rx.text("Nenhuma chamada anterior.", size="3", color=COR_SECUNDARIA, padding="16px 24px"),
                rx.vstack(rx.foreach(PainelState.ultimas, linha_ultima), spacing="0", padding="8px", width="100%"),
            ),
            background=COR_SUPERFICIE,
            border=f"1px solid {COR_BORDA}",
            border_radius="12px",
            box_shadow=SOMBRA,
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def painel() -> rx.Component:
    return rx.box(
        rx.moment(interval=5000, on_change=lambda _: PainelState.atualizar, display="none"),
        cabecalho("PAINEL DE CHAMADAS", "Sistema de Gerenciamento de Filas Prioritárias", com_sessao=False),
        rx.vstack(
            rx.cond(PainelState.aviso != "", rx.callout(PainelState.aviso, color_scheme="orange", width="100%")),
            rx.grid(cartao_atual(), cartao_triagem(), grid_template_columns=rx.breakpoints(initial="1fr", md="2.2fr 1fr"),
                    gap="24px", width="100%"),
            tabela_ultimas(),
            spacing="6",
            padding="36px 48px",
            width="100%",
            max_width="1440px",
            margin="0 auto",
        ),
        rx.center(
            rx.cond(PainelState.reconectando,
                    rx.text("Reconectando… mostrando a última informação recebida.", size="1", weight="medium", color="var(--ps-alerta)")),
            padding="16px",
            width="100%",
        ),
        rx.cond(
            ~PainelState.som_ativo,
            rx.button("Toque para ativar o som", on_click=PainelState.ativar_som, variant="soft", size="2", position="fixed",
                      bottom="16px", right="16px", cursor="pointer"),
        ),
        background=COR_FUNDO,
        font_family="Inter, sans-serif",
        min_height="100vh",
        width="100%",
    )

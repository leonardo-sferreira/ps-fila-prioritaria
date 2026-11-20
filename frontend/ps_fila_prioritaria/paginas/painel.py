"""Painéis públicos da sala de espera (add-painel-publico; tela 5 do Figma, D4 e D6).

Sem login e sem nenhuma ação que altere dados. Decisão do PO (20/11/2026): duas telas, cada uma numa TV.
- /painel/medico: cartão "Chamando agora" com a senha chamada pelo médico e a tabela das últimas chamadas.
- /painel/triagem: cartão "Chamando agora" com o ticket chamado pela Recepção/Triagem e os últimos tickets.
/painel só oferece os dois endereços. Nenhuma tela mostra a previsão das próximas senhas.
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
# Intervalo da atualização (D2): o plano do Xano aceita poucas requisições por janela de 20 s para o sistema inteiro.
INTERVALO_MS = 5000
SUBTITULO = "Sistema de Gerenciamento de Filas Prioritárias"
COLUNAS_MEDICO = [("Senha", "30%"), ("Especialidade", "30%"), ("Sala", "20%"), ("Horário", "20%")]
COLUNAS_TRIAGEM = [("Ticket", "60%"), ("Horário", "40%")]


def cor_clinica(cor: Any) -> rx.Var:
    return rx.match(cor, *COR_CLINICA.items(), COR_AZUL)


def rotulo(texto: Any) -> rx.Component:
    return rx.text(texto, size="2", weight="medium", color=COR_SECUNDARIA, text_transform="uppercase", letter_spacing="0.04em")


def aguardando() -> rx.Component:
    return rx.vstack(rotulo("Chamando agora"), rx.text("Aguardando a próxima chamada", size="6", weight="medium", color=COR_SECUNDARIA),
                     spacing="3")


def cartao_destaque(conteudo: rx.Component, borda: Any) -> rx.Component:
    return rx.box(
        conteudo,
        # A key muda a cada chamada nova ou repetida e remonta o cartão, o que reinicia o destaque.
        key=PainelState.destaques.to_string(),
        class_name=rx.cond(PainelState.destaques > 0, "ps-painel-destaque", ""),
        background=COR_SUPERFICIE,
        border=f"1px solid {COR_BORDA}",
        border_left=borda,
        border_radius="16px",
        box_shadow=SOMBRA,
        padding="40px 48px",
        width="100%",
        min_height="240px",
        display="flex",
        align_items="center",
    )


def cartao_medico() -> rx.Component:
    a = PainelState.atual
    return cartao_destaque(
        rx.cond(
            a.length() > 0,
            rx.vstack(
                rotulo("Chamando agora"),
                rx.text(a["senha"], weight="bold", font_size="clamp(56px, 8vw, 140px)", line_height="1.05", color=COR_MARINHO),
                rx.text("Dirija-se à ", a["destino"], " · ", a["tentativa"], size="5", color=COR_TEXTO),
                spacing="3",
            ),
            aguardando(),
        ),
        rx.cond(a.length() > 0, "8px solid " + cor_clinica(a["cor"]).to(str), f"8px solid {COR_BORDA}"),
    )


def cartao_triagem() -> rx.Component:
    t = PainelState.triagem
    return cartao_destaque(
        rx.cond(
            t.length() > 0,
            rx.vstack(
                rotulo("Chamando agora"),
                rx.text(t["ticket"], weight="bold", font_size="clamp(56px, 8vw, 140px)", line_height="1.05", color=COR_MARINHO),
                rx.text("Dirija-se à Recepção/Triagem · ", t["tentativa"], size="5", color=COR_TEXTO),
                spacing="3",
            ),
            aguardando(),
        ),
        rx.cond(t.length() > 0, f"8px solid {COR_AZUL}", f"8px solid {COR_BORDA}"),
    )


def celula(valor: Any, largura: str, destaque: bool = False) -> rx.Component:
    return rx.text(valor, size="4" if destaque else "3", weight="bold" if destaque else "regular", color=COR_TEXTO, width=largura)


def linha_medico(u: Any, i: Any) -> rx.Component:
    return linha(i, celula(u["senha"], "30%", True), celula(u["especialidade"], "30%"), celula(u["sala"], "20%"), celula(u["hora"], "20%"))


def linha_triagem(t: Any, i: Any) -> rx.Component:
    return linha(i, celula(t["ticket"], "60%", True), celula(t["hora"], "40%"))


def linha(i: Any, *celulas: rx.Component) -> rx.Component:
    return rx.hstack(*celulas, padding="14px 24px", width="100%", align="center",
                     background=rx.cond(i % 2 == 1, COR_HOVER, "transparent"), border_radius="8px")


def tabela(titulo: str, colunas: list[tuple[str, str]], itens: Any, desenhar: Any) -> rx.Component:
    return rx.vstack(
        rx.text(titulo, size="4", weight="bold", color=COR_TEXTO),
        rx.box(
            rx.hstack(*[rx.text(nome, size="1", weight="bold", color=COR_SECUNDARIA, text_transform="uppercase", width=largura)
                        for nome, largura in colunas],
                      padding="14px 24px", width="100%", border_bottom=f"1px solid {COR_BORDA}"),
            rx.cond(
                itens.length() == 0,
                rx.text("Nenhuma chamada anterior.", size="3", color=COR_SECUNDARIA, padding="16px 24px"),
                rx.vstack(rx.foreach(itens, desenhar), spacing="0", padding="8px", width="100%"),
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


def layout_painel(titulo: str, *conteudo: rx.Component) -> rx.Component:
    return rx.box(
        rx.moment(interval=INTERVALO_MS, on_change=lambda _: PainelState.atualizar, display="none"),
        cabecalho(titulo, SUBTITULO, com_sessao=False),
        rx.vstack(
            rx.cond(PainelState.aviso != "", rx.callout(PainelState.aviso, color_scheme="orange", width="100%")),
            *conteudo,
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


def painel_medico() -> rx.Component:
    return layout_painel("PAINEL DE CHAMADAS — CONSULTÓRIOS", cartao_medico(),
                         tabela("Últimas chamadas", COLUNAS_MEDICO, PainelState.ultimas, linha_medico))


def painel_triagem() -> rx.Component:
    return layout_painel("PAINEL DE CHAMADAS — TRIAGEM", cartao_triagem(),
                         tabela("Últimos tickets chamados", COLUNAS_TRIAGEM, PainelState.triagem_ultimas, linha_triagem))


def opcao(titulo: str, descricao: str, href: str) -> rx.Component:
    return rx.link(
        rx.vstack(rx.text(titulo, size="5", weight="bold", color=COR_TEXTO), rx.text(descricao, size="2", color=COR_SECUNDARIA),
                  rx.text(href, size="2", weight="medium", color=COR_AZUL), spacing="2"),
        href=href, underline="none", background=COR_SUPERFICIE, border=f"1px solid {COR_BORDA}", border_radius="16px",
        box_shadow=SOMBRA, padding="28px", flex="1", _hover={"border_color": COR_AZUL},
    )


def painel_escolha() -> rx.Component:
    """/painel: cada TV abre o painel do seu local."""
    return rx.box(
        cabecalho("PAINEL DE CHAMADAS", SUBTITULO, com_sessao=False),
        rx.vstack(
            rx.text("Escolha o painel desta TV", size="6", weight="bold", color=COR_TEXTO),
            rx.flex(
                opcao("Consultórios", "Senha chamada pelo médico, com especialidade e Sala, e as últimas chamadas.", "/painel/medico"),
                opcao("Triagem", "Ticket chamado pela Recepção/Triagem e os últimos tickets chamados.", "/painel/triagem"),
                gap="24px", width="100%", direction=rx.breakpoints(initial="column", md="row"),
            ),
            spacing="5", padding="48px", width="100%", max_width="1100px", margin="0 auto",
        ),
        background=COR_FUNDO, font_family="Inter, sans-serif", min_height="100vh", width="100%",
    )

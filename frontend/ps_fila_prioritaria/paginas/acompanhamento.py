"""Fila geral e detalhe da ficha do Administrador, só leitura (add-acompanhamento-administrador, D4)."""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.componentes import COR_BORDA, COR_HOVER, COR_SECUNDARIA, COR_TEXTO, botao_secundario
from ps_fila_prioritaria.estados.acompanhamento import CORES_FILTRO, STATUS_FILTRO, FichaAdminState, FilaGeralState
from ps_fila_prioritaria.paginas.cadastros import cabecalho_colunas, celula, layout_admin, mensagem, painel, texto

COR_SELO = {"VERMELHA": "#C62828", "AMARELA": "#ED8B00", "AZUL": "#1565C0"}
COLUNAS = [("SENHA", "130px"), ("COR", "150px"), ("ESPECIALIDADE", "160px"), ("STATUS", "120px"), ("SITUAÇÃO", None), ("ESPERA", "110px"), ("", "90px")]


def selo_cor(cor: Any, nome: Any) -> rx.Component:
    return rx.hstack(
        rx.box(width="10px", height="10px", border_radius="50%",
               background=rx.match(cor, *[(c, hexa) for c, hexa in COR_SELO.items()], "#9E9E9E")),
        rx.text(nome, size="2", color=COR_TEXTO),
        spacing="2",
        align="center",
    )


def linha(f: Any) -> rx.Component:
    return rx.hstack(
        celula(texto(f["senha"], weight="bold"), "130px"),
        celula(rx.vstack(selo_cor(f["cor"], f["cor_nome"]),
                         rx.cond(f["condicao"] != "", rx.text(f["condicao"], size="1", color=COR_SECUNDARIA)), spacing="0"), "150px"),
        celula(texto(f["especialidade"], color=COR_SECUNDARIA), "160px"),
        celula(texto(f["status_nome"]), "120px"),
        celula(texto(f["detalhe"], color=COR_SECUNDARIA), None),
        celula(texto(f["espera"]), "110px"),
        celula(rx.link(rx.button("Detalhe", variant="ghost", size="1", color_scheme="gray"), href="/admin/fichas/" + f["id"].to_string()), "90px"),
        align="center",
        spacing="3",
        width="100%",
        padding="10px 16px",
        border_bottom=f"1px solid {COR_BORDA}",
        _hover={"background": COR_HOVER},
    )


def seletor(rotulo: str, valor: Any, ao_mudar: Any, *itens: rx.Component, largura: str = "200px") -> rx.Component:
    return rx.vstack(
        rx.text(rotulo, size="1", color=COR_SECUNDARIA),
        rx.select.root(rx.select.trigger(width=largura), rx.select.content(*itens), value=valor, on_change=ao_mudar, size="2"),
        spacing="1",
    )


def pagina_fila_geral() -> rx.Component:
    st = FilaGeralState
    return layout_admin(
        "/admin/fila-geral",
        "Fila geral",
        "Todas as fichas em andamento no plantão, só para acompanhamento. As que aguardam aparecem na ordem prevista de chamada "
        "de cada especialidade. Atualiza sozinha a cada 10 segundos. Nome e CPF dos pacientes não aparecem aqui.",
        rx.flex(
            seletor("Especialidade", st.especialidade_id, st.set_especialidade, rx.select.item("Todas", value="0"),
                    rx.foreach(st.opcoes_especialidades, lambda e: rx.select.item(e["nome"], value=e["id"]))),
            seletor("Cor", st.cor, st.set_cor, *[rx.select.item(nome, value=valor) for valor, nome in CORES_FILTRO], largura="170px"),
            seletor("Status", st.status, st.set_status, *[rx.select.item(nome, value=valor) for valor, nome in STATUS_FILTRO], largura="170px"),
            rx.spacer(),
            rx.vstack(
                rx.text(st.resumo, size="2", color=COR_TEXTO),
                rx.cond(st.atualizado_em != "", rx.text("Atualizado às ", st.atualizado_em, size="1", color=COR_SECUNDARIA)),
                spacing="0",
                align="end",
            ),
            botao_secundario("Atualizar", on_click=st.atualizar, loading=st.carregando),
            rx.moment(interval=10000, on_change=lambda _: FilaGeralState.atualizar, display="none"),
            align="end",
            gap="12px",
            wrap="wrap",
            width="100%",
        ),
        mensagem(st),
        painel(rx.cond(
            st.carregando & (st.itens.length() == 0),
            rx.center(rx.spinner(), padding="24px"),
            rx.cond(
                st.itens.length() == 0,
                rx.text("Nenhuma ficha em andamento neste filtro.", size="2", color=COR_SECUNDARIA, padding="20px 16px"),
                rx.box(rx.vstack(cabecalho_colunas(COLUNAS), rx.foreach(st.itens, linha), spacing="0", min_width="900px"),
                       overflow_x="auto", width="100%"),
            ),
        )),
    )


def campo_leitura(rotulo: str, valor: Any) -> rx.Component:
    return rx.vstack(rx.text(rotulo, size="1", color=COR_SECUNDARIA), rx.text(valor, size="2", color=COR_TEXTO, weight="medium"), spacing="0")


def secao(titulo: str, *conteudo: rx.Component) -> rx.Component:
    return painel(rx.vstack(rx.text(titulo, size="3", weight="bold", color=COR_TEXTO), *conteudo, spacing="3", width="100%"), padding="16px 20px")


def pagina_ficha_admin() -> rx.Component:
    st = FichaAdminState
    f = st.ficha
    return layout_admin(
        "/admin/fila-geral",
        "Detalhe da ficha",
        "Somente leitura: o Administrador acompanha, mas não altera a ficha.",
        rx.link(botao_secundario("Voltar à fila geral"), href="/admin/fila-geral"),
        rx.cond(st.mensagem != "", rx.callout(st.mensagem, color_scheme="red", width="100%")),
        rx.cond(
            st.carregando,
            rx.center(rx.spinner(), padding="24px"),
            rx.cond(
                f.length() > 0,
                rx.vstack(
                    secao("Situação",
                          rx.grid(campo_leitura("Senha atual", f["senha"].to(str)), campo_leitura("Senhas que a ficha teve", f["senhas"].to(str)),
                                  campo_leitura("Status", f["status"].to(str)), campo_leitura("Cor", f["cor"].to(str)),
                                  campo_leitura("Escore", f["escore"].to(str)), campo_leitura("Condição prioritária", f["condicao"].to(str)),
                                  campo_leitura("Chegada", f["chegada"].to(str)), campo_leitura("Especialidade sugerida", f["sugerida"].to(str)),
                                  campo_leitura("Especialidade atribuída", f["atribuida"].to(str)),
                                  columns=rx.breakpoints(initial="2", md="3"), gap="12px", width="100%"),
                          rx.cond(f["ajuste"].to(str) != "", rx.callout(f["ajuste"].to(str), color_scheme="orange", width="100%"))),
                    secao("Triagem",
                          rx.text("Sinais vitais", size="1", color=COR_SECUNDARIA),
                          rx.flex(rx.foreach(f["sinais"].to(list[dict[str, str]]), lambda s: rx.badge(s["nome"], ": ", s["valor"], size="2", variant="soft")),
                                  gap="8px", wrap="wrap"),
                          rx.text("Sintomas", size="1", color=COR_SECUNDARIA),
                          rx.flex(rx.foreach(f["sintomas"].to(list[dict[str, Any]]),
                                             lambda s: rx.badge(s["nome"], " · ", s["pontos"], " pt", size="2", variant="outline")),
                                  gap="8px", wrap="wrap"),
                          rx.cond(f["observacao"].to(str) != "", campo_leitura("Observação", f["observacao"].to(str)))),
                    secao("Chamadas",
                          rx.cond(f["chamadas"].to(list).length() == 0, rx.text("Nenhuma chamada.", size="2", color=COR_SECUNDARIA)),
                          rx.foreach(f["chamadas"].to(list[dict[str, str]]), lambda c: rx.hstack(
                              texto(c["quando"], color=COR_SECUNDARIA), texto(c["tipo"], weight="medium"), texto(c["medico"]),
                              texto(c["tentativa"], color=COR_SECUNDARIA), spacing="4", wrap="wrap"))),
                    secao("Histórico de alterações",
                          rx.cond(f["historico"].to(list).length() == 0, rx.text("Nenhuma alteração registrada.", size="2", color=COR_SECUNDARIA)),
                          rx.foreach(f["historico"].to(list[dict[str, str]]), lambda h: rx.vstack(
                              rx.hstack(texto(h["quando"], color=COR_SECUNDARIA), texto(h["evento"], weight="medium"), texto(h["usuario"]), spacing="4", wrap="wrap"),
                              rx.text("Antes: ", h["anterior"], size="1", color=COR_SECUNDARIA, word_break="break-word"),
                              rx.text("Depois: ", h["novo"], size="1", color=COR_TEXTO, word_break="break-word"),
                              rx.cond(h["justificativa"] != "", rx.text("Justificativa: ", h["justificativa"], size="1", color=COR_SECUNDARIA)),
                              spacing="0", padding_bottom="8px", border_bottom=f"1px solid {COR_BORDA}", width="100%"))),
                    spacing="4",
                    width="100%",
                ),
            ),
        ),
    )

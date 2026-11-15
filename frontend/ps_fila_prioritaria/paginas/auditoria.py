"""Tela de auditoria do Administrador, só leitura (add-acompanhamento-administrador, D4)."""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.componentes import COR_BORDA, COR_HOVER, COR_SECUNDARIA, COR_TEXTO, botao_secundario
from ps_fila_prioritaria.estados.auditoria import ORIGENS, AuditoriaState
from ps_fila_prioritaria.paginas.cadastros import cabecalho_colunas, celula, layout_admin, mensagem, painel, texto

COLUNAS = [("QUANDO", "150px"), ("QUEM", "170px"), ("O QUE ACONTECEU", "200px"), ("ONDE", "150px"), ("ANTES", None), ("DEPOIS", None)]


def linha(e: Any) -> rx.Component:
    return rx.hstack(
        celula(texto(e["quando"], color=COR_SECUNDARIA), "150px"),
        celula(rx.hstack(texto(e["usuario"], weight="medium"),
                         rx.cond(e["sistema"], rx.badge("automático", color_scheme="gray", size="1")), spacing="1", align="center"), "170px"),
        celula(rx.vstack(texto(e["evento"]), rx.text(e["origem"], size="1", color=COR_SECUNDARIA), spacing="0"), "200px"),
        celula(texto(e["alvo"], color=COR_SECUNDARIA), "150px"),
        celula(rx.text(e["anterior"], size="1", color=COR_SECUNDARIA, word_break="break-word"), None),
        celula(rx.vstack(rx.text(e["novo"], size="1", color=COR_TEXTO, word_break="break-word"),
                         rx.cond(e["justificativa"] != "", rx.text("Justificativa: ", e["justificativa"], size="1", color=COR_SECUNDARIA)),
                         spacing="1"), None),
        align="start",
        spacing="3",
        width="100%",
        padding="10px 16px",
        border_bottom=f"1px solid {COR_BORDA}",
        _hover={"background": COR_HOVER},
    )


def filtros() -> rx.Component:
    a = AuditoriaState
    return rx.flex(
        rx.vstack(rx.text("De", size="1", color=COR_SECUNDARIA), rx.input(type="date", value=a.data_inicio, on_change=a.set_data_inicio, size="2"), spacing="1"),
        rx.vstack(rx.text("Até", size="1", color=COR_SECUNDARIA), rx.input(type="date", value=a.data_fim, on_change=a.set_data_fim, size="2"), spacing="1"),
        rx.vstack(rx.text("Tipo", size="1", color=COR_SECUNDARIA), rx.select.root(
            rx.select.trigger(width="180px"),
            rx.select.content(*[rx.select.item(nome, value=valor) for valor, nome in ORIGENS]),
            value=a.origem, on_change=a.set_origem, size="2"), spacing="1"),
        rx.vstack(rx.text("Usuário", size="1", color=COR_SECUNDARIA), rx.select.root(
            rx.select.trigger(width="220px"),
            rx.select.content(rx.select.item("Todos", value="0"), rx.foreach(a.opcoes_usuarios, lambda u: rx.select.item(u["nome"], value=u["id"]))),
            value=a.usuario_id, on_change=a.set_usuario, size="2"), spacing="1"),
        rx.spacer(),
        botao_secundario("Atualizar", on_click=a.carregar, loading=a.carregando),
        rx.button(rx.icon("download", size=16), "Exportar CSV", on_click=a.exportar_csv, loading=a.exportando, size="2", variant="outline"),
        align="end",
        gap="12px",
        wrap="wrap",
        width="100%",
    )


def paginacao() -> rx.Component:
    a = AuditoriaState
    return rx.hstack(
        rx.text(a.total.to_string() + " registro(s)", size="2", color=COR_SECUNDARIA),
        rx.spacer(),
        botao_secundario("Anterior", on_click=a.pagina_anterior, disabled=a.pagina <= 1),
        rx.text("Página ", a.pagina.to_string(), " de ", a.total_paginas.to_string(), size="2", color=COR_TEXTO),
        botao_secundario("Próxima", on_click=a.proxima_pagina, disabled=a.pagina >= a.total_paginas),
        align="center",
        spacing="3",
        width="100%",
    )


def pagina_auditoria() -> rx.Component:
    a = AuditoriaState
    return layout_admin(
        "/admin/auditoria",
        "Auditoria",
        "Quem alterou o quê e quando: cadastros e regras, chamadas da fila médica e entradas e saídas do sistema. "
        "Somente leitura; os registros não podem ser editados nem apagados. \"Exportar CSV\" baixa todos os registros do filtro atual. \"Sistema\" é a carga automática dos dados iniciais.",
        filtros(),
        mensagem(a),
        painel(rx.cond(
            a.carregando & (a.itens.length() == 0),
            rx.center(rx.spinner(), padding="24px"),
            rx.cond(
                a.itens.length() == 0,
                rx.text("Nenhum registro neste período e filtro.", size="2", color=COR_SECUNDARIA, padding="20px 16px"),
                rx.box(rx.vstack(cabecalho_colunas(COLUNAS), rx.foreach(a.itens, linha), spacing="0", min_width="980px"),
                       overflow_x="auto", width="100%"),
            ),
        )),
        paginacao(),
    )

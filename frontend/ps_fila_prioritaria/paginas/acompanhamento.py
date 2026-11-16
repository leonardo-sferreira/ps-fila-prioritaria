"""Acompanhamento administrativo, sem ações de operação da fila."""
import reflex as rx

from ps_fila_prioritaria.componentes import COR_ALERTA, COR_SECUNDARIA, botao_secundario
from ps_fila_prioritaria.estados.fila_geral import CORES, STATUS, FilaGeralState
from ps_fila_prioritaria.paginas.cadastros import cabecalho_colunas, celula, layout_admin, mensagem, painel, texto
from ps_fila_prioritaria.paginas.painel_admin import equipe_agora

VISIBILIDADE = "document.visibilityState === 'visible' && window.location.pathname.replace(/\\/$/, '') === '/admin/acompanhamento'"
COLUNAS = [("FICHA / SENHA", "145px"), ("SITUAÇÃO / COR", "160px"), ("CONDIÇÃO", "110px"),
           ("ESPECIALIDADE", None), ("CHEGADA", "125px"), ("ESPERA", "90px"),
           ("POSIÇÃO NA ESP.", "100px"), ("MÉDICO / TENTATIVA", "170px")]


def linha(item: rx.Var) -> rx.Component:
    return rx.hstack(
        celula(rx.vstack(texto("Ficha #" + item["id"]), texto(item["senha"]), spacing="1"), "145px"),
        celula(rx.vstack(texto(item["status"]), texto(item["cor"], color=item["cor_css"]), spacing="1"), "160px"),
        celula(texto(item["condicao"]), "110px"),
        celula(texto(item["especialidade"]), None),
        celula(texto(item["chegada"]), "125px"),
        celula(texto(item["espera"]), "90px"),
        celula(texto(item["ordem"]), "100px"),
        celula(rx.vstack(texto(item["medico"]), texto("Tentativa: " + item["tentativa"]), spacing="1"), "170px"),
        spacing="3", width="100%", padding="12px 16px", align="center",
    )


def filtros() -> rx.Component:
    st = FilaGeralState
    return rx.flex(
        rx.select.root(
            rx.select.trigger(placeholder="Especialidade", width="220px"),
            rx.select.content(rx.select.item("Todas as especialidades", value="0"),
                              rx.foreach(st.especialidades, lambda e: rx.select.item(e["nome"], value=e["id"]))),
            value=st.especialidade_id, on_change=lambda v: st.filtrar("especialidade_id", v), disabled=st.carregando,
        ),
        rx.select.root(
            rx.select.trigger(width="150px"),
            rx.select.content(rx.select.item("Todas as cores", value="TODAS"),
                              *[rx.select.item(nome, value=cor) for cor, (nome, _) in CORES.items()]),
            value=st.cor, on_change=lambda v: st.filtrar("cor", v), disabled=st.carregando,
        ),
        rx.select.root(
            rx.select.trigger(width="170px"),
            rx.select.content(rx.select.item("Todas as situações", value="TODOS"),
                              *[rx.select.item(nome, value=status) for status, nome in STATUS.items()]),
            value=st.status, on_change=lambda v: st.filtrar("status", v), disabled=st.carregando,
        ),
        botao_secundario("Atualizar", on_click=st.carregar, disabled=st.carregando),
        rx.cond(st.carregando, rx.spinner(size="1")),
        gap="12px", wrap="wrap", align="center", width="100%",
    )


def pagina_acompanhamento() -> rx.Component:
    st = FilaGeralState
    conteudo = layout_admin(
        "/admin/acompanhamento", "Fila geral",
        "Acompanhamento somente leitura. A posição prevista vale dentro de cada especialidade; não é uma ordem global entre médicos. Atualização a cada 10 segundos enquanto esta aba estiver visível.",
        filtros(), mensagem(st),
        rx.cond(st.aviso != "", rx.text(st.aviso, color=COR_ALERTA, size="2")),
        rx.cond(st.atualizado_em != "", rx.text("Última consulta confirmada: ", st.atualizado_em, color=COR_SECUNDARIA, size="2")),
        painel(rx.cond(
            st.carregando & (st.itens.length() == 0), rx.center(rx.spinner(), padding="24px"),
            rx.cond(st.itens.length() == 0,
                    rx.text(rx.cond(st.erro, "Consulta indisponível.", "Nenhuma ficha neste filtro."), padding="20px", size="2"),
                    rx.box(rx.vstack(cabecalho_colunas(COLUNAS), rx.foreach(st.itens, linha), spacing="0", min_width="1180px"), overflow_x="auto")),
        )),
        equipe_agora(),
        rx.link("Abrir auditoria", href="/admin/auditoria"),
        rx.moment(interval=10000, on_change=lambda _: rx.call_script(VISIBILIDADE, callback=st.consultar_se_visivel), display="none"),
    )
    return rx.box(conteudo, on_unmount=st.sair)

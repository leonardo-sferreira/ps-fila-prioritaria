"""Telas de cadastro do Administrador (add-cadastros-administrador, D9).

Todas seguem o mesmo desenho: lista com filtro de situação e busca, botão "Novo", edição num diálogo e
ativar/desativar. Plantões e Parâmetros têm telas próprias.
"""

from typing import Any, Callable

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_AZUL_BOTAO,
    COR_BORDA,
    COR_ERRO,
    COR_FUNDO,
    COR_HOVER,
    COR_SECUNDARIA,
    COR_SUCESSO,
    COR_SUPERFICIE,
    COR_TEXTO,
    botao_secundario,
    cabecalho,
    menu_admin,
    protegido,
)
from ps_fila_prioritaria.estados.cadastros import (
    GRUPOS_SINTOMA,
    EspecialidadesState,
    MedicosState,
    ParametrosState,
    PlantoesState,
    RecepcaoState,
    SalasState,
    SintomasState,
)

FILTROS = [("ATIVOS", "Ativos"), ("INATIVOS", "Inativos"), ("TODOS", "Todos")]


# ---------- Peças comuns ----------

def layout_admin(rota: str, titulo: str, descricao: str, *conteudo: rx.Component) -> rx.Component:
    return protegido(
        "ADMINISTRADOR",
        rx.box(
            cabecalho("ADMINISTRADOR", "Cadastros e configuração do PS"),
            menu_admin(rota),
            rx.center(
                rx.vstack(
                    rx.vstack(
                        rx.text(titulo, size="6", weight="bold", color=COR_TEXTO),
                        rx.text(descricao, size="2", color=COR_SECUNDARIA),
                        spacing="1",
                    ),
                    *conteudo,
                    spacing="4",
                    width="min(100%, 1184px)",
                ),
                padding="28px 16px 48px",
                width="100%",
            ),
            background=COR_FUNDO,
            font_family="Inter, sans-serif",
            min_height="100vh",
            width="100%",
        ),
    )


def painel(*filhos: rx.Component, **props: Any) -> rx.Component:
    return rx.box(*filhos, background=COR_SUPERFICIE, border=f"1px solid {COR_BORDA}", border_radius="6px", width="100%", **props)


def mensagem(estado: Any) -> rx.Component:
    return rx.cond(estado.mensagem != "", rx.text(estado.mensagem, size="2", color=rx.cond(estado.erro, COR_ERRO, COR_SUCESSO)))


def barra_lista(estado: Any, rotulo_novo: str, busca: str) -> rx.Component:
    return rx.flex(
        rx.segmented_control.root(
            *[rx.segmented_control.item(rotulo, value=valor) for valor, rotulo in FILTROS],
            value=estado.filtro,
            on_change=estado.set_filtro,
            size="2",
        ),
        rx.input(
            rx.input.slot(rx.icon("search", size=16)),
            value=estado.busca,
            on_change=estado.set_busca,
            placeholder=busca,
            size="2",
            width=rx.breakpoints(initial="100%", sm="260px"),
        ),
        rx.spacer(),
        rx.button(rx.icon("plus", size=16), rotulo_novo, on_click=estado.abrir_novo, size="2", background=COR_AZUL_BOTAO),
        align="center",
        gap="12px",
        wrap="wrap",
        width="100%",
    )


def celula(conteudo: rx.Component, largura: str | None) -> rx.Component:
    return rx.box(conteudo, width=largura or "auto", flex="1" if largura is None else "0 0 auto", min_width="0")


def texto(valor: Any, **props: Any) -> rx.Component:
    return rx.text(valor, size="2", color=props.pop("color", COR_TEXTO), white_space="nowrap", overflow="hidden", text_overflow="ellipsis", **props)


def situacao(ativo: rx.Var) -> rx.Component:
    """Situação com marcador quadrado, sem pílula."""
    return rx.hstack(
        rx.box(width="8px", height="8px", background=rx.cond(ativo, COR_SUCESSO, COR_SECUNDARIA), border_radius="1px"),
        rx.text(rx.cond(ativo, "Ativo", "Inativo"), size="2", color=COR_SECUNDARIA),
        align="center",
        spacing="2",
    )


def acoes(estado: Any, item: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.button("Editar", on_click=estado.abrir_edicao(item), variant="ghost", size="1", color_scheme="gray"),
        rx.cond(
            item["ativo"],
            rx.button("Desativar", on_click=estado.alternar_ativo(item["id"], False), variant="ghost", size="1", color_scheme="red"),
            rx.button("Ativar", on_click=estado.alternar_ativo(item["id"], True), variant="ghost", size="1", color_scheme="green"),
        ),
        spacing="1",
        justify="end",
    )


def tabela(estado: Any, colunas: list[tuple[str, str | None]], celulas: Callable[[Any], list[rx.Component]], vazio: str) -> rx.Component:
    """Tabela com cabeçalho fixo de colunas; a última coluna é a de ações."""
    def linha(item: Any) -> rx.Component:
        conteudos = celulas(item) + [situacao(item["ativo"]), acoes(estado, item)]
        return rx.hstack(
            *[celula(c, largura) for c, (_, largura) in zip(conteudos, colunas + [("SITUAÇÃO", "90px"), ("", "160px")])],
            align="center",
            spacing="3",
            width="100%",
            padding="10px 16px",
            border_bottom=f"1px solid {COR_BORDA}",
            _hover={"background": COR_HOVER},
        )

    cabecalho_tabela = rx.hstack(
        *[celula(rx.text(rotulo, size="1", weight="bold", color=COR_SECUNDARIA, letter_spacing="0.06em"), largura)
          for rotulo, largura in colunas + [("SITUAÇÃO", "90px"), ("", "160px")]],
        spacing="3",
        width="100%",
        padding="12px 16px",
        border_bottom=f"1px solid {COR_BORDA}",
    )
    return painel(
        rx.cond(
            estado.carregando & (estado.itens.length() == 0),
            rx.center(rx.spinner(), padding="24px"),
            rx.cond(
                estado.itens_filtrados.length() == 0,
                rx.text(vazio, size="2", color=COR_SECUNDARIA, padding="20px 16px"),
                rx.box(
                    rx.vstack(cabecalho_tabela, rx.foreach(estado.itens_filtrados, linha), spacing="0", min_width="820px"),
                    overflow_x="auto",
                    width="100%",
                ),
            ),
        ),
    )


def campo(rotulo: str, componente: rx.Component, ajuda: str = "") -> rx.Component:
    return rx.vstack(
        rx.text(rotulo, size="1", weight="medium", color=COR_SECUNDARIA),
        componente,
        *([rx.text(ajuda, size="1", color=COR_SECUNDARIA)] if ajuda else []),
        spacing="1",
        width="100%",
    )


def entrada(estado: Any, chave: str, **props: Any) -> rx.Component:
    return rx.input(value=estado.form[chave].to(str), on_change=lambda v: estado.set_campo(chave, v), size="2", width="100%", **props)


def escolha_especialidades(estado: Any) -> rx.Component:
    """Especialidades marcáveis (quadradas, sem pílula); a ordem de marcação é a ordem de preferência."""
    def opcao(esp: Any) -> rx.Component:
        marcada = estado.form["especialidade_ids"].to(list[int]).contains(esp["id"])
        return rx.button(
            rx.cond(marcada, rx.icon("check", size=14), rx.icon("plus", size=14)),
            esp["nome"],
            on_click=estado.alternar_especialidade(esp["id"]),
            type="button",
            size="1",
            variant=rx.cond(marcada, "solid", "outline"),
            color_scheme="gray",
            radius="small",
        )

    return rx.flex(rx.foreach(estado.opcoes_especialidades, opcao), gap="6px", wrap="wrap")


def dialogo(estado: Any, titulo_novo: str, titulo_edicao: str, *campos: rx.Component) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(rx.cond(estado.editando, titulo_edicao, titulo_novo)),
            rx.vstack(
                *campos,
                rx.cond(estado.erro_form != "", rx.text(estado.erro_form, size="2", color=COR_ERRO)),
                rx.hstack(
                    rx.dialog.close(botao_secundario("Cancelar")),
                    rx.button("Salvar", on_click=estado.salvar, loading=estado.salvando, size="3", background=COR_AZUL_BOTAO),
                    justify="end",
                    spacing="3",
                    width="100%",
                ),
                spacing="3",
                margin_top="8px",
                width="100%",
            ),
            max_width="560px",
        ),
        open=estado.dialogo_aberto,
        on_open_change=estado.set_dialogo_aberto,
    )


# ---------- Especialidades ----------

def pagina_especialidades() -> rx.Component:
    e = EspecialidadesState
    return layout_admin(
        "/admin/especialidades",
        "Especialidades",
        "Filas por especialidade e siglas das senhas. A sigla não muda depois de criada; especialidade é desativada, nunca excluída.",
        barra_lista(e, "Nova especialidade", "Buscar por nome ou sigla"),
        mensagem(e),
        tabela(
            e,
            [("NOME", None), ("SIGLA", "70px"), ("DESCRIÇÃO", "300px")],
            lambda i: [texto(i["nome"], weight="medium"), texto(i["sigla"], weight="bold"), texto(i["descricao"], color=COR_SECUNDARIA)],
            "Nenhuma especialidade neste filtro.",
        ),
        dialogo(
            e, "Nova especialidade", "Editar especialidade",
            campo("Nome", entrada(e, "nome", placeholder="Ex.: Dermatologia")),
            campo("Sigla", entrada(e, "sigla", placeholder="DER", max_length=3, disabled=e.editando),
                  "3 letras, usadas na senha (ex.: A-DER-001). Não muda depois de criada."),
            campo("Descrição (opcional)", entrada(e, "descricao")),
        ),
    )


# ---------- Sintomas ----------

def pagina_sintomas() -> rx.Component:
    s = SintomasState
    return layout_admin(
        "/admin/sintomas",
        "Sintomas",
        "Catálogo usado na triagem: a pontuação soma no escore e os destinos indicam a especialidade da ficha.",
        barra_lista(s, "Novo sintoma", "Buscar por nome ou grupo"),
        mensagem(s),
        tabela(
            s,
            [("SINTOMA", None), ("GRUPO", "170px"), ("PONTOS", "70px"), ("DESTINOS", "260px")],
            lambda i: [texto(i["nome"], weight="medium"), texto(i["grupo_nome"], color=COR_SECUNDARIA),
                       texto(i["pontuacao"], weight="bold"), texto(i["destinos"], color=COR_SECUNDARIA)],
            "Nenhum sintoma neste filtro.",
        ),
        dialogo(
            s, "Novo sintoma", "Editar sintoma",
            campo("Nome", entrada(s, "nome", placeholder="Ex.: Palpitação")),
            campo("Descrição (opcional)", entrada(s, "descricao")),
            rx.grid(
                campo("Grupo", rx.select.root(
                    rx.select.trigger(width="100%"),
                    rx.select.content(*[rx.select.item(nome, value=valor) for valor, nome in GRUPOS_SINTOMA]),
                    value=s.form["grupo"].to(str),
                    on_change=lambda v: s.set_campo("grupo", v),
                )),
                campo("Pontuação", rx.segmented_control.root(
                    *[rx.segmented_control.item(p, value=p) for p in ("1", "2", "3")],
                    value=s.form["pontuacao"].to(str),
                    on_change=lambda v: s.set_campo("pontuacao", v),
                )),
                columns="2",
                gap="12px",
                width="100%",
            ),
            campo("Destinos (marque na ordem de preferência)", escolha_especialidades(s)),
            rx.text("Ordem: ", s.ordem_destinos, size="1", color=COR_SECUNDARIA),
        ),
    )


# ---------- Salas ----------

def pagina_salas() -> rx.Component:
    s = SalasState
    return layout_admin(
        "/admin/salas",
        "Salas",
        "Locais de atendimento. O médico pode ter uma sala atual; desativar a sala tira o vínculo dos médicos que a usavam.",
        barra_lista(s, "Nova sala", "Buscar por nome"),
        mensagem(s),
        tabela(
            s,
            [("SALA", None), ("DESCRIÇÃO", "320px"), ("MÉDICOS", "90px")],
            lambda i: [texto(i["nome"], weight="medium"), texto(i["descricao"], color=COR_SECUNDARIA), texto(i["medicos"])],
            "Nenhuma sala neste filtro.",
        ),
        dialogo(
            s, "Nova sala", "Editar sala",
            campo("Nome", entrada(s, "nome", placeholder="Ex.: Consultório 3")),
            campo("Descrição (opcional)", entrada(s, "descricao")),
        ),
    )


# ---------- Médicos ----------

def pagina_medicos() -> rx.Component:
    m = MedicosState
    return layout_admin(
        "/admin/medicos",
        "Médicos",
        "O cadastro cria o login do médico. As especialidades próprias orientam a chamada sem impedir o apoio a outras filas.",
        barra_lista(m, "Novo médico", "Buscar por nome, e-mail ou CRM"),
        mensagem(m),
        tabela(
            m,
            [("MÉDICO", None), ("E-MAIL", "220px"), ("CRM", "110px"), ("ESPECIALIDADES", "200px"), ("SALA", "120px")],
            lambda i: [texto(i["nome"], weight="medium"), texto(i["email"], color=COR_SECUNDARIA), texto(i["crm"]),
                       texto(i["lista_especialidades"], color=COR_SECUNDARIA), texto(i["sala"], color=COR_SECUNDARIA)],
            "Nenhum médico neste filtro.",
        ),
        dialogo(
            m, "Novo médico", "Editar médico",
            campo("Nome", entrada(m, "nome", placeholder="Nome completo")),
            rx.grid(
                campo("E-mail de login", entrada(m, "email", type="email", placeholder="nome@ps.com.br")),
                campo("CRM", entrada(m, "crm", placeholder="12345-SP")),
                columns="2",
                gap="12px",
                width="100%",
            ),
            rx.cond(
                ~m.editando,
                campo("Senha inicial", entrada(m, "senha", type="password", placeholder="8 ou mais caracteres"),
                      "O médico pode trocá-la depois em \"Esqueci minha senha\"."),
            ),
            campo("Especialidades próprias", escolha_especialidades(m)),
            campo("Sala atual", rx.select.root(
                rx.select.trigger(placeholder="Sem sala", width="100%"),
                rx.select.content(rx.select.item("Sem sala", value="0"), rx.foreach(m.opcoes_salas, lambda o: rx.select.item(o["nome"], value=o["id"]))),
                value=m.form["sala_id"].to(str),
                on_change=lambda v: m.set_campo("sala_id", v),
            )),
        ),
    )


# ---------- Recepção/Triagem ----------

def pagina_recepcao() -> rx.Component:
    r = RecepcaoState
    return layout_admin(
        "/admin/recepcao",
        "Recepção/Triagem",
        "O cadastro cria o login de quem faz a recepção e a triagem. A especialidade de referência é só cadastral.",
        barra_lista(r, "Nova pessoa", "Buscar por nome ou e-mail"),
        mensagem(r),
        tabela(
            r,
            [("NOME", None), ("E-MAIL", "240px"), ("CPF", "130px"), ("ESPECIALIDADE DE REFERÊNCIA", "200px")],
            lambda i: [texto(i["nome"], weight="medium"), texto(i["email"], color=COR_SECUNDARIA), texto(i["cpf_exibido"]),
                       texto(i["especialidade_referencia"], color=COR_SECUNDARIA)],
            "Ninguém neste filtro.",
        ),
        dialogo(
            r, "Nova pessoa da Recepção/Triagem", "Editar Recepção/Triagem",
            campo("Nome", entrada(r, "nome", placeholder="Nome completo")),
            rx.grid(
                campo("E-mail de login", entrada(r, "email", type="email", placeholder="nome@ps.com.br")),
                campo("CPF", entrada(r, "cpf", placeholder="000.000.000-00")),
                columns="2",
                gap="12px",
                width="100%",
            ),
            rx.cond(
                ~r.editando,
                campo("Senha inicial", entrada(r, "senha", type="password", placeholder="8 ou mais caracteres"),
                      "A pessoa pode trocá-la depois em \"Esqueci minha senha\"."),
            ),
            campo("Especialidade de referência (opcional)", rx.select.root(
                rx.select.trigger(placeholder="Nenhuma", width="100%"),
                rx.select.content(rx.select.item("Nenhuma", value="0"),
                                  rx.foreach(r.opcoes_especialidades, lambda o: rx.select.item(o["nome"], value=o["id"].to(str)))),
                value=r.form["especialidade_referencia_id"].to(str),
                on_change=lambda v: r.set_campo("especialidade_referencia_id", v),
            )),
        ),
    )


# ---------- Plantões ----------

def linha_plantao(p: Any) -> rx.Component:
    st = PlantoesState
    return rx.hstack(
        celula(texto(p["horario"], weight="bold"), "180px"),
        celula(texto(p["medico"], weight="medium"), None),
        celula(texto(p["especialidades"], color=COR_SECUNDARIA), "150px"),
        celula(texto(p["sala"], color=COR_SECUNDARIA), "120px"),
        celula(texto(p["situacao"], color=COR_SECUNDARIA), "110px"),
        celula(
            rx.hstack(
                rx.cond(p["situacao"] != "Encerrado",
                        rx.button("Editar", on_click=st.abrir_edicao(p), variant="ghost", size="1", color_scheme="gray")),
                rx.cond(~p["iniciado"],
                        rx.button("Remover", on_click=st.remover(p["id"]), variant="ghost", size="1", color_scheme="red")),
                spacing="1",
                justify="end",
            ),
            "150px",
        ),
        align="center",
        spacing="3",
        width="100%",
        padding="10px 16px",
        border_bottom=f"1px solid {COR_BORDA}",
        _hover={"background": COR_HOVER},
    )


def pagina_plantoes() -> rx.Component:
    st = PlantoesState
    return layout_admin(
        "/admin/disponibilidade",
        "Plantões",
        "Períodos em que cada médico está de plantão (horário de Brasília). Fim menor que o início termina no dia seguinte.",
        rx.flex(
            rx.input(type="date", value=st.data, on_change=st.mudar_dia, size="2", width="180px"),
            botao_secundario("Atualizar", on_click=st.carregar, loading=st.carregando),
            rx.spacer(),
            rx.button(rx.icon("plus", size=16), "Novo plantão", on_click=st.abrir_novo, size="2", background=COR_AZUL_BOTAO),
            align="center",
            gap="12px",
            wrap="wrap",
            width="100%",
        ),
        mensagem(st),
        painel(
            rx.cond(
                st.plantoes.length() == 0,
                rx.text("Nenhum plantão neste dia.", size="2", color=COR_SECUNDARIA, padding="20px 16px"),
                rx.box(rx.vstack(rx.foreach(st.plantoes, linha_plantao), spacing="0", min_width="820px"), overflow_x="auto", width="100%"),
            ),
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(rx.cond(st.editando_id != 0, "Editar plantão", "Novo plantão")),
                rx.vstack(
                    campo("Médico", rx.select.root(
                        rx.select.trigger(placeholder="Escolha o médico", width="100%"),
                        rx.select.content(rx.foreach(st.opcoes_medicos, lambda o: rx.select.item(o["nome"], value=o["id"]))),
                        value=st.form["medico_id"].to(str),
                        on_change=lambda v: st.set_campo("medico_id", v),
                        disabled=st.editando_id != 0,
                    )),
                    rx.grid(
                        campo("Data", rx.input(type="date", value=st.form["data"].to(str), on_change=lambda v: st.set_campo("data", v), disabled=st.editando_iniciado)),
                        campo("Início", rx.input(type="time", value=st.form["hora_inicio"].to(str), on_change=lambda v: st.set_campo("hora_inicio", v), disabled=st.editando_iniciado)),
                        campo("Fim", rx.input(type="time", value=st.form["hora_fim"].to(str), on_change=lambda v: st.set_campo("hora_fim", v))),
                        columns="3",
                        gap="12px",
                        width="100%",
                    ),
                    rx.cond(st.editando_iniciado, rx.text("Plantão em andamento: só o horário de fim pode mudar.", size="1", color=COR_SECUNDARIA)),
                    rx.cond(st.erro_form != "", rx.text(st.erro_form, size="2", color=COR_ERRO)),
                    rx.hstack(
                        rx.dialog.close(botao_secundario("Cancelar")),
                        rx.button("Salvar", on_click=st.salvar, loading=st.salvando, size="3", background=COR_AZUL_BOTAO),
                        justify="end",
                        spacing="3",
                        width="100%",
                    ),
                    spacing="3",
                    margin_top="8px",
                    width="100%",
                ),
                max_width="560px",
            ),
            open=st.dialogo_aberto,
            on_open_change=st.set_dialogo_aberto,
        ),
    )


# ---------- Parâmetros e faixas ----------

def linha_parametro(p: Any) -> rx.Component:
    st = ParametrosState
    return rx.hstack(
        celula(rx.vstack(texto(p["rotulo"], weight="medium"), rx.text(p["chave"], size="1", color=COR_SECUNDARIA), spacing="0"), None),
        celula(texto(p["limites"], color=COR_SECUNDARIA), "150px"),
        celula(
            rx.cond(
                p["tipo"] == "ESPECIALIDADE",
                rx.select.root(
                    rx.select.trigger(width="100%"),
                    rx.select.content(rx.foreach(st.opcoes_especialidades, lambda o: rx.select.item(o["nome"], value=o["id"]))),
                    value=p["edicao"],
                    on_change=lambda v: st.set_valor(p["chave"], v),
                ),
                rx.input(value=p["edicao"], on_change=lambda v: st.set_valor(p["chave"], v), input_mode="numeric", size="2", width="100%"),
            ),
            "190px",
        ),
        celula(botao_secundario("Salvar", on_click=st.salvar_parametro(p["chave"])), "90px"),
        align="center",
        spacing="3",
        width="100%",
        padding="10px 16px",
        border_bottom=f"1px solid {COR_BORDA}",
    )


def linha_faixa(f: Any) -> rx.Component:
    return rx.hstack(
        celula(texto(f["sinal"], weight="medium"), None),
        celula(texto(f["condicao"], color=COR_SECUNDARIA), "190px"),
        celula(texto(f["intervalo"]), "140px"),
        celula(texto(f["pontos"] + " ponto(s)", weight="bold"), "100px"),
        celula(rx.button("Editar", on_click=ParametrosState.abrir_faixa(f), variant="ghost", size="1", color_scheme="gray"), "80px"),
        align="center",
        spacing="3",
        width="100%",
        padding="8px 16px",
        border_bottom=f"1px solid {COR_BORDA}",
        _hover={"background": COR_HOVER},
    )


def pagina_parametros() -> rx.Component:
    st = ParametrosState
    ff = st.faixa_form
    return layout_admin(
        "/admin/parametros",
        "Parâmetros e faixas",
        "Valores das regras do PS, dentro de limites seguros. O fuso horário (Brasília) não é configurável.",
        mensagem(st),
        painel(rx.box(rx.vstack(rx.foreach(st.parametros, linha_parametro), spacing="0", min_width="700px"), overflow_x="auto", width="100%")),
        rx.text("Faixas de pontuação dos sinais vitais", size="4", weight="bold", color=COR_TEXTO, padding_top="8px"),
        rx.text("Extremos inclusivos; não pode haver sobreposição entre faixas do mesmo sinal vital.", size="2", color=COR_SECUNDARIA),
        painel(rx.box(rx.vstack(rx.foreach(st.faixas, linha_faixa), spacing="0", min_width="700px"), overflow_x="auto", width="100%")),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Editar faixa"),
                rx.text(ff["sinal"].to(str), " ", ff["condicao"].to(str), size="2", color=COR_SECUNDARIA),
                rx.vstack(
                    rx.grid(
                        campo("Mínimo", rx.input(value=ff["minimo"].to(str), on_change=lambda v: st.set_campo_faixa("minimo", v), placeholder="sem limite")),
                        campo("Máximo", rx.input(value=ff["maximo"].to(str), on_change=lambda v: st.set_campo_faixa("maximo", v), placeholder="sem limite")),
                        campo("Pontos", rx.segmented_control.root(
                            *[rx.segmented_control.item(p, value=p) for p in ("0", "1", "2", "3")],
                            value=ff["pontos"].to(str),
                            on_change=lambda v: st.set_campo_faixa("pontos", v),
                        )),
                        columns="3",
                        gap="12px",
                        width="100%",
                    ),
                    rx.text("Deixe um limite vazio para extremo aberto (ex.: \"≥ 96\" tem máximo vazio).", size="1", color=COR_SECUNDARIA),
                    rx.cond(st.erro_faixa != "", rx.text(st.erro_faixa, size="2", color=COR_ERRO)),
                    rx.hstack(
                        rx.dialog.close(botao_secundario("Cancelar")),
                        rx.button("Salvar", on_click=st.salvar_faixa, size="3", background=COR_AZUL_BOTAO),
                        justify="end",
                        spacing="3",
                        width="100%",
                    ),
                    spacing="3",
                    margin_top="12px",
                    width="100%",
                ),
                max_width="520px",
            ),
            open=st.faixa_aberta,
            on_open_change=st.set_faixa_aberta,
        ),
    )

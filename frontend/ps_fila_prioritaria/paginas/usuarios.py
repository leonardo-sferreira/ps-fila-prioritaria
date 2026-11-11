"""Tela de usuários do Administrador (add-autenticacao-perfis, D14).

Administradores são criados, editados e ativados aqui; médicos e Recepção/Triagem têm o cadastro próprio, e a
linha leva até ele. "Trocar perfil" vale para todos, menos o próprio usuário, e pede os dados do perfil novo.
"""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.componentes import COR_ALERTA, COR_AZUL_BOTAO, COR_BORDA, COR_ERRO, COR_HOVER, COR_SECUNDARIA, botao_secundario
from ps_fila_prioritaria.estados.usuarios import PERFIS, UsuariosState
from ps_fila_prioritaria.paginas.cadastros import (
    barra_lista,
    campo,
    celula,
    dialogo,
    entrada,
    escolha_especialidades,
    layout_admin,
    mensagem,
    painel,
    situacao,
    texto,
)

COLUNAS = [("NOME", None), ("E-MAIL", "260px"), ("PERFIL", "150px"), ("SITUAÇÃO", "90px"), ("", "250px")]


def acoes_usuario(u: Any) -> rx.Component:
    e = UsuariosState
    return rx.hstack(
        rx.cond(
            u["admin"],
            rx.hstack(
                rx.button("Editar", on_click=e.abrir_edicao(u), variant="ghost", size="1", color_scheme="gray"),
                rx.cond(
                    ~u["proprio"],
                    rx.cond(
                        u["ativo"],
                        rx.button("Desativar", on_click=e.alternar_ativo(u["id"], False), variant="ghost", size="1", color_scheme="red"),
                        rx.button("Ativar", on_click=e.alternar_ativo(u["id"], True), variant="ghost", size="1", color_scheme="green"),
                    ),
                ),
                spacing="1",
            ),
            rx.link(rx.button("Abrir cadastro", variant="ghost", size="1", color_scheme="gray"), href=u["rota_cadastro"]),
        ),
        rx.cond(
            u["proprio"],
            rx.text("Você", size="1", color=COR_SECUNDARIA, padding="0 8px"),
            rx.button("Trocar perfil", on_click=e.abrir_troca(u), variant="ghost", size="1", color_scheme="blue"),
        ),
        spacing="1",
        justify="end",
    )


def linha(u: Any) -> rx.Component:
    conteudos = [texto(u["nome"], weight="medium"), texto(u["email"], color=COR_SECUNDARIA), texto(u["perfil_nome"]),
                 situacao(u["ativo"]), acoes_usuario(u)]
    return rx.hstack(
        *[celula(c, largura) for c, (_, largura) in zip(conteudos, COLUNAS)],
        align="center",
        spacing="3",
        width="100%",
        padding="10px 16px",
        border_bottom=f"1px solid {COR_BORDA}",
        _hover={"background": COR_HOVER},
    )


def tabela_usuarios() -> rx.Component:
    e = UsuariosState
    cabecalho = rx.hstack(
        *[celula(rx.text(rotulo, size="1", weight="bold", color=COR_SECUNDARIA, letter_spacing="0.06em"), largura) for rotulo, largura in COLUNAS],
        spacing="3",
        width="100%",
        padding="12px 16px",
        border_bottom=f"1px solid {COR_BORDA}",
    )
    return painel(
        rx.cond(
            e.carregando & (e.itens.length() == 0),
            rx.center(rx.spinner(), padding="24px"),
            rx.cond(
                e.itens_filtrados.length() == 0,
                rx.text("Nenhum usuário neste filtro.", size="2", color=COR_SECUNDARIA, padding="20px 16px"),
                rx.box(rx.vstack(cabecalho, rx.foreach(e.itens_filtrados, linha), spacing="0", min_width="900px"), overflow_x="auto", width="100%"),
            ),
        ),
    )


def filtro_perfil() -> rx.Component:
    e = UsuariosState
    return rx.select.root(
        rx.select.trigger(width=rx.breakpoints(initial="100%", sm="200px")),
        rx.select.content(rx.select.item("Todos os perfis", value="TODOS"), *[rx.select.item(nome, value=valor) for valor, nome in PERFIS]),
        value=e.filtro_perfil,
        on_change=e.set_filtro_perfil,
        size="2",
    )


def campos_medico() -> rx.Component:
    e = UsuariosState
    return rx.vstack(
        campo("CRM", entrada(e, "crm", placeholder="12345-SP")),
        campo("Especialidades próprias", escolha_especialidades(e)),
        campo("Sala atual (opcional)", rx.select.root(
            rx.select.trigger(placeholder="Sem sala", width="100%"),
            rx.select.content(rx.select.item("Sem sala", value="0"), rx.foreach(e.opcoes_salas, lambda o: rx.select.item(o["nome"], value=o["id"]))),
            value=e.form["sala_id"].to(str),
            on_change=lambda v: e.set_campo("sala_id", v),
        )),
        spacing="3",
        width="100%",
    )


def campos_recepcao() -> rx.Component:
    e = UsuariosState
    return rx.vstack(
        campo("CPF", entrada(e, "cpf", placeholder="000.000.000-00")),
        campo("Especialidade de referência (opcional)", rx.select.root(
            rx.select.trigger(placeholder="Nenhuma", width="100%"),
            rx.select.content(rx.select.item("Nenhuma", value="0"),
                              rx.foreach(e.opcoes_especialidades, lambda o: rx.select.item(o["nome"], value=o["id"].to(str)))),
            value=e.form["especialidade_referencia_id"].to(str),
            on_change=lambda v: e.set_campo("especialidade_referencia_id", v),
        )),
        spacing="3",
        width="100%",
    )


def dialogo_troca() -> rx.Component:
    e = UsuariosState
    perfil = e.form["perfil"].to(str)
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Trocar perfil"),
            rx.dialog.description(
                rx.text(e.troca_usuario["nome"].to(str), weight="medium"),
                rx.text("Perfil atual: ", e.troca_usuario["perfil_nome"].to(str), size="2", color=COR_SECUNDARIA),
            ),
            rx.vstack(
                campo("Novo perfil", rx.select.root(
                    rx.select.trigger(width="100%"),
                    rx.select.content(rx.foreach(e.opcoes_perfil_troca, lambda o: rx.select.item(o[1], value=o[0]))),
                    value=perfil,
                    on_change=e.set_perfil_troca,
                )),
                rx.match(
                    perfil,
                    ("MEDICO", campos_medico()),
                    ("RECEPCAO_TRIAGEM", campos_recepcao()),
                    rx.fragment(),
                ),
                rx.text(
                    "O cadastro do perfil atual fica desativado (o histórico é mantido). A troca vale no próximo acesso do usuário.",
                    size="2",
                    color=COR_ALERTA,
                ),
                rx.cond(e.erro_troca != "", rx.text(e.erro_troca, size="2", color=COR_ERRO)),
                rx.hstack(
                    rx.dialog.close(botao_secundario("Cancelar")),
                    rx.button("Confirmar troca", on_click=e.trocar_perfil, loading=e.salvando, size="3", background=COR_AZUL_BOTAO),
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
        open=e.troca_aberta,
        on_open_change=e.set_troca_aberta,
    )


def pagina_usuarios() -> rx.Component:
    e = UsuariosState
    return layout_admin(
        "/admin/usuarios",
        "Usuários",
        "Todos os acessos do sistema. Administradores são mantidos aqui; médicos e Recepção/Triagem, nos cadastros. "
        "A senha não é redefinida pelo Administrador: cada pessoa usa \"Esqueci minha senha\".",
        rx.flex(filtro_perfil(), barra_lista(e, "Novo administrador", "Buscar por nome ou e-mail"), gap="12px", wrap="wrap", width="100%"),
        mensagem(e),
        tabela_usuarios(),
        dialogo(
            e, "Novo administrador", "Editar administrador",
            campo("Nome", entrada(e, "nome", placeholder="Nome completo")),
            campo("E-mail de login", entrada(e, "email", type="email", placeholder="nome@ps.com.br")),
            rx.cond(
                ~e.editando,
                campo("Senha inicial", entrada(e, "senha", type="password", placeholder="8 ou mais caracteres"),
                      "A pessoa pode trocá-la depois em \"Esqueci minha senha\"."),
            ),
        ),
        dialogo_troca(),
    )

"""Páginas de login, código de acesso e redefinição de senha."""

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
    COR_SUCESSO_FUNDO,
    COR_SUPERFICIE,
    COR_TEXTO,
    botao_tema,
    campo_rotulado,
    campo_senha,
    carregando,
    logo_prioriza_completo,
    logo_ps,
)
from ps_fila_prioritaria.estados.autenticacao import AuthState, SenhaState, VisibilidadeSenhaState


def index() -> rx.Component:
    # A raiz só encaminha: para o login ou para a área do perfil logado.
    return carregando()


def cartao_acesso(icone: rx.Component, titulo: str, subtitulo: rx.Component | str, *corpo: rx.Component, on_submit: Any = None) -> rx.Component:
    """Cartão centralizado das telas de acesso (login, código e redefinição de senha), como no Figma."""
    cartao = rx.vstack(
        icone,
        *([rx.text(titulo, weight="bold", size="5", color=COR_TEXTO)] if titulo else []),
        *([] if subtitulo == "" else [rx.text(subtitulo, size="2", color=COR_SECUNDARIA, text_align="center") if isinstance(subtitulo, str) else subtitulo]),
        rx.box(height="8px"),
        *corpo,
        align="center",
        spacing="3",
        padding="40px 20px",
        background=COR_SUPERFICIE,
        border=f"1px solid {COR_BORDA}",
        border_radius="16px",
        box_shadow="0 2px 8px rgba(18, 60, 107, 0.06)",
        width="min(100%, 420px)",
    )
    return fundo_acesso(rx.form(cartao, on_submit=on_submit, width="min(100%, 420px)") if on_submit is not None else cartao)


def fundo_acesso(conteudo: rx.Component) -> rx.Component:
    """Fundo das páginas públicas, com o rodapé e o link do aviso de privacidade (add-privacidade, D2)."""
    return rx.center(
        rx.box(botao_tema(), position="absolute", top="16px", right="16px"),
        rx.vstack(
            conteudo,
            rx.hstack(
                rx.text("Acesso restrito a profissionais autorizados do PS", size="1", color=COR_SECUNDARIA),
                rx.text("·", size="1", color=COR_SECUNDARIA),
                rx.link("Aviso de privacidade", href="/privacidade", size="1", color=COR_AZUL),
                spacing="2",
                wrap="wrap",
                justify="center",
            ),
            align="center",
            spacing="6",
            width="100%",
        ),
        background=COR_FUNDO,
        font_family="Inter, sans-serif",
        min_height="100vh",
        padding="24px 16px",
        position="relative",
        width="100%",
    )


def mensagens_acesso(mensagem: rx.Var, aviso: rx.Var | None = None) -> rx.Component:
    erro = rx.cond(mensagem != "", rx.text(mensagem, size="2", color=COR_ERRO, width="100%"))
    if aviso is None:
        return erro
    return rx.fragment(erro, rx.cond(aviso != "", rx.text("✓ ", aviso, size="2", color=COR_SUCESSO, width="100%")))


def botao_principal(texto: str, ocupado: rx.Var) -> rx.Component:
    return rx.button(texto, type="submit", loading=ocupado, size="3", background=COR_AZUL_BOTAO, width="100%")


def link_acao(texto: str, **props: Any) -> rx.Component:
    return rx.button(texto, type="button", variant="ghost", size="2", color=COR_AZUL, **props)


def campo_codigo() -> rx.Component:
    return campo_rotulado(
        "CÓDIGO DE VERIFICAÇÃO",
        rx.input(
            name="codigo",
            placeholder="000000",
            max_length=6,
            input_mode="numeric",
            custom_attrs={"autoComplete": "one-time-code"},
            auto_focus=True,
            size="3",
            width="100%",
            text_align="center",
            letter_spacing="8px",
            font_size="22px",
        ),
    )


def bloco_reenvio(segundos: rx.Var, texto: rx.Var, ao_reenviar: Any) -> rx.Component:
    return rx.cond(
        segundos > 0,
        rx.text(texto, size="2", color=COR_SECUNDARIA),
        link_acao("Reenviar código", on_click=ao_reenviar),
    )


def login() -> rx.Component:
    return cartao_acesso(
        logo_prioriza_completo(),
        "",
        "",
        campo_rotulado("E-MAIL", rx.input(name="email", type="email", placeholder="nome@ps.com.br", size="3", width="100%")),
        campo_rotulado("SENHA", campo_senha("senha", VisibilidadeSenhaState.login, VisibilidadeSenhaState.alternar_login)),
        mensagens_acesso(AuthState.mensagem),
        botao_principal("Entrar", AuthState.entrando),
        rx.link("Esqueci minha senha", href="/senha", size="2", color=COR_AZUL),
        rx.divider(color=COR_BORDA),
        # Só ida: o Totem é público e não tem caminho de volta ao login (decisão do PO, 08/11/2026).
        rx.link("Abrir o Totem de autoatendimento →", href="/totem", size="2", color=COR_SECUNDARIA),
        on_submit=AuthState.entrar,
    )


def login_codigo() -> rx.Component:
    # Segunda etapa do login (design D13), no padrão da tela A2 do Figma.
    return cartao_acesso(
        logo_ps(),
        "Digite o código",
        rx.text(
            "Enviamos um código de 6 dígitos para ",
            AuthState.email_exibido,
            ". Digite-o abaixo para entrar.",
            size="2",
            color=COR_SECUNDARIA,
            text_align="center",
        ),
        campo_codigo(),
        mensagens_acesso(AuthState.mensagem, AuthState.aviso),
        botao_principal("Verificar código", AuthState.entrando),
        bloco_reenvio(AuthState.segundos_reenvio, AuthState.texto_reenvio, AuthState.reenviar_codigo),
        rx.text("Não recebeu? Confira a caixa de spam.", size="1", color=COR_SECUNDARIA),
        link_acao("Voltar ao login", on_click=AuthState.voltar_ao_login),
        on_submit=AuthState.verificar_codigo,
    )


def senha_email() -> rx.Component:
    # A1 — Esqueci minha senha (e-mail).
    return cartao_acesso(
        logo_ps(),
        "Redefinir senha",
        "Informe o e-mail cadastrado. Enviaremos um código de verificação.",
        campo_rotulado("E-MAIL", rx.input(name="email", type="email", placeholder="nome@ps.com.br", size="3", width="100%")),
        mensagens_acesso(SenhaState.mensagem),
        botao_principal("Enviar código", SenhaState.enviando),
        link_acao("Voltar ao login", on_click=SenhaState.voltar_ao_login),
        on_submit=SenhaState.solicitar_codigo,
    )


def senha_codigo() -> rx.Component:
    # A2 — Código enviado por e-mail; a A2b é esta tela com a mensagem "Código inválido ou expirado".
    return cartao_acesso(
        logo_ps(),
        "Digite o código",
        rx.text(
            "Se o e-mail estiver cadastrado, enviamos um código de 6 dígitos para ",
            SenhaState.email_exibido,
            ".",
            size="2",
            color=COR_SECUNDARIA,
            text_align="center",
        ),
        campo_codigo(),
        mensagens_acesso(SenhaState.mensagem, SenhaState.aviso),
        botao_principal("Verificar código", SenhaState.enviando),
        bloco_reenvio(SenhaState.segundos_reenvio, SenhaState.texto_reenvio, SenhaState.reenviar_codigo),
        rx.text("Não recebeu? Confira a caixa de spam.", size="1", color=COR_SECUNDARIA),
        link_acao("Voltar ao login", on_click=SenhaState.voltar_ao_login),
        on_submit=SenhaState.verificar_codigo,
    )


def senha_nova() -> rx.Component:
    # A3 — Nova senha.
    return cartao_acesso(
        logo_ps(),
        "Crie uma nova senha",
        "Código confirmado. Escolha a nova senha de acesso.",
        campo_rotulado("NOVA SENHA", campo_senha("nova_senha", VisibilidadeSenhaState.nova, VisibilidadeSenhaState.alternar_nova)),
        campo_rotulado("CONFIRMAR NOVA SENHA", campo_senha("confirmacao", VisibilidadeSenhaState.nova, VisibilidadeSenhaState.alternar_nova)),
        rx.text("Mínimo de 8 caracteres. As duas senhas devem ser iguais.", size="1", color=COR_SECUNDARIA, width="100%"),
        mensagens_acesso(SenhaState.mensagem),
        botao_principal("Salvar nova senha", SenhaState.enviando),
        on_submit=SenhaState.redefinir,
    )


def senha_sucesso() -> rx.Component:
    # A4 — Senha redefinida.
    return cartao_acesso(
        rx.center(rx.icon("check", size=28, color=COR_SUCESSO), width="64px", height="64px", border_radius="50%", background=COR_SUCESSO_FUNDO),
        "Senha redefinida",
        "Sua senha foi alterada. A senha anterior deixou de funcionar; entre com a nova senha.",
        rx.link(rx.button("Ir para o login", size="3", background=COR_AZUL_BOTAO, width="100%"), href="/login", width="100%"),
    )

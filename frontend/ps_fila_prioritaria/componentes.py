"""Componentes visuais compartilhados: cores, cabeçalho, menu da Recepção e proteção das páginas."""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.pacientes import PacienteState


# Cores do protótipo no Figma (telas 3 e 3a–3e).
COR_MARINHO = "#123C6B"


COR_AZUL = "#1565C0"


COR_FUNDO = "#F3F5F7"


COR_BORDA = "#DDE3E8"


COR_TEXTO = "#1A2027"


COR_SECUNDARIA = "#66707A"


COR_SUCESSO = "#2E7D32"


COR_ERRO = "#C62828"


def sessao_no_cabecalho() -> rx.Component:
    return rx.hstack(
        rx.text(AuthState.nome, size="2", color="#CCDEF0"),
        rx.button("Sair", on_click=AuthState.sair, variant="outline", size="2", color="white", border_color="rgba(255, 255, 255, 0.4)"),
        align="center",
        spacing="3",
        padding_right="24px",
    )


def cabecalho(titulo: str, subtitulo: str, com_sessao: bool = True) -> rx.Component:
    return rx.hstack(
        # Ícone Prioriza branco no lugar da sigla do perfil (Figma: Marca/Ícone Prioriza, versão branca).
        rx.image(src="/logo/icone-prioriza-branco.svg", alt="Prioriza", width="48px", height="48px", flex_shrink="0"),
        rx.vstack(
            rx.text(titulo, weight="bold", size="5", color="white"),
            *([rx.text(subtitulo, size="2", color="#CCDEF0")] if subtitulo else []),
            spacing="1",
        ),
        rx.spacer(),
        # Telas públicas (Totem) não têm sessão da equipe.
        *([sessao_no_cabecalho()] if com_sessao else []),
        rx.vstack(
            # Relógio do navegador, atualizado a cada segundo no fuso do PS.
            rx.moment(format="DD/MM/YYYY", interval=1000, tz="America/Sao_Paulo", color="#CCDEF0", font_size="14px", font_weight="500"),
            rx.moment(format="HH:mm:ss", interval=1000, tz="America/Sao_Paulo", color="white", font_size="26px", font_weight="700", font_variant_numeric="tabular-nums"),
            spacing="0",
            align="end",
        ),
        align="center",
        spacing="4",
        background=COR_MARINHO,
        padding="0 48px",
        height="96px",
        width="100%",
    )


def campo_senha(nome: str, visivel: rx.Var, ao_alternar: Any) -> rx.Component:
    """Campo de senha com o ícone de olho para conferir o que foi digitado."""
    return rx.input(
        rx.input.slot(
            rx.icon_button(
                rx.cond(visivel, rx.icon("eye-off", size=18), rx.icon("eye", size=18)),
                type="button",
                variant="ghost",
                color_scheme="gray",
                size="2",
                on_click=ao_alternar,
                aria_label=rx.cond(visivel, "Ocultar senha", "Mostrar senha"),
                cursor="pointer",
            ),
            side="right",
        ),
        name=nome,
        type=rx.cond(visivel, "text", "password"),
        placeholder="••••••••",
        size="3",
        width="100%",
    )


# Menu da Recepção/Triagem abaixo do cabeçalho, no padrão "Navegação/Menu" do Figma: dá caminho de volta às
# opções do menu em todas as telas internas.
ABAS_RECEPCAO = [
    ("Início", "/recepcao"),
    ("Fila de pré-triagem", "/recepcao/fila"),
    ("Identificar paciente", "/recepcao/pacientes"),
]


def aba_menu(nome: str, rota: str, ativa: bool) -> rx.Component:
    conteudo = rx.box(
        rx.text(nome, size="2", weight="bold" if ativa else "medium", color=COR_AZUL if ativa else COR_SECUNDARIA),
        padding="12px 16px",
        background="#E8F0FB" if ativa else "transparent",
        border_bottom=f"2px solid {COR_AZUL}" if ativa else "2px solid transparent",
        _hover={"background": "#E8F0FB"},
    )
    if rota == "/recepcao/pacientes":
        # Identificação a partir do menu começa sem ticket (o ticket chega pela fila, em "Identificar").
        return rx.box(conteudo, on_click=PacienteState.iniciar_sem_ticket, cursor="pointer")
    return rx.link(conteudo, href=rota, underline="none")


def menu_recepcao(rota_ativa: str = "") -> rx.Component:
    return rx.hstack(
        *[aba_menu(nome, rota, rota == rota_ativa) for nome, rota in ABAS_RECEPCAO],
        spacing="1",
        align="end",
        background="white",
        border_bottom=f"1px solid {COR_BORDA}",
        padding="0 32px",
        width="100%",
        overflow_x="auto",
        class_name="nao-imprimir",
    )


def campo_rotulado(rotulo: str, campo: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(rotulo, size="1", weight="medium", color=COR_SECUNDARIA),
        campo,
        spacing="1",
        width="100%",
    )


def botao_secundario(texto: str, **props: Any) -> rx.Component:
    return rx.button(texto, variant="outline", color_scheme="gray", size="3", color=COR_TEXTO, **props)


def carregando() -> rx.Component:
    return rx.center(rx.spinner(size="3"), height="100vh", width="100%", background=COR_FUNDO)


# Contagem de inatividade no navegador (add-privacidade, D5). Instala os ouvintes uma única vez; só conta
# enquanto o marcador #ps-inatividade estiver na página, então as telas públicas não encerram nada.
SCRIPT_INATIVIDADE = """
(function () {
  if (window.__psInatividade) return;
  window.__psInatividade = true;
  var ultima = Date.now();
  ["mousemove", "mousedown", "keydown", "scroll", "touchstart"].forEach(function (evento) {
    window.addEventListener(evento, function () { ultima = Date.now(); }, { passive: true, capture: true });
  });
  setInterval(function () {
    var marcador = document.getElementById("ps-inatividade");
    if (!marcador) { ultima = Date.now(); return; }
    var limite = parseInt(marcador.getAttribute("data-inatividade-ms") || "0", 10);
    if (limite > 0 && Date.now() - ultima >= limite) {
      window.__psInatividade = false;
      window.location.href = "/sair/inatividade";
    }
  }, 1000);
})();
"""


def protegido(perfil: str, conteudo: rx.Component) -> rx.Component:
    """Só mostra a página ao perfil certo; enquanto a sessão é conferida, mostra o carregamento."""
    return rx.cond(
        AuthState.perfil == perfil,
        rx.fragment(
            conteudo,
            rx.el.div(id="ps-inatividade", custom_attrs={"data-inatividade-ms": AuthState.inatividade_segundos * 1000}, display="none"),
            rx.script(SCRIPT_INATIVIDADE),
        ),
        carregando(),
    )


def logo_ps() -> rx.Component:
    """Ícone Prioriza das telas de acesso (Figma: Marca/Ícone Prioriza, versão colorida)."""
    return rx.image(src="/logo/icone-prioriza.svg", alt="Prioriza", width="64px", height="64px")


def logo_prioriza_completo() -> rx.Component:
    """Logo com o nome, usado só no login (Figma: Marca/Logo Prioriza, versão colorida)."""
    return rx.image(src="/logo/logo-prioriza.svg", alt="Prioriza · Fila de atendimento", width="260px", height="80px")


def cartao_painel(*filhos: rx.Component, **props: Any) -> rx.Component:
    props.setdefault("width", "100%")
    return rx.box(
        *filhos,
        background="white",
        border=f"1px solid {COR_BORDA}",
        border_radius="12px",
        box_shadow="0 2px 8px rgba(18, 60, 107, 0.06)",
        **props,
    )

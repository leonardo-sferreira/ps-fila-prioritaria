"""Página da ficha de atendimento."""

from typing import Any

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_ALERTA,
    COR_AZUL_BOTAO,
    COR_BORDA,
    COR_ERRO,
    COR_FUNDO,
    COR_SECUNDARIA,
    COR_SUCESSO,
    COR_SUPERFICIE,
    COR_TEXTO,
    botao_secundario,
    cabecalho,
    cartao_painel,
    menu_recepcao,
    protegido,
)
from ps_fila_prioritaria.estados.ficha import FichaState, SeletorSintomasState


def opcao_sintoma(sintoma: dict[str, Any]) -> rx.Component:
    return rx.button(
        sintoma["nome"],
        on_click=[FichaState.alternar_sintoma(sintoma["id"], True), SeletorSintomasState.limpar_busca],
        variant="ghost",
        color_scheme="gray",
        justify="start",
        white_space="normal",
        text_align="left",
        height="auto",
        min_height="2rem",
        padding="0.4rem 0.5rem",
        width="100%",
    )


def sintoma_selecionado(sintoma: dict[str, Any]) -> rx.Component:
    selecionado = FichaState.sintoma_ids_selecionados.contains(sintoma["id"])
    return rx.cond(
        selecionado,
        rx.hstack(
            rx.text(
                sintoma["nome"],
                min_width="0",
                white_space="normal",
                line_height="1.35",
            ),
            rx.spacer(),
            rx.button(
                "×",
                on_click=FichaState.alternar_sintoma(sintoma["id"], False),
                aria_label="Remover sintoma",
                variant="ghost",
                color_scheme="gray",
                size="2",
                flex_shrink="0",
            ),
            align="center",
            spacing="2",
            border="1px solid var(--gray-5)",
            border_radius="0.375rem",
            padding="0.35rem 0.5rem",
            width="100%",
        ),
    )


# Cores e textos das prioridades, como na tela 4 do Figma.
CORES_PRIORIDADE = [
    ("VERMELHA", "Vermelha", "Risco de morte", "#C62828"),
    ("AMARELA", "Amarela", "Urgente", "#ED8B00"),
    ("AZUL", "Azul", "Não urgente", "#1565C0"),
]


def rotulo_secao(texto: str) -> rx.Component:
    return rx.text(texto, size="1", weight="bold", color=COR_SECUNDARIA, letter_spacing="0.02em")


def icone_situacao_sinal(campo: str) -> rx.Component:
    """Mostra se o campo ainda não foi preenchido, foi alterado sem salvar ou já está salvo."""
    situacao = FichaState.situacao_sinais[campo]
    return rx.match(
        situacao,
        ("vazio", rx.tooltip(rx.icon("circle-dashed", size=16, color=COR_SECUNDARIA, aria_label="Não preenchido"), content="Não preenchido")),
        ("alterado", rx.tooltip(rx.icon("pencil", size=16, color=COR_ALERTA, aria_label="Alterado, falta salvar"), content="Alterado, falta salvar")),
        rx.tooltip(rx.icon("circle-check", size=16, color=COR_SUCESSO, aria_label="Salvo"), content="Salvo"),
    )


def campo_sinal(rotulo: str, campo: str, exemplo: str) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(rotulo, size="1", weight="medium", color=COR_SECUNDARIA),
            rx.text(FichaState.referencias_sinais[campo], size="1", color=COR_SECUNDARIA),
            justify="between",
            gap="8px",
            wrap="wrap",
            width="100%",
        ),
        rx.input(
            rx.input.slot(icone_situacao_sinal(campo), side="right"),
            value=FichaState.sinais[campo],
            on_change=lambda valor: FichaState.set_sinal(campo, valor),
            placeholder=exemplo,
            input_mode="decimal",
            size="3",
            width="100%",
        ),
        spacing="1",
        width="100%",
    )


def sinais_vitais_ficha() -> rx.Component:
    return rx.vstack(
        rotulo_secao("SINAIS VITAIS"),
        rx.grid(
            campo_sinal("PA SISTÓLICA (mmHg)", "pa_sistolica", "Ex.: 150"),
            campo_sinal("FREQUÊNCIA CARDÍACA (bpm)", "fc", "Ex.: 112"),
            campo_sinal("FREQUÊNCIA RESPIRATÓRIA (irpm)", "fr", "Ex.: 24"),
            campo_sinal("TEMPERATURA (°C)", "temperatura", "Ex.: 37,1"),
            campo_sinal("SpO2 (%)", "spo2", "Ex.: 96"),
            rx.vstack(
                campo_sinal("GLICEMIA (OPCIONAL, mg/dL)", "glicemia", "Ex.: 110"),
                rx.checkbox(
                    "glicemia com sinais de gravidade",
                    checked=FichaState.glicemia_gravidade,
                    on_change=FichaState.set_glicemia_gravidade,
                    size="2",
                ),
                spacing="2",
                width="100%",
            ),
            columns=rx.breakpoints(initial="1", sm="2", md="3"),
            spacing="4",
            width="100%",
        ),
        spacing="2",
        width="100%",
    )


def sintoma_livre_selecionado(livre: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.text(livre["descricao"], min_width="0", white_space="normal", line_height="1.35"),
        rx.badge("não listado · ", livre["pontuacao"], " pt(s)", color_scheme="gray", variant="soft"),
        rx.spacer(),
        rx.button(
            "×",
            on_click=FichaState.remover_sintoma_livre(livre["descricao"]),
            aria_label="Remover sintoma não listado",
            variant="ghost",
            color_scheme="gray",
            size="2",
            flex_shrink="0",
        ),
        align="center",
        spacing="2",
        border="1px dashed var(--gray-6)",
        border_radius="0.375rem",
        padding="0.35rem 0.5rem",
        width="100%",
    )


def adicionar_nao_listado() -> rx.Component:
    """Sintoma digitado (D9): a Recepção/Triagem escolhe a gravidade; vale só para esta ficha."""
    busca = SeletorSintomasState.busca.strip()
    return rx.cond(
        busca.length() >= 3,
        rx.vstack(
            rx.divider(),
            rx.text("Não encontrou? Adicionar \"", busca, "\" como sintoma não listado:", size="2", color=COR_SECUNDARIA),
            rx.hstack(
                *[
                    rx.button(
                        nome,
                        on_click=[FichaState.adicionar_sintoma_livre(busca, pontos), SeletorSintomasState.limpar_busca],
                        variant="outline",
                        color_scheme="gray",
                        size="2",
                    )
                    for pontos, nome in ((1, "Leve · 1 pt"), (2, "Moderado · 2 pts"), (3, "Grave · 3 pts"))
                ],
                spacing="2",
                wrap="wrap",
            ),
            spacing="2",
            width="100%",
        ),
    )


def sintomas_ficha() -> rx.Component:
    return rx.vstack(
        rotulo_secao("SINTOMAS (DA LISTA OU NÃO LISTADOS) E OBSERVAÇÃO"),
        rx.popover.root(
            rx.popover.trigger(
                rx.button("+ Pesquisar ou adicionar sintoma...", variant="soft", color_scheme="gray", justify="between", width="100%")
            ),
            rx.popover.content(
                rx.vstack(
                    rx.input(
                        placeholder="Pesquisar por nome...",
                        value=SeletorSintomasState.busca,
                        on_change=SeletorSintomasState.set_busca,
                        width="100%",
                        auto_focus=True,
                    ),
                    rx.box(
                        rx.vstack(
                            rx.foreach(
                                FichaState.catalogo_sintomas,
                                lambda sintoma: rx.cond(
                                    (~FichaState.sintoma_ids_selecionados.contains(sintoma["id"].to(int)))
                                    & sintoma["nome"].to(str).lower().contains(SeletorSintomasState.busca.strip().lower()),
                                    opcao_sintoma(sintoma),
                                ),
                            ),
                            spacing="1",
                            align="stretch",
                            width="100%",
                        ),
                        max_height="15rem",
                        overflow_y="auto",
                        width="100%",
                    ),
                    adicionar_nao_listado(),
                    spacing="2",
                    align="stretch",
                    width="100%",
                ),
                width="min(34rem, calc(100vw - 3rem))",
            ),
        ),
        rx.cond(
            (FichaState.sintoma_ids_selecionados.length() > 0) | (FichaState.sintomas_livres.length() > 0),
            rx.vstack(
                rx.foreach(FichaState.catalogo_sintomas, sintoma_selecionado),
                rx.foreach(FichaState.sintomas_livres, sintoma_livre_selecionado),
                spacing="1",
                align="stretch",
                width="100%",
            ),
            rx.text("Nenhum sintoma selecionado.", size="2", color=COR_SECUNDARIA),
        ),
        rx.text_area(
            value=FichaState.observacao,
            on_change=FichaState.set_observacao,
            placeholder="Observação / queixa geral (opcional se houver sintoma).",
            width="100%",
        ),
        spacing="2",
        align="stretch",
        width="100%",
    )


def cartao_prioridade(codigo: str, nome: str, descricao: str, cor: str) -> rx.Component:
    atual = FichaState.prioridade_exibida == codigo
    calculada_diferente = FichaState.ajustada_manualmente & (FichaState.prioridade_calculada == codigo)
    return rx.box(
        rx.text(nome, weight="bold", size="4", color=rx.cond(atual, cor, COR_TEXTO)),
        rx.text(descricao, size="2", color=COR_SECUNDARIA),
        rx.cond(atual & FichaState.ajustada_manualmente, rx.badge("ajuste manual", color_scheme="gray", margin_top="4px")),
        rx.cond(calculada_diferente, rx.badge("calculada", color_scheme="gray", variant="outline", margin_top="4px")),
        border=rx.cond(atual, f"2px solid {cor}", f"1px solid {COR_BORDA}"),
        border_left=f"6px solid {cor}",
        background=rx.cond(atual, f"{cor}14", COR_SUPERFICIE),
        border_radius="8px",
        padding="12px 16px",
        flex="1",
        min_width="140px",
    )


def classificacao_ficha() -> rx.Component:
    return rx.vstack(
        rotulo_secao("CLASSIFICAÇÃO"),
        rx.text(FichaState.resumo_escore, size="2", weight="medium", color=COR_TEXTO),
        rx.hstack(*[cartao_prioridade(*cor) for cor in CORES_PRIORIDADE], spacing="3", wrap="wrap", width="100%"),
        rx.cond(
            FichaState.ajustada_manualmente,
            rx.text("Justificativa do ajuste: ", FichaState.classificacao["justificativa_ajuste"], size="2", color=COR_SECUNDARIA),
        ),
        rx.cond(
            FichaState.aviso_classificacao != "",
            rx.callout(FichaState.aviso_classificacao, icon="triangle-alert", color_scheme="amber", size="1", width="100%"),
        ),
        rx.checkbox(
            "Gestante — idoso e criança são identificados automaticamente pela data de nascimento",
            checked=FichaState.gestante,
            on_change=FichaState.set_gestante,
            size="2",
        ),
        rx.text(
            "Escala de simulação acadêmica (Azul 0–4, Amarela 5–9, Vermelha 10 ou mais; item de 3 pontos gera Vermelha). Não é protocolo clínico.",
            size="1",
            color=COR_SECUNDARIA,
        ),
        spacing="2",
        width="100%",
    )


def dialogo_ajuste_prioridade() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajustar prioridade"),
            rx.dialog.description(
                "A justificativa é obrigatória e fica na auditoria. Se sintomas ou sinais vitais mudarem depois, o ajuste é descartado e a cor é recalculada.",
                size="2",
            ),
            rx.vstack(
                rx.radio_group(
                    ["VERMELHA", "AMARELA", "AZUL"],
                    value=FichaState.ajuste_prioridade,
                    on_change=FichaState.set_ajuste_prioridade,
                    direction="row",
                    spacing="4",
                ),
                rx.text_area(
                    value=FichaState.ajuste_justificativa,
                    on_change=FichaState.set_ajuste_justificativa,
                    placeholder="Justificativa (obrigatória)",
                    width="100%",
                ),
                rx.cond(FichaState.ajuste_erro != "", rx.text(FichaState.ajuste_erro, size="2", color=COR_ERRO)),
                rx.hstack(
                    rx.dialog.close(botao_secundario("Cancelar")),
                    rx.button("Confirmar ajuste", on_click=FichaState.confirmar_ajuste, loading=FichaState.ajustando, size="3", background=COR_AZUL_BOTAO),
                    justify="end",
                    spacing="3",
                    width="100%",
                ),
                spacing="3",
                margin_top="12px",
                width="100%",
            ),
            max_width="480px",
        ),
        open=FichaState.ajuste_aberto,
        on_open_change=FichaState.set_ajuste_aberto,
    )


def cartao_paciente_ficha() -> rx.Component:
    return cartao_painel(
        rx.vstack(
            rotulo_secao("FICHA"),
            rx.badge(FichaState.ficha["status"], color_scheme="gray", size="2"),
            rx.divider(),
            rotulo_secao("NOME"),
            rx.text(FichaState.paciente["nome"], size="3", color=COR_TEXTO),
            rotulo_secao("CPF"),
            rx.text(FichaState.cpf_exibido, size="3", color=COR_TEXTO),
            rotulo_secao("IDADE · CONDIÇÃO PRIORITÁRIA"),
            rx.text(FichaState.idade_texto, " · ", FichaState.condicao_texto, size="3", color=COR_TEXTO),
            rx.text("A condição prioritária reordena dentro da mesma cor; não soma pontos.", size="1", color=COR_SECUNDARIA),
            spacing="2",
            align="start",
            width="100%",
        ),
        padding="24px",
        width=rx.breakpoints(initial="100%", md="320px"),
        flex_shrink="0",
    )


def recepcao_ficha() -> rx.Component:
    return rx.box(
        cabecalho("RECEPÇÃO/TRIAGEM — FICHA DE ATENDIMENTO", "Registre sintomas e sinais vitais — a cor é recalculada ao salvar"),
        menu_recepcao(),
        rx.center(
            rx.cond(
                FichaState.carregando,
                rx.spinner(size="3"),
                rx.flex(
                    cartao_paciente_ficha(),
                    cartao_painel(
                        rx.vstack(
                            rx.text("Ficha de atendimento", weight="bold", size="5", color=COR_TEXTO),
                            rx.cond(
                                FichaState.mensagem != "",
                                rx.callout(FichaState.mensagem, color_scheme=rx.cond(FichaState.erro, "red", "green"), width="100%"),
                            ),
                            sinais_vitais_ficha(),
                            sintomas_ficha(),
                            classificacao_ficha(),
                            rx.divider(),
                            rx.cond(
                                FichaState.em_triagem,
                                rx.vstack(
                                    rx.hstack(
                                        rotulo_secao("DESTINO PREVISTO"),
                                        rx.text(FichaState.destino_texto, size="2", weight="medium", color=COR_TEXTO),
                                        align="center",
                                        spacing="3",
                                        wrap="wrap",
                                    ),
                                    rx.flex(
                                        botao_secundario("Ajustar prioridade (justificativa obrigatória)", on_click=FichaState.abrir_ajuste),
                                        rx.hstack(
                                            botao_secundario("Salvar ficha", on_click=FichaState.salvar, loading=FichaState.salvando),
                                            rx.button("Confirmar e gerar senha", on_click=FichaState.confirmar_triagem, loading=FichaState.confirmando, size="3", background=COR_AZUL_BOTAO, min_width="220px"),
                                            spacing="3",
                                            wrap="wrap",
                                        ),
                                        justify="between",
                                        gap="12px",
                                        wrap="wrap",
                                        width="100%",
                                    ),
                                    spacing="3",
                                    width="100%",
                                ),
                                rx.vstack(
                                    # Um aviso só: senha alterada (âmbar, até ser fechado) ou triagem confirmada (verde).
                                    rx.callout(
                                        rx.hstack(
                                            rx.cond(
                                                FichaState.aviso_senha != "",
                                                rx.text(FichaState.aviso_senha, " · ", FichaState.especialidade_ficha, size="2"),
                                                rx.text("Triagem confirmada: senha ", rx.text.strong(FichaState.senha_ficha), " · ", FichaState.especialidade_ficha, size="2"),
                                            ),
                                            rx.spacer(),
                                            rx.button("Reimprimir comprovante", on_click=FichaState.reimprimir, size="1", background=COR_AZUL_BOTAO),
                                            rx.cond(
                                                FichaState.aviso_senha != "",
                                                rx.icon_button(rx.icon("x", size=14), on_click=FichaState.fechar_aviso_senha, variant="ghost", size="1", aria_label="Fechar aviso"),
                                            ),
                                            align="center",
                                            wrap="wrap",
                                            width="100%",
                                        ),
                                        icon=rx.cond(FichaState.aviso_senha != "", "triangle-alert", "circle-check"),
                                        color_scheme=rx.cond(FichaState.aviso_senha != "", "amber", "green"),
                                        size="1",
                                        width="100%",
                                    ),
                                    # Reavaliação (RF12): AGUARDANDO continua editável, sem "Confirmar e gerar senha";
                                    # salvar refaz cor, destino e senha no Xano. CHAMADO e finais ficam só de leitura.
                                    rx.cond(
                                        FichaState.aguardando,
                                        rx.flex(
                                            botao_secundario("Ajustar prioridade (justificativa obrigatória)", on_click=FichaState.abrir_ajuste),
                                            botao_secundario("Salvar alterações", on_click=FichaState.salvar, loading=FichaState.salvando),
                                            justify="between",
                                            gap="12px",
                                            wrap="wrap",
                                            width="100%",
                                        ),
                                    ),
                                    spacing="3",
                                    width="100%",
                                ),
                            ),
                            spacing="4",
                            width="100%",
                        ),
                        padding="28px",
                        flex="1",
                        min_width="0",
                    ),
                    direction=rx.breakpoints(initial="column", md="row"),
                    gap="24px",
                    align="start",
                    width="min(100%, 1184px)",
                ),
            ),
            padding="28px 16px 40px",
            width="100%",
        ),
        dialogo_ajuste_prioridade(),
        background=COR_FUNDO,
        font_family="Inter, sans-serif",
        min_height="100vh",
        width="100%",
    )


def pagina_recepcao_ficha() -> rx.Component:
    return protegido("RECEPCAO_TRIAGEM", recepcao_ficha())

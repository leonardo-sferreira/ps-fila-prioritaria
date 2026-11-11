"""Página de identificação do paciente pela Recepção/Triagem."""

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
    campo_rotulado,
    menu_recepcao,
    protegido,
)
from ps_fila_prioritaria.estados.pacientes import PacienteState


def formulario_paciente() -> rx.Component:
    return rx.vstack(
        campo_rotulado(
            "NOME COMPLETO",
            rx.input(value=PacienteState.nome, on_change=PacienteState.set_nome, placeholder="Digite o nome completo", size="3", width="100%"),
        ),
        rx.hstack(
            campo_rotulado(
                "DATA DE NASCIMENTO",
                rx.input(type="date", value=PacienteState.data_nascimento, on_change=PacienteState.set_data_nascimento, on_blur=PacienteState.set_data_nascimento, size="3", width="100%"),
            ),
            campo_rotulado(
                "TELEFONE (OPCIONAL)",
                rx.input(value=PacienteState.telefone, on_change=PacienteState.set_telefone, placeholder="(00) 00000-0000", size="3", width="100%"),
            ),
            spacing="5",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def mensagem_identificacao() -> rx.Component:
    na_fila = PacienteState.ficha_atual_id != 0
    cor = rx.cond(
        PacienteState.erro,
        COR_ERRO,
        rx.cond(na_fila, COR_ALERTA, rx.cond(PacienteState.paciente_encontrado, COR_SUCESSO, COR_SECUNDARIA)),
    )
    return rx.cond(
        PacienteState.mensagem != "",
        rx.text(
            rx.cond(PacienteState.paciente_encontrado & ~PacienteState.erro & ~na_fila, "✓ ", ""),
            PacienteState.mensagem,
            size="2",
            color=cor,
        ),
    )


def rodape_identificacao() -> rx.Component:
    return rx.cond(
        PacienteState.paciente_encontrado | PacienteState.exibir_cadastro,
        rx.vstack(
            rx.divider(color=COR_BORDA),
            rx.hstack(
                rx.spacer(),
                botao_secundario("Cancelar", on_click=PacienteState.cancelar),
                rx.cond(
                    PacienteState.paciente_encontrado,
                    rx.hstack(
                        botao_secundario("Salvar alterações", on_click=PacienteState.atualizar),
                        rx.cond(
                            PacienteState.ficha_atual_id != 0,
                            rx.button(
                                "Abrir ficha atual",
                                on_click=PacienteState.abrir_ficha_atual,
                                size="3",
                                background=COR_AZUL_BOTAO,
                                min_width="240px",
                            ),
                            rx.button(
                                "Continuar",
                                on_click=PacienteState.continuar_atendimento,
                                loading=PacienteState.abrindo_ficha,
                                size="3",
                                background=COR_AZUL_BOTAO,
                                min_width="240px",
                            ),
                        ),
                        spacing="3",
                    ),
                    rx.button("Salvar cadastro", on_click=PacienteState.cadastrar, size="3", background=COR_AZUL_BOTAO, min_width="240px"),
                ),
                align="center",
                spacing="3",
                width="100%",
                padding="16px 32px",
            ),
            spacing="0",
            width="100%",
        ),
    )


def recepcao_pacientes() -> rx.Component:
    return rx.box(
        cabecalho(
            "RECEPÇÃO/TRIAGEM — IDENTIFICAÇÃO DO PACIENTE",
            "Identifique o paciente pelo CPF antes de abrir a ficha",
        ),
        menu_recepcao("/recepcao/pacientes"),
        rx.center(
            rx.vstack(
                rx.vstack(
                    rx.text("Identificação do paciente", weight="bold", size="5", color=COR_TEXTO),
                    rx.box(height="8px"),
                    campo_rotulado(
                        "CPF",
                        rx.hstack(
                            rx.input(
                                value=PacienteState.cpf_busca,
                                on_change=PacienteState.set_cpf_busca,
                                placeholder="000.000.000-00",
                                size="3",
                                width="100%",
                                max_width="342px",
                                color_scheme=rx.cond(PacienteState.erro, "red", "gray"),
                            ),
                            rx.button("Pesquisar", on_click=PacienteState.buscar, size="3", background=COR_AZUL_BOTAO, min_width="160px"),
                            spacing="4",
                            width="100%",
                        ),
                    ),
                    mensagem_identificacao(),
                    rx.cond(
                        PacienteState.paciente_encontrado | PacienteState.exibir_cadastro,
                        rx.box(formulario_paciente(), padding_top="12px", width="100%"),
                    ),
                    spacing="3",
                    padding="28px 32px",
                    width="100%",
                ),
                rodape_identificacao(),
                spacing="0",
                background=COR_SUPERFICIE,
                border=f"1px solid {COR_BORDA}",
                border_radius="12px",
                box_shadow="0 2px 8px rgba(18, 60, 107, 0.06)",
                width="min(100%, 772px)",
            ),
            padding="40px 16px",
            width="100%",
        ),
        background=COR_FUNDO,
        font_family="Inter, sans-serif",
        min_height="100vh",
        width="100%",
    )


def pagina_recepcao_pacientes() -> rx.Component:
    return protegido("RECEPCAO_TRIAGEM", recepcao_pacientes())

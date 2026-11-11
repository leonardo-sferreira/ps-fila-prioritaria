"""Páginas do Médico: fila de atendimento e impressão da ficha atribuída."""

import reflex as rx

from ps_fila_prioritaria.componentes import (
    COR_AZUL,
    COR_FUNDO,
    COR_SECUNDARIA,
    botao_secundario,
    cabecalho,
    cartao_painel,
    protegido,
)
from ps_fila_prioritaria.estados.medico import ImpressaoMedicoState, MedicoState


def area_medico() -> rx.Component:
    return protegido(
        "MEDICO",
        rx.box(
            cabecalho("MÉDICO — FILA DE ATENDIMENTO", "A próxima ficha é escolhida pelas regras de prioridade"),
            rx.center(rx.vstack(
                rx.hstack(
                    rx.text("Status: ", MedicoState.status_operacional, weight="medium"),
                    rx.badge(rx.cond(MedicoState.plantao_vigente, "Plantão vigente", "Sem plantão vigente"), color_scheme=rx.cond(MedicoState.plantao_vigente, "green", "gray")),
                    rx.button("Ficar disponível", on_click=MedicoState.definir_status("DISPONIVEL"), disabled=MedicoState.ocupado | ~MedicoState.plantao_vigente | (MedicoState.status_operacional == "DISPONIVEL"), color_scheme="green"),
                    botao_secundario("Pausar", on_click=MedicoState.definir_status("PAUSA"), disabled=MedicoState.ocupado | (MedicoState.status_operacional == "PAUSA")),
                    botao_secundario("Ausente", on_click=MedicoState.definir_status("AUSENTE"), disabled=MedicoState.ocupado | (MedicoState.status_operacional == "AUSENTE")),
                    rx.spacer(),
                    botao_secundario("Atualizar", on_click=MedicoState.carregar),
                    rx.button("Chamar próximo", on_click=MedicoState.chamar, disabled=MedicoState.ocupado | MedicoState.tem_ficha | ~MedicoState.apto, background=COR_AZUL),
                    width="100%", align="center", wrap="wrap", spacing="3",
                ),
                rx.cond(MedicoState.status_operacional == "INDISPONÍVEL", rx.callout("Para receber chamadas, escolha ‘Ficar disponível’ quando estiver pronto para atender.", color_scheme="blue", width="100%")),
                rx.cond(MedicoState.mensagem != "", rx.callout(MedicoState.mensagem, color_scheme=rx.cond(MedicoState.erro, "red", "green"), width="100%")),
                rx.cond(
                    MedicoState.tem_ficha,
                    cartao_painel(rx.vstack(
                        rx.text("Ficha sob sua responsabilidade", weight="bold", size="5"),
                        rx.hstack(rx.text(MedicoState.ficha_atual["senha"], weight="bold", size="7", color=COR_AZUL), rx.text(MedicoState.ficha_atual["especialidade"], size="3"), wrap="wrap", spacing="4"),
                        rx.text("Paciente: ", MedicoState.ficha_atual["nome"], size="3"),
                        rx.text("Oportunidade ", MedicoState.ficha_atual["oportunidade"], " · tentativa ", MedicoState.ficha_atual["tentativa"], size="2"),
                        rx.hstack(
                            rx.button("Repetir chamada", on_click=MedicoState.repetir, disabled=MedicoState.ocupado, background=COR_AZUL),
                            rx.button("Compareceu", on_click=MedicoState.compareceu, disabled=MedicoState.ocupado, color_scheme="green"),
                            rx.button("Registrar desistência", on_click=MedicoState.pedir_desistencia, disabled=MedicoState.ocupado, color_scheme="red", variant="outline"),
                            rx.link(botao_secundario("Imprimir ficha"), href="/medico/ficha/" + MedicoState.ficha_atual["id"].to_string() + "/imprimir", target="_blank"),
                            wrap="wrap", spacing="3",
                        ),
                        rx.text("Histórico", weight="bold"),
                        rx.foreach(MedicoState.historico, lambda evento: rx.text(evento["tipo"], " · oportunidade ", evento["oportunidade"], " · tentativa ", evento["tentativa"], size="2")),
                        spacing="3", width="100%",
                    ), padding="24px"),
                    rx.callout("Nenhuma ficha atribuída. Use ‘Chamar próximo’ para receber uma ficha.", color_scheme="blue", width="100%"),
                ),
                rx.text("Filas de especialidade", weight="bold", size="5"),
                rx.text("Antes da atribuição, aparecem somente quantidades. O médico também pode apoiar outras especialidades.", size="2", color=COR_SECUNDARIA),
                rx.foreach(MedicoState.filas, lambda fila: cartao_painel(rx.hstack(
                    rx.text(fila["nome"], weight="medium"),
                    rx.cond(fila["propria"], rx.badge("Própria", color_scheme="blue"), rx.badge("Outra especialidade", color_scheme="gray")),
                    rx.spacer(), rx.text(fila["aguardando"], " aguardando", size="2"),
                    width="100%", align="center", wrap="wrap",
                ), padding="16px")),
                width="min(100%, 960px)", spacing="4", padding="28px 16px 48px",
            )),
            rx.alert_dialog.root(
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Confirmar desistência"),
                    rx.alert_dialog.description("A ficha será retirada definitivamente da fila."),
                    rx.hstack(rx.button("Cancelar", on_click=MedicoState.cancelar_desistencia, variant="outline"), rx.button("Confirmar desistência", on_click=MedicoState.desistiu, color_scheme="red"), justify="end", spacing="3", padding_top="16px"),
                ), open=MedicoState.confirmando_desistencia,
            ),
            background=COR_FUNDO, min_height="100vh", width="100%",
        ),
    )


def pagina_impressao_medico() -> rx.Component:
    return protegido("MEDICO", rx.box(
        rx.el.style("@media print { .nao-imprimir { display: none !important; } body { background: white !important; } }"),
        rx.cond(ImpressaoMedicoState.mensagem != "", rx.callout(ImpressaoMedicoState.mensagem, color_scheme="red"),
            rx.cond(ImpressaoMedicoState.tem_dados,
                rx.vstack(
                    rx.heading("Ficha de atendimento", size="6"),
                    rx.text("Senha: ", ImpressaoMedicoState.senha, weight="bold"),
                    rx.text("Especialidade: ", ImpressaoMedicoState.especialidade),
                    rx.text("Paciente: ", ImpressaoMedicoState.nome),
                    rx.text("Idade: ", ImpressaoMedicoState.idade),
                    rx.text("Prioridade: ", ImpressaoMedicoState.prioridade),
                    rx.text("Condição prioritária: ", ImpressaoMedicoState.condicao),
                    rx.text("Escore: ", ImpressaoMedicoState.escore),
                    rx.text("Classificação: ", ImpressaoMedicoState.classificacao),
                    rx.heading("Sintomas", size="4"),
                    rx.foreach(ImpressaoMedicoState.sintomas, lambda sintoma: rx.text(sintoma)),
                    rx.text("Observação: ", ImpressaoMedicoState.observacao),
                    rx.heading("Sinais vitais", size="4"),
                    rx.text("PA sistólica: ", ImpressaoMedicoState.pa_sistolica),
                    rx.text("FC: ", ImpressaoMedicoState.fc),
                    rx.text("FR: ", ImpressaoMedicoState.fr),
                    rx.text("Temperatura: ", ImpressaoMedicoState.temperatura),
                    rx.text("SpO₂: ", ImpressaoMedicoState.spo2),
                    rx.text("Glicemia: ", ImpressaoMedicoState.glicemia),
                    rx.hstack(rx.button("Imprimir", on_click=rx.call_script("window.print()")), rx.link("Voltar", href="/medico"), class_name="nao-imprimir"),
                    spacing="3", width="min(100%, 800px)", padding="32px", background="white",
                ), rx.text("Carregando ficha..."))),
        padding="24px", background=COR_FUNDO, min_height="100vh",
    ))

"""Resumo documental dos seis roteiros abertos da Sprint 5.

Lê resultados já coletados; nunca executa testes nem acessa o Xano.
"""

from __future__ import annotations

import argparse
from collections import Counter
from fnmatch import fnmatchcase
import json
from pathlib import Path


def verificacao(titulo: str, seletores: tuple[str, ...], pendencia: str) -> dict:
    return {"titulo": titulo, "seletores": seletores, "pendencia": pendencia}


# Snapshot dos cards 101–106 abertos na lista Sprint 5 do export Trello de 12/11/2026.
# O card 63 (ponta a ponta) e todos os cards closed ficam fora deste catálogo.
ROTEIROS = (
    {
        "numero": 101,
        "titulo": "Totem e fila de pré-triagem",
        "url": "https://trello.com/c/U2NEx9ZV/101-teste-totem-e-fila-de-pr%C3%A9-triagem",
        "verificacoes": (
            verificacao("Emissão do ticket sem dados pessoais no estado público", (
                "frontend/tests/test_totem_state.py::test_emissao_mostra_o_codigo_e_manda_a_chave_so_ao_backend",
            ), "Confirmar os três tipos, a numeração simultânea e a ausência de dados pessoais na API real."),
            verificacao("Tipo, horário e contagem dos tickets aguardando", (
                "frontend/tests/test_fila_tickets_state.py::TestApresentacaoFila.test_ticket_do_totem_ganha_tipo_cor_e_hora_de_brasilia",
                "frontend/tests/test_fila_tickets_state.py::TestApresentacaoFila.test_resumo_conta_somente_aguardando_por_tipo",
            ), "Conferir a lista e as contagens na tela autenticada."),
            verificacao("Intervalos configurados e chamada sempre manual", (
                "frontend/tests/test_chamada_manual.py::TestContagemPorChamada.test_primeira_chamada_espera_30_segundos",
                "frontend/tests/test_chamada_manual.py::TestContagemPorChamada.test_segunda_e_terceira_chamada_esperam_10_segundos",
                "frontend/tests/test_chamada_manual.py::TestAcoesManuais.test_tela_nunca_avanca_sozinha",
            ), "Cronometrar as ações e confirmar a ordem 2:1 na fila real."),
            verificacao("Presença, identificação e desistência", (
                "frontend/tests/test_fila_tickets_state.py::TestFilaTicketsState.test_marcar_presente_envia_acao_e_atualiza_ticket",
                "frontend/tests/test_fila_tickets_state.py::TestFilaTicketsState.test_identificacao_preserva_ticket",
                "frontend/tests/test_fila_tickets_state.py::TestFilaTicketsState.test_desistencia_envia_acao_e_recarrega",
            ), "Verificar a reentrada e o segundo não comparecimento no Xano real."),
        ),
    },
    {
        "numero": 102,
        "titulo": "Identificação do paciente e classificação na ficha",
        "url": "https://trello.com/c/q6VyShFt/102-teste-identifica%C3%A7%C3%A3o-do-paciente-e-classifica%C3%A7%C3%A3o-na-ficha",
        "verificacoes": (
            verificacao("CPF válido e inválido; abrir ou retomar ficha", (
                "backend/xano/function/pacientes/normalizar_cpf.xs::recusa dígitos verificadores inválidos",
                "frontend/tests/test_paciente_state.py::test_continuar_cria_ficha_para_paciente_identificado",
                "frontend/tests/test_paciente_state.py::test_continuar_reabre_ficha_em_triagem_existente",
            ), "Pesquisar, cadastrar e recusar nascimento futuro na API real."),
            verificacao("Limites do escore, sinais vitais e glicemia", (
                "backend/xano/function/classificacao/pontuar.xs::escore 4 sem item 3 é Azul",
                "backend/xano/function/classificacao/pontuar.xs::escore 5 sem item 3 é Amarela",
                "backend/xano/function/classificacao/pontuar.xs::escore 10 sem item 3 é Vermelha",
                "backend/xano/function/classificacao/pontuar.xs::glicemia 53 com gravidade gera Vermelha",
                "backend/xano/function/classificacao/pontuar.xs::SpO2 91 é Vermelha pela exceção",
            ), "Conferir os valores digitados e as mensagens na ficha real."),
            verificacao("Sintoma digitado, pendência e classificação manual", (
                "backend/xano/function/classificacao/pontuar.xs::sintoma digitado de 2 pontos soma ao escore",
                "backend/xano/function/classificacao/pontuar.xs::SpO2 ausente bloqueia o cálculo",
                "backend/xano/function/classificacao/pontuar.xs::11 anos é criança",
                "backend/xano/function/classificacao/pontuar.xs::gestante exige classificação manual",
            ), "Conferir recusa de sintoma repetido, justificativa e descarte do ajuste após edição na API real."),
        ),
    },
    {
        "numero": 103,
        "titulo": "Direcionamento, senha e comprovante",
        "url": "https://trello.com/c/4bgJ3BKZ/103-teste-direcionamento-senha-e-comprovante",
        "verificacoes": (
            verificacao("Destino pelos sintomas e idade", (
                "backend/xano/function/direcionamento/escolher_destino.xs::maior pontuação individual vence*",
                "backend/xano/function/direcionamento/escolher_destino.xs::empate na maior decidido pela soma*",
                "backend/xano/function/direcionamento/escolher_destino.xs::11 anos vai para Pediatria",
                "backend/xano/function/direcionamento/escolher_destino.xs::12 anos segue os sintomas",
                "backend/xano/function/direcionamento/escolher_destino.xs::sem sintoma do catálogo vai para a especialidade padrão",
            ), "Confirmar o destino previsto na ficha real."),
            verificacao("Formato da senha e regra de reavaliação", (
                "backend/xano/function/direcionamento/formatar_senha.xs::Amarela de Cardiologia número 42",
                "backend/xano/function/direcionamento/senha_reavaliada.xs::só a cor muda troca a letra e mantém o número",
                "backend/xano/function/direcionamento/senha_reavaliada.xs::especialidade muda pede número novo",
            ), "Conferir numeração sequencial diária e senha persistida na API real."),
            verificacao("Confirmar, reimprimir e proteger o comprovante", (
                "frontend/tests/test_ficha_state.py::TestConfirmacaoTriagem.test_confirmacao_envia_post_e_abre_o_comprovante",
                "frontend/tests/test_ficha_state.py::TestConfirmacaoTriagem.test_reimprimir_abre_o_comprovante",
                "frontend/tests/test_ficha_state.py::TestComprovante.test_carrega_so_os_campos_do_comprovante",
                "frontend/tests/test_ficha_state.py::TestComprovante.test_comprovante_renderizado_nao_expoe_dados_pessoais_ou_clinicos",
            ), "Imprimir e inspecionar o papel de 80 mm; confirmar os dados da API real."),
        ),
    },
    {
        "numero": 104,
        "titulo": "Fila do médico e atendimento",
        "url": "https://trello.com/c/CllOO9y9/104-teste-fila-do-m%C3%A9dico-e-atendimento",
        "verificacoes": (
            verificacao("Ordem de cor, prioridade e apoio entre filas", (
                "tests/api/test_ordenacao.py::OrdenacaoTest.test_ciclo_amarela_amarela_azul",
                "tests/api/test_ordenacao.py::OrdenacaoTest.test_prioritarios_dentro_da_cor_sem_precedencia_entre_tipos",
                "tests/api/test_selecao_entre_filas.py::SelecaoEntreFilasTest.test_descoberta_mais_grave_supera_propria",
            ), "Confirmar a ordem com fichas e médicos reais."),
            verificacao("Ações sobre a ficha atribuída e fila vazia", (
                "frontend/tests/test_medico_state.py::MedicoStateTest.test_chamar_nao_envia_id_de_ficha_e_mostra_fila_vazia",
                "frontend/tests/test_medico_state.py::MedicoStateTest.test_desistencia_exige_confirmacao_antes_de_enviar",
                "frontend/tests/test_medico_state.py::MedicoStateTest.test_comparecimento_envia_acao_da_ficha_atribuida",
            ), "Conferir chamadas, impressão e plantão na API real."),
            verificacao("Dois médicos chamando ao mesmo tempo", (),
                       "Teste de integração com escrita existente fora do CI; requer workspace descartável confirmado."),
        ),
    },
    {
        "numero": 105,
        "titulo": "Painel público e privacidade",
        "url": "https://trello.com/c/LcyWdDfe/105-teste-painel-p%C3%BAblico-e-privacidade",
        "verificacoes": (
            verificacao("CPF mascarado e texto do aviso público", (
                "frontend/tests/test_privacidade.py::test_cpf_com_11_digitos_mostra_so_do_4o_ao_9o",
                "frontend/tests/test_privacidade.py::test_pagina_mostra_o_texto_do_arquivo_do_aviso",
            ), "Conferir todas as telas internas e o link do aviso no navegador."),
            verificacao("Mensagem e encerramento por inatividade", (
                "frontend/tests/test_auth_state.py::test_saida_por_inatividade_encerra_a_sessao_e_avisa_no_login",
            ), "Conferir inatividade e movimento do mouse em sessão real."),
            verificacao("Painel, som, previsão e reconexão", (),
                       "A página e o endpoint do painel ainda não foram entregues nesta branch."),
        ),
    },
    {
        "numero": 106,
        "titulo": "Administrador: usuários, cadastros, acompanhamento e permissões",
        "url": "https://trello.com/c/vFMKYEh1/106-teste-administrador-usu%C3%A1rios-cadastros-acompanhamento-e-permiss%C3%B5es",
        "verificacoes": (
            verificacao("Login com código e proteção de perfil", (
                "frontend/tests/test_auth_state.py::test_codigo_correto_guarda_token_e_vai_para_a_area_do_perfil",
                "frontend/tests/test_auth_state.py::test_guarda_com_perfil_errado_redireciona_para_a_propria_area",
            ), "Confirmar e-mail recebido e recusa pelo backend ao acessar outro perfil."),
            verificacao("Redefinição e reenvio de código", (
                "frontend/tests/test_senha_state.py::test_codigo_invalido_mostra_a_mensagem_da_tela_a2b",
                "frontend/tests/test_senha_state.py::test_reenvio_avisa_e_reinicia_o_contador",
            ), "Confirmar o fluxo com e-mail real e limites de tempo."),
            verificacao("Usuários, troca de perfil e permissões", (
                "frontend/tests/test_usuarios_state.py::test_filtro_por_perfil_situacao_e_busca",
                "frontend/tests/test_usuarios_state.py::test_criar_admin_envia_senha_e_edicao_nao",
                "frontend/tests/test_usuarios_state.py::test_trocar_perfil_mostra_erro_do_ultimo_admin_e_mantem_dialogo",
            ), "Confirmar criação, troca de perfil e autorização na API real."),
            verificacao("Cadastros, parâmetros e plantões", (
                "frontend/tests/test_cadastros_state.py::test_especialidade_nova_envia_sigla_em_maiusculas_e_edicao_nao_envia_sigla",
                "frontend/tests/test_cadastros_state.py::test_sintoma_converte_pontuacao_e_mantem_ordem_dos_destinos",
                "frontend/tests/test_cadastros_state.py::test_plantao_sobreposto_mostra_a_mensagem",
                "frontend/tests/test_cadastros_state.py::test_parametro_nao_numerico_nem_chama_a_api",
            ), "Conferir as operações e os limites nas APIs reais e nas telas."),
            verificacao("Dashboard do plantão do Administrador", (
                "frontend/tests/test_painel_admin.py::test_indicadores_do_dia",
                "frontend/tests/test_painel_admin.py::test_equipe_conta_medicos_por_status",
                "frontend/tests/test_plantao_state.py::test_na_espera_soma_pre_triagem_e_fila_medica",
            ), "Conferir os indicadores com dados reais do plantão."),
            verificacao("Acompanhamento completo da fila, equipe, fichas e auditoria", (),
                       "As consultas e telas de acompanhamento detalhado ainda estão pendentes na change ativa."),
        ),
    },
)


TIPOS = {
    "unitario_nativo": "Xano (função pura)",
    "integracao_funcao_pura": "Xano (função pura)",
    "integracao_mock": "Reflex (API simulada)",
    "unitario": "Reflex (teste local)",
}


def avaliar(verificacao_item: dict, casos: list[dict]) -> tuple[str, list[dict]]:
    """Retorna o resultado técnico sem confundi-lo com aceite do roteiro."""
    seletores = verificacao_item["seletores"]
    if not seletores:
        return "PENDENTE", []
    grupos = [
        [caso for caso in casos if caso.get("tipo") != "e2e" and fnmatchcase(caso.get("node", ""), seletor)]
        for seletor in seletores
    ]
    selecionados = {caso["node"]: caso for grupo in grupos for caso in grupo}
    encontrados = list(selecionados.values())
    estados = {caso.get("status") for caso in encontrados}
    if estados & {"FAIL", "ERROR"}:
        return "FALHOU", encontrados
    if any(not grupo for grupo in grupos):
        return "SEM EVIDÊNCIA", encontrados
    if estados & {"NOT_RUN", "SKIPPED"}:
        return "NÃO EXECUTADO", encontrados
    if estados == {"PASS"}:
        return "PASS técnico", encontrados
    return "SEM EVIDÊNCIA", encontrados


def _celula(valor: str) -> str:
    return str(valor).replace("|", "\\|").replace("\n", " ")


def _resumir_evidencia(encontrados: list[dict]) -> str:
    if not encontrados:
        return "—"
    contagens = Counter(TIPOS.get(caso.get("tipo"), "Outro teste") for caso in encontrados)
    return "; ".join(
        f"{origem}: {quantidade} {'teste' if quantidade == 1 else 'testes'}"
        for origem, quantidade in contagens.items()
    )


def gerar_relatorio(dados: dict) -> str:
    casos = dados.get("casos") or []
    totais: Counter[str] = Counter()
    blocos = [
        "# Testes dos roteiros abertos da Sprint 5",
        "",
        f"Commit: `{_celula(dados.get('commit') or 'não informado')}` · Execução: `{_celula(dados.get('execucao_id') or 'não informada')}` · Data UTC: {_celula(dados.get('data_utc') or 'não informada')}",
        "",
        "Este resumo reúne somente os cards abertos 101–106 da Sprint 5. O card de integração ponta a ponta e os cards fechados não entram aqui.",
        "",
        "**PASS técnico** confirma apenas os testes citados; nenhum roteiro é considerado aprovado por inteiro sem executar seus passos pendentes.",
        "",
        "Os nomes e identificadores de cada teste estão no arquivo detalhado `resultados.json`.",
        "",
    ]
    limitacoes = dados.get("limitacoes") or []
    if any("Árvore de trabalho com alterações locais" in item for item in limitacoes):
        blocos += ["**Rastreabilidade:** esta coleta local incluiu arquivos ainda não commitados; o SHA acima identifica apenas o commit de base.", ""]
    if any("equivalência integral do código remoto" in item for item in limitacoes):
        blocos += ["**Xano:** esta execução não comparou integralmente o código remoto da branch `v1` com os XanoScripts versionados.", ""]
    for roteiro in ROTEIROS:
        blocos += [
            f"## {roteiro['numero']} — [{roteiro['titulo']}]({roteiro['url']})",
            "",
            "| Verificação disponível | Resultado | Evidência automatizada | Falta para concluir o roteiro |",
            "|---|---|---|---|",
        ]
        for item in roteiro["verificacoes"]:
            resultado, encontrados = avaliar(item, casos)
            totais[resultado] += 1
            evidencia = _resumir_evidencia(encontrados)
            blocos.append("| " + " | ".join(map(_celula, (
                item["titulo"], resultado, evidencia, item["pendencia"],
            ))) + " |")
        blocos.append("")
    resumo = (f"Verificações: {sum(totais.values())} · PASS técnico: {totais['PASS técnico']} · "
              f"Falhou: {totais['FALHOU']} · Não executado: {totais['NÃO EXECUTADO']} · "
              f"Sem evidência: {totais['SEM EVIDÊNCIA']} · Pendente: {totais['PENDENTE']}")
    blocos[4:4] = [resumo, ""]
    blocos += ["## Leitura dos resultados", "",
               "- **PASS técnico:** todos os testes ligados à verificação passaram; a coluna final ainda precisa ser conferida.",
               "- **FALHOU:** pelo menos um teste ligado falhou ou teve erro.",
               "- **NÃO EXECUTADO:** há teste ignorado ou ainda não executado.",
               "- **SEM EVIDÊNCIA:** um teste esperado não apareceu nos resultados; conferir a coleta ou o nome do teste.",
               "- **PENDENTE:** a verificação depende de implementação ou ambiente ainda indisponível.", ""]
    return "\n".join(blocos)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="resultados.json consolidado")
    parser.add_argument("--output", type=Path, required=True, help="Markdown para documentação")
    argumentos = parser.parse_args()
    dados = json.loads(argumentos.input.read_text(encoding="utf-8"))
    argumentos.output.parent.mkdir(parents=True, exist_ok=True)
    argumentos.output.write_text(gerar_relatorio(dados), encoding="utf-8")


if __name__ == "__main__":
    main()

"""Confere a rastreabilidade e a apresentação dos testes da Sprint 5."""

from fnmatch import fnmatchcase

from scripts import roteiros_sprint5, run_test_evidence


def _caso(node: str, status: str, tipo: str = "unitario_nativo") -> dict:
    return {"node": node, "status": status, "tipo": tipo, "nome": node.split("::")[-1]}


def test_catalogo_tem_somente_os_seis_roteiros_abertos_sem_ponta_a_ponta() -> None:
    numeros = [roteiro["numero"] for roteiro in roteiros_sprint5.ROTEIROS]
    assert numeros == [101, 102, 103, 104, 105, 106]
    assert all("ponta-a-ponta" not in roteiro["url"] for roteiro in roteiros_sprint5.ROTEIROS)
    assert all(roteiro["verificacoes"] for roteiro in roteiros_sprint5.ROTEIROS)


def test_todos_os_seletores_disponiveis_apontam_para_casos_reais() -> None:
    inventario = run_test_evidence.catalog("reflex") + run_test_evidence.catalog("xano-safe")
    seletores = [
        seletor
        for roteiro in roteiros_sprint5.ROTEIROS
        for verificacao in roteiro["verificacoes"]
        for seletor in verificacao["seletores"]
    ]
    assert seletores
    assert all(any(fnmatchcase(caso["node"], seletor) for caso in inventario) for seletor in seletores)


def test_resultado_tecnico_propagado_sem_aprovar_execucao_parcial() -> None:
    item = roteiros_sprint5.verificacao("exemplo", ("a::*", "b::*"), "pendência")
    casos = [_caso("a::um", "PASS"), _caso("b::dois", "PASS")]
    assert roteiros_sprint5.avaliar(item, casos)[0] == "PASS técnico"
    assert roteiros_sprint5.avaliar(item, casos[:1])[0] == "SEM EVIDÊNCIA"
    assert roteiros_sprint5.avaliar(item, [casos[0], _caso("b::dois", "NOT_RUN")])[0] == "NÃO EXECUTADO"
    assert roteiros_sprint5.avaliar(item, [casos[0], _caso("b::dois", "FAIL")])[0] == "FALHOU"
    assert roteiros_sprint5.avaliar(item, [casos[0], _caso("b::dois", "ERROR")])[0] == "FALHOU"
    assert roteiros_sprint5.avaliar(item, [casos[0], _caso("b::dois", "SKIPPED")])[0] == "NÃO EXECUTADO"
    assert roteiros_sprint5.avaliar(item, [_caso("a::um", "FAIL")])[0] == "FALHOU"


def test_caso_e2e_nao_conta_como_evidencia_deste_relatorio() -> None:
    item = roteiros_sprint5.verificacao("exemplo", ("a::*",), "pendência")
    assert roteiros_sprint5.avaliar(item, [_caso("a::um", "PASS", "e2e")])[0] == "SEM EVIDÊNCIA"
    assert roteiros_sprint5.avaliar(roteiros_sprint5.verificacao("pendente", (), "a entregar"), [])[0] == "PENDENTE"


def test_markdown_e_legivel_e_nao_contem_dados_de_entrada() -> None:
    primeiro = roteiros_sprint5.ROTEIROS[0]["verificacoes"][0]
    caso = _caso(primeiro["seletores"][0], "PASS", "integracao_mock")
    caso["entradas"] = "nome e CPF fictícios que não devem ir para o relatório"
    texto = roteiros_sprint5.gerar_relatorio({
        "commit": "abc123", "execucao_id": "41", "casos": [caso],
        "limitacoes": ["reflex: Árvore de trabalho com alterações locais"],
    })
    assert texto.count("## 101 —") == 1
    assert texto.count("## 106 —") == 1
    assert "PASS técnico" in texto
    assert "SEM EVIDÊNCIA" in texto
    assert "PENDENTE" in texto
    assert "nenhum roteiro é considerado aprovado por inteiro" in texto
    assert "SHA acima identifica apenas o commit de base" in texto
    assert "CPF fictícios" not in texto
    assert "Reflex (API simulada): 1 teste" in texto
    assert "emissao mostra o codigo" not in texto

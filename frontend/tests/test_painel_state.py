"""Formatação e detecção de novidade do painel público (add-painel-publico, D2 a D4)."""

from ps_fila_prioritaria.estados.painel import chave_novidade, destino, montar_painel, siglas_do_filtro, tentativa_texto

CORPO = {
    "atual": {"chamada_id": 74, "senha": "V-CAR-003", "cor": "VERMELHA", "especialidade": "Cardiologia", "sigla": "CAR",
              "sala": "2", "tentativa": 2, "chamado_em": 1794792045412},
    "ultimas": [{"senha": f"A-CLI-00{i}", "cor": "AMARELA", "especialidade": "Clínica Geral", "sigla": "CLI", "sala": None,
                 "chamado_em": 1794792000000} for i in range(1, 6)],
    "triagem": {"ticket_id": 80, "tipo": "PEDIATRICO", "numero": 4, "tentativa": 1, "chamado_em": 1794693165409},
    "previsoes": [{"especialidade": "Cardiologia", "sigla": "CAR", "senhas": [{"senha": "A-CAR-001", "cor": "AMARELA"}]},
                  {"especialidade": "Neurologia", "sigla": "NEU", "senhas": []}],
    "gerado_em": 1794792050000,
}


def test_destino_com_e_sem_sala():
    assert destino({"especialidade": "Clínica Geral", "sala": "2"}) == "Clínica Geral — Sala 2"
    assert destino({"especialidade": "Clínica Geral", "sala": "Sala 3"}) == "Clínica Geral — Sala 3"
    assert destino({"especialidade": "Ortopedia", "sala": None}) == "Ortopedia"


def test_tentativa_so_aparece_na_repeticao():
    assert tentativa_texto(1) == ""
    assert tentativa_texto(None) == ""
    assert tentativa_texto(2) == "2ª chamada"


def test_montar_painel_formata_para_a_tv():
    painel = montar_painel(CORPO)
    assert painel["atual"]["senha"] == "V-CAR-003"
    assert painel["atual"]["destino"] == "Cardiologia — Sala 2"
    assert painel["atual"]["tentativa"] == "2ª chamada"
    assert painel["atual"]["cor_nome"] == "Vermelha"
    assert len(painel["ultimas"]) == 4
    assert painel["triagem"]["ticket"] == "C-004"
    assert painel["previsoes"][1]["senhas"] == []


def test_painel_vazio():
    painel = montar_painel({"atual": None, "ultimas": [], "triagem": None, "previsoes": []})
    assert painel["atual"] is None and painel["triagem"] is None and painel["ultimas"] == []


def test_novidade_muda_com_chamada_repeticao_e_ticket():
    base = chave_novidade(CORPO)
    assert chave_novidade(CORPO) == base
    repetida = {**CORPO, "atual": {**CORPO["atual"], "chamada_id": 75}}
    assert chave_novidade(repetida) != base
    rechamado = {**CORPO, "triagem": {**CORPO["triagem"], "chamado_em": 1794693199999}}
    assert chave_novidade(rechamado) != base
    # Só a previsão mudou: não é chamada nova, então não toca o aviso.
    assert chave_novidade({**CORPO, "previsoes": []}) == base


def test_filtro_do_endereco():
    assert siglas_do_filtro("car, ort") == "CAR,ORT"
    assert siglas_do_filtro("") == ""
    assert siglas_do_filtro(None) == ""

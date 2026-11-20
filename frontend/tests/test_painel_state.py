"""Formatação e detecção de novidade do painel público (add-painel-publico, D2 a D4)."""

from ps_fila_prioritaria.estados.painel import chave_novidade, destino, montar_painel, siglas_do_filtro, tela_da_rota, tentativa_texto

CORPO = {
    "atual": {"chamada_id": 74, "senha": "V-CAR-003", "cor": "VERMELHA", "especialidade": "Cardiologia", "sigla": "CAR",
              "sala": "2", "tentativa": 2, "chamado_em": 1794792045412},
    "ultimas": [{"senha": f"A-CLI-00{i}", "cor": "AMARELA", "especialidade": "Clínica Geral", "sigla": "CLI", "sala": None,
                 "chamado_em": 1794792000000} for i in range(1, 6)],
    "triagem": {"ticket_id": 80, "tipo": "PEDIATRICO", "numero": 4, "tentativa": 1, "chamado_em": 1794693165409},
    "triagem_ultimas": [{"ticket_id": 79, "tipo": "NORMAL", "numero": 31, "chamado_em": 1794693000000}],
    "previsoes": [{"especialidade": "Cardiologia", "sigla": "CAR", "senhas": [{"senha": "A-CAR-001", "cor": "AMARELA"}]},
                  {"especialidade": "Neurologia", "sigla": "NEU", "senhas": []}],
    "gerado_em": 1794792050000,
}


def test_destino_com_e_sem_sala():
    assert destino({"especialidade": "Clínica Geral", "sala": "2"}) == "Clínica Geral · Sala 2"
    assert destino({"especialidade": "Clínica Geral", "sala": "Sala 3"}) == "Clínica Geral · Sala 3"
    assert destino({"especialidade": "Ortopedia", "sala": None}) == "Ortopedia"


def test_tentativa_sempre_indicada():
    assert tentativa_texto(1) == "1ª chamada"
    assert tentativa_texto(None) == "1ª chamada"
    assert tentativa_texto(2) == "2ª chamada"


def test_montar_painel_formata_para_a_tv():
    painel = montar_painel(CORPO)
    assert painel["atual"]["senha"] == "V-CAR-003"
    assert painel["atual"]["destino"] == "Cardiologia · Sala 2"
    assert painel["atual"]["tentativa"] == "2ª chamada"
    assert painel["atual"]["cor_nome"] == "Vermelha"
    assert len(painel["ultimas"]) == 4
    assert painel["triagem"]["ticket"] == "C-004"
    assert painel["triagem_ultimas"][0]["ticket"] == "N-031"
    assert (painel["ultimas"][0]["especialidade"], painel["ultimas"][0]["sala"]) == ("Clínica Geral", "—")
    # Decisão do PO: o painel não mostra a previsão das próximas senhas.
    assert "previsoes" not in painel


def test_painel_vazio():
    painel = montar_painel({"atual": None, "ultimas": [], "triagem": None})
    assert painel["atual"] is None and painel["triagem"] is None and painel["ultimas"] == []


def test_novidade_de_cada_tela():
    repetida = {**CORPO, "atual": {**CORPO["atual"], "chamada_id": 75}}
    rechamado = {**CORPO, "triagem": {**CORPO["triagem"], "chamado_em": 1794693199999}}
    # Painel dos médicos: só a chamada médica nova ou repetida conta.
    assert chave_novidade(repetida, "medico") != chave_novidade(CORPO, "medico")
    assert chave_novidade(rechamado, "medico") == chave_novidade(CORPO, "medico")
    # Painel da triagem: só o ticket chamado ou rechamado conta.
    assert chave_novidade(rechamado, "triagem") != chave_novidade(CORPO, "triagem")
    assert chave_novidade(repetida, "triagem") == chave_novidade(CORPO, "triagem")


def test_tela_pela_rota():
    assert tela_da_rota("/painel/triagem") == "triagem"
    assert tela_da_rota("/painel/triagem/") == "triagem"
    assert tela_da_rota("/painel/medico") == "medico"


def test_filtro_do_endereco():
    assert siglas_do_filtro("car, ort") == "CAR,ORT"
    assert siglas_do_filtro("") == ""
    assert siglas_do_filtro(None) == ""

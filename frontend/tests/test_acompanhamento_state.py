"""Fila geral e detalhe da ficha do Administrador (add-acompanhamento-administrador, D3/D4)."""

import asyncio
from datetime import datetime
from unittest.mock import patch

from ps_fila_prioritaria.comum import FUSO_BRASILIA
from ps_fila_prioritaria.estados import acompanhamento as a
from tests.test_cadastros_state import REQUISITAR, Resposta, estado_falso

AGORA = datetime(2026, 11, 15, 15, 0, tzinfo=FUSO_BRASILIA)
MS = int(AGORA.timestamp() * 1000)


def _ficha(id_, status, cor="AZUL", especialidade="Cardiologia", posicao=None, minutos=10, **extra):
    return {"id": id_, "senha": f"X-{id_}", "status": status, "cor": cor, "especialidade": especialidade, "posicao": posicao,
            "chegada_em": MS - minutos * 60_000, "condicao_prioritaria": "NENHUMA", **extra}


def test_espera_em_minutos_e_horas():
    assert a.espera(MS - 45 * 60_000, AGORA) == "45 min"
    assert a.espera(MS - 125 * 60_000, AGORA) == "2 h 05 min"
    assert a.espera(None, AGORA) == "—"


def test_linha_mostra_medico_e_tentativa_na_chamada_e_posicao_na_espera():
    chamada = a.linha_fila(_ficha(1, "CHAMADO", medico="Dra. Ana", tentativa=2), AGORA)
    assert chamada["detalhe"] == "Dra. Ana · tentativa 2" and chamada["status_nome"] == "Chamado"
    assert a.linha_fila(_ficha(2, "AGUARDANDO", posicao=3), AGORA)["detalhe"] == "3º na fila"
    assert a.linha_fila(_ficha(3, "AGUARDANDO"), AGORA)["detalhe"] == "depois da 20ª"
    assert a.linha_fila(_ficha(4, "EM_TRIAGEM", condicao_prioritaria="IDOSO"), AGORA)["condicao"] == "Idoso"


def test_ordem_chamadas_depois_aguardando_pela_posicao_depois_triagem():
    linhas = [a.linha_fila(f, AGORA) for f in [
        _ficha(1, "EM_TRIAGEM", minutos=50),
        _ficha(2, "AGUARDANDO", especialidade="Cardiologia", posicao=2),
        _ficha(3, "CHAMADO"),
        _ficha(4, "AGUARDANDO", especialidade="Cardiologia", posicao=1),
        _ficha(5, "AGUARDANDO", especialidade="Clínica Geral", posicao=1),
    ]]
    assert [l["id"] for l in a.ordenar_fila(linhas)] == [3, 4, 2, 5, 1]


def test_filtros_vazios_nao_vao_para_a_api():
    assert a.parametros_fila("0", "TODAS", "TODOS") == {}
    assert a.parametros_fila("3", "VERMELHA", "CHAMADO") == {"especialidade_id": 3, "cor": "VERMELHA", "status": "CHAMADO"}


def test_detalhe_mostra_ajuste_chamadas_e_historico():
    corpo = {"id": 9, "senha": "V-CAR-007", "senhas": ["A-CAR-007", "V-CAR-007"], "status": "CHAMADO", "cor": "VERMELHA",
             "cor_calculada": "AMARELA", "justificativa_ajuste": "Dor intensa", "sinais": {"fc": 120, "spo2": None},
             "sintomas": [{"nome": "Dor no peito", "pontuacao": 2, "digitado": False}],
             "chamadas": [{"em": MS, "tipo": "CHAMADA", "tentativa": 1, "oportunidade": 1, "medico": "Dra. Ana"},
                          {"em": MS, "tipo": "CHAMADA", "tentativa": 2, "oportunidade": 1, "medico": "Dra. Ana"}],
             "historico": [{"em": MS, "tipo_evento": "PRIORIDADE_AJUSTADA", "usuario": "Rita", "valor_anterior": {"cor": "AMARELA"},
                            "valor_novo": {"cor": "VERMELHA"}, "justificativa": "Dor intensa"}]}
    d = a.detalhe_ficha(corpo)
    assert d["senhas"] == "A-CAR-007, V-CAR-007" and d["cor"] == "Vermelha"
    assert d["ajuste"] == "Ajustada de Amarela para Vermelha: Dor intensa"
    assert d["sinais"] == [{"nome": "FC", "valor": "120 bpm"}]
    assert [c["tentativa"] for c in d["chamadas"]] == ["oportunidade 1, tentativa 1", "oportunidade 1, tentativa 2"]
    assert d["historico"][0]["anterior"] == "cor: AMARELA" and d["historico"][0]["justificativa"] == "Dor intensa"


def test_trocar_filtro_consulta_de_novo():
    estado = estado_falso(a.FilaGeralState, itens=[], especialidade_id="0", cor="TODAS", status="TODOS", opcoes_especialidades=[],
                          carregando=False, mensagem="", erro=False, atualizado_em="")
    estado.atualizar = lambda _=None: a.FilaGeralState.atualizar.fn(estado)
    chamadas = []

    def requisitar(metodo, _variavel, caminho, **kw):
        chamadas.append((caminho, kw.get("params")))
        return Resposta(200, [_ficha(1, "AGUARDANDO", cor="VERMELHA", posicao=1)])

    with patch(REQUISITAR, side_effect=requisitar):
        asyncio.run(a.FilaGeralState.set_cor.fn(estado, "VERMELHA"))
    assert chamadas == [("/admin/fila-geral", {"cor": "VERMELHA"})]
    assert estado.itens[0]["detalhe"] == "1º na fila"

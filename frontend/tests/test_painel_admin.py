"""Dashboard do Administrador (add-acompanhamento-administrador, D6): indicadores do dia e equipe logada."""

import asyncio
from unittest.mock import patch

from ps_fila_prioritaria.estados import equipe as eq
from ps_fila_prioritaria.estados.plantao import resumir_plantao
from tests.test_cadastros_state import REQUISITAR, Resposta, estado_falso
from tests.test_plantao_state import AGORA, FICHAS, TICKETS, ficha, ms


def test_indicadores_do_dia() -> None:
    indicadores = {i["rotulo"]: i for i in resumir_plantao(FICHAS, TICKETS, AGORA)["indicadores"]}
    assert [indicadores[n]["valor"] for n in ("Atendidas", "Desistências", "Canceladas")] == ["1", "1", "0"]
    # Fila médica agora: 90, 140, 25, 10 e 880 min → média de 229 min.
    assert indicadores["Espera média"]["valor"] == "3 h 49 min"
    assert indicadores["Espera média"]["detalhe"] == "de 5 na fila médica agora"


def test_indicadores_com_fila_vazia_e_cancelada() -> None:
    indicadores = {i["rotulo"]: i for i in resumir_plantao([ficha(1, "CANCELADO", ms(9, 0))], [], AGORA)["indicadores"]}
    assert indicadores["Canceladas"]["valor"] == "1"
    assert indicadores["Espera média"]["valor"] == "—" and indicadores["Espera média"]["detalhe"] == "fila médica vazia"


def test_espera_media_abaixo_de_uma_hora() -> None:
    fichas = [ficha(1, "AGUARDANDO", ms(14, 0)), ficha(2, "AGUARDANDO", ms(14, 20))]  # 30 e 10 min
    indicadores = {i["rotulo"]: i for i in resumir_plantao(fichas, [], AGORA)["indicadores"]}
    assert indicadores["Espera média"]["valor"] == "20 min"


EQUIPE = [
    {"usuario_id": 3, "nome": "Carla", "perfil": "RECEPCAO_TRIAGEM", "status": "DISPONIVEL", "login_em": ms(7, 5)},
    {"usuario_id": 1, "nome": "Ana Admin", "perfil": "ADMINISTRADOR", "status": None, "login_em": ms(8, 0)},
    {"usuario_id": 5, "nome": "Bruno", "perfil": "MEDICO", "status": "PAUSA", "login_em": ms(6, 58)},
    {"usuario_id": 6, "nome": "alice", "perfil": "MEDICO", "status": None, "login_em": ms(13, 30)},
]


def test_equipe_medicos_primeiro_e_por_nome() -> None:
    r = eq.resumir_equipe(EQUIPE)
    assert [p["nome"] for p in r["pessoas"]] == ["alice", "Bruno", "Carla", "Ana Admin"]
    assert [p["status"] for p in r["pessoas"]] == ["Sem status", "Pausa", "Disponível", "—"]
    assert r["pessoas"][1]["login"] == "06:58"


def test_equipe_conta_medicos_por_status() -> None:
    r = eq.resumir_equipe(EQUIPE)
    contagem = {s["nome"]: s["quantidade"] for s in r["medicos_por_status"]}
    assert contagem == {"Disponível": 0, "Em atendimento": 0, "Pausa": 1, "Ausente": 0, "Sem status": 1}
    assert r["medicos_logados"] == 2 and r["recepcao_logada"] == 1


def test_equipe_vazia() -> None:
    r = eq.resumir_equipe([])
    assert r["pessoas"] == [] and r["medicos_logados"] == 0 and all(s["quantidade"] == 0 for s in r["medicos_por_status"])


def _estado():
    estado = estado_falso(eq.EquipeState, pessoas=[], medicos_por_status=[], medicos_logados=0, recepcao_logada=0)
    return estado


def test_carregar_busca_a_equipe() -> None:
    estado = _estado()
    with patch(REQUISITAR, return_value=Resposta(200, {"equipe": EQUIPE, "agora": ms(14, 30)})) as requisitar:
        asyncio.run(eq.EquipeState.carregar.fn(estado))
    assert requisitar.call_args.args[:3] == ("GET", "XANO_CADASTROS_API_URL", "/admin/equipe")
    assert estado.medicos_logados == 2 and estado.mensagem == ""


def test_carregar_mostra_erro_e_mantem_os_dados() -> None:
    estado = _estado()
    estado.medicos_logados = 4
    with patch(REQUISITAR, return_value=Resposta(403, {"message": "Acesso negado."})):
        asyncio.run(eq.EquipeState.carregar.fn(estado))
    assert estado.medicos_logados == 4 and estado.mensagem == "Acesso negado."

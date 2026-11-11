"""Painel do plantão da Recepção: números calculados a partir das fichas e dos tickets."""

import asyncio
from datetime import datetime
from unittest.mock import patch

import httpx

from ps_fila_prioritaria.comum import FUSO_BRASILIA
from ps_fila_prioritaria.estados.plantao import PlantaoState, resumir_plantao

# Quarta, 11/11/2026, 14:30 em Brasília.
AGORA = datetime(2026, 11, 11, 14, 30, tzinfo=FUSO_BRASILIA).timestamp()


def ms(hora: int, minuto: int = 0, dia: int = 11) -> int:
    return int(datetime(2026, 11, dia, hora, minuto, tzinfo=FUSO_BRASILIA).timestamp() * 1000)


def ficha(id_: int, status: str, chegada: int, prioridade: str | None = None, especialidade: str | None = None, senha: str | None = None) -> dict:
    return {"id": id_, "status": status, "chegada_em": chegada, "prioridade_atual": prioridade, "especialidade": especialidade, "senha": senha}


FICHAS = [
    ficha(1, "AGUARDANDO", ms(13, 0), "VERMELHA", "Cardiologia", "V-CAR-001"),
    ficha(2, "AGUARDANDO", ms(12, 10), "AMARELA", "Clínica Geral", "A-CLI-001"),  # a mais antiga na fila: 2 h 20 min
    ficha(3, "AGUARDANDO", ms(14, 5), "AMARELA", "Cardiologia", "A-CAR-002"),
    ficha(4, "AGUARDANDO", ms(14, 20), "AZUL", "Cardiologia", "Z-CAR-003"),
    ficha(5, "EM_TRIAGEM", ms(14, 25)),
    ficha(6, "CHAMADO", ms(11, 0), "AZUL", "Ortopedia", "Z-ORT-001"),
    ficha(7, "ATENDIDO", ms(9, 0), "AZUL", "Ortopedia", "Z-ORT-002"),
    ficha(8, "DESISTENCIA", ms(10, 0), "AZUL", "Clínica Geral", "Z-CLI-004"),
    ficha(9, "AGUARDANDO", ms(23, 50, dia=10), "AZUL", "Neurologia", "Z-NEU-001"),  # chegou ontem: fora do gráfico de hoje
]
TICKETS = [
    {"id": 1, "tipo": "NORMAL", "numero": 31, "status": "AGUARDANDO", "emitido_em": ms(14, 0)},
    {"id": 2, "tipo": "PEDIATRICO", "numero": 4, "status": "AGUARDANDO", "emitido_em": ms(14, 28)},
    {"id": 3, "tipo": "PREFERENCIAL", "numero": 12, "status": "CHAMADO", "emitido_em": ms(14, 10)},
]


def test_na_espera_soma_pre_triagem_e_fila_medica() -> None:
    r = resumir_plantao(FICHAS, TICKETS, AGORA)
    assert (r["na_espera"], r["tickets_aguardando"], r["fichas_aguardando"]) == (7, 2, 5)


def test_barra_por_cor_soma_100_e_rotula_so_o_que_cabe() -> None:
    r = resumir_plantao(FICHAS, TICKETS, AGORA)
    cores = {c["codigo"]: c for c in r["cores"]}
    assert [cores[c]["quantidade"] for c in ("VERMELHA", "AMARELA", "AZUL")] == [1, 2, 2]
    assert round(sum(c["percentual"] for c in r["cores"])) == 100
    assert cores["AMARELA"]["rotulo"] == "2 Amarela" and cores["AMARELA"]["texto"] == "#1A1A1A"
    assert cores["VERMELHA"]["rotulo"] == "1"  # 20%: só o número
    assert cores["VERMELHA"]["dica"] == "Vermelha: 1 na fila médica"


def test_cor_sem_ficha_nao_aparece_e_bloco_estreito_fica_sem_rotulo() -> None:
    muitas_azuis = [ficha(i, "AGUARDANDO", ms(14), "AZUL") for i in range(10)] + [ficha(99, "AGUARDANDO", ms(14), "VERMELHA")]
    cores = {c["codigo"]: c for c in resumir_plantao(muitas_azuis, [], AGORA)["cores"]}
    assert not cores["AMARELA"]["visivel"]
    assert cores["VERMELHA"]["percentual"] < 30 and cores["VERMELHA"]["rotulo"] == "1"  # bloco médio: só o número
    assert cores["AZUL"]["rotulo"] == "10 Azul"


def test_espera_mais_longa_em_minutos_e_horas() -> None:
    r = resumir_plantao(FICHAS, TICKETS, AGORA)
    assert r["maior_ficha"] == {"identificacao": "Z-NEU-001", "texto": "14 h 40 min"}
    assert r["maior_ticket"] == {"identificacao": "N-031", "texto": "30 min"}


def test_percurso_do_dia() -> None:
    etapas = {e["rotulo"]: e for e in resumir_plantao(FICHAS, TICKETS, AGORA)["etapas"]}
    assert etapas["Totem"]["quantidade"] == 3 and etapas["Totem"]["detalhe"] == "1 em chamada"
    assert [etapas[n]["quantidade"] for n in ("Em triagem", "Fila médica", "Em chamada", "Concluídas")] == [1, 5, 1, 1]
    assert etapas["Concluídas"]["detalhe"] == "+ 1 encerrada(s)"
    assert etapas["Totem"]["rota"] == "/recepcao/fila"


def test_fila_por_especialidade_ordenada_e_relativa_a_maior() -> None:
    especialidades = resumir_plantao(FICHAS, TICKETS, AGORA)["especialidades"]
    assert [(e["nome"], e["quantidade"], e["largura"]) for e in especialidades] == [
        ("Cardiologia", 3, "100.0%"), ("Clínica Geral", 1, "33.3%"), ("Neurologia", 1, "33.3%"),
    ]


def test_chegadas_por_hora_ultimas_12_horas_com_a_atual_em_destaque() -> None:
    r = resumir_plantao(FICHAS, TICKETS, AGORA)
    chegadas = r["chegadas"]
    assert [c["hora"] for c in chegadas][0] == "03h" and chegadas[-1]["hora"] == "14h" and len(chegadas) == 12
    hora14 = chegadas[-1]
    assert hora14["atual"] and hora14["quantidade"] == 3 and hora14["valor"] == "3" and hora14["altura"] == "100.0%"
    assert next(c for c in chegadas if c["hora"] == "13h")["valor"] == ""  # só a hora atual leva número
    assert r["chegadas_hoje"] == 8  # a ficha de ontem não conta
    assert r["data_extenso"] == "Quarta, 11 de novembro"


def test_dia_vazio() -> None:
    r = resumir_plantao([], [], AGORA)
    assert r["na_espera"] == 0 and r["especialidades"] == [] and r["maior_ficha"]["texto"] == ""
    assert all(c["altura"] == "0%" and c["altura_minima"] == "0" for c in r["chegadas"])


class Resposta:
    def __init__(self, status_code: int, corpo: object):
        self.status_code = status_code
        self._corpo = corpo

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> object:
        return self._corpo


class AuthFalso:
    token = "t"
    encerrada = False

    def _encerrar_sessao_local(self, mensagem: str = "") -> None:
        self.encerrada = True


class EstadoFalso:
    _buscar = PlantaoState._buscar
    carregar = PlantaoState.carregar.fn

    def __init__(self) -> None:
        self.na_espera = 0
        self.carregado = False
        self.atualizado_em = ""
        self.mensagem = ""
        self.auth = AuthFalso()

    async def get_state(self, estado):
        return self.auth


def test_carregar_busca_fichas_e_tickets() -> None:
    estado = EstadoFalso()
    respostas = [Resposta(200, {"fichas": FICHAS, "agora": int(AGORA * 1000)}), Resposta(200, {"tickets": TICKETS})]
    with patch("ps_fila_prioritaria.api.requisitar", side_effect=respostas) as requisitar:
        asyncio.run(estado.carregar())
    assert [c.args[2] for c in requisitar.call_args_list] == ["/fichas", "/tickets"]
    assert estado.na_espera == 7 and estado.carregado and estado.atualizado_em == "14:30"


def test_falha_mantem_os_ultimos_dados() -> None:
    estado = EstadoFalso()
    estado.na_espera = 4
    with patch("ps_fila_prioritaria.api.requisitar", side_effect=httpx.ConnectError("x")):
        asyncio.run(estado.carregar())
    assert estado.na_espera == 4 and "últimos dados" in estado.mensagem


def test_sessao_expirada() -> None:
    estado = EstadoFalso()
    with patch("ps_fila_prioritaria.api.requisitar", return_value=Resposta(401, {"message": "x"})):
        asyncio.run(estado.carregar())
    assert estado.auth.encerrada and not estado.carregado

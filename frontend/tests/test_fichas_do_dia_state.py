"""Estado da aba "Fichas do dia" (add-fichas-do-dia): carga, filtro, busca e falhas."""

import asyncio
from unittest.mock import patch

import httpx

from ps_fila_prioritaria.estados.fichas_do_dia import FichasDoDiaState, filtrar_fichas

REQUISITAR = "ps_fila_prioritaria.api.requisitar"


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
    token = "token-teste"

    def __init__(self) -> None:
        self.encerrada = False

    def _encerrar_sessao_local(self, mensagem: str = "") -> None:
        self.encerrada = True


class EstadoFalso:
    carregar = FichasDoDiaState.carregar.fn

    def __init__(self) -> None:
        self.fichas = []
        self.filtro = "TODAS"
        self.busca = ""
        self.carregando = False
        self.mensagem = ""
        self.erro = False
        self.atualizado_em = ""
        self.auth = AuthFalso()

    async def get_state(self, estado):
        return self.auth


def _ficha(id_: int, status: str, nome: str, senha: str | None = None, prioridade: str | None = None) -> dict:
    return {"id": id_, "status": status, "chegada_em": 1794155580000, "senha": senha, "prioridade_atual": prioridade,
            "especialidade": "Neurologia" if senha else None, "paciente": {"id": id_, "nome": nome}}


CORPO = {
    "fichas": [
        _ficha(5, "AGUARDANDO", "José da Silva", "A-NEU-002", "AMARELA"),
        _ficha(4, "EM_TRIAGEM", "Maria Souza"),
        _ficha(3, "CHAMADO", "Ana Lima", "V-NEU-001", "VERMELHA"),
        _ficha(2, "ATENDIDO", "Josefa Prado", "Z-CLI-001", "AZUL"),
        _ficha(1, "DESISTENCIA", "Carlos Reis", "Z-CLI-002", "AZUL"),
    ],
    "agora": 1794155580000,
}


def _carregado() -> EstadoFalso:
    estado = EstadoFalso()
    with patch(REQUISITAR, return_value=Resposta(200, CORPO)) as requisitar:
        asyncio.run(estado.carregar())
    assert requisitar.call_args.args == ("GET", "XANO_TRIAGEM_API_URL", "/fichas")
    assert requisitar.call_args.kwargs["token"] == "token-teste"
    return estado


def test_carregar_prepara_as_linhas() -> None:
    estado = _carregado()
    primeira = estado.fichas[0]
    assert primeira == {
        "id": 5, "status": "AGUARDANDO", "situacao": "Aguardando", "chegada": "13:33", "nome": "José da Silva",
        "senha": "A-NEU-002", "prioridade": "AMARELA", "nome_prioridade": "Amarela", "especialidade": "Neurologia",
    }
    assert estado.fichas[1]["senha"] == "" and estado.fichas[1]["nome_prioridade"] == ""
    assert not estado.erro and not estado.carregando


def test_cada_filtro_e_finais_agrupadas() -> None:
    fichas = _carregado().fichas
    ids = lambda filtro: [f["id"] for f in filtrar_fichas(fichas, filtro, "")]
    assert ids("TODAS") == [5, 4, 3, 2, 1]
    assert ids("EM_TRIAGEM") == [4]
    assert ids("AGUARDANDO") == [5]
    assert ids("CHAMADO") == [3]
    assert ids("FINALIZADAS") == [2, 1]


def test_busca_sem_acento_e_maiusculas_por_nome_e_senha() -> None:
    fichas = _carregado().fichas
    assert [f["id"] for f in filtrar_fichas(fichas, "TODAS", "JOSE")] == [5, 2]
    assert [f["id"] for f in filtrar_fichas(fichas, "AGUARDANDO", "jose")] == [5]
    assert [f["id"] for f in filtrar_fichas(fichas, "TODAS", "a-neu-002")] == [5]


def test_filtro_sem_resultado_devolve_lista_vazia() -> None:
    assert filtrar_fichas(_carregado().fichas, "CHAMADO", "maria") == []


def test_erro_da_api_mantem_a_ultima_lista() -> None:
    estado = _carregado()
    with patch(REQUISITAR, return_value=Resposta(500, {"message": "falha"})):
        asyncio.run(estado.carregar())
    assert len(estado.fichas) == 5
    assert estado.erro and estado.mensagem


def test_sem_conexao_mantem_a_ultima_lista() -> None:
    estado = _carregado()
    with patch(REQUISITAR, side_effect=httpx.ConnectError("sem rede")):
        asyncio.run(estado.carregar())
    assert len(estado.fichas) == 5
    assert estado.mensagem == "Não foi possível conectar à lista de fichas."
    assert not estado.carregando


def test_sessao_expirada_encerra_a_sessao() -> None:
    estado = EstadoFalso()
    with patch(REQUISITAR, return_value=Resposta(401, {"message": "Invalid token."})):
        asyncio.run(estado.carregar())
    assert estado.auth.encerrada
    assert estado.fichas == []

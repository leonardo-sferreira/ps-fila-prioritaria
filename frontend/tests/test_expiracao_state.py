"""Estado da dispensa por prazo do Administrador (add-expiracao-24h): prévia, dispensa e falhas."""

import asyncio
from collections import deque
from unittest.mock import patch

import httpx

from ps_fila_prioritaria.estados.expiracao import ORDEM_MAIOR_TEMPO, ORDEM_MENOR_TEMPO, ExpiracaoState, recortar_pagina, total_paginas

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
    token = "token-admin"

    def __init__(self) -> None:
        self.encerrada = False

    def _encerrar_sessao_local(self, mensagem: str = "") -> None:
        self.encerrada = True


class EstadoFalso:
    _requisitar = ExpiracaoState._requisitar
    _aplicar_resposta = ExpiracaoState._aplicar_resposta
    carregar = ExpiracaoState.carregar.fn
    dispensar = ExpiracaoState.dispensar.fn

    def __init__(self) -> None:
        self.fichas = []
        self.tickets = []
        self.horas = 0
        self.carregando = False
        self.dispensando = False
        self.confirmacao_aberta = False
        self.mensagem = ""
        self.erro = False
        self.pagina = 1
        self.auth = AuthFalso()

    async def get_state(self, estado):
        return self.auth


PREVIA = {
    "horas_expiracao": 24,
    "aplicado": False,
    "fichas": [
        {"id": 7, "senha": None, "status": "EM_TRIAGEM", "chegada_em": 1794155580000},
        {"id": 9, "senha": "A-NEU-002", "status": "AGUARDANDO", "chegada_em": 1794155580000},
    ],
    "tickets": [{"id": 3, "tipo": "NORMAL", "numero": 31, "status": "CHAMADO", "emitido_em": 1794155580000}],
    "motivo": None,
}
VAZIA = {"horas_expiracao": 24, "aplicado": False, "fichas": [], "tickets": [], "motivo": None}


def _api(*respostas: Resposta):
    fila = deque(respostas)
    return patch(REQUISITAR, side_effect=lambda *args, **kwargs: fila.popleft())


def test_previa_prepara_fichas_e_tickets() -> None:
    estado = EstadoFalso()
    with _api(Resposta(200, PREVIA)) as requisitar:
        asyncio.run(estado.carregar())
    assert requisitar.call_args.args == ("GET", "XANO_TRIAGEM_API_URL", "/expiracao")
    assert requisitar.call_args.kwargs["token"] == "token-admin"
    assert estado.fichas == [
        {"id": 7, "identificacao": "Sem senha", "tipo": "Ficha", "situacao": "Em triagem", "horario": "08/11/2026 13:33", "instante": 1794155580.0},
        {"id": 9, "identificacao": "A-NEU-002", "tipo": "Ficha", "situacao": "Aguardando", "horario": "08/11/2026 13:33", "instante": 1794155580.0},
    ]
    assert estado.tickets == [
        {"id": 3, "identificacao": "N-031", "tipo": "Ticket", "situacao": "Chamado", "horario": "08/11/2026 13:33", "instante": 1794155580.0}
    ]
    assert estado.horas == 24 and not estado.erro and not estado.carregando


def test_previa_vazia() -> None:
    estado = EstadoFalso()
    with _api(Resposta(200, VAZIA)):
        asyncio.run(estado.carregar())
    assert estado.fichas == [] and estado.tickets == [] and not estado.erro


def test_dispensar_envia_post_e_recarrega_a_previa() -> None:
    estado = EstadoFalso()
    estado.confirmacao_aberta = True
    aplicado = {**PREVIA, "aplicado": True}
    with _api(Resposta(200, aplicado), Resposta(200, VAZIA)) as requisitar:
        asyncio.run(estado.dispensar())
    metodos = [chamada.args[0] for chamada in requisitar.call_args_list]
    assert metodos == ["POST", "GET"]
    assert estado.mensagem == "Dispensados: 2 ficha(s) e 1 ticket(s)."
    assert estado.fichas == [] and not estado.confirmacao_aberta and not estado.dispensando


def test_parametro_invalido_mostra_o_motivo_sem_recarregar() -> None:
    estado = EstadoFalso()
    corpo = {**VAZIA, "horas_expiracao": None, "motivo": "HORAS_EXPIRACAO não configurado como inteiro positivo; nada foi alterado."}
    with _api(Resposta(200, corpo)) as requisitar:
        asyncio.run(estado.dispensar())
    assert requisitar.call_count == 1
    assert estado.erro and "HORAS_EXPIRACAO" in estado.mensagem


def test_erro_da_api_mantem_a_previa() -> None:
    estado = EstadoFalso()
    with _api(Resposta(200, PREVIA)):
        asyncio.run(estado.carregar())
    with _api(Resposta(500, {"message": "falha"})):
        asyncio.run(estado.carregar())
    assert len(estado.fichas) == 2 and estado.erro and estado.mensagem


def test_sem_conexao() -> None:
    estado = EstadoFalso()
    with patch(REQUISITAR, side_effect=httpx.ConnectError("sem rede")):
        asyncio.run(estado.carregar())
    assert estado.mensagem == "Não foi possível conectar à API." and not estado.carregando


def test_sessao_expirada() -> None:
    estado = EstadoFalso()
    with _api(Resposta(401, {"message": "Invalid token."})):
        asyncio.run(estado.carregar())
    assert estado.auth.encerrada


def test_perfil_recusado_nao_altera_nada() -> None:
    estado = EstadoFalso()
    with _api(Resposta(403, {"message": "Acesso negado."})):
        asyncio.run(estado.dispensar())
    assert estado.erro and estado.fichas == []


def _itens(quantidade: int) -> list[dict]:
    """Itens com instantes crescentes: o de índice 0 é o mais antigo (maior tempo parado)."""
    return [{"identificacao": f"P-{i:03d}", "instante": 1000 + i} for i in range(quantidade)]


def _ids(itens: list[dict]) -> list[str]:
    return [item["identificacao"] for item in itens]


def test_paginacao_limites_de_10() -> None:
    assert total_paginas(0, 10) == 1
    assert total_paginas(10, 10) == 1
    assert total_paginas(11, 10) == 2
    assert _ids(recortar_pagina(_itens(10), 1, 10, ORDEM_MAIOR_TEMPO)) == _ids(_itens(10))
    assert _ids(recortar_pagina(_itens(11), 2, 10, ORDEM_MAIOR_TEMPO)) == ["P-010"]


def test_paginacao_troca_de_tamanho() -> None:
    assert len(recortar_pagina(_itens(25), 1, 25, ORDEM_MAIOR_TEMPO)) == 25
    assert total_paginas(26, 25) == 2
    assert len(recortar_pagina(_itens(26), 1, 50, ORDEM_MAIOR_TEMPO)) == 26


def test_ordem_maior_e_menor_tempo() -> None:
    itens = list(reversed(_itens(3)))
    assert _ids(recortar_pagina(itens, 1, 10, ORDEM_MAIOR_TEMPO)) == ["P-000", "P-001", "P-002"]
    assert _ids(recortar_pagina(itens, 1, 10, ORDEM_MENOR_TEMPO)) == ["P-002", "P-001", "P-000"]


def test_pagina_fora_do_intervalo_fica_no_limite() -> None:
    assert _ids(recortar_pagina(_itens(11), 9, 10, ORDEM_MAIOR_TEMPO)) == ["P-010"]
    assert len(recortar_pagina(_itens(11), 0, 10, ORDEM_MAIOR_TEMPO)) == 10


def test_recarregar_volta_para_a_primeira_pagina() -> None:
    estado = EstadoFalso()
    estado.pagina = 3
    with _api(Resposta(200, PREVIA)):
        asyncio.run(estado.carregar())
    assert estado.pagina == 1

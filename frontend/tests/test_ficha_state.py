"""Regressões do estado Reflex da ficha de atendimento."""

import asyncio
from collections import deque
import unittest
from unittest.mock import patch

import httpx

from ps_fila_prioritaria.ps_fila_prioritaria import FichaState, sintomas_disponiveis


class Resposta:
    def __init__(self, status_code: int, corpo: object):
        self.status_code = status_code
        self._corpo = corpo

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> object:
        return self._corpo


FICHA = {
    "ficha": {"id": 10, "paciente_id": 7, "status": "EM_TRIAGEM", "observacao": "Queixa inicial"},
    "paciente": {"id": 7, "nome": "Paciente da Ficha", "cpf": "52998224725"},
    "sintomas": [{"id": 1, "nome": "Febre", "grupo": "GERAL", "pontuacao": 1}],
}
CATALOGO = [
    {"id": 2, "nome": "Mal-estar", "descricao": None, "grupo": "GERAL", "pontuacao": 1},
    {"id": 1, "nome": "Febre", "descricao": None, "grupo": "GERAL", "pontuacao": 1},
]


class EstadoFichaFalso:
    _url = FichaState._url
    _limpar_feedback = FichaState._limpar_feedback
    _carregar_resposta_ficha = FichaState._carregar_resposta_ficha
    carregar = FichaState.carregar.fn
    set_observacao = FichaState.set_observacao.fn
    alternar_sintoma = FichaState.alternar_sintoma.fn
    salvar = FichaState.salvar.fn

    def __init__(self) -> None:
        self.ficha_id = 0
        self.paciente = {}
        self.catalogo_sintomas = []
        self.sintoma_ids_selecionados = []
        self.observacao = ""
        self.sintomas_alterados = False
        self.observacao_alterada = False
        self.carregando = False
        self.salvando = False
        self.mensagem = ""
        self.erro = False

    def _url(self, caminho: str) -> str:
        return f"https://xano.test{caminho}"


async def _executar_salvamento(estado: EstadoFichaFalso) -> None:
    async for _ in estado.salvar():
        pass


def test_carrega_catalogo_e_ficha_para_edicao() -> None:
    estado = EstadoFichaFalso()
    respostas = deque([Resposta(200, FICHA), Resposta(200, CATALOGO)])
    with patch("ps_fila_prioritaria.ps_fila_prioritaria.httpx.get", side_effect=lambda *args, **kwargs: respostas.popleft()):
        estado.carregar("10")

    assert estado.ficha_id == 10
    assert estado.paciente["id"] == 7
    assert estado.observacao == "Queixa inicial"
    assert estado.sintoma_ids_selecionados == [1]
    assert [sintoma["nome"] for sintoma in estado.catalogo_sintomas] == ["Febre", "Mal-estar"]


def test_selecao_nao_duplica_e_desmarcacao_remove() -> None:
    estado = EstadoFichaFalso()
    estado.alternar_sintoma(2, True)
    estado.alternar_sintoma(2, True)
    estado.alternar_sintoma(1, True)
    estado.alternar_sintoma(2, False)
    assert estado.sintoma_ids_selecionados == [1]
    assert estado.sintomas_alterados


def test_edicao_de_observacao_marca_intencao_de_patch() -> None:
    estado = EstadoFichaFalso()
    estado.set_observacao("Nova queixa")
    assert estado.observacao == "Nova queixa"
    assert estado.observacao_alterada


def test_disponiveis_excluem_selecionados_e_respeitam_busca() -> None:
    assert [sintoma["id"] for sintoma in sintomas_disponiveis(CATALOGO, [1], "")] == [2]
    assert [sintoma["id"] for sintoma in sintomas_disponiveis(CATALOGO, [1], "mal")] == [2]
    assert sintomas_disponiveis(CATALOGO, [1], "feb") == []


def test_adicionar_e_remover_atualizam_opcoes_sem_persistir() -> None:
    estado = EstadoFichaFalso()
    estado.catalogo_sintomas = CATALOGO
    estado.alternar_sintoma(2, True)
    estado.alternar_sintoma(2, True)
    assert estado.sintoma_ids_selecionados == [2]
    assert [sintoma["id"] for sintoma in sintomas_disponiveis(CATALOGO, estado.sintoma_ids_selecionados, "")] == [1]

    estado.alternar_sintoma(2, False)
    assert estado.sintoma_ids_selecionados == []
    assert [sintoma["id"] for sintoma in sintomas_disponiveis(CATALOGO, estado.sintoma_ids_selecionados, "")] == [1, 2]


def test_salvar_recusa_rn04_antes_da_requisicao() -> None:
    estado = EstadoFichaFalso()
    estado.ficha_id = 10
    estado.observacao = "   "
    with patch("ps_fila_prioritaria.ps_fila_prioritaria.httpx.patch") as patch_http:
        asyncio.run(_executar_salvamento(estado))
    patch_http.assert_not_called()
    assert estado.erro


def test_salvar_entrega_loading_antes_do_patch() -> None:
    async def executar() -> None:
        estado = EstadoFichaFalso()
        estado.ficha_id = 10
        estado.sintoma_ids_selecionados = [1]
        estado.sintomas_alterados = True
        salvamento = estado.salvar()
        with patch(
            "ps_fila_prioritaria.ps_fila_prioritaria.httpx.patch",
            return_value=Resposta(400, {"code": "FICHA_SEM_SINTOMA_OU_OBSERVACAO"}),
        ) as patch_http:
            await anext(salvamento)
            assert estado.salvando
            patch_http.assert_not_called()
            try:
                await anext(salvamento)
            except StopAsyncIteration:
                pass
        assert not estado.salvando

    asyncio.run(executar())


def test_salvar_ignora_segunda_invocacao_enquanto_esta_em_andamento() -> None:
    async def executar() -> None:
        estado = EstadoFichaFalso()
        estado.ficha_id = 10
        estado.sintoma_ids_selecionados = [1]
        estado.sintomas_alterados = True
        primeiro_salvamento = estado.salvar()
        respostas_get = _respostas_recarga([CATALOGO[1]], "")
        with patch(
            "ps_fila_prioritaria.ps_fila_prioritaria.httpx.patch",
            return_value=Resposta(200, {"id": 10}),
        ) as patch_http, patch(
            "ps_fila_prioritaria.ps_fila_prioritaria.httpx.get",
            side_effect=lambda *args, **kwargs: respostas_get.popleft(),
        ):
            await anext(primeiro_salvamento)
            assert estado.salvando
            async for _ in estado.salvar():
                pass
            patch_http.assert_not_called()
            try:
                await anext(primeiro_salvamento)
            except StopAsyncIteration:
                pass
        patch_http.assert_called_once()
        assert not estado.salvando

    asyncio.run(executar())


def _respostas_recarga(sintomas: list[dict[str, object]], observacao: str) -> deque[Resposta]:
    return deque(
        [
            Resposta(200, {**FICHA, "ficha": {**FICHA["ficha"], "observacao": observacao}, "sintomas": sintomas}),
            Resposta(200, CATALOGO),
        ]
    )


def test_salvar_somente_sintomas_envia_patch_parcial_e_recarrega() -> None:
    estado = EstadoFichaFalso()
    estado.ficha_id = 10
    estado.sintoma_ids_selecionados = [1, 2]
    estado.observacao = "Queixa persistida"
    estado.sintomas_alterados = True
    respostas_get = _respostas_recarga(CATALOGO, "Queixa persistida")
    with patch("ps_fila_prioritaria.ps_fila_prioritaria.httpx.patch", return_value=Resposta(200, {"id": 10})) as patch_http, patch(
        "ps_fila_prioritaria.ps_fila_prioritaria.httpx.get", side_effect=lambda *args, **kwargs: respostas_get.popleft()
    ), patch("ps_fila_prioritaria.ps_fila_prioritaria.httpx.post") as post_http:
        asyncio.run(_executar_salvamento(estado))

    assert patch_http.call_args.args[0] == "https://xano.test/fichas/10"
    assert patch_http.call_args.kwargs["json"] == {"sintoma_ids": [1, 2]}
    post_http.assert_not_called()
    assert estado.sintoma_ids_selecionados == [1, 2]
    assert estado.observacao == "Queixa persistida"
    assert estado.mensagem == "Ficha salva com sucesso."
    assert not estado.erro
    assert not estado.salvando
    assert not estado.sintomas_alterados


def test_salvar_somente_observacao_envia_patch_parcial() -> None:
    estado = EstadoFichaFalso()
    estado.ficha_id = 10
    estado.sintoma_ids_selecionados = [1]
    estado.observacao = "Dor iniciada pela manhã"
    estado.observacao_alterada = True
    respostas_get = _respostas_recarga([CATALOGO[1]], "Dor iniciada pela manhã")
    with patch("ps_fila_prioritaria.ps_fila_prioritaria.httpx.patch", return_value=Resposta(200, {"id": 10})) as patch_http, patch(
        "ps_fila_prioritaria.ps_fila_prioritaria.httpx.get", side_effect=lambda *args, **kwargs: respostas_get.popleft()
    ):
        asyncio.run(_executar_salvamento(estado))

    assert patch_http.call_args.kwargs["json"] == {"observacao": "Dor iniciada pela manhã"}
    assert estado.observacao == "Dor iniciada pela manhã"
    assert not estado.observacao_alterada


def test_salvar_sintomas_e_observacao_envia_ambos_e_preserva_colecao_final() -> None:
    estado = EstadoFichaFalso()
    estado.ficha_id = 10
    estado.sintoma_ids_selecionados = []
    estado.observacao = "Queixa geral"
    estado.sintomas_alterados = True
    estado.observacao_alterada = True
    respostas_get = _respostas_recarga([], "Queixa geral")
    with patch("ps_fila_prioritaria.ps_fila_prioritaria.httpx.patch", return_value=Resposta(200, {"id": 10})) as patch_http, patch(
        "ps_fila_prioritaria.ps_fila_prioritaria.httpx.get", side_effect=lambda *args, **kwargs: respostas_get.popleft()
    ):
        asyncio.run(_executar_salvamento(estado))

    assert patch_http.call_args.kwargs["json"] == {"sintoma_ids": [], "observacao": "Queixa geral"}
    assert estado.sintoma_ids_selecionados == []
    assert estado.observacao == "Queixa geral"


def test_salvar_erro_exibe_feedback_e_libera_loading() -> None:
    estado = EstadoFichaFalso()
    estado.ficha_id = 10
    estado.sintoma_ids_selecionados = [1]
    estado.sintomas_alterados = True
    with patch(
        "ps_fila_prioritaria.ps_fila_prioritaria.httpx.patch",
        return_value=Resposta(400, {"code": "FICHA_SEM_SINTOMA_OU_OBSERVACAO"}),
    ), patch("ps_fila_prioritaria.ps_fila_prioritaria.httpx.get") as get_http:
        asyncio.run(_executar_salvamento(estado))

    get_http.assert_not_called()
    assert estado.erro
    assert estado.mensagem == "Informe ao menos um sintoma ou uma observação."
    assert not estado.salvando


def test_salvar_erro_de_conexao_exibe_feedback_e_libera_loading() -> None:
    estado = EstadoFichaFalso()
    estado.ficha_id = 10
    estado.sintoma_ids_selecionados = [1]
    estado.sintomas_alterados = True
    with patch(
        "ps_fila_prioritaria.ps_fila_prioritaria.httpx.patch",
        side_effect=httpx.RequestError("falha de rede"),
    ):
        asyncio.run(_executar_salvamento(estado))

    assert estado.erro
    assert estado.mensagem == "Não foi possível conectar à API de Fichas."
    assert not estado.salvando


class TestFichaState(unittest.TestCase):
    def test_carregamento(self) -> None:
        test_carrega_catalogo_e_ficha_para_edicao()

    def test_selecao(self) -> None:
        test_selecao_nao_duplica_e_desmarcacao_remove()

    def test_edicao_de_observacao(self) -> None:
        test_edicao_de_observacao_marca_intencao_de_patch()

    def test_disponiveis(self) -> None:
        test_disponiveis_excluem_selecionados_e_respeitam_busca()

    def test_adicionar_e_remover(self) -> None:
        test_adicionar_e_remover_atualizam_opcoes_sem_persistir()

    def test_rn04(self) -> None:
        test_salvar_recusa_rn04_antes_da_requisicao()

    def test_salvar_entrega_loading(self) -> None:
        test_salvar_entrega_loading_antes_do_patch()

    def test_salvar_ignora_segunda_invocacao(self) -> None:
        test_salvar_ignora_segunda_invocacao_enquanto_esta_em_andamento()

    def test_salvar_somente_sintomas(self) -> None:
        test_salvar_somente_sintomas_envia_patch_parcial_e_recarrega()

    def test_salvar_somente_observacao(self) -> None:
        test_salvar_somente_observacao_envia_patch_parcial()

    def test_salvar_ambos(self) -> None:
        test_salvar_sintomas_e_observacao_envia_ambos_e_preserva_colecao_final()

    def test_salvar_erro(self) -> None:
        test_salvar_erro_exibe_feedback_e_libera_loading()

    def test_salvar_erro_de_conexao(self) -> None:
        test_salvar_erro_de_conexao_exibe_feedback_e_libera_loading()

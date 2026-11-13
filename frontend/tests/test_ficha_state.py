"""Regressões do estado Reflex da ficha de atendimento (sintomas, observação, sinais vitais e classificação)."""

import asyncio
from collections import deque
import unittest
from unittest.mock import patch

import httpx

from ps_fila_prioritaria.ps_fila_prioritaria import ComprovanteState, FichaState, comprovante_senha, sintomas_disponiveis

REQUISITAR = "ps_fila_prioritaria.ps_fila_prioritaria.api.requisitar"


class Resposta:
    def __init__(self, status_code: int, corpo: object):
        self.status_code = status_code
        self._corpo = corpo

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> object:
        return self._corpo


CLASSIFICACAO = {
    "pontos_sinais": {"PA_SISTOLICA": 0, "FC": 0, "FR": 0, "TEMPERATURA": 0, "SPO2": 0, "GLICEMIA": None},
    "escore_sintomas": 1,
    "escore_sinais": 0,
    "escore_total": 1,
    "item_critico": False,
    "tabela_adulta": True,
    "pendencias": [],
    "condicao_prioritaria": "IDOSO",
    "prioridade_calculada": "AZUL",
    "prioridade_atual": "AZUL",
    "justificativa_ajuste": None,
}
FICHA = {
    "ficha": {"id": 10, "paciente_id": 7, "status": "EM_TRIAGEM", "observacao": "Queixa inicial", "gestante": False,
              "pa_sistolica": 120, "fc": 80, "fr": 16, "temperatura": 36.5, "spo2": 98, "glicemia": None,
              "glicemia_sinais_gravidade": False},
    "paciente": {"id": 7, "nome": "Paciente da Ficha", "cpf": "52998224725", "idade": 68},
    "sintomas": [{"id": 1, "nome": "Febre", "grupo": "GERAL", "pontuacao": 1}],
    "sintomas_livres": [],
    "classificacao": CLASSIFICACAO,
}
CATALOGO = [
    {"id": 2, "nome": "Mal-estar", "descricao": None, "grupo": "GERAL", "pontuacao": 1},
    {"id": 1, "nome": "Febre", "descricao": None, "grupo": "GERAL", "pontuacao": 1},
]


class AuthFalso:
    token = "token-teste"

    def __init__(self) -> None:
        self.encerrada = False

    def _encerrar_sessao_local(self, mensagem: str = "") -> None:
        self.encerrada = True


class EstadoFichaFalso:
    _limpar_feedback = FichaState._limpar_feedback
    _requisitar = FichaState._requisitar
    _carregar_resposta_ficha = FichaState._carregar_resposta_ficha
    _recarregar = FichaState._recarregar
    _sinais_para_envio = FichaState._sinais_para_envio
    _alteracoes_pendentes = FichaState._alteracoes_pendentes
    _registrar_senha = FichaState._registrar_senha
    _dados_alterados = FichaState._dados_alterados
    _enviar_alteracoes = FichaState._enviar_alteracoes
    _ajustar_com_alteracoes = FichaState._ajustar_com_alteracoes
    carregar = FichaState.carregar.fn
    set_observacao = FichaState.set_observacao.fn
    alternar_sintoma = FichaState.alternar_sintoma.fn
    set_sinal = FichaState.set_sinal.fn
    set_gestante = FichaState.set_gestante.fn
    adicionar_sintoma_livre = FichaState.adicionar_sintoma_livre.fn
    remover_sintoma_livre = FichaState.remover_sintoma_livre.fn
    salvar = FichaState.salvar.fn
    abrir_ajuste = FichaState.abrir_ajuste.fn
    confirmar_ajuste = FichaState.confirmar_ajuste.fn
    confirmar_triagem = FichaState.confirmar_triagem.fn
    reimprimir = FichaState.reimprimir.fn
    prioridade_calculada = property(lambda self: str(self.classificacao.get("prioridade_calculada") or ""))

    def __init__(self) -> None:
        self.ficha_id = 0
        self.ficha = {}
        self.paciente = {}
        self.catalogo_sintomas = []
        self.sintoma_ids_selecionados = []
        self.observacao = ""
        self.sintomas_livres = []
        self.sinais = {campo: "" for campo in ["pa_sistolica", "fc", "fr", "temperatura", "spo2", "glicemia"]}
        self.glicemia_gravidade = False
        self.gestante = False
        self.classificacao = {}
        self.sintomas_alterados = False
        self.observacao_alterada = False
        self.livres_alterados = False
        self.sinais_alterados = False
        self.carregando = False
        self.salvando = False
        self.mensagem = ""
        self.erro = False
        self.ajuste_aberto = False
        self.ajuste_prioridade = ""
        self.ajuste_justificativa = ""
        self.ajuste_erro = ""
        self.ajustando = False
        self.destino_previsto = {}
        self.confirmando = False
        self.aviso_senha = ""
        self.ultimo_erro = ""
        self.auth = AuthFalso()

    async def get_state(self, estado):
        return self.auth


def _api(*respostas: Resposta):
    """Simula api.requisitar devolvendo as respostas em ordem e guardando as chamadas."""
    fila = deque(respostas)
    return patch(REQUISITAR, side_effect=lambda *args, **kwargs: fila.popleft())


def _recarga(**ficha) -> list[Resposta]:
    return [Resposta(200, {**FICHA, "ficha": {**FICHA["ficha"], **ficha}}), Resposta(200, CATALOGO)]


async def _executar_salvamento(estado: EstadoFichaFalso) -> None:
    async for _ in estado.salvar():
        pass


def _estado_carregado() -> EstadoFichaFalso:
    estado = EstadoFichaFalso()
    with _api(*_recarga()):
        asyncio.run(estado.carregar("10"))
    return estado


class TestCarregamento(unittest.TestCase):
    def test_carrega_ficha_catalogo_sinais_e_classificacao_com_token(self) -> None:
        estado = EstadoFichaFalso()
        with _api(*_recarga()) as requisitar:
            asyncio.run(estado.carregar("10"))
        self.assertEqual([c.args[:3] for c in requisitar.call_args_list],
                         [("GET", "XANO_TRIAGEM_API_URL", "/fichas/10"), ("GET", "XANO_TRIAGEM_API_URL", "/sintomas")])
        self.assertTrue(all(c.kwargs["token"] == "token-teste" for c in requisitar.call_args_list))
        self.assertEqual(estado.ficha_id, 10)
        self.assertEqual(estado.observacao, "Queixa inicial")
        self.assertEqual(estado.sintoma_ids_selecionados, [1])
        self.assertEqual([s["nome"] for s in estado.catalogo_sintomas], ["Febre", "Mal-estar"])
        self.assertEqual(estado.sinais["temperatura"], "36,5")
        self.assertEqual(estado.sinais["glicemia"], "")
        self.assertEqual(estado.classificacao["prioridade_calculada"], "AZUL")
        self.assertFalse(estado.carregando)

    def test_sessao_expirada_encerra_a_sessao(self) -> None:
        estado = EstadoFichaFalso()
        with _api(Resposta(401, {"message": "Sessão inválida."})):
            asyncio.run(estado.carregar("10"))
        self.assertTrue(estado.auth.encerrada)
        self.assertTrue(estado.erro)

    def test_erro_de_conexao(self) -> None:
        estado = EstadoFichaFalso()
        with patch(REQUISITAR, side_effect=httpx.RequestError("falha de rede")):
            asyncio.run(estado.carregar("10"))
        self.assertEqual(estado.mensagem, "Não foi possível conectar à API de Fichas.")


class TestSintomas(unittest.TestCase):
    def test_selecao_nao_duplica_e_desmarcacao_remove(self) -> None:
        estado = EstadoFichaFalso()
        for sintoma_id, marcado in ((2, True), (2, True), (1, True), (2, False)):
            estado.alternar_sintoma(sintoma_id, marcado)
        self.assertEqual(estado.sintoma_ids_selecionados, [1])
        self.assertTrue(estado.sintomas_alterados)

    def test_disponiveis_excluem_selecionados_e_respeitam_busca(self) -> None:
        self.assertEqual([s["id"] for s in sintomas_disponiveis(CATALOGO, [1], "")], [2])
        self.assertEqual([s["id"] for s in sintomas_disponiveis(CATALOGO, [1], "mal")], [2])
        self.assertEqual(sintomas_disponiveis(CATALOGO, [1], "feb"), [])

    def test_adiciona_e_remove_sintoma_digitado(self) -> None:
        estado = EstadoFichaFalso()
        estado.catalogo_sintomas = CATALOGO
        estado.adicionar_sintoma_livre("  Dor   no joelho ", 2)
        self.assertEqual(estado.sintomas_livres, [{"descricao": "Dor no joelho", "pontuacao": 2}])
        self.assertTrue(estado.livres_alterados)
        estado.remover_sintoma_livre("Dor no joelho")
        self.assertEqual(estado.sintomas_livres, [])

    def test_sintoma_digitado_invalido_e_recusado_na_tela(self) -> None:
        estado = EstadoFichaFalso()
        estado.catalogo_sintomas = CATALOGO
        for descricao, pontuacao in (("ab", 2), ("Dor nas costas", 0), ("Dor nas costas", 4), ("FÉBRE", 1), ("febre", 2)):
            estado.adicionar_sintoma_livre(descricao, pontuacao)
            self.assertTrue(estado.erro, descricao)
        estado.adicionar_sintoma_livre("Dor no joelho", 2)
        estado.adicionar_sintoma_livre("dor no JOELHO", 3)
        self.assertEqual(len(estado.sintomas_livres), 1)
        self.assertTrue(estado.erro)

    def test_limite_de_dez_sintomas_digitados(self) -> None:
        estado = EstadoFichaFalso()
        for indice in range(11):
            estado.adicionar_sintoma_livre(f"Sintoma digitado {indice}", 1)
        self.assertEqual(len(estado.sintomas_livres), 10)
        self.assertTrue(estado.erro)


class TestSalvar(unittest.TestCase):
    def test_rn04_recusada_antes_da_requisicao(self) -> None:
        estado = EstadoFichaFalso()
        estado.ficha_id = 10
        estado.observacao = "   "
        with patch(REQUISITAR) as requisitar:
            asyncio.run(_executar_salvamento(estado))
        requisitar.assert_not_called()
        self.assertTrue(estado.erro)

    def test_sintoma_digitado_atende_a_rn04(self) -> None:
        estado = EstadoFichaFalso()
        estado.ficha_id = 10
        estado.adicionar_sintoma_livre("Dor no joelho", 2)
        with _api(Resposta(200, {}), *_recarga()) as requisitar:
            asyncio.run(_executar_salvamento(estado))
        self.assertEqual(requisitar.call_args_list[0].kwargs["json"], {"sintomas_livres": [{"descricao": "Dor no joelho", "pontuacao": 2}]})

    def test_salvar_entrega_loading_antes_do_patch(self) -> None:
        async def executar() -> None:
            estado = EstadoFichaFalso()
            estado.ficha_id = 10
            estado.alternar_sintoma(1, True)
            salvamento = estado.salvar()
            with _api(Resposta(400, {"code": "FICHA_SEM_SINTOMA_OU_OBSERVACAO"})) as requisitar:
                await anext(salvamento)
                self.assertTrue(estado.salvando)
                requisitar.assert_not_called()
                with self.assertRaises(StopAsyncIteration):
                    await anext(salvamento)
            self.assertFalse(estado.salvando)

        asyncio.run(executar())

    def test_segunda_invocacao_e_ignorada(self) -> None:
        async def executar() -> None:
            estado = EstadoFichaFalso()
            estado.ficha_id = 10
            estado.alternar_sintoma(1, True)
            primeiro = estado.salvar()
            with _api(Resposta(200, {}), *_recarga()) as requisitar:
                await anext(primeiro)
                async for _ in estado.salvar():
                    pass
                requisitar.assert_not_called()
                with self.assertRaises(StopAsyncIteration):
                    await anext(primeiro)
            self.assertEqual(requisitar.call_args_list[0].args[0], "PATCH")
            self.assertFalse(estado.salvando)

        asyncio.run(executar())

    def test_somente_sintomas_envia_patch_parcial_e_recarrega(self) -> None:
        estado = EstadoFichaFalso()
        estado.ficha_id = 10
        estado.alternar_sintoma(1, True)
        estado.alternar_sintoma(2, True)
        with _api(Resposta(200, {}), *_recarga()) as requisitar:
            asyncio.run(_executar_salvamento(estado))
        patch_chamada = requisitar.call_args_list[0]
        self.assertEqual(patch_chamada.args[:3], ("PATCH", "XANO_TRIAGEM_API_URL", "/fichas/10"))
        self.assertEqual(patch_chamada.kwargs["json"], {"sintoma_ids": [1, 2]})
        self.assertEqual(estado.mensagem, "Ficha salva. A prioridade foi recalculada.")
        self.assertFalse(estado.sintomas_alterados)

    def test_sintomas_e_observacao_vazia_preservam_colecao_final(self) -> None:
        estado = EstadoFichaFalso()
        estado.ficha_id = 10
        estado.sintomas_alterados = True
        estado.set_observacao("Queixa geral")
        with _api(Resposta(200, {}), *_recarga()) as requisitar:
            asyncio.run(_executar_salvamento(estado))
        self.assertEqual(requisitar.call_args_list[0].kwargs["json"], {"sintoma_ids": [], "observacao": "Queixa geral"})

    def test_sinais_vitais_enviados_como_conjunto_final(self) -> None:
        estado = _estado_carregado()
        estado.set_sinal("temperatura", "38,6")
        estado.set_sinal("fc", "")
        estado.set_gestante(True)
        with _api(Resposta(200, {}), *_recarga()) as requisitar:
            asyncio.run(_executar_salvamento(estado))
        self.assertEqual(requisitar.call_args_list[0].kwargs["json"], {"sinais_vitais": {
            "glicemia_sinais_gravidade": False, "gestante": True, "pa_sistolica": 120, "fc": None, "fr": 16,
            "temperatura": 38.6, "spo2": 98, "glicemia": None}})

    def test_sinal_vital_nao_numerico_e_recusado_na_tela(self) -> None:
        estado = _estado_carregado()
        estado.set_sinal("spo2", "noventa")
        with patch(REQUISITAR) as requisitar:
            asyncio.run(_executar_salvamento(estado))
        requisitar.assert_not_called()
        self.assertEqual(estado.mensagem, "Valor inválido em SpO2.")

    def test_pendencias_da_classificacao_sao_lidas(self) -> None:
        estado = EstadoFichaFalso()
        bloqueada = {**CLASSIFICACAO, "escore_total": None, "prioridade_calculada": None, "prioridade_atual": None,
                     "pendencias": ["SPO2_NAO_INFORMADO"]}
        with _api(Resposta(200, {**FICHA, "classificacao": bloqueada}), Resposta(200, CATALOGO)):
            asyncio.run(estado.carregar("10"))
        self.assertEqual(estado.classificacao["pendencias"], ["SPO2_NAO_INFORMADO"])
        self.assertIsNone(estado.classificacao["prioridade_calculada"])

    def test_erro_do_backend_libera_loading(self) -> None:
        estado = EstadoFichaFalso()
        estado.ficha_id = 10
        estado.alternar_sintoma(1, True)
        with _api(Resposta(400, {"code": "FICHA_SEM_SINTOMA_OU_OBSERVACAO"})):
            asyncio.run(_executar_salvamento(estado))
        self.assertTrue(estado.erro)
        self.assertEqual(estado.mensagem, "Informe ao menos um sintoma ou uma observação.")
        self.assertFalse(estado.salvando)


class TestAjustePrioridade(unittest.TestCase):
    def test_ajuste_envia_cor_e_justificativa_e_recarrega(self) -> None:
        estado = _estado_carregado()
        estado.abrir_ajuste()
        estado.ajuste_prioridade = "AMARELA"
        estado.ajuste_justificativa = "  Dor intensa relatada  "
        with _api(Resposta(200, {}), *_recarga()) as requisitar:
            asyncio.run(estado.confirmar_ajuste())
        chamada = requisitar.call_args_list[0]
        self.assertEqual(chamada.args[:3], ("POST", "XANO_TRIAGEM_API_URL", "/fichas/10/prioridade"))
        self.assertEqual(chamada.kwargs["json"], {"prioridade": "AMARELA", "justificativa": "Dor intensa relatada"})
        self.assertFalse(estado.ajuste_aberto)
        self.assertEqual(estado.mensagem, "Prioridade ajustada. A justificativa ficou registrada na auditoria.")

    def test_justificativa_vazia_e_bloqueada_na_tela(self) -> None:
        estado = _estado_carregado()
        estado.abrir_ajuste()
        estado.ajuste_prioridade = "AMARELA"
        estado.ajuste_justificativa = "   "
        with patch(REQUISITAR) as requisitar:
            asyncio.run(estado.confirmar_ajuste())
        requisitar.assert_not_called()
        self.assertEqual(estado.ajuste_erro, "A justificativa é obrigatória.")

    def test_cor_igual_a_calculada_e_bloqueada(self) -> None:
        estado = _estado_carregado()
        estado.abrir_ajuste()
        estado.ajuste_prioridade = "AZUL"
        estado.ajuste_justificativa = "Sem motivo"
        with patch(REQUISITAR) as requisitar:
            asyncio.run(estado.confirmar_ajuste())
        requisitar.assert_not_called()
        self.assertTrue(estado.ajuste_erro)

    def test_alteracao_nao_salva_bloqueia_o_ajuste(self) -> None:
        estado = _estado_carregado()
        estado.set_sinal("fc", "120")
        estado.abrir_ajuste()
        estado.ajuste_prioridade = "AMARELA"
        estado.ajuste_justificativa = "Dor intensa"
        with patch(REQUISITAR) as requisitar:
            asyncio.run(estado.confirmar_ajuste())
        requisitar.assert_not_called()
        self.assertIn("Salve a ficha", estado.ajuste_erro)

    def test_erro_do_backend_fica_no_dialogo(self) -> None:
        estado = _estado_carregado()
        estado.abrir_ajuste()
        estado.ajuste_prioridade = "AMARELA"
        estado.ajuste_justificativa = "Dor intensa"
        with _api(Resposta(400, {"message": "FICHA_FORA_DA_TRIAGEM"})):
            asyncio.run(estado.confirmar_ajuste())
        self.assertEqual(estado.ajuste_erro, "Esta ficha já foi chamada ou encerrada e não pode mais ser alterada.")
        self.assertTrue(estado.ajuste_aberto)


FICHA_DESTINO = {**FICHA, "destino_previsto": {"especialidade": {"id": 1, "nome": "Cardiologia", "sigla": "CAR"}, "motivo": "SINTOMAS"}}


class TestConfirmacaoTriagem(unittest.TestCase):
    def _estado(self, ficha=FICHA_DESTINO) -> EstadoFichaFalso:
        estado = EstadoFichaFalso()
        with _api(Resposta(200, ficha), Resposta(200, CATALOGO)):
            asyncio.run(estado.carregar("10"))
        return estado

    def test_le_o_destino_previsto(self) -> None:
        estado = self._estado()
        self.assertEqual(estado.destino_previsto["especialidade"]["sigla"], "CAR")

    def test_confirmacao_envia_post_e_abre_o_comprovante(self) -> None:
        estado = self._estado()
        with _api(Resposta(200, {"id": 10, "senha": "B-CAR-001"})) as requisitar:
            redirecionamento = asyncio.run(estado.confirmar_triagem())
        self.assertEqual(requisitar.call_args.args[:3], ("POST", "XANO_TRIAGEM_API_URL", "/fichas/10/confirmar-triagem"))
        self.assertIn("/recepcao/comprovante/10", str(redirecionamento))
        self.assertFalse(estado.confirmando)

    def test_sem_cor_nao_confirma(self) -> None:
        estado = self._estado({**FICHA_DESTINO, "classificacao": {**CLASSIFICACAO, "prioridade_atual": None, "prioridade_calculada": None}})
        with patch(REQUISITAR) as requisitar:
            self.assertIsNone(asyncio.run(estado.confirmar_triagem()))
        requisitar.assert_not_called()
        self.assertIn("Defina a cor", estado.mensagem)

    def test_alteracao_nao_salva_nao_confirma(self) -> None:
        estado = self._estado()
        estado.set_sinal("fc", "130")
        with patch(REQUISITAR) as requisitar:
            asyncio.run(estado.confirmar_triagem())
        requisitar.assert_not_called()
        self.assertEqual(estado.mensagem, "Salve a ficha antes de confirmar.")

    def test_recusa_do_backend_fica_na_ficha(self) -> None:
        estado = self._estado()
        with _api(Resposta(400, {"message": "FICHA_FORA_DA_TRIAGEM"})):
            self.assertIsNone(asyncio.run(estado.confirmar_triagem()))
        self.assertTrue(estado.erro)

    def test_reimprimir_abre_o_comprovante(self) -> None:
        estado = self._estado()
        self.assertIn("/recepcao/comprovante/10", str(estado.reimprimir()))


FICHA_AGUARDANDO = {
    **FICHA,
    "ficha": {**FICHA["ficha"], "status": "AGUARDANDO", "senha": "A-CAR-001", "especialidade": {"id": 1, "nome": "Cardiologia", "sigla": "CAR"}},
    "classificacao": {**CLASSIFICACAO, "prioridade_calculada": "AMARELA", "prioridade_atual": "AMARELA"},
}


class TestReavaliacaoAguardando(unittest.TestCase):
    """RF12: ficha AGUARDANDO editável, com troca de senha e ajuste no mesmo envio (add-reavaliacao-ficha-aguardando)."""

    def _estado(self, ficha=FICHA_AGUARDANDO) -> EstadoFichaFalso:
        estado = EstadoFichaFalso()
        with _api(Resposta(200, ficha), Resposta(200, CATALOGO)):
            asyncio.run(estado.carregar("10"))
        return estado

    def _recarga_aguardando(self, **ficha) -> list[Resposta]:
        return [Resposta(200, {**FICHA_AGUARDANDO, "ficha": {**FICHA_AGUARDANDO["ficha"], **ficha}}), Resposta(200, CATALOGO)]

    def test_salvar_com_troca_de_senha_mostra_aviso(self) -> None:
        estado = self._estado()
        estado.set_sinal("spo2", "88")
        resultado = {"id": 10, "senha_alterada": True, "senha_anterior": "A-CAR-001", "senha": "V-CAR-001"}
        with _api(Resposta(200, resultado), *self._recarga_aguardando(senha="V-CAR-001")) as requisitar:
            asyncio.run(_executar_salvamento(estado))
        self.assertEqual(requisitar.call_args_list[0].args[:3], ("PATCH", "XANO_TRIAGEM_API_URL", "/fichas/10"))
        self.assertIn("A-CAR-001 para V-CAR-001", estado.aviso_senha)
        self.assertFalse(estado.erro)
        self.assertEqual(estado.ficha["senha"], "V-CAR-001")

    def test_salvar_sem_troca_de_senha_nao_mostra_aviso(self) -> None:
        estado = self._estado()
        estado.set_observacao("Refere melhora")
        resultado = {"id": 10, "senha_alterada": False, "senha_anterior": "A-CAR-001", "senha": "A-CAR-001"}
        with _api(Resposta(200, resultado), *self._recarga_aguardando()):
            asyncio.run(_executar_salvamento(estado))
        self.assertEqual(estado.aviso_senha, "")
        self.assertFalse(estado.erro)

    def test_recusa_sem_cor_abre_o_ajuste_e_envia_tudo_junto(self) -> None:
        estado = self._estado()
        estado.set_gestante(True)
        with _api(Resposta(400, {"message": "FICHA_SEM_PRIORIDADE"})):
            asyncio.run(_executar_salvamento(estado))
        self.assertTrue(estado.ajuste_aberto)
        self.assertIn("Escolha a prioridade com justificativa", estado.mensagem)
        self.assertTrue(estado.sinais_alterados)

        estado.ajuste_prioridade = "AMARELA"
        estado.ajuste_justificativa = " Gestante com dor "
        resultado = {"id": 10, "senha_alterada": False, "senha_anterior": "A-CAR-001", "senha": "A-CAR-001"}
        with _api(Resposta(200, resultado), *self._recarga_aguardando(gestante=True)) as requisitar:
            asyncio.run(estado.confirmar_ajuste())
        envio = requisitar.call_args_list[0]
        self.assertEqual(envio.args[:3], ("PATCH", "XANO_TRIAGEM_API_URL", "/fichas/10"))
        self.assertEqual(envio.kwargs["json"]["prioridade_ajuste"], "AMARELA")
        self.assertEqual(envio.kwargs["json"]["justificativa_ajuste"], "Gestante com dor")
        self.assertTrue(envio.kwargs["json"]["sinais_vitais"]["gestante"])
        self.assertFalse(estado.ajuste_aberto)
        self.assertFalse(estado.sinais_alterados)

    def test_ajuste_sem_alteracoes_usa_o_endpoint_de_prioridade_e_avisa_a_senha(self) -> None:
        estado = self._estado()
        estado.abrir_ajuste()
        estado.ajuste_prioridade = "VERMELHA"
        estado.ajuste_justificativa = "Piora relatada"
        resultado = {"id": 10, "senha_alterada": True, "senha_anterior": "A-CAR-001", "senha": "V-CAR-001"}
        with _api(Resposta(200, resultado), *self._recarga_aguardando(senha="V-CAR-001")) as requisitar:
            asyncio.run(estado.confirmar_ajuste())
        self.assertEqual(requisitar.call_args_list[0].args[:3], ("POST", "XANO_TRIAGEM_API_URL", "/fichas/10/prioridade"))
        self.assertIn("V-CAR-001", estado.aviso_senha)

    def test_ficha_chamada_e_recusada_pelo_backend(self) -> None:
        estado = self._estado({**FICHA_AGUARDANDO, "ficha": {**FICHA_AGUARDANDO["ficha"], "status": "CHAMADO"}})
        estado.set_observacao("Tentativa")
        with _api(Resposta(400, {"message": "FICHA_FORA_DA_TRIAGEM"})):
            asyncio.run(_executar_salvamento(estado))
        self.assertTrue(estado.erro)
        self.assertEqual(estado.mensagem, "Esta ficha já foi chamada ou encerrada e não pode mais ser alterada.")
        self.assertFalse(estado.ajuste_aberto)


class ComprovanteFalso:
    carregar = ComprovanteState.carregar.fn

    def __init__(self) -> None:
        self.ficha_id = 0
        self.senha = ""
        self.prioridade = ""
        self.especialidade = ""
        self.entrada = ""
        self.carregando = False
        self.mensagem = ""
        self.auth = AuthFalso()

    async def get_state(self, estado):
        return self.auth


class TestComprovante(unittest.TestCase):
    def test_comprovante_renderizado_nao_expoe_dados_pessoais_ou_clinicos(self) -> None:
        arvore = str(comprovante_senha().render()).lower()
        self.assertIn("80mm", arvore)
        for campo_proibido in ("cpf", "nome", "nascimento", "telefone", "sintoma", "sinal vital"):
            self.assertNotIn(campo_proibido, arvore)

    def test_carrega_so_os_campos_do_comprovante(self) -> None:
        estado = ComprovanteFalso()
        corpo = {"senha": "A-CAR-001", "prioridade": "AMARELA", "especialidade": {"nome": "Cardiologia", "sigla": "CAR"},
                 "chegada_em": 1794155580000, "nome": "Pessoa de Teste", "cpf": "12345678901",
                 "data_nascimento": "1980-01-01", "sintomas": ["dor de teste"],
                 "sinais_vitais": {"fc": 80}, "paciente": {"nome": "Pessoa de Teste"}}
        with _api(Resposta(200, corpo)) as requisitar:
            asyncio.run(estado.carregar("10"))
        self.assertEqual(requisitar.call_args.args[:3], ("GET", "XANO_TRIAGEM_API_URL", "/fichas/10/comprovante"))
        self.assertEqual((estado.senha, estado.prioridade, estado.especialidade), ("A-CAR-001", "Amarela", "Cardiologia"))
        self.assertEqual(estado.entrada, "08/11/2026 13:33")
        self.assertFalse(hasattr(estado, "nome") or hasattr(estado, "cpf"))
        estado_publicado = repr({chave: valor for chave, valor in vars(estado).items() if chave != "auth"})
        for dado_privado in ("Pessoa de Teste", "12345678901", "1980-01-01", "dor de teste", "fc"):
            self.assertNotIn(dado_privado, estado_publicado)

    def test_ficha_sem_senha_ativa_mostra_mensagem(self) -> None:
        estado = ComprovanteFalso()
        with _api(Resposta(400, {"message": "SENHA_NAO_ATIVA"})):
            asyncio.run(estado.carregar("10"))
        self.assertTrue(estado.mensagem)
        self.assertEqual(estado.senha, "")

"""A tela médica envia só ações; a escolha e os limites permanecem no Xano."""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.medico import ImpressaoMedicoState, MedicoState


class Resposta:
    def __init__(self, dados, status_code=200):
        self.dados = dados
        self.status_code = status_code
        self.is_success = 200 <= status_code < 300

    def json(self):
        return self.dados


class EstadoFalso:
    _requisitar = MedicoState._requisitar
    carregar = MedicoState.carregar.fn
    definir_status = MedicoState.definir_status.fn
    chamar = MedicoState.chamar.fn
    _agir = MedicoState._agir
    repetir = MedicoState.repetir.fn
    compareceu = MedicoState.compareceu.fn
    pedir_desistencia = MedicoState.pedir_desistencia.fn
    cancelar_desistencia = MedicoState.cancelar_desistencia.fn
    desistiu = MedicoState.desistiu.fn

    def __init__(self):
        self.filas = []
        self.ficha_atual = {}
        self.historico = []
        self.tem_ficha = False
        self.apto = True
        self.plantao_vigente = False
        self.status_operacional = ""
        self.mensagem = ""
        self.erro = False
        self.ocupado = False
        self.confirmando_desistencia = False
        self.auth = type("Auth", (), {"token": "token-teste"})()

    async def get_state(self, estado):
        assert estado is AuthState
        return self.auth


class MedicoStateTest(unittest.TestCase):
    def test_chamar_nao_envia_id_de_ficha_e_mostra_fila_vazia(self):
        estado = EstadoFalso()
        with patch("ps_fila_prioritaria.api.requisitar", side_effect=[
            Resposta({"fila_vazia": True}),
            Resposta({"medico": {"apto": True, "status": "DISPONIVEL"}, "filas": [], "ficha_atual": None}),
        ]) as requisitar:
            asyncio.run(estado.chamar())
        self.assertEqual(requisitar.call_args_list[0].args[2], "/medico/chamar-proximo")
        self.assertEqual(requisitar.call_args_list[0].kwargs["json"], {})
        self.assertIn("Nenhum paciente", estado.mensagem)

    def test_repetir_usa_apenas_ficha_atribuida(self):
        estado = EstadoFalso()
        estado.ficha_atual = {"id": 42}
        estado.tem_ficha = True
        with patch("ps_fila_prioritaria.api.requisitar", side_effect=[
            Resposta({"status": "CHAMADO"}),
            Resposta({"medico": {"apto": True, "status": "DISPONIVEL"}, "filas": [], "ficha_atual": {"id": 42}}),
        ]) as requisitar:
            asyncio.run(estado.repetir())
        self.assertEqual(requisitar.call_args_list[0].args[2], "/medico/fichas/42/acao")
        self.assertEqual(requisitar.call_args_list[0].kwargs["json"], {"acao": "REPETIR"})

    def test_ocupado_bloqueia_requisicao_repetida(self):
        estado = EstadoFalso()
        estado.ocupado = True
        with patch("ps_fila_prioritaria.api.requisitar") as requisitar:
            asyncio.run(estado.chamar())
        requisitar.assert_not_called()

    def test_carregar_mostra_estado_do_plantao(self):
        estado = EstadoFalso()
        with patch("ps_fila_prioritaria.api.requisitar", return_value=Resposta({
            "medico": {"apto": True, "status": "DISPONIVEL", "plantao_vigente": True},
            "filas": [], "ficha_atual": None,
        })):
            asyncio.run(estado.carregar())
        self.assertTrue(estado.plantao_vigente)

    def test_ativacao_explicita_envia_status_e_recarrega_cobertura(self):
        estado = EstadoFalso()
        with patch("ps_fila_prioritaria.api.requisitar", side_effect=[
            Resposta({"status": "DISPONIVEL"}),
            Resposta({"medico": {"apto": True, "status": "DISPONIVEL", "plantao_vigente": True}, "filas": [], "ficha_atual": None}),
        ]) as requisitar:
            asyncio.run(estado.definir_status("DISPONIVEL"))
        self.assertEqual(requisitar.call_args_list[0].args[:3], ("PATCH", "XANO_AUTH_API_URL", "/me/status"))
        self.assertEqual(requisitar.call_args_list[0].kwargs["json"], {"status": "DISPONIVEL"})
        self.assertEqual(estado.status_operacional, "DISPONIVEL")
        self.assertTrue(estado.apto)

    def test_intervalo_retorna_mensagem_sem_nova_chamada(self):
        estado = EstadoFalso()
        estado.ficha_atual = {"id": 42}
        estado.tem_ficha = True
        with patch("ps_fila_prioritaria.api.requisitar", return_value=Resposta({"message": "AGUARDE_INTERVALO:12"}, 400)) as requisitar:
            asyncio.run(estado.repetir())
        self.assertEqual(requisitar.call_count, 1)
        self.assertTrue(estado.erro)
        self.assertIn("12 segundos", estado.mensagem)

    def test_desistencia_exige_confirmacao_antes_de_enviar(self):
        estado = EstadoFalso()
        estado.ficha_atual = {"id": 42}
        estado.tem_ficha = True
        with patch("ps_fila_prioritaria.api.requisitar", side_effect=[
            Resposta({"status": "DESISTENCIA"}),
            Resposta({"medico": {"apto": True}, "filas": [], "ficha_atual": None}),
        ]) as requisitar:
            estado.pedir_desistencia()
            self.assertTrue(estado.confirmando_desistencia)
            requisitar.assert_not_called()
            estado.cancelar_desistencia()
            self.assertFalse(estado.confirmando_desistencia)
            requisitar.assert_not_called()
            estado.pedir_desistencia()
            asyncio.run(estado.desistiu())
        self.assertFalse(estado.confirmando_desistencia)
        self.assertEqual(requisitar.call_args_list[0].kwargs["json"], {"acao": "DESISTENCIA"})

    def test_comparecimento_envia_acao_da_ficha_atribuida(self):
        estado = EstadoFalso()
        estado.ficha_atual = {"id": 42}
        estado.tem_ficha = True
        with patch("ps_fila_prioritaria.api.requisitar", side_effect=[
            Resposta({"status": "ATENDIDO"}),
            Resposta({"medico": {"apto": True}, "filas": [], "ficha_atual": None}),
        ]) as requisitar:
            asyncio.run(estado.compareceu())
        self.assertEqual(requisitar.call_args_list[0].args[2], "/medico/fichas/42/acao")
        self.assertEqual(requisitar.call_args_list[0].kwargs["json"], {"acao": "COMPARECEU"})


class EstadoImpressaoFalso:
    carregar_da_rota = ImpressaoMedicoState.carregar_da_rota.fn

    def __init__(self, caminho):
        self.router = SimpleNamespace(url=SimpleNamespace(path=caminho))
        self.auth = SimpleNamespace(token="token-teste")
        self.tem_dados = False
        self.mensagem = ""
        self.sintomas = []

    async def get_state(self, estado):
        assert estado is AuthState
        return self.auth


class ImpressaoMedicoStateTest(unittest.TestCase):
    def test_rota_usa_id_da_ficha_e_carrega_dados_proprios(self):
        estado = EstadoImpressaoFalso("/medico/ficha/42/imprimir")
        dados = {
            "ficha": {"senha": "V-CAR-001", "especialidade": {"nome": "Cardiologia"}, "prioridade_atual": "VERMELHA"},
            "paciente": {"nome": "Paciente de Teste", "idade": 35},
            "sintomas": [{"nome": "Sintoma de teste"}], "sintomas_livres": [],
        }
        with patch("ps_fila_prioritaria.api.requisitar", return_value=Resposta(dados)) as requisitar:
            asyncio.run(estado.carregar_da_rota())
        self.assertEqual(requisitar.call_args.args[2], "/fichas/42/impressao")
        self.assertTrue(estado.tem_dados)
        self.assertEqual(estado.senha, "V-CAR-001")
        self.assertEqual(estado.sintomas, ["Sintoma de teste"])

    def test_ficha_alheia_e_id_invalido_nao_exibem_dados(self):
        estado = EstadoImpressaoFalso("/medico/ficha/42/imprimir")
        with patch("ps_fila_prioritaria.api.requisitar", return_value=Resposta({"message": "FICHA_NAO_ATRIBUIDA"}, 403)):
            asyncio.run(estado.carregar_da_rota())
        self.assertFalse(estado.tem_dados)
        self.assertEqual(estado.mensagem, "Você não pode imprimir esta ficha.")
        invalida = EstadoImpressaoFalso("/medico/ficha/x/imprimir")
        with patch("ps_fila_prioritaria.api.requisitar") as requisitar:
            asyncio.run(invalida.carregar_da_rota())
        requisitar.assert_not_called()
        self.assertFalse(invalida.tem_dados)


if __name__ == "__main__":
    unittest.main()

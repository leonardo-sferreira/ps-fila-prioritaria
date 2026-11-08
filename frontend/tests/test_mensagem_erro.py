"""Mensagens de erro da API mostradas na tela."""
import unittest

import httpx

from ps_fila_prioritaria.ps_fila_prioritaria import MENSAGEM_LIMITE_XANO, _mensagem_erro

LIMITE_XANO = ("Whoa there! Your plan only supports 10 requests per 20 seconds. Upgrade options and additional "
               "information is available at: https://docs.xano.com/api-rate-limit")


class TestMensagemErro(unittest.TestCase):
    def test_limite_do_xano_vira_mensagem_em_portugues(self):
        resposta = httpx.Response(429, json={"code": "ERROR_CODE_TOO_MANY_REQUESTS", "message": LIMITE_XANO})
        self.assertEqual(_mensagem_erro(resposta), MENSAGEM_LIMITE_XANO)

    def test_429_do_nosso_backend_continua_igual(self):
        resposta = httpx.Response(429, json={"message": "Aguarde 30 segundos para pedir um novo código."})
        self.assertEqual(_mensagem_erro(resposta), "Aguarde 30 segundos para pedir um novo código.")


class TestMensagensDaFicha(unittest.TestCase):
    def test_ficha_ja_na_fila_tem_mensagem_clara(self):
        resposta = httpx.Response(400, json={"code": "ERROR_CODE_INPUT_ERROR", "message": "FICHA_NAO_FINALIZADA_EXISTENTE"})
        self.assertIn("já está na fila de atendimento", _mensagem_erro(resposta))

    def test_sinal_vital_invalido_cita_o_campo(self):
        resposta = httpx.Response(400, json={"message": "SINAL_VITAL_INVALIDO:spo2"})
        self.assertEqual(_mensagem_erro(resposta), "Valor fora do aceito em SpO2. Confira o número digitado.")

    def test_codigo_desconhecido_continua_aparecendo(self):
        resposta = httpx.Response(400, json={"message": "OUTRO_ERRO"})
        self.assertEqual(_mensagem_erro(resposta), "OUTRO_ERRO")


class TestIdDaRota(unittest.TestCase):
    def test_extrai_o_id_do_caminho(self):
        from ps_fila_prioritaria.ps_fila_prioritaria import _id_da_rota
        self.assertEqual(_id_da_rota("/recepcao/ficha/12"), "12")
        self.assertEqual(_id_da_rota("/recepcao/comprovante/7/"), "7")
        self.assertEqual(_id_da_rota(""), "")

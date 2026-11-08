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

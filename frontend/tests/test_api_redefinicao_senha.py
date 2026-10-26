"""Testes de integração da redefinição de senha contra a API real do Xano (spec autenticacao).

O código chega só por e-mail; por isso aqui ficam as recusas e a resposta genérica. O caminho até a nova
senha e os limites de tempo (9 min 59 s / 10 min, 59 / 60 s) ficam no roteiro manual (design D13).
"""

import os
import ssl
import time

import httpx
import pytest

from ps_fila_prioritaria.ps_fila_prioritaria import carregar_variaveis_ambiente

carregar_variaveis_ambiente()

BASE = os.getenv("XANO_AUTH_API_URL", "").strip().rstrip("/")
EMAIL = os.getenv("TEST_RECEPCAO_EMAIL", "")
SENHA = os.getenv("TEST_RECEPCAO_SENHA", "")
GENERICA = "Se o e-mail estiver cadastrado, enviamos um código"

pytestmark = pytest.mark.skipif(
    not BASE or not EMAIL or not SENHA,
    reason="Configure XANO_AUTH_API_URL e TEST_RECEPCAO_* no frontend/.env",
)


def _chamar(caminho: str, corpo: dict) -> httpx.Response:
    time.sleep(2.5)  # Respeita o limite do plano gratuito do Xano (10 requisições / 20 s).
    return httpx.post(f"{BASE}{caminho}", json=corpo, timeout=15, verify=ssl.create_default_context())


def test_resposta_igual_para_email_inexistente_e_campo_obrigatorio() -> None:
    inexistente = _chamar("/auth/senha/solicitar", {"email": "ninguem@ps.test"})
    assert inexistente.status_code == 200, inexistente.text
    assert inexistente.json()["mensagem"] == GENERICA
    vazio = _chamar("/auth/senha/solicitar", {})
    assert vazio.status_code == 400 and vazio.json()["message"] == "Informe o e-mail."


def test_solicitacao_valida_responde_igual_e_bloqueia_reenvio_imediato() -> None:
    primeira = _chamar("/auth/senha/solicitar", {"email": EMAIL})
    if primeira.status_code == 429:
        pytest.skip("Código pedido há menos de 60 s por outra execução; rode de novo em 1 minuto.")
    assert primeira.status_code == 200, primeira.text
    assert primeira.json()["mensagem"] == GENERICA
    segunda = _chamar("/auth/senha/solicitar", {"email": EMAIL})
    assert segunda.status_code == 429, segunda.text
    assert segunda.json()["message"].startswith("Aguarde ")


def test_codigo_errado_e_tentativas_esgotadas_sao_recusados() -> None:
    # Nenhum código real tem 7 dígitos, então todas as tentativas erram.
    for _tentativa in range(6):
        resposta = _chamar("/auth/senha/verificar", {"email": EMAIL, "codigo": "0000000"})
        assert resposta.status_code == 401, resposta.text
        assert resposta.json()["message"] == "Código inválido ou expirado"


def test_senha_curta_e_codigo_errado_nao_trocam_a_senha() -> None:
    curta = _chamar("/auth/senha/redefinir", {"email": EMAIL, "codigo": "0000000", "nova_senha": "1234567"})
    assert curta.status_code == 400 and curta.json()["message"] == "A nova senha deve ter pelo menos 8 caracteres."
    errado = _chamar("/auth/senha/redefinir", {"email": EMAIL, "codigo": "0000000", "nova_senha": "12345678"})
    assert errado.status_code == 401 and errado.json()["message"] == "Código inválido ou expirado"
    # A senha anterior continua valendo.
    login = _chamar("/auth/login", {"email": EMAIL, "senha": SENHA})
    assert login.status_code == 200, login.text

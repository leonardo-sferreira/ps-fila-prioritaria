"""Testes de integração do login contra a API real do Xano (spec autenticacao).

As URLs e credenciais vêm do frontend/.env (nunca do repositório). Sem elas, os testes são ignorados.
"""

import os
import ssl
import time

import httpx
import pytest

from ps_fila_prioritaria.ps_fila_prioritaria import carregar_variaveis_ambiente

carregar_variaveis_ambiente()

BASE = os.getenv("XANO_AUTH_API_URL", "").strip().rstrip("/")
USUARIOS = {
    "ADMINISTRADOR": (os.getenv("TEST_ADMIN_EMAIL", ""), os.getenv("TEST_ADMIN_SENHA", "")),
    "RECEPCAO_TRIAGEM": (os.getenv("TEST_RECEPCAO_EMAIL", ""), os.getenv("TEST_RECEPCAO_SENHA", "")),
    "MEDICO": (os.getenv("TEST_MEDICO_EMAIL", ""), os.getenv("TEST_MEDICO_SENHA", "")),
}

pytestmark = pytest.mark.skipif(
    not BASE or not all(email and senha for email, senha in USUARIOS.values()),
    reason="Configure XANO_AUTH_API_URL e as credenciais TEST_* no frontend/.env",
)


def _chamar(metodo: str, caminho: str, token: str = "", **kwargs) -> httpx.Response:
    time.sleep(2.5)  # Respeita o limite do plano gratuito do Xano (10 requisições / 20 s).
    cabecalhos = {"Authorization": f"Bearer {token}"} if token else {}
    # Certificados do sistema operacional, como o teste de integração existente (urllib), para funcionar em redes com proxy TLS.
    return httpx.request(
        metodo, f"{BASE}{caminho}", headers=cabecalhos, timeout=15, verify=ssl.create_default_context(), **kwargs
    )


def _login(perfil: str) -> httpx.Response:
    email, senha = USUARIOS[perfil]
    return _chamar("POST", "/auth/login", json={"email": email, "senha": senha})


@pytest.mark.parametrize("perfil", ["ADMINISTRADOR", "RECEPCAO_TRIAGEM", "MEDICO"])
def test_senha_correta_envia_o_codigo_e_ainda_nao_devolve_token(perfil: str) -> None:
    resposta = _login(perfil)
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["codigo_enviado"] is True
    assert corpo["reenvio_em_segundos"] > 0
    assert "token" not in corpo
    assert "password" not in corpo


def test_email_com_maiusculas_e_espacos_tambem_entra() -> None:
    email, senha = USUARIOS["RECEPCAO_TRIAGEM"]
    resposta = _chamar("POST", "/auth/login", json={"email": f"  {email.upper()}  ", "senha": senha})
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["codigo_enviado"] is True


def test_senha_errada_usa_a_mesma_mensagem_generica() -> None:
    email, _ = USUARIOS["MEDICO"]
    senha_errada = _chamar("POST", "/auth/login", json={"email": email, "senha": "senha-incorreta-123"})
    email_inexistente = _chamar("POST", "/auth/login", json={"email": "ninguem@ps.test", "senha": "senha-incorreta-123"})
    assert senha_errada.status_code == email_inexistente.status_code == 401
    assert senha_errada.json()["message"] == email_inexistente.json()["message"] == "E-mail ou senha inválidos"


def test_campos_ausentes_sao_recusados_sem_token() -> None:
    sem_email = _chamar("POST", "/auth/login", json={"senha": "qualquer-coisa"})
    sem_senha = _chamar("POST", "/auth/login", json={"email": USUARIOS["ADMINISTRADOR"][0]})
    assert sem_email.status_code == 400 and sem_email.json()["message"] == "Informe o e-mail."
    assert sem_senha.status_code == 400 and sem_senha.json()["message"] == "Informe a senha."


def test_codigo_errado_e_tentativas_esgotadas_sao_recusados_sem_token() -> None:
    assert _login("MEDICO").status_code == 200
    email, _ = USUARIOS["MEDICO"]
    # Nenhum código real tem 7 dígitos, então todas as tentativas erram.
    for _tentativa in range(6):
        resposta = _chamar("POST", "/auth/login/verificar", json={"email": email, "codigo": "0000000"})
        assert resposta.status_code == 401, resposta.text
        assert resposta.json()["message"] == "Código inválido ou expirado"
        assert "token" not in resposta.json()


def test_reenvio_antes_do_intervalo_informa_quanto_falta() -> None:
    assert _login("ADMINISTRADOR").status_code == 200
    resposta = _chamar("POST", "/auth/login/reenviar", json={"email": USUARIOS["ADMINISTRADOR"][0]})
    assert resposta.status_code == 429, resposta.text
    assert resposta.json()["message"].startswith("Aguarde ")


def test_reenvio_sem_login_pendente_pede_novo_login() -> None:
    resposta = _chamar("POST", "/auth/login/reenviar", json={"email": "ninguem@ps.test"})
    assert resposta.status_code == 403, resposta.text
    assert resposta.json()["message"] == "Não foi possível reenviar o código. Faça login novamente."


def test_verificar_sem_codigo_e_recusado() -> None:
    resposta = _chamar("POST", "/auth/login/verificar", json={"email": USUARIOS["ADMINISTRADOR"][0]})
    assert resposta.status_code == 400 and resposta.json()["message"] == "Informe o código."


def test_me_recusa_requisicao_sem_token_ou_com_token_adulterado() -> None:
    assert _chamar("GET", "/auth/me").status_code == 401
    assert _chamar("GET", "/auth/me", token="token.adulterado.invalido").status_code == 401

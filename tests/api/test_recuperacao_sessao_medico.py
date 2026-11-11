"""Integração do login médico com usuário sintético e código criado só pelo CLI."""

import concurrent.futures
import json
import os
import secrets
import ssl
import subprocess
import time
import unittest
from pathlib import Path

import httpx
from dotenv import dotenv_values


RAIZ = Path(__file__).resolve().parents[2]
BASE = os.getenv("XANO_AUTH_API_URL") or dotenv_values(RAIZ / "frontend/.env").get("XANO_AUTH_API_URL")
BASE_FILA = os.getenv("XANO_FILA_API_URL") or dotenv_values(RAIZ / "frontend/.env").get("XANO_FILA_API_URL")


def _cenario(acao: str, marcador: str, codigo: str = "", senha: str = "") -> dict:
    entrada = {"acao": acao, "marcador": marcador}
    # O CLI exige os campos opcionais mesmo quando a ação não os utiliza.
    entrada["codigo"] = codigo or f"{secrets.randbelow(1_000_000):06d}"
    entrada["senha"] = senha or secrets.token_urlsafe(18)
    processo = subprocess.run(
        ["xano", "function", "run", "auth/teste_sessao_unica", "--json", "-", "--branch", "v1", "-p", "ps-impacta", "-o", "json"],
        input=json.dumps(entrada), text=True, capture_output=True, check=True, timeout=30,
    )
    resposta = json.loads(processo.stdout)
    assert resposta["status"] == "ok", resposta
    return resposta["result"]


def _verificar(email: str, codigo: str) -> httpx.Response:
    time.sleep(2.2)
    return httpx.post(
        f"{BASE.rstrip('/')}/auth/login/verificar",
        json={"email": email, "codigo": codigo},
        timeout=20, verify=ssl.create_default_context(),
    )


def _protegida(metodo: str, base: str, caminho: str, token: str, **kwargs) -> httpx.Response:
    time.sleep(2.2)
    return httpx.request(
        metodo, f"{base.rstrip('/')}{caminho}",
        headers={"Authorization": f"Bearer {token}"}, timeout=20,
        verify=ssl.create_default_context(), **kwargs,
    )


def _novo_codigo(marcador: str) -> str:
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    _cenario("CODIGO", marcador, codigo=codigo)
    time.sleep(2.2)  # Plano gratuito do Xano: evita 429 entre chamadas isoladas.
    return codigo


@unittest.skipUnless(BASE and BASE_FILA, "Configure XANO_AUTH_API_URL e XANO_FILA_API_URL")
def _verificar_recuperacao_sem_disponibilidade_automatica() -> None:
    marcador = secrets.token_hex(5)
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    criado = _cenario("CRIAR", marcador, codigo=codigo, senha=secrets.token_urlsafe(18))
    email = criado["email"]

    try:
        primeira = _verificar(email, codigo)
        assert primeira.status_code == 200, primeira.text
        token = primeira.json()["token"]
        assert _cenario("CONSULTAR", marcador)["status_atual"] is None
        filas = _protegida("GET", BASE_FILA, "/medico/filas", token)
        assert filas.status_code == 200, filas.text
        assert filas.json()["medico"]["apto"] is False

        ativacao = _protegida("PATCH", BASE, "/me/status", token, json={"status": "DISPONIVEL"})
        assert ativacao.status_code == 200, ativacao.text
        assert _cenario("CONSULTAR", marcador)["status_atual"] == "DISPONIVEL"
        filas = _protegida("GET", BASE_FILA, "/medico/filas", token)
        assert filas.status_code == 200 and filas.json()["medico"]["apto"] is True

        for status in ("PAUSA", "AUSENTE"):
            alteracao = _protegida("PATCH", BASE, "/me/status", token, json={"status": status})
            assert alteracao.status_code == 200, alteracao.text
            assert _cenario("CONSULTAR", marcador)["status_atual"] == status
            novo_login = _verificar(email, _novo_codigo(marcador))
            assert novo_login.status_code == 200, novo_login.text
            token = novo_login.json()["token"]
            atual = _cenario("CONSULTAR", marcador)
            assert atual["status_atual"] is None
            assert status in atual["status_sessoes"], atual
            filas = _protegida("GET", BASE_FILA, "/medico/filas", token)
            assert filas.status_code == 200 and filas.json()["medico"]["apto"] is False

        invalido = _protegida("PATCH", BASE, "/me/status", token, json={"status": "EM_ATENDIMENTO"})
        assert invalido.status_code == 400, invalido.text

        saida = _protegida("POST", BASE, "/auth/logout", token)
        assert saida.status_code == 200, saida.text
        assert _cenario("CONSULTAR", marcador)["sessoes_ativas"] == 0

        depois_logout = _verificar(email, _novo_codigo(marcador))
        assert depois_logout.status_code == 200, depois_logout.text
        atual = _cenario("CONSULTAR", marcador)
        assert atual["sessoes_ativas"] == 1 and atual["status_atual"] is None

        _cenario("EXPIRAR", marcador)
        depois_expirar = _verificar(email, _novo_codigo(marcador))
        assert depois_expirar.status_code == 200, depois_expirar.text
        atual = _cenario("CONSULTAR", marcador)
        assert atual["sessoes_ativas"] == 1 and atual["status_atual"] is None

        _cenario("EXPIRAR", marcador)
        codigo_concorrente = _novo_codigo(marcador)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            respostas = list(executor.map(lambda _: _verificar(email, codigo_concorrente), range(2)))
        assert sum(r.status_code == 200 for r in respostas) == 1, [(r.status_code, r.text) for r in respostas]
        assert all(r.status_code in (200, 401, 429) for r in respostas)
        assert _cenario("CONSULTAR", marcador)["sessoes_ativas"] == 1
    finally:
        _cenario("ENCERRAR", marcador)


class RecuperacaoSessaoMedicoTeste(unittest.TestCase):
    def test_fluxo(self) -> None:
        _verificar_recuperacao_sem_disponibilidade_automatica()

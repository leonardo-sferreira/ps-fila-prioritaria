"""Testes de integração da emissão do Totem contra a API real do Xano (spec totem).

Usam XANO_TRIAGEM_API_URL e TOTEM_CHAVE do frontend/.env; sem elas, são ignorados. Cada execução cria
tickets reais do dia na fila de pré-triagem. A virada do dia fica no roteiro manual (não dá para mudar a data).
"""

import concurrent.futures
import os
import ssl
import time

import httpx
import pytest

from ps_fila_prioritaria.ps_fila_prioritaria import carregar_variaveis_ambiente

carregar_variaveis_ambiente()

BASE = os.getenv("XANO_TRIAGEM_API_URL", "").strip().rstrip("/")
CHAVE = os.getenv("TOTEM_CHAVE", "")
PREFIXO = {"PEDIATRICO": "C", "PREFERENCIAL": "P", "NORMAL": "N"}

pytestmark = pytest.mark.skipif(not BASE or not CHAVE, reason="Configure XANO_TRIAGEM_API_URL e TOTEM_CHAVE no frontend/.env")


def _emitir(tipo: str, chave: str = CHAVE, esperar: bool = True) -> httpx.Response:
    if esperar:
        time.sleep(2.5)  # Respeita o limite do plano gratuito do Xano (10 requisições / 20 s).
    return httpx.post(f"{BASE}/totem/tickets", json={"chave_dispositivo": chave, "tipo": tipo}, timeout=20, verify=ssl.create_default_context())


@pytest.mark.parametrize("tipo", ["PEDIATRICO", "PREFERENCIAL", "NORMAL"])
def test_emissao_de_cada_tipo_usa_o_prefixo_e_so_dados_operacionais(tipo: str) -> None:
    resposta = _emitir(tipo)
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert set(corpo) == {"tipo", "numero", "codigo"}
    assert corpo["tipo"] == tipo
    assert corpo["codigo"] == f"{PREFIXO[tipo]}-{corpo['numero']:03d}"


def test_sequencia_do_tipo_avanca_sem_mexer_nos_outros_tipos() -> None:
    primeiro = _emitir("NORMAL").json()["numero"]
    _emitir("PEDIATRICO")
    segundo = _emitir("NORMAL").json()["numero"]
    assert segundo == primeiro + 1


def test_chave_ausente_ou_errada_nao_emite() -> None:
    for chave in ("", "chave-errada"):
        resposta = _emitir("NORMAL", chave=chave)
        assert resposta.status_code == 401, resposta.text
        assert resposta.json()["message"] == "Dispositivo não autorizado."


def test_tipo_ausente_ou_invalido_nao_emite() -> None:
    for tipo in ("", "VIP"):
        resposta = _emitir(tipo)
        assert resposta.status_code == 400, resposta.text
        assert resposta.json()["message"] == "Tipo de ticket inválido."


def test_emissoes_simultaneas_do_mesmo_tipo_nao_repetem_numero() -> None:
    time.sleep(20)  # Janela livre do limite de requisições antes do disparo simultâneo.
    with concurrent.futures.ThreadPoolExecutor(4) as executor:
        respostas = list(executor.map(lambda _: _emitir("PREFERENCIAL", esperar=False), range(4)))
    assert all(r.status_code == 200 for r in respostas), [r.text for r in respostas]
    numeros = [r.json()["numero"] for r in respostas]
    assert len(set(numeros)) == len(numeros)

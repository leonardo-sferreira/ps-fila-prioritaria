"""Registra apenas metadados de HTTP; nunca grava URL completa, body ou headers."""

import json
import os
from pathlib import Path
import threading
from urllib.parse import urlparse
import urllib.error
import urllib.request

import httpx
import pytest


def _route(url) -> str:
    # Somente segmentos de rotas conhecidos; valores dinâmicos nunca são publicados.
    allowed = {"api", "auth", "login", "verificar", "solicitar", "redefinir", "senha", "codigo", "me", "logout", "pacientes", "fichas", "sintomas", "sinais-vitais", "classificacao", "prioridade", "confirmar", "comprovante", "totem", "tickets", "parametros", "medicos", "fila", "chamar", "disponibilidade", "comparecimento", "desistencia", "{id}"}
    parts = urlparse(str(url)).path.split("/")
    return "/" + "/".join("{id}" if p.isdigit() else p if p in allowed else "{omitido}" for p in parts if p)


def _example(response) -> dict:
    # Nem nomes de campos arbitrários nem valores do corpo saem da memória.
    return {"tipo": "conteúdo omitido"}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    events = []
    nested = threading.local()
    original_request, original_post, original_urlopen = httpx.request, httpx.post, urllib.request.urlopen

    def request(method, url, *args, **kwargs):
        response = original_request(method, url, *args, **kwargs)
        if not getattr(nested, "inside_post", False):
            events.append({"metodo": str(method).upper(), "endpoint": _route(url), "status": response.status_code, "resposta": _example(response)})
        return response

    def post(url, *args, **kwargs):
        nested.inside_post = True
        try:
            response = original_post(url, *args, **kwargs)
        finally:
            nested.inside_post = False
        events.append({"metodo": "POST", "endpoint": _route(url), "status": response.status_code, "resposta": _example(response)})
        return response

    def urlopen(request_or_url, *args, **kwargs):
        method = request_or_url.get_method() if isinstance(request_or_url, urllib.request.Request) else "GET"
        url = request_or_url.full_url if isinstance(request_or_url, urllib.request.Request) else request_or_url
        try:
            response = original_urlopen(request_or_url, *args, **kwargs)
            events.append({"metodo": method, "endpoint": _route(url), "status": response.status, "resposta": {"tipo": "urllib; corpo não registrado"}})
            return response
        except urllib.error.HTTPError as error:
            events.append({"metodo": method, "endpoint": _route(url), "status": error.code, "resposta": {"tipo": "erro HTTP; corpo não registrado"}})
            raise

    httpx.request, httpx.post, urllib.request.urlopen = request, post, urlopen
    try:
        yield
    finally:
        httpx.request, httpx.post, urllib.request.urlopen = original_request, original_post, original_urlopen
        path = os.getenv("EVIDENCE_HTTP_EVENTS")
        if path:
            with Path(path).open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"node": item.nodeid, "eventos": events}, ensure_ascii=False) + "\n")

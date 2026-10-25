"""Cliente HTTP único para a API do Xano: monta a URL a partir do .env e injeta o token (design D6)."""

import os
from typing import Any

import httpx


class ConfiguracaoAusente(Exception):
    """A variável de ambiente com a URL do grupo de API não foi configurada."""


def url_api(variavel: str, caminho: str) -> str:
    base_url = os.getenv(variavel, "").strip().rstrip("/")
    if not base_url:
        raise ConfiguracaoAusente(variavel)
    return f"{base_url}{caminho}"


def requisitar(metodo: str, variavel: str, caminho: str, token: str = "", **kwargs: Any) -> httpx.Response:
    cabecalhos = dict(kwargs.pop("headers", None) or {})
    if token:
        cabecalhos["Authorization"] = f"Bearer {token}"
    return httpx.request(metodo, url_api(variavel, caminho), headers=cabecalhos, timeout=10, **kwargs)

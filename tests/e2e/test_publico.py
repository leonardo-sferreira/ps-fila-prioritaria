"""Fluxos públicos, sem credenciais nem gravação no Xano.

Exige REFLEX_E2E_BASE_URL apontando para uma instância controlada já iniciada.
"""

import os

from playwright.sync_api import Page, expect


BASE = os.environ["REFLEX_E2E_BASE_URL"].rstrip("/")


def test_login_abre_aviso_e_volta(page: Page) -> None:
    """O link de privacidade abre o aviso público e o retorno mostra o login."""
    page.goto(BASE + "/login")
    expect(page.get_by_role("button", name="Entrar")).to_be_visible()
    page.get_by_role("link", name="Aviso de privacidade").click()
    expect(page).to_have_url(BASE + "/privacidade")
    expect(page.get_by_text("Dados da equipe")).to_be_visible()
    page.get_by_role("link", name="Voltar ao login").click()
    expect(page.get_by_role("button", name="Entrar")).to_be_visible()


def test_area_interna_sem_sessao_redireciona(page: Page) -> None:
    """Uma rota médica sem sessão não exibe a área protegida."""
    page.goto(BASE + "/medico")
    expect(page).to_have_url(BASE + "/login")
    expect(page.get_by_role("button", name="Entrar")).to_be_visible()

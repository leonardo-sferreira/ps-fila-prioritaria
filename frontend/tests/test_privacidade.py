"""Regressões da change add-privacidade: aviso de privacidade e CPF mascarado."""

import unittest

from ps_fila_prioritaria.ps_fila_prioritaria import (
    ARQUIVO_AVISO_PRIVACIDADE,
    FichaState,
    carregar_aviso_privacidade,
    mascarar_cpf,
)


def test_cpf_com_11_digitos_mostra_so_do_4o_ao_9o() -> None:
    assert mascarar_cpf("123.456.789-01") == "***.456.789-**"
    assert mascarar_cpf("12345678901") == "***.456.789-**"


def test_cpf_ausente_ou_sem_11_digitos_nao_aparece_em_parte() -> None:
    for valor in ("1234567890", "123456789012", "", None, "abc"):
        assert mascarar_cpf(valor) == "—"


def test_cabecalho_da_ficha_usa_o_cpf_mascarado() -> None:
    cpf_exibido = FichaState.computed_vars["cpf_exibido"]._fget

    class Ficha:
        paciente = {"cpf": "123.456.789-01"}

    class FichaSemPaciente:
        paciente: dict = {}

    assert cpf_exibido(Ficha()) == "***.456.789-**"
    assert cpf_exibido(FichaSemPaciente()) == "—"


def test_pagina_mostra_o_texto_do_arquivo_do_aviso() -> None:
    assert carregar_aviso_privacidade() == ARQUIVO_AVISO_PRIVACIDADE.read_text(encoding="utf-8")


def test_aviso_tem_as_secoes_obrigatorias_para_equipe_e_pacientes() -> None:
    texto = carregar_aviso_privacidade()
    for secao in ("## Dados da equipe", "## Dados dos pacientes", "## Com quem compartilhamos", "## Por quanto tempo guardamos", "## Seus direitos"):
        assert secao in texto
    for item in ("**Quais dados:**", "**Para quê:**"):
        assert texto.count(item) >= 2  # um bloco para a equipe e outro para os pacientes
    assert "**Como pedir:**" in texto


class TestPrivacidade(unittest.TestCase):
    """Compatível tanto com unittest quanto com pytest."""

    def test_cpf_11_digitos(self) -> None:
        test_cpf_com_11_digitos_mostra_so_do_4o_ao_9o()

    def test_cpf_invalido(self) -> None:
        test_cpf_ausente_ou_sem_11_digitos_nao_aparece_em_parte()

    def test_cabecalho_ficha(self) -> None:
        test_cabecalho_da_ficha_usa_o_cpf_mascarado()

    def test_texto_do_aviso(self) -> None:
        test_pagina_mostra_o_texto_do_arquivo_do_aviso()

    def test_secoes_do_aviso(self) -> None:
        test_aviso_tem_as_secoes_obrigatorias_para_equipe_e_pacientes()

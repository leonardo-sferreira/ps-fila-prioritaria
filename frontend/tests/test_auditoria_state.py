"""Auditoria do Administrador (add-acompanhamento-administrador, D2/D4): tradução das linhas e filtros enviados."""

import asyncio
from unittest.mock import patch

from ps_fila_prioritaria.estados import auditoria as a
from tests.test_cadastros_state import REQUISITAR, Resposta, estado_falso

# 14/11/2026 14:30:00 em Brasília (17:30 UTC).
EM = 1794677400000


def test_alteracao_do_admin_mostra_evento_alvo_e_valores():
    linha = a.linha_auditoria({"em": EM, "origem": "ALTERACAO", "tipo_evento": "USUARIO_EDITADO", "entidade": "USUARIO", "registro_id": 7,
                               "usuario_id": 1, "usuario": "Ana", "valor_anterior": {"nome": "Bia"}, "valor_novo": {"nome": "Beatriz"}})
    assert linha["quando"] == "14/11/2026 14:30:00"
    assert linha["evento"] == "Usuario editado" and linha["alvo"] == "Usuario #7"
    assert linha["anterior"] == "nome: Bia" and linha["novo"] == "nome: Beatriz"
    assert not linha["sistema"]


def test_carga_automatica_aparece_como_sistema():
    linha = a.linha_auditoria({"em": EM, "origem": "ALTERACAO", "tipo_evento": "CARGA_INICIAL", "entidade": "PARAMETRO", "registro_id": 3,
                               "usuario_id": None, "usuario": "Sistema", "valor_anterior": None, "valor_novo": {"chave": "tamanho_previsao", "valor": "5"}})
    assert linha["sistema"] and linha["usuario"] == "Sistema" and linha["evento"] == "Carga inicial" and linha["anterior"] == "—"


def test_login_e_chamada_traduzidos():
    assert a.linha_auditoria({"em": EM, "origem": "SESSAO", "tipo_evento": "LOGIN", "usuario_id": 2})["evento"] == "Entrou no sistema"
    chamada = a.linha_auditoria({"em": EM, "origem": "CHAMADA", "tipo_evento": "DESISTENCIA", "entidade": "FICHA", "registro_id": 9, "usuario_id": 4})
    assert chamada["evento"] == "Paciente desistiu" and chamada["origem"] == "Chamada" and not chamada["sistema"]


def test_parametros_so_levam_filtros_preenchidos():
    assert a.parametros_consulta("2026-11-14", "2026-11-15", "TODAS", "0", 1) == {"pagina": 1, "data_inicio": "2026-11-14", "data_fim": "2026-11-15"}
    assert a.parametros_consulta("", "", "CHAMADA", "4", 0) == {"pagina": 1, "origem": "CHAMADA", "usuario_id": 4}


def test_filtro_volta_para_a_primeira_pagina_e_consulta():
    estado = estado_falso(a.AuditoriaState, itens=[], total=0, pagina=3, data_inicio="2026-11-14", data_fim="2026-11-14",
                          origem="TODAS", usuario_id="0", opcoes_usuarios=[], carregando=False, mensagem="", erro=False)
    estado._consultar = lambda: a.AuditoriaState._consultar(estado)
    estado._filtrar = lambda: a.AuditoriaState._filtrar(estado)
    chamadas = []

    def requisitar(metodo, _variavel, caminho, **kw):
        chamadas.append((metodo, caminho, kw.get("params")))
        return Resposta(200, {"itens": [{"em": EM, "origem": "SESSAO", "tipo_evento": "LOGOUT", "usuario_id": 1, "usuario": "Ana"}], "total": 1})

    with patch(REQUISITAR, side_effect=requisitar):
        asyncio.run(a.AuditoriaState.set_origem.fn(estado, "SESSAO"))
    assert chamadas == [("GET", "/admin/auditoria", {"pagina": 1, "data_inicio": "2026-11-14", "data_fim": "2026-11-14", "origem": "SESSAO"})]
    assert estado.pagina == 1 and estado.total == 1 and estado.itens[0]["evento"] == "Saiu do sistema"


def test_csv_tem_cabecalho_ponto_e_virgula_e_bom():
    texto = a.gerar_csv([{"quando": "14/11/2026 14:30:00", "usuario": "Ana", "evento": "Usuario editado", "origem": "Alteração",
                          "alvo": "Usuario #7", "anterior": "nome: Bia", "novo": "nome: Beatriz; ativa", "justificativa": ""}])
    linhas = texto.lstrip("﻿").splitlines()
    assert texto.startswith("﻿")
    assert linhas[0] == "Data e hora;Usuário;Evento;Tipo;Registro;Valor anterior;Valor novo;Justificativa"
    assert linhas[1] == '14/11/2026 14:30:00;Ana;Usuario editado;Alteração;Usuario #7;nome: Bia;"nome: Beatriz; ativa";'
    assert a.nome_arquivo("2026-11-14", "2026-11-14") == "auditoria_2026-11-14.csv"
    assert a.nome_arquivo("2026-11-01", "2026-11-14") == "auditoria_2026-11-01_a_2026-11-14.csv"


def test_exportar_busca_todas_as_paginas():
    estado = estado_falso(a.AuditoriaState, itens=[], total=0, pagina=1, data_inicio="2026-11-14", data_fim="2026-11-14",
                          origem="TODAS", usuario_id="0", opcoes_usuarios=[], carregando=False, exportando=False, mensagem="", erro=False)
    paginas = []

    def requisitar(metodo, _variavel, caminho, **kw):
        n = kw["params"]["pagina"]
        paginas.append(n)
        quantos = 50 if n == 1 else 10
        return Resposta(200, {"itens": [{"em": EM, "origem": "SESSAO", "tipo_evento": "LOGIN", "usuario_id": 1, "usuario": "Ana"}] * quantos, "total": 60})

    with patch(REQUISITAR, side_effect=requisitar):
        asyncio.run(a.AuditoriaState.exportar_csv.fn(estado))
    assert paginas == [1, 2] and "60 registro" in estado.mensagem and not estado.exportando

"""Sprint 4: status com HTTP simulado e contratos XS estáticos; nenhum acesso ao Live."""

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.status_equipe import STATUS_RECEPCAO, StatusRecepcaoState
from ps_fila_prioritaria.paginas.plantao import area_recepcao, seletor_status_recepcao
from test_medico_state import EstadoFalso as MedicoFalso, Resposta

RAIZ = Path(__file__).resolve().parents[2]


class RecepcaoFalsa:
    _executar = StatusRecepcaoState._executar
    carregar = StatusRecepcaoState.carregar.fn
    definir_status = StatusRecepcaoState.definir_status.fn

    def __init__(self):
        self.status_operacional = ""
        self.ocupado = False
        self.erro = False
        self.mensagem = ""
        self.auth = SimpleNamespace(token="token-simulado", perfil="RECEPCAO_TRIAGEM")
        def encerrar(mensagem):
            self.auth.token = ""
        self.auth._encerrar_sessao_local = encerrar

    async def get_state(self, classe):
        assert classe is AuthState
        return self.auth


@pytest.fixture(autouse=True)
def somente_http_simulado(monkeypatch):
    monkeypatch.setenv("XANO_AUTH_API_URL", "https://auth.test")
    def bloquear(*args, **kwargs):
        raise AssertionError("HTTP real proibido neste teste")
    monkeypatch.setattr("ps_fila_prioritaria.api.httpx.request", bloquear)
    monkeypatch.setattr("ps_fila_prioritaria.estados.status_equipe.rx.redirect", lambda rota: rota)


async def concluir(eventos):
    retorno = None
    async for evento in eventos:
        if evento is not None:
            retorno = evento
    return retorno


def consultar(estado, resposta):
    with patch("ps_fila_prioritaria.api.httpx.request", side_effect=resposta if callable(resposta) else [resposta]) as http:
        resultado = asyncio.run(concluir(estado.carregar()))
    return http, resultado


def alterar(estado, resposta, destino="PAUSA"):
    with patch("ps_fila_prioritaria.api.httpx.request", side_effect=resposta if callable(resposta) else [resposta]) as http:
        resultado = asyncio.run(concluir(estado.definir_status(destino)))
    return http, resultado


def test_consulta_status_real_da_api_sem_escrita():
    estado = RecepcaoFalsa()
    http, _ = consultar(estado, httpx.Response(200, json={"status": "PAUSA"}))
    assert estado.status_operacional == "PAUSA" and not estado.erro
    assert http.call_args.args == ("GET", "https://auth.test/me/status")
    assert http.call_args.kwargs["headers"] == {"Authorization": "Bearer token-simulado"}


def test_altera_tres_estados_manuais_somente_apos_confirmacao():
    for destino in STATUS_RECEPCAO:
        estado = RecepcaoFalsa()
        http, _ = alterar(estado, httpx.Response(200, json={"status": destino}), destino)
        assert estado.status_operacional == destino and not estado.erro
        assert http.call_args.args[0] == "PATCH"
        assert http.call_args.kwargs["json"] == {"status": destino}
        assert http.call_count == 1 and not estado.ocupado
        repetido, _ = alterar(estado, httpx.Response(200, json={"status": destino}), destino)
        repetido.assert_not_called()


def test_estado_manual_invalido_inclusive_em_atendimento_nao_envia():
    for destino in ("EM_ATENDIMENTO", "", None, True, [], "pausa"):
        estado = RecepcaoFalsa()
        with patch("ps_fila_prioritaria.api.httpx.request") as http:
            asyncio.run(concluir(estado.definir_status(destino)))
        http.assert_not_called()
        assert estado.erro and not estado.status_operacional


def test_ausencia_de_token_redireciona_sem_http():
    estado = RecepcaoFalsa()
    estado.auth.token = ""
    http, resultado = consultar(estado, httpx.Response(500))
    http.assert_not_called()
    assert resultado == "/login"


def test_outros_perfis_nao_consultam_nem_alteram_status_da_recepcao():
    for perfil, rota in (("ADMINISTRADOR", "/admin"), ("MEDICO", "/medico")):
        estado = RecepcaoFalsa()
        estado.auth.perfil = perfil
        http, resultado = alterar(estado, httpx.Response(500))
        http.assert_not_called()
        assert resultado == rota


def test_401_encerra_sessao_e_redireciona():
    estado = RecepcaoFalsa()
    estado.status_operacional = "DISPONIVEL"
    _, resultado = alterar(estado, httpx.Response(401))
    assert resultado == "/login" and estado.auth.token == "" and estado.status_operacional == ""


def test_403_preserva_status_anterior_sem_confirmar_mudanca():
    estado = RecepcaoFalsa()
    estado.status_operacional = "DISPONIVEL"
    alterar(estado, httpx.Response(403))
    assert estado.erro and estado.status_operacional == "DISPONIVEL"
    assert "Acesso negado" in estado.mensagem


def test_get_nao_publicado_mostra_indisponibilidade_sem_status_ficticio():
    estado = RecepcaoFalsa()
    consultar(estado, httpx.Response(404))
    assert estado.erro and estado.status_operacional == ""
    assert "precisa estar publicado" in estado.mensagem


def test_erro_publico_do_servidor_nao_confirma():
    estado = RecepcaoFalsa()
    alterar(estado, httpx.Response(400, json={"message": "Alteração recusada."}))
    assert estado.erro and estado.mensagem == "Alteração recusada."


def test_timeout_nao_repete_e_nao_presume_status_anterior():
    estado = RecepcaoFalsa()
    estado.status_operacional = "DISPONIVEL"
    http, _ = alterar(estado, httpx.ReadTimeout("simulado"))
    assert http.call_count == 1 and estado.erro and not estado.ocupado
    assert estado.status_operacional == "" and "não confirmado" in estado.mensagem


def test_falha_de_rede_nao_repete():
    estado = RecepcaoFalsa()
    http, _ = alterar(estado, httpx.ConnectError("simulado"))
    assert http.call_count == 1 and estado.erro and not estado.ocupado
    assert "atualize" in estado.mensagem


def test_respostas_inesperadas_nao_confirmam_nem_repetem():
    respostas = [
        httpx.Response(200, text="<html>erro</html>"), httpx.Response(200, json=[]),
        httpx.Response(200, json={}), httpx.Response(200, json={"status": None}),
        httpx.Response(200, json={"status": True}), httpx.Response(200, json={"status": "EM_ATENDIMENTO"}),
        httpx.Response(200, json={"status": "AUSENTE"}), httpx.Response(202, json={"status": "PAUSA"}),
        httpx.Response(500, json={"message": "detalhe interno SQL"}),
    ]
    for resposta in respostas:
        estado = RecepcaoFalsa()
        estado.status_operacional = "DISPONIVEL"
        http, _ = alterar(estado, resposta)
        assert http.call_count == 1 and estado.erro and estado.status_operacional == ""
        assert "Status atualizado" not in estado.mensagem and "SQL" not in estado.mensagem


def test_ambiente_ausente_nao_chama_http(monkeypatch):
    monkeypatch.setenv("XANO_AUTH_API_URL", "")
    estado = RecepcaoFalsa()
    http, _ = consultar(estado, httpx.Response(500))
    http.assert_not_called()
    assert estado.erro and "não está configurada" in estado.mensagem


def test_processamento_bloqueia_reentrada_de_consulta_e_alteracao():
    estado = RecepcaoFalsa()
    estado.ocupado = True
    with patch("ps_fila_prioritaria.api.httpx.request") as http:
        asyncio.run(concluir(estado.carregar()))
        asyncio.run(concluir(estado.definir_status("PAUSA")))
    http.assert_not_called()


async def conferir_carregamento_publicado():
    estado = RecepcaoFalsa()
    evento = estado.definir_status("PAUSA")
    assert await anext(evento) is None and estado.ocupado
    assert await concluir(estado.definir_status("AUSENTE")) is None
    assert await concluir(estado.carregar()) is None
    await evento.aclose()
    assert not estado.ocupado


def test_guardiao_ja_esta_ativo_durante_requisicao():
    asyncio.run(conferir_carregamento_publicado())
    estado = RecepcaoFalsa()
    def resposta(*args, **kwargs):
        assert estado.ocupado
        return httpx.Response(200, json={"status": "PAUSA"})
    alterar(estado, resposta)
    assert not estado.ocupado


def test_consulta_invalida_nao_reutiliza_status_de_sessao_anterior():
    estado = RecepcaoFalsa()
    estado.status_operacional = "PAUSA"
    consultar(estado, httpx.Response(200, json={}))
    assert estado.erro and estado.status_operacional == ""


def test_seletor_nao_oferece_em_atendimento_e_nao_envia_ao_renderizar():
    painel = seletor_status_recepcao()
    def visitar(componente):
        yield componente
        for filho in componente.children:
            yield from visitar(filho)
    itens = [c for c in visitar(painel) if c.tag == "Select.Item"]
    assert {str(c.value).strip(chr(34)) for c in itens} == set(STATUS_RECEPCAO)
    assert "EM_ATENDIMENTO" not in str(painel)
    seletores = [c for c in visitar(painel) if c.tag == "Select.Root"]
    assert len(seletores) == 1 and "ocupado" in str(seletores[0].disabled)


def test_pagina_recepcao_preserva_protecao_de_perfil():
    with patch("ps_fila_prioritaria.paginas.plantao.protegido", side_effect=lambda perfil, pagina: (perfil, pagina)):
        perfil, _ = area_recepcao()
    assert perfil == "RECEPCAO_TRIAGEM"


def test_contrato_get_status_e_apenas_leitura_da_propria_sessao():
    codigo = (RAIZ / "backend/xano/api/autenticacao/me_status_get.xs").read_text(encoding="utf-8")
    assert 'query "me/status" verb=GET' in codigo and 'auth = "usuario"' in codigo
    assert 'perfis_permitidos: ["MEDICO", "RECEPCAO_TRIAGEM"]' in codigo
    assert "$db.sessao.usuario_id == $usuario.id" in codigo
    assert "$db.sessao.logout_em == null" in codigo and "$db.sessao.expira_em > now" in codigo
    assert 'sort = {login_em: "desc"}' in codigo and 'error_type = "unauthorized"' in codigo
    for escrita in ("db.add ", "db.edit ", "db.patch ", "db.del ", "usuario_id?"):
        assert escrita not in codigo


def test_contrato_status_manual_recusa_admin_e_estado_automatico():
    codigo = (RAIZ / "backend/xano/api/autenticacao/me_status_patch.xs").read_text(encoding="utf-8")
    assert 'values = ["DISPONIVEL", "PAUSA", "AUSENTE"]' in codigo
    assert 'perfis_permitidos: ["MEDICO", "RECEPCAO_TRIAGEM"]' in codigo
    assert "EM_ATENDIMENTO" not in codigo


def test_contrato_medico_inicia_indisponivel_recepcao_disponivel():
    codigo = (RAIZ / "backend/xano/api/autenticacao/auth_login_verificar_post.xs").read_text(encoding="utf-8")
    assert 'status_operacional: ($usuario.perfil == "RECEPCAO_TRIAGEM") ? "DISPONIVEL" : null' in codigo


def test_contrato_chamada_e_comparecimento_preservam_status_automatico():
    chamada = (RAIZ / "backend/xano/function/fila/chamar_proximo.xs").read_text(encoding="utf-8")
    cobertura = (RAIZ / "backend/xano/function/fila/avaliar_cobertura.xs").read_text(encoding="utf-8")
    acao = (RAIZ / "backend/xano/function/fila/agir_chamada.xs").read_text(encoding="utf-8")
    assert "MEDICO_INDISPONIVEL" in chamada and "DISPONIVEL" in chamada
    assert "DISPONIVEL" in cobertura and "EM_ATENDIMENTO" in cobertura
    assert 'if ($input.acao == "COMPARECEU")' in acao
    assert 'data = {status_operacional: "EM_ATENDIMENTO"}' in acao


def test_medico_em_pausa_recusado_sem_sucesso_ou_repeticao():
    estado = MedicoFalso()
    estado.status_operacional, estado.apto = "PAUSA", False
    with patch("ps_fila_prioritaria.api.requisitar", return_value=Resposta({"message": "MEDICO_INDISPONIVEL"}, 400)) as http:
        asyncio.run(estado.chamar())
    assert estado.erro and "não está disponível" in estado.mensagem
    assert http.call_count == 1


def test_comparecimento_em_pausa_atualiza_status_pelo_retorno_do_servidor():
    estado = MedicoFalso()
    estado.status_operacional, estado.tem_ficha, estado.ficha_atual = "PAUSA", True, {"id": 42}
    with patch("ps_fila_prioritaria.api.requisitar", side_effect=[
        Resposta({"status": "ATENDIDO"}),
        Resposta({"medico": {"apto": True, "status": "EM_ATENDIMENTO"}, "filas": [], "ficha_atual": None}),
    ]) as http:
        asyncio.run(estado.compareceu())
    assert estado.status_operacional == "EM_ATENDIMENTO" and http.call_count == 2


def test_proxima_chamada_confirmada_restaura_disponivel():
    estado = MedicoFalso()
    estado.status_operacional = "EM_ATENDIMENTO"
    with patch("ps_fila_prioritaria.api.requisitar", side_effect=[
        Resposta({"fila_vazia": False}),
        Resposta({"medico": {"apto": True, "status": "DISPONIVEL"}, "filas": [], "ficha_atual": {"id": 42}}),
    ]):
        asyncio.run(estado.chamar())
    assert estado.status_operacional == "DISPONIVEL"

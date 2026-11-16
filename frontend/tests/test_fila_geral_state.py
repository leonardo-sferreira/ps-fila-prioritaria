"""HTTP simulado e contratos XS estáticos; não executa o engine nem usa o Xano."""
import asyncio
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.equipe import EquipeState
from ps_fila_prioritaria.estados import fila_geral as f

ROOT = Path(__file__).resolve().parents[2]
XS = ROOT / "backend/xano/api/cadastros/admin_fila_geral_get.xs"


class Estado:
    _consultar = f.FilaGeralState._consultar
    entrar = f.FilaGeralState.entrar.fn
    carregar = f.FilaGeralState.carregar.fn
    filtrar = f.FilaGeralState.filtrar.fn
    consultar_se_visivel = f.FilaGeralState.consultar_se_visivel.fn
    sair = f.FilaGeralState.sair.fn

    def __init__(self):
        self.itens, self.especialidades = [], []
        self.especialidade_id, self.cor, self.status = "0", "TODAS", "TODOS"
        self.carregando, self.ativa, self.erro, self.desatualizado = False, True, False, False
        self.mensagem = self.aviso = self.atualizado_em = ""
        self.router = SimpleNamespace(url=SimpleNamespace(path=f.ROTA))
        self.auth = SimpleNamespace(token="simulado", perfil="ADMINISTRADOR")
        def encerrar(_):
            self.auth.token, self.auth.perfil = "", ""
        self.auth._encerrar_sessao_local = encerrar
        self.consultas_equipe = 0
        async def equipe():
            self.consultas_equipe += 1
        self.equipe = SimpleNamespace(carregar=equipe, mensagem="")

    async def get_state(self, classe):
        return self.auth if classe is AuthState else self.equipe if classe is EquipeState else None


@pytest.fixture(autouse=True)
def http_apenas_simulado(monkeypatch):
    monkeypatch.setenv("XANO_CADASTROS_API_URL", "https://cadastros.test")
    def proibido(*args, **kwargs):
        raise AssertionError("HTTP real proibido")
    monkeypatch.setattr("ps_fila_prioritaria.api.httpx.request", proibido)
    monkeypatch.setattr(f.rx, "redirect", lambda rota: rota)


async def concluir(eventos):
    retorno = None
    async for evento in eventos:
        if evento is not None:
            retorno = evento
    return retorno


def ficha(id=1, status="AGUARDANDO", **campos):
    row = dict(id=id, status=status, senha="A-ESP-001", cor="AMARELA",
               condicao_prioritaria="NENHUMA", especialidade_id=7, especialidade="Especialidade",
               chegada_em=1794780000000, espera_minutos=5, posicao=1, consultado_em=1794780300000, avisos=[], medico=None, tentativa=None)
    row.update(campos)
    return row


def corpo(linhas=None):
    return [ficha()] if linhas is None else linhas


def consultar(estado, resposta, eventos=None):
    with patch("ps_fila_prioritaria.api.httpx.request", side_effect=[resposta]) as http:
        retorno = asyncio.run(concluir(eventos if eventos is not None else estado.carregar()))
    return http, retorno


def test_get_admin_usa_token_existente_e_grupo_cadastros():
    estado = Estado()
    http, _ = consultar(estado, httpx.Response(200, json=corpo()))
    assert http.call_args.args == ("GET", "https://cadastros.test/admin/fila-geral")
    assert http.call_args.kwargs["headers"] == {"Authorization": "Bearer simulado"}
    assert estado.itens[0]["id"] == "1" and not estado.erro
    assert estado.consultas_equipe == 1


def test_resposta_vazia_confirmada():
    estado = Estado()
    consultar(estado, httpx.Response(200, json=corpo([])))
    assert estado.itens == [] and not estado.erro and estado.atualizado_em


def test_tres_status_nao_finalizados_e_campos_de_chamado():
    rows = [ficha(1, "EM_TRIAGEM"), ficha(2), ficha(3, "CHAMADO", medico="Médico de teste", tentativa=2)]
    itens, _, _, _ = f.apresentar(corpo(rows))
    assert [i["status"] for i in itens] == ["Em triagem", "Aguardando", "Chamado"]
    assert itens[2]["tentativa"] == "2" and itens[2]["medico"] == "Médico de teste"
    assert itens[0]["medico"] == "—"


def test_finalizados_recebidos_indevidamente_sao_recusados():
    for status in ("ATENDIDO", "DESISTENCIA", "CANCELADO"):
        with pytest.raises(ValueError):
            f.apresentar(corpo([ficha(1, status)]))


def test_filtros_enviados_ao_servidor():
    estado = Estado()
    estado.especialidade_id, estado.cor, estado.status = "7", "VERMELHA", "AGUARDANDO"
    http, _ = consultar(estado, httpx.Response(200, json=corpo()))
    assert http.call_args.kwargs["params"] == {"especialidade_id": 7, "cor": "VERMELHA", "status": "AGUARDANDO"}
    assert f.parametros_consulta("0", "TODAS", "TODOS") == {}


def test_filtros_invalidos_nao_consultam():
    estado = Estado()
    for campo, valor in (("cor", "VERDE"), ("status", "ATENDIDO"), ("especialidade_id", "-1")):
        with patch("ps_fila_prioritaria.api.httpx.request") as http:
            asyncio.run(concluir(estado.filtrar(campo, valor)))
        http.assert_not_called()
        assert estado.erro


def test_troca_de_filtro_nao_exibe_lista_do_filtro_anterior():
    estado = Estado()
    estado.itens = [{"id": "anterior"}]
    _, _ = consultar(estado, httpx.Response(404), estado.filtrar("cor", "AZUL"))
    assert estado.cor == "AZUL" and estado.itens == [] and estado.erro


def test_preserva_ordem_recebida_vermelha_e_ciclo_sem_reordenar_por_chegada():
    # Fixture da resposta: valida apresentação, não execução do algoritmo Xano.
    rows = [ficha(9, cor="VERMELHA", chegada_em=400, posicao=1),
            ficha(3, chegada_em=300, posicao=2),
            ficha(2, chegada_em=200, posicao=3),
            ficha(1, cor="AZUL", chegada_em=100, posicao=4)]
    itens = f.apresentar(corpo(rows))[0]
    assert [i["id"] for i in itens] == ["9", "3", "2", "1"]
    assert [i["ordem"] for i in itens] == ["1", "2", "3", "4"]


def test_condicao_prioritaria_e_reentrada_nao_sao_recalculadas_no_cliente():
    rows = [ficha(2, condicao_prioritaria="IDOSO", posicao=1),
            ficha(1, fila_em=1794781000000, posicao=2)]
    itens = f.apresentar(corpo(rows))[0]
    assert itens[0]["condicao"] == "Idoso" and itens[1]["id"] == "1"


def test_mais_de_vinte_fichas_sem_truncar():
    rows = [ficha(i, posicao=i) for i in range(1, 36)]
    itens = f.apresentar(corpo(rows))[0]
    assert len(itens) == 35 and itens[-1]["ordem"] == "35"


def test_sem_especialidade_ou_catalogo_permanece_sem_posicao_ficticia():
    rows = [ficha(1, especialidade=None, especialidade_id=None, posicao=None),
            ficha(2, especialidade=None, especialidade_id=999, cor=None, posicao=None)]
    itens = f.apresentar(corpo(rows))[0]
    assert len(itens) == 2
    assert itens[0]["especialidade"] == "Sem especialidade"
    assert itens[1]["especialidade"] == "Sem cadastro encontrado"
    assert itens[1]["cor"] == "Sem cor" and itens[1]["ordem"] == "—"


def test_duplicacao_na_resposta_e_recusada():
    with pytest.raises(ValueError):
        f.apresentar(corpo([ficha(1), ficha(1)]))


def test_projecao_no_cliente_nao_guarda_dados_pessoais_extras():
    row = ficha(1, paciente={"nome": "Privado", "cpf": "omitido"}, email="omitido", observacao="Privada")
    itens = f.apresentar(corpo([row]))[0]
    assert not any(k in itens[0] for k in ("paciente", "email", "cpf", "observacao"))
    assert "Privado" not in str(itens)


def test_avisos_de_previsao_invalida_nao_ocultam_fichas():
    itens, _, _, aviso = f.apresentar(corpo([ficha(posicao=None, avisos=["CICLO_FILA_INVALIDO"])]))
    assert len(itens) == 1 and itens[0]["ordem"] == "—" and "inválido" in aviso


def test_sem_token_medico_e_recepcao_nao_enviam_get():
    for token, perfil, rota in (("", "", "/login"), ("simulado", "MEDICO", "/medico"),
                                 ("simulado", "RECEPCAO_TRIAGEM", "/recepcao")):
        estado = Estado()
        estado.auth.token, estado.auth.perfil = token, perfil
        http, retorno = consultar(estado, httpx.Response(500))
        http.assert_not_called()
        assert retorno == rota and not estado.ativa


def test_401_limpa_sessao_e_lista():
    estado = Estado()
    estado.itens = [{"id": "anterior"}]
    _, retorno = consultar(estado, httpx.Response(401))
    assert retorno == "/login" and estado.auth.token == "" and estado.itens == []


def test_403_e_endpoint_nao_publicado():
    for status, texto in ((403, "Acesso negado"), (404, "precisa estar publicado")):
        estado = Estado()
        consultar(estado, httpx.Response(status))
        assert estado.erro and texto in estado.mensagem and estado.itens == []


def test_timeout_e_conexao_sem_repeticao_e_com_aviso_de_dados_antigos():
    for erro in (httpx.ReadTimeout("simulado"), httpx.ConnectError("simulado")):
        estado = Estado()
        estado.itens = [{"id": "anterior"}]
        http, _ = consultar(estado, erro)
        assert http.call_count == 1 and estado.erro and estado.desatualizado
        assert estado.itens == [{"id": "anterior"}] and "Dados anteriores" in estado.mensagem


def test_json_invalido_contagem_incorreta_e_respostas_inesperadas():
    for resposta in (httpx.Response(200, text="não JSON"), httpx.Response(200, json={"fichas": []}),
                     httpx.Response(200, json=corpo([ficha(posicao=True)])), httpx.Response(204),
                     httpx.Response(500, json={"message": "detalhe SQL privado"})):
        estado = Estado()
        consultar(estado, resposta)
        assert estado.erro and not estado.itens and "SQL" not in estado.mensagem


def test_sem_configuracao_nao_envia_http(monkeypatch):
    monkeypatch.setenv("XANO_CADASTROS_API_URL", "")
    estado = Estado()
    http, _ = consultar(estado, httpx.Response(500))
    http.assert_not_called()
    assert estado.erro and "não está configurada" in estado.mensagem


def test_polling_so_na_rota_ativa_e_quando_visivel():
    for ativa, rota, visivel in ((False, f.ROTA, True), (True, "/admin", True), (True, f.ROTA, False)):
        estado = Estado()
        estado.ativa = ativa
        estado.router.url.path = rota
        http, _ = consultar(estado, httpx.Response(500), estado.consultar_se_visivel(visivel))
        http.assert_not_called()
    estado = Estado()
    http, _ = consultar(estado, httpx.Response(200, json=corpo()), estado.consultar_se_visivel(True))
    assert http.call_count == 1


def test_carregamento_publicado_bloqueia_reentrada_e_saida_cancela_consulta():
    async def verificar():
        estado = Estado()
        evento = estado.carregar()
        assert await anext(evento) is None and estado.carregando
        with patch("ps_fila_prioritaria.api.httpx.request") as http:
            await concluir(estado.carregar())
            await concluir(estado.filtrar("cor", "AZUL"))
            estado.sair()
            await concluir(evento)
        http.assert_not_called()
        assert not estado.carregando and not estado.ativa
    asyncio.run(verificar())


def test_pagina_so_leitura_reutiliza_equipe_e_auditoria_sem_edicao():
    from ps_fila_prioritaria.paginas.acompanhamento import pagina_acompanhamento, VISIBILIDADE
    pagina = str(pagina_acompanhamento())
    assert "Editar" not in pagina and "Chamar próximo" not in pagina and "Excluir" not in pagina
    assert "document.visibilityState" in VISIBILIDADE and f.ROTA in VISIBILIDADE
    source = (ROOT / "frontend/ps_fila_prioritaria/paginas/acompanhamento.py").read_text(encoding="utf-8")
    assert "interval=10000" in source and "on_unmount=st.sair" in source
    assert "equipe_agora()" in source and 'href="/admin/auditoria"' in source


def test_contrato_auth_admin_ativo_e_somente_identidade_autenticada():
    code = XS.read_text(encoding="utf-8")
    assert 'auth = "usuario"' in code and 'perfis_permitidos: ["ADMINISTRADOR"]' in code
    assert "usuario_id: $auth.id" in code
    auth = (ROOT / "backend/xano/function/auth/verificar_acesso.xs").read_text(encoding="utf-8")
    assert "$usuario.ativo" in auth and '"accessdenied"' in auth


def test_contrato_apenas_estados_nao_finalizados_e_filtros_validados():
    code = XS.read_text(encoding="utf-8")
    assert '$db.ficha_atendimento.status in ["EM_TRIAGEM", "AGUARDANDO", "CHAMADO"]' in code
    assert 'filters=trim|upper' in code and '"COR_INVALIDA"' in code and '"STATUS_INVALIDO"' in code
    assert "$input.especialidade_id >= 0" in code


def test_contrato_selecao_oficial_sem_limite_de_vinte_ou_ordem_global():
    code = XS.read_text(encoding="utf-8")
    assert 'function.run "fila/proxima_ficha"' in code
    assert "foreach ($aguardando)" in code and "value = $escolha.proxima_posicao" in code
    assert 'function.run "fila/prever_fila"' not in code
    assert 'function.run "fila/selecionar_entre_filas"' not in code
    assert "|slice:" not in code


def test_contrato_vermelha_condicao_ciclo_e_reentrada_reutilizados():
    code = (ROOT / "backend/xano/function/fila/proxima_ficha.xs").read_text(encoding="utf-8")
    for parte in ('if ($vermelha)', '$item.condicao_prioritaria', '$item.fila_em ?? $item.chegada_em',
                  '$input.posicao <= $input.amarelas', '$melhor.id', '$cor != "VERMELHA"'):
        assert parte in code


def test_contrato_inclusao_de_seguranca_por_id_e_filtros_apos_previsao():
    code = XS.read_text(encoding="utf-8")
    assert '$ordenadas|find:($$.ficha.id == $ficha.id)' in code and 'if ($incluida == null)' in code
    assert 'ordem_prevista: null' in code
    assert code.index('function.run "fila/proxima_ficha"') < code.index('$input.especialidade_id == 0')


def test_contrato_sem_ciclo_valido_mantem_fichas_sem_inventar_parametros():
    code = XS.read_text(encoding="utf-8")
    assert '"PARAMETROS_NAO_CONFIGURADOS"' in code and '"CICLO_FILA_INVALIDO"' in code
    assert "$posicao <= ($amarelas + $azuis)" in code
    assert 'field_value = "amarelas_por_ciclo"' in code and 'field_value = "azuis_por_ciclo"' in code


def test_contrato_consultas_usuarios_restritas_e_resposta_sem_paciente():
    code = XS.read_text(encoding="utf-8")
    assert 'where = $db.medico.id in $medico_ids' in code
    assert 'where = $db.usuario.id in $usuario_ids' in code
    projection = code.split('value = $lista|push:{', 1)[1].split('\n              }', 1)[0]
    for privado in ("paciente", "cpf", "email", "observacao", "sintomas", "pa_sistolica"):
        assert privado not in projection
    assert '($ficha.status == "CHAMADO") ? $ficha.tentativas_chamada : null' in projection


def test_contrato_grafo_chamado_nao_tem_operacoes_de_escrita():
    files = [XS, ROOT / "backend/xano/function/fila/proxima_ficha.xs",
             ROOT / "backend/xano/function/auth/verificar_acesso.xs"]
    for path in files:
        code = re.sub(r"//[^\n]*", "", path.read_text(encoding="utf-8"))
        assert not re.search(r"\bdb\.(add|edit|patch|del|delete|truncate|transaction)\b", code)


def test_contrato_publicado_lista_posicao_e_metadados_aditivos():
    rows = [ficha(2, posicao=2), ficha(3, "CHAMADO"), ficha(4, especialidade_id=8, posicao=1),
            ficha(1, posicao=1), ficha(5, posicao=None)]
    for row in rows:
        row.pop("consultado_em")
        row.pop("espera_minutos")
    itens, opcoes, _, aviso = f.apresentar(rows)
    assert [i["id"] for i in itens] == ["1", "3", "4", "2", "5"]
    assert itens[0]["espera"] == "—" and itens[-1]["ordem"] == "—"
    assert len(opcoes) == 2 and "vigésima" in aviso
    code = XS.read_text(encoding="utf-8")
    assert "response = $lista" in code and "posicao: $entrada.ordem_prevista" in code
    assert "oportunidade:" in code


def test_filtro_preserva_opcoes_observadas_apos_resposta_vazia():
    estado = Estado()
    consultar(estado, httpx.Response(200, json=corpo()))
    consultar(estado, httpx.Response(200, json=[]), estado.filtrar("cor", "AZUL"))
    assert estado.itens == [] and estado.especialidades == [{"id": "7", "nome": "Especialidade"}]


def test_cor_nula_nao_recebe_posicao_por_igualdade_null_no_seletor():
    code = XS.read_text(encoding="utf-8")
    filtro = code.split("var $restantes {", 1)[1].split("}", 1)[0]
    assert "$aguardando|filter:" in filtro
    assert all(f'$$.prioridade_atual == "{cor}"' in filtro for cor in ("VERMELHA", "AMARELA", "AZUL"))
    assert "if ($incluida == null)" in code and "ordem_prevista: null" in code

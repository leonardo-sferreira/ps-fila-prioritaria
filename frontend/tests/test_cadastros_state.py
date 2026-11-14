"""Estados das telas de cadastro do Administrador (add-cadastros-administrador): corpo enviado, filtros,
formatação de plantões e faixas e tratamento de erro da API. As regras ficam no Xano; aqui só o que é da tela."""

import asyncio
from collections import deque
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from ps_fila_prioritaria.comum import FUSO_BRASILIA
from ps_fila_prioritaria.estados import cadastros as c

REQUISITAR = "ps_fila_prioritaria.api.requisitar"


class Resposta:
    def __init__(self, status_code: int, corpo: object):
        self.status_code = status_code
        self._corpo = corpo

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> object:
        return self._corpo


class AuthFalso:
    token = "token-admin"
    encerrada = False

    def _encerrar_sessao_local(self, mensagem: str = "") -> None:
        self.encerrada = True


def estado_falso(classe: type, **campos: object) -> SimpleNamespace:
    """Objeto com os campos do estado e os métodos reais da classe (event handlers pelo .fn)."""
    auth = AuthFalso()
    base = {"itens": [], "filtro": "ATIVOS", "busca": "", "carregando": False, "mensagem": "", "erro": False,
            "dialogo_aberto": False, "editando_id": 0, "form": {}, "erro_form": "", "salvando": False,
            "opcoes_especialidades": [], "opcoes_salas": []}
    estado = SimpleNamespace(**{**base, **campos}, auth=auth)

    async def get_state(_):
        return auth

    estado.get_state = get_state
    for constante in ("CAMINHO", "CAMPOS_BUSCA"):
        if hasattr(classe, constante):
            setattr(estado, constante, getattr(classe, constante))
    for nome in ("_corpo", "_form_vazio", "_form_de", "_carregar_extras", "_carregar_especialidades"):
        if hasattr(classe, nome):
            setattr(estado, nome, getattr(classe, nome).__get__(estado))
    return estado


def _api(*respostas: Resposta):
    fila = deque(respostas)
    return patch(REQUISITAR, side_effect=lambda *a, **k: fila.popleft())


# ---------- Corpo enviado ----------

def test_especialidade_nova_envia_sigla_em_maiusculas_e_edicao_nao_envia_sigla() -> None:
    nova = estado_falso(c.EspecialidadesState, form={"nome": "Dermatologia", "sigla": "der", "descricao": ""})
    assert nova._corpo() == {"nome": "Dermatologia", "descricao": None, "sigla": "DER"}
    edicao = estado_falso(c.EspecialidadesState, editando_id=7, form={"nome": "Dermato", "sigla": "DER", "descricao": "Pele"})
    assert edicao._corpo() == {"nome": "Dermato", "descricao": "Pele"}


def test_medico_novo_envia_senha_e_edicao_nao() -> None:
    form = {"nome": "Ana Lima", "email": "ana@ps.com", "senha": "segredo123", "crm": "12345-SP", "especialidade_ids": [1, 3], "sala_id": "4"}
    novo = estado_falso(c.MedicosState, form=form)
    assert novo._corpo() == {"nome": "Ana Lima", "email": "ana@ps.com", "crm": "12345-SP", "especialidade_ids": [1, 3], "sala_id": 4, "senha": "segredo123"}
    edicao = estado_falso(c.MedicosState, editando_id=2, form={**form, "sala_id": "0"})
    corpo = edicao._corpo()
    assert "senha" not in corpo and corpo["sala_id"] == 0  # 0 = sem sala (o Xano trata 0 como vazio)
    sem_sala = estado_falso(c.MedicosState, form={**form, "sala_id": ""})
    assert sem_sala._corpo()["sala_id"] is None


def test_recepcao_especialidade_de_referencia_opcional() -> None:
    estado = estado_falso(c.RecepcaoState, form={"nome": "Bia", "email": "bia@ps.com", "senha": "12345678", "cpf": "529.982.247-25", "especialidade_referencia_id": ""})
    assert estado._corpo()["especialidade_referencia_id"] is None
    estado.form["especialidade_referencia_id"] = "2"
    assert estado._corpo()["especialidade_referencia_id"] == 2


def test_sintoma_converte_pontuacao_e_mantem_ordem_dos_destinos() -> None:
    estado = estado_falso(c.SintomasState, form={"nome": "Palpitação", "descricao": "", "grupo": "CARDIOVASCULAR", "pontuacao": "2", "especialidade_ids": [1, 2]})
    assert estado._corpo() == {"nome": "Palpitação", "descricao": None, "grupo": "CARDIOVASCULAR", "pontuacao": 2, "especialidade_ids": [1, 2]}


def test_marcar_e_desmarcar_especialidade_preserva_a_ordem() -> None:
    estado = estado_falso(c.SintomasState, form={"especialidade_ids": [3]})
    c.SintomasState.alternar_especialidade.fn(estado, 1)
    assert estado.form["especialidade_ids"] == [3, 1]
    c.SintomasState.alternar_especialidade.fn(estado, 3)
    assert estado.form["especialidade_ids"] == [1]


def test_ordem_dos_destinos_em_texto() -> None:
    ordem = c.SintomasState.computed_vars["ordem_destinos"]._fget
    estado = SimpleNamespace(opcoes_especialidades=[{"id": 1, "nome": "Cardiologia"}, {"id": 2, "nome": "Clínica Geral"}],
                             form={"especialidade_ids": [2, 1]})
    assert ordem(estado) == "Clínica Geral → Cardiologia"
    estado.form = {"especialidade_ids": []}
    assert ordem(estado) == "Nenhum destino marcado"


# ---------- Lista ----------

def test_filtro_de_situacao_e_busca_sem_acento() -> None:
    itens = [{"nome": "Clínica Geral", "sigla": "CLI", "ativo": True}, {"nome": "Ortopedia", "sigla": "ORT", "ativo": False}]
    assert [i["nome"] for i in c.filtrar(itens, "ATIVOS", "", ("nome",))] == ["Clínica Geral"]
    assert [i["nome"] for i in c.filtrar(itens, "INATIVOS", "", ("nome",))] == ["Ortopedia"]
    assert len(c.filtrar(itens, "TODOS", "", ("nome",))) == 2
    assert [i["nome"] for i in c.filtrar(itens, "TODOS", "clinica", ("nome",))] == ["Clínica Geral"]
    assert [i["nome"] for i in c.filtrar(itens, "TODOS", "ort", ("nome", "sigla"))] == ["Ortopedia"]


def test_salvar_novo_usa_post_e_edicao_usa_patch_no_caminho_do_item() -> None:
    estado = estado_falso(c.SalasState, form={"nome": "Consultório 3", "descricao": ""}, dialogo_aberto=True)
    estado.carregar = lambda: _nada()
    with _api(Resposta(200, {"id": 9})) as requisitar:
        asyncio.run(c.SalasState.salvar.fn(estado))
    assert requisitar.call_args.args[:3] == ("POST", "XANO_CADASTROS_API_URL", "/salas")
    assert not estado.dialogo_aberto and estado.mensagem == "Alteração salva."
    estado.editando_id, estado.dialogo_aberto = 9, True
    with _api(Resposta(200, {"id": 9})) as requisitar:
        asyncio.run(c.SalasState.salvar.fn(estado))
    assert requisitar.call_args.args[:3] == ("PATCH", "XANO_CADASTROS_API_URL", "/salas/9")


async def _nada() -> None:
    return None


def test_erro_ao_salvar_fica_no_dialogo() -> None:
    estado = estado_falso(c.MedicosState, form={"nome": "Ana", "email": "ana@ps.com", "senha": "x", "crm": "1", "especialidade_ids": [], "sala_id": ""}, dialogo_aberto=True)
    with _api(Resposta(400, {"message": "Este e-mail já é usado por outro usuário."})):
        asyncio.run(c.MedicosState.salvar.fn(estado))
    assert estado.dialogo_aberto and estado.erro_form == "Este e-mail já é usado por outro usuário."


def test_desativar_com_codigo_traduzido() -> None:
    estado = estado_falso(c.EspecialidadesState)
    with _api(Resposta(400, {"message": "ESPECIALIDADE_COM_FICHAS"})) as requisitar:
        asyncio.run(c.EspecialidadesState.alternar_ativo.fn(estado, 5, False))
    assert requisitar.call_args.args[2] == "/especialidades/5/ativo" and requisitar.call_args.kwargs["json"] == {"ativo": False}
    assert estado.erro and "fichas aguardando" in estado.mensagem


def test_sem_conexao_e_sessao_expirada() -> None:
    estado = estado_falso(c.SalasState)
    with patch(REQUISITAR, side_effect=httpx.ConnectError("x")):
        asyncio.run(c.SalasState.carregar.fn(estado))
    assert estado.erro and "conectar" in estado.mensagem
    with _api(Resposta(401, {"message": "Invalid token."})):
        asyncio.run(c.SalasState.carregar.fn(estado))
    assert estado.auth.encerrada


# ---------- Plantões ----------

def ms(dia: int, hora: int, minuto: int = 0) -> int:
    return int(datetime(2026, 11, dia, hora, minuto, tzinfo=FUSO_BRASILIA).timestamp() * 1000)


def test_linha_de_plantao_diurno_e_noturno() -> None:
    diurno = c.linha_plantao({"id": 1, "medico_id": 2, "medico": "Ana", "sala": None, "especialidades": ["CAR", "CLI"],
                              "inicio": ms(11, 7), "fim": ms(11, 19), "iniciado": True, "em_andamento": True})
    assert diurno["horario"] == "07:00 – 19:00" and diurno["situacao"] == "Em andamento" and diurno["sala"] == "—"
    assert diurno["especialidades"] == "CAR · CLI" and diurno["data"] == "2026-11-11"
    noturno = c.linha_plantao({"id": 2, "inicio": ms(11, 19), "fim": ms(12, 7), "iniciado": False})
    assert noturno["horario"] == "19:00 – 07:00 (+1 dia)" and noturno["situacao"] == "Agendado"
    encerrado = c.linha_plantao({"id": 3, "inicio": ms(10, 7), "fim": ms(10, 19), "iniciado": True, "encerrado_em": ms(10, 18)})
    assert encerrado["situacao"] == "Encerrado"


def test_novo_plantao_exige_medico() -> None:
    estado = SimpleNamespace(salvando=False, editando_id=0, form={"medico_id": "", "data": "2026-11-11", "hora_inicio": "07:00", "hora_fim": "19:00"}, erro_form="")
    asyncio.run(c.PlantoesState.salvar.fn(estado))
    assert estado.erro_form == "Escolha o médico."


def test_plantao_sobreposto_mostra_a_mensagem() -> None:
    estado = estado_falso(c.PlantoesState, data="2026-11-11", form={"medico_id": "2", "data": "2026-11-11", "hora_inicio": "18:00", "hora_fim": "23:00"})
    with _api(Resposta(400, {"message": "PLANTAO_SOBREPOSTO"})) as requisitar:
        asyncio.run(c.PlantoesState.salvar.fn(estado))
    assert requisitar.call_args.kwargs["json"] == {"data": "2026-11-11", "hora_inicio": "18:00", "hora_fim": "23:00", "medico_id": 2}
    assert "sobrepõe" in estado.erro_form



def test_escala_12x36_exige_data_final() -> None:
    estado = SimpleNamespace(salvando=False, editando_id=0, erro_form="",
                             form={"medico_id": "2", "data": "2026-11-11", "hora_inicio": "07:00", "hora_fim": "19:00", "repetir": True, "data_fim": ""})
    asyncio.run(c.PlantoesState.salvar.fn(estado))
    assert estado.erro_form == "Informe até quando vai a escala."


def test_escala_12x36_envia_data_final() -> None:
    form = {"medico_id": "2", "data": "2026-11-11", "hora_inicio": "07:00", "hora_fim": "19:00", "repetir": True, "data_fim": "2026-11-30"}
    estado = estado_falso(c.PlantoesState, data="2026-11-11", form=form)
    with _api(Resposta(400, {"message": "PLANTAO_SOBREPOSTO"})) as requisitar:
        asyncio.run(c.PlantoesState.salvar.fn(estado))
    assert requisitar.call_args.kwargs["json"]["data_fim"] == "2026-11-30"


def test_plantao_unico_nao_envia_data_final() -> None:
    form = {"medico_id": "2", "data": "2026-11-11", "hora_inicio": "07:00", "hora_fim": "19:00", "repetir": False, "data_fim": "2026-11-30"}
    estado = estado_falso(c.PlantoesState, data="2026-11-11", form=form)
    with _api(Resposta(400, {"message": "PLANTAO_SOBREPOSTO"})) as requisitar:
        asyncio.run(c.PlantoesState.salvar.fn(estado))
    assert "data_fim" not in requisitar.call_args.kwargs["json"]

# ---------- Parâmetros e faixas ----------

def test_linha_de_parametro_com_limites() -> None:
    linha = c.linha_parametro({"chave": "HORAS_EXPIRACAO", "valor": "24", "rotulo": "Prazo", "minimo": 6, "maximo": 168, "unidade": "horas", "editavel": True, "tipo": "INTEIRO"})
    assert linha["limites"] == "6 a 168 horas" and linha["edicao"] == "24"
    padrao = c.linha_parametro({"chave": "ESPECIALIDADE_PADRAO", "valor": "2", "tipo": "ESPECIALIDADE", "editavel": True})
    assert padrao["limites"] == "" and padrao["tipo"] == "ESPECIALIDADE"


def test_parametro_nao_numerico_nem_chama_a_api() -> None:
    estado = SimpleNamespace(parametros=[{"chave": "HORAS_EXPIRACAO", "edicao": "vinte"}], erro=False, mensagem="")
    with patch(REQUISITAR) as requisitar:
        asyncio.run(c.ParametrosState.salvar_parametro.fn(estado, "HORAS_EXPIRACAO"))
    requisitar.assert_not_called()
    assert estado.erro and estado.mensagem == "Informe um número inteiro."


def test_set_valor_muda_so_a_linha_do_parametro() -> None:
    estado = SimpleNamespace(parametros=[{"chave": "A", "edicao": "1"}, {"chave": "B", "edicao": "2"}])
    c.ParametrosState.set_valor.fn(estado, "B", "5")
    assert [p["edicao"] for p in estado.parametros] == ["1", "5"]


def test_linha_de_faixa() -> None:
    assert c.linha_faixa({"id": 1, "parametro": "SPO2", "minimo": 96, "maximo": None, "pontos": 0})["intervalo"] == "≥ 96"
    assert c.linha_faixa({"id": 2, "parametro": "PA_SISTOLICA", "minimo": None, "maximo": 90, "pontos": 3})["intervalo"] == "≤ 90"
    temperatura = c.linha_faixa({"id": 3, "parametro": "TEMPERATURA", "minimo": 36.1, "maximo": 38.0, "pontos": 0})
    assert temperatura["intervalo"] == "36,1 a 38" and temperatura["sinal"] == "Temperatura (°C)"
    glicemia = c.linha_faixa({"id": 4, "parametro": "GLICEMIA", "minimo": None, "maximo": 53, "pontos": 3, "condicao_gravidade": True})
    assert glicemia["condicao"] == "com sinais de gravidade"


def test_faixa_com_limite_nao_numerico() -> None:
    estado = SimpleNamespace(faixa_form={"id": 1, "minimo": "abc", "maximo": "", "pontos": "1"}, erro_faixa="")
    with patch(REQUISITAR) as requisitar:
        asyncio.run(c.ParametrosState.salvar_faixa.fn(estado))
    requisitar.assert_not_called()
    assert "números" in estado.erro_faixa


def test_faixa_envia_limite_vazio_como_extremo_aberto() -> None:
    estado = estado_falso(c.ParametrosState, faixa_form={"id": 7, "minimo": "95", "maximo": "", "pontos": "0"}, faixa_aberta=True, erro_faixa="")
    estado.carregar = lambda: _nada()
    with _api(Resposta(200, {"id": 7})) as requisitar:
        asyncio.run(c.ParametrosState.salvar_faixa.fn(estado))
    assert requisitar.call_args.args[2] == "/faixas/7"
    assert requisitar.call_args.kwargs["json"] == {"minimo": 95.0, "maximo": None, "pontos": 0}
    assert not estado.faixa_aberta

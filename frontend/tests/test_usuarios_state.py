"""Tela de usuários (add-autenticacao-perfis, D9/D14): filtros, corpo da troca de perfil e erros da API.
As regras (próprio usuário, último administrador, médico com ficha chamada) ficam no Xano."""

import asyncio
from collections import deque
from unittest.mock import patch

from ps_fila_prioritaria.comum import MENSAGENS_ERRO_API
from ps_fila_prioritaria.estados import usuarios as u
from tests.test_cadastros_state import REQUISITAR, Resposta, estado_falso

USUARIOS = [
    {"id": 1, "nome": "Ana Admin", "email": "ana@ps.com.br", "perfil": "ADMINISTRADOR", "ativo": True, "proprio": True},
    {"id": 2, "nome": "Bruno Médico", "email": "bruno@ps.com.br", "perfil": "MEDICO", "ativo": True, "proprio": False, "medico_id": 5},
    {"id": 3, "nome": "Carla Recepção", "email": "carla@ps.com.br", "perfil": "RECEPCAO_TRIAGEM", "ativo": False, "proprio": False},
]


def _estado(**campos):
    padrao = {"filtro_perfil": "TODOS", "troca_aberta": False, "troca_usuario": {}, "erro_troca": ""}
    estado = estado_falso(u.UsuariosState, **{**padrao, **campos})
    estado.carregar = lambda: _nada()
    return estado


async def _nada():
    return None


def test_linha_usuario_marca_admin_e_rota_do_cadastro():
    linhas = [u.linha_usuario(x) for x in USUARIOS]
    assert [l["perfil_nome"] for l in linhas] == ["Administrador", "Médico", "Recepção/Triagem"]
    assert [l["admin"] for l in linhas] == [True, False, False]
    assert [l["rota_cadastro"] for l in linhas] == ["", "/admin/medicos", "/admin/recepcao"]


def test_filtro_por_perfil_situacao_e_busca():
    assert [x["id"] for x in u.filtrar_usuarios(USUARIOS, "TODOS", "", "TODOS")] == [1, 2, 3]
    assert [x["id"] for x in u.filtrar_usuarios(USUARIOS, "TODOS", "", "MEDICO")] == [2]
    assert [x["id"] for x in u.filtrar_usuarios(USUARIOS, "ATIVOS", "", "TODOS")] == [1, 2]
    assert [x["id"] for x in u.filtrar_usuarios(USUARIOS, "TODOS", "recepcao", "TODOS")] == [3]
    assert [x["id"] for x in u.filtrar_usuarios(USUARIOS, "TODOS", "carla@", "MEDICO")] == []


def test_corpo_troca_para_medico_leva_crm_especialidades_e_sala():
    form = {"perfil": "MEDICO", "crm": "12345-SP", "especialidade_ids": [3, 1], "sala_id": "4", "cpf": "ignorado"}
    assert u.corpo_troca(form) == {"perfil": "MEDICO", "crm": "12345-SP", "especialidade_ids": [3, 1], "sala_id": 4}
    assert u.corpo_troca({**form, "sala_id": "0"})["sala_id"] is None


def test_corpo_troca_para_recepcao_leva_cpf_e_referencia_opcional():
    form = {"perfil": "RECEPCAO_TRIAGEM", "cpf": "123.456.789-09", "especialidade_referencia_id": "", "crm": "ignorado"}
    assert u.corpo_troca(form) == {"perfil": "RECEPCAO_TRIAGEM", "cpf": "123.456.789-09", "especialidade_referencia_id": None}
    assert u.corpo_troca({**form, "especialidade_referencia_id": "2"})["especialidade_referencia_id"] == 2


def test_corpo_troca_para_admin_leva_so_o_perfil():
    assert u.corpo_troca({"perfil": "ADMINISTRADOR", "crm": "x", "cpf": "y"}) == {"perfil": "ADMINISTRADOR"}


def test_criar_admin_envia_senha_e_edicao_nao():
    estado = _estado(form={"nome": "Nova", "email": "nova@ps.com.br", "senha": "12345678"})
    assert u.UsuariosState._corpo(estado) == {"nome": "Nova", "email": "nova@ps.com.br", "senha": "12345678"}
    estado.editando_id = 9
    assert u.UsuariosState._corpo(estado) == {"nome": "Nova", "email": "nova@ps.com.br"}


def test_abrir_troca_escolhe_outro_perfil_e_limpa_dados():
    estado = _estado(form={"crm": "velho"})
    u.UsuariosState.abrir_troca.fn(estado, USUARIOS[1])
    assert estado.troca_aberta and estado.troca_usuario["id"] == 2
    assert estado.form["perfil"] != "MEDICO" and estado.form["crm"] == ""


def test_trocar_perfil_envia_patch_e_fecha():
    estado = _estado(troca_aberta=True, troca_usuario={"id": 3}, form={"perfil": "ADMINISTRADOR"})
    chamadas = []

    def requisitar(metodo, _variavel, caminho, **kw):
        chamadas.append((metodo, caminho, kw.get("json")))
        return Resposta(200, {"id": 3, "perfil": "ADMINISTRADOR"})

    with patch(REQUISITAR, side_effect=requisitar):
        asyncio.run(u.UsuariosState.trocar_perfil.fn(estado))
    assert chamadas == [("PATCH", "/usuarios/3/perfil", {"perfil": "ADMINISTRADOR"})]
    assert not estado.troca_aberta and not estado.erro and "Administrador" in estado.mensagem


def test_trocar_perfil_mostra_erro_do_ultimo_admin_e_mantem_dialogo():
    estado = _estado(troca_aberta=True, troca_usuario={"id": 4}, form={"perfil": "MEDICO"})
    respostas = deque([Resposta(400, {"message": "ULTIMO_ADMINISTRADOR"})])
    with patch(REQUISITAR, side_effect=lambda *a, **k: respostas.popleft()):
        asyncio.run(u.UsuariosState.trocar_perfil.fn(estado))
    assert estado.troca_aberta
    assert estado.erro_troca == MENSAGENS_ERRO_API["ULTIMO_ADMINISTRADOR"]


def test_mensagens_das_regras_existem():
    for codigo in ("ULTIMO_ADMINISTRADOR", "PROPRIO_PERFIL", "USUARIO_EDITADO_NOS_CADASTROS", "MEDICO_COM_FICHA_CHAMADA"):
        assert codigo in MENSAGENS_ERRO_API

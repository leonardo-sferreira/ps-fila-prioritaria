"""Regressões de estado da identificação de Paciente."""

from collections import deque
import unittest
from unittest.mock import patch

from ps_fila_prioritaria.ps_fila_prioritaria import ARQUIVO_ENV, PacienteState, carregar_variaveis_ambiente


class Resposta:
    def __init__(self, status_code: int, corpo: object):
        self.status_code = status_code
        self._corpo = corpo

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> object:
        return self._corpo


class EstadoFalso:
    """Permite testar os handlers sem uma sessão Reflex em execução."""

    _resetar_paciente_atual = PacienteState._resetar_paciente_atual
    _carregar_paciente = PacienteState._carregar_paciente
    buscar = PacienteState.buscar.fn
    cadastrar = PacienteState.cadastrar.fn
    atualizar = PacienteState.atualizar.fn
    set_telefone = PacienteState.set_telefone.fn
    continuar_atendimento = PacienteState.continuar_atendimento.fn

    def __init__(self, cpf: str = "") -> None:
        self.cpf_busca = cpf
        self.cpf = ""
        self.nome = ""
        self.data_nascimento = ""
        self.telefone = ""
        self.paciente_id = 0
        self.paciente_encontrado = False
        self.exibir_cadastro = False
        self.mensagem = ""
        self.erro = False
        self.alterado = None
        self.telefone_alterado = False
        self.abrindo_ficha = False

    def _url(self, caminho: str) -> str:
        return f"https://xano.test{caminho}"


PACIENTE_A = {
    "id": 1,
    "cpf": "11111111111",
    "nome": "Paciente A",
    "data_nascimento": "1980-01-01",
    "telefone": "11999999999",
}
PACIENTE_B = {
    "id": 2,
    "cpf": "22222222222",
    "nome": "Paciente B",
    "data_nascimento": "1990-02-02",
    "telefone": "11888888888",
}


def _assert_cadastro_vazio(estado: EstadoFalso, cpf: str) -> None:
    assert estado.cpf_busca == cpf
    assert estado.cpf == cpf
    assert estado.nome == ""
    assert estado.data_nascimento == ""
    assert estado.telefone == ""
    assert estado.paciente_id == 0
    assert not estado.paciente_encontrado
    assert estado.exibir_cadastro
    assert estado.alterado is None


def test_buscas_sequenciais_nao_reaproveitam_dados_do_paciente_anterior() -> None:
    estado = EstadoFalso(PACIENTE_A["cpf"])
    respostas_get = deque([
        Resposta(200, PACIENTE_A),
        Resposta(200, None),
        Resposta(200, PACIENTE_A),
        Resposta(200, None),
    ])

    with patch("ps_fila_prioritaria.ps_fila_prioritaria.httpx.get", side_effect=lambda *args, **kwargs: respostas_get.popleft()), patch(
        "ps_fila_prioritaria.ps_fila_prioritaria.httpx.post", return_value=Resposta(200, PACIENTE_B)
    ):
        estado.buscar()
        assert estado.nome == "Paciente A"
        assert estado.paciente_encontrado

        # Simula edição e retorno de PATCH antes da nova pesquisa.
        estado.nome = "Paciente A editado"
        estado.alterado = True
        estado.mensagem = "Dados atualizados."
        estado.cpf_busca = "22222222222"
        # Apenas digitar uma nova busca não pode alterar o Paciente aberto.
        assert estado.cpf == PACIENTE_A["cpf"]
        assert estado.nome == "Paciente A editado"
        estado.buscar()
        _assert_cadastro_vazio(estado, "22222222222")

        estado.nome = "Paciente B"
        estado.data_nascimento = "1990-02-02"
        estado.telefone = "11888888888"
        estado.cadastrar()
        assert estado.paciente_encontrado
        assert not estado.exibir_cadastro
        assert estado.paciente_id == PACIENTE_B["id"]
        assert estado.nome == PACIENTE_B["nome"]

        estado.cpf_busca = PACIENTE_A["cpf"]
        estado.buscar()
        assert estado.paciente_id == PACIENTE_A["id"]
        assert estado.nome == PACIENTE_A["nome"]

        estado.cpf_busca = "33333333333"
        estado.buscar()
        _assert_cadastro_vazio(estado, "33333333333")


def test_cpf_invalido_descarta_o_paciente_carregado() -> None:
    estado = EstadoFalso("cpf-invalido")
    estado.nome = PACIENTE_A["nome"]
    estado.data_nascimento = PACIENTE_A["data_nascimento"]
    estado.telefone = PACIENTE_A["telefone"]
    estado.paciente_id = PACIENTE_A["id"]
    estado.paciente_encontrado = True
    estado.alterado = True

    with patch(
        "ps_fila_prioritaria.ps_fila_prioritaria.httpx.get",
        return_value=Resposta(400, {"message": "CPF inválido"}),
    ):
        estado.buscar()

    assert estado.cpf_busca == "cpf-invalido"
    assert estado.cpf == ""
    assert estado.nome == ""
    assert estado.data_nascimento == ""
    assert estado.telefone == ""
    assert estado.paciente_id == 0
    assert not estado.paciente_encontrado
    assert not estado.exibir_cadastro
    assert estado.alterado is None
    assert estado.erro
    assert estado.mensagem == "CPF inválido"


def test_atualizar_envia_telefone_vazio_so_quando_usuario_apaga() -> None:
    estado = EstadoFalso()
    estado._carregar_paciente(PACIENTE_A)
    respostas = deque([
        Resposta(200, {"alterado": True, "paciente": {**PACIENTE_A, "telefone": None}}),
        Resposta(200, {"alterado": False, "paciente": {**PACIENTE_A, "telefone": None}}),
        Resposta(200, {"alterado": False, "paciente": {**PACIENTE_A, "telefone": None}}),
    ])

    with patch(
        "ps_fila_prioritaria.ps_fila_prioritaria.httpx.patch",
        side_effect=lambda *args, **kwargs: respostas.popleft(),
    ) as patch_http:
        # Outro campo pode ser salvo sem tocar no telefone: ele fica omitido.
        estado.nome = "Paciente A atualizado"
        estado.atualizar()
        primeiro_payload = patch_http.call_args_list[0].kwargs["json"]
        assert "telefone" not in primeiro_payload

        # Ao apagar, o payload preserva a intenção do usuário com texto vazio.
        estado.set_telefone("")
        estado.atualizar()
        segundo_payload = patch_http.call_args_list[1].kwargs["json"]
        assert segundo_payload["telefone"] == ""
        assert estado.telefone == ""
        assert not estado.telefone_alterado

        # Novo salvar sem tocar no campo não reenvia o telefone já limpo.
        estado.atualizar()
        assert "telefone" not in patch_http.call_args_list[2].kwargs["json"]


def test_continuar_cria_ficha_para_paciente_identificado() -> None:
    estado = EstadoFalso()
    estado.paciente_id = PACIENTE_A["id"]

    with patch.dict("os.environ", {"XANO_TRIAGEM_API_URL": "https://triagem.test"}, clear=False), patch(
        "ps_fila_prioritaria.ps_fila_prioritaria.httpx.post",
        return_value=Resposta(201, {"id": 10, "paciente_id": PACIENTE_A["id"]}),
    ) as post:
        redirecionamento = estado.continuar_atendimento()

    assert post.call_args.args[0] == "https://triagem.test/fichas"
    assert post.call_args.kwargs["json"] == {"paciente_id": PACIENTE_A["id"]}
    assert redirecionamento is not None
    assert not estado.erro
    assert not estado.abrindo_ficha


def test_continuar_exibe_erro_de_configuracao_na_tela_de_pacientes() -> None:
    estado = EstadoFalso()
    estado.paciente_id = PACIENTE_A["id"]

    with patch.dict("os.environ", {"XANO_TRIAGEM_API_URL": ""}, clear=False), patch(
        "ps_fila_prioritaria.ps_fila_prioritaria.httpx.post"
    ) as post:
        estado.continuar_atendimento()

    post.assert_not_called()
    assert estado.erro
    assert estado.mensagem == "Configure XANO_TRIAGEM_API_URL para conectar a ficha à API do PS."


def test_carregamento_de_env_usa_o_arquivo_do_frontend() -> None:
    assert ARQUIVO_ENV.name == ".env"
    assert ARQUIVO_ENV.parent.name == "frontend"
    with patch("ps_fila_prioritaria.ps_fila_prioritaria.load_dotenv") as carregar:
        carregar_variaveis_ambiente()
    carregar.assert_called_once_with(dotenv_path=ARQUIVO_ENV)


class TestPacienteState(unittest.TestCase):
    """Compatível tanto com unittest quanto com a suíte pytest planejada do projeto."""

    def test_buscas_sequenciais(self) -> None:
        test_buscas_sequenciais_nao_reaproveitam_dados_do_paciente_anterior()

    def test_cpf_invalido(self) -> None:
        test_cpf_invalido_descarta_o_paciente_carregado()

    def test_telefone_vazio(self) -> None:
        test_atualizar_envia_telefone_vazio_so_quando_usuario_apaga()

    def test_continuar(self) -> None:
        test_continuar_cria_ficha_para_paciente_identificado()

    def test_erro_configuracao_triagem(self) -> None:
        test_continuar_exibe_erro_de_configuracao_na_tela_de_pacientes()

    def test_arquivo_env(self) -> None:
        test_carregamento_de_env_usa_o_arquivo_do_frontend()

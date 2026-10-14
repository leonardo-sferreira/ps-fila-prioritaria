"""Fluxo de identificação e cadastro de Paciente da Recepção/Triagem."""

import os
from typing import Any

import httpx
import reflex as rx
from dotenv import load_dotenv


load_dotenv()


def _mensagem_erro(resposta: httpx.Response) -> str:
    """Extrai a mensagem pública devolvida pela API sem expor detalhes internos."""
    try:
        corpo: Any = resposta.json()
    except ValueError:
        return "Não foi possível concluir a solicitação."

    if isinstance(corpo, dict):
        mensagem = corpo.get("message") or corpo.get("error") or corpo.get("code")
        if mensagem == "CPF_DUPLICADO":
            return "CPF_DUPLICADO: já existe um Paciente cadastrado com este CPF."
        if isinstance(mensagem, str):
            return mensagem
    return "Não foi possível concluir a solicitação."


class PacienteState(rx.State):
    """Estado efêmero; não persiste seleção clínica ou operacional."""

    cpf_busca: str = ""
    cpf: str = ""
    nome: str = ""
    data_nascimento: str = ""
    telefone: str = ""
    paciente_id: int = 0
    paciente_encontrado: bool = False
    exibir_cadastro: bool = False
    mensagem: str = ""
    erro: bool = False
    alterado: bool | None = None
    telefone_alterado: bool = False

    def set_cpf_busca(self, valor: str) -> None:
        self.cpf_busca = valor

    def set_nome(self, valor: str) -> None:
        self.nome = valor

    def set_data_nascimento(self, valor: str) -> None:
        self.data_nascimento = valor

    def set_telefone(self, valor: str) -> None:
        self.telefone = valor
        self.telefone_alterado = True

    def _url(self, caminho: str) -> str | None:
        base_url = os.getenv("XANO_API_URL", "").strip().rstrip("/")
        if not base_url:
            self.mensagem = "Configure XANO_API_URL para conectar a tela à API do PS."
            self.erro = True
            return None
        return f"{base_url}{caminho}"

    def _resetar_paciente_atual(self) -> None:
        """Descarta os dados do Paciente anterior, sem tocar no CPF pesquisado."""
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

    def _carregar_paciente(self, paciente: dict[str, Any]) -> None:
        """Preenche a tela exclusivamente com os dados de um Paciente retornado pela API."""
        self.paciente_id = int(paciente["id"])
        self.cpf = str(paciente["cpf"])
        self.nome = str(paciente["nome"])
        self.data_nascimento = str(paciente["data_nascimento"])
        self.telefone = str(paciente.get("telefone") or "")
        self.paciente_encontrado = True
        self.exibir_cadastro = False
        self.telefone_alterado = False

    def buscar(self) -> None:
        """Busca somente por CPF; a validação definitiva é do backend Xano."""
        cpf_consultado = self.cpf_busca
        self._resetar_paciente_atual()
        if not cpf_consultado.strip():
            self.mensagem = "Informe o CPF para pesquisar."
            self.erro = True
            return

        url = self._url("/pacientes")
        if not url:
            return
        try:
            resposta = httpx.get(url, params={"cpf": cpf_consultado}, timeout=10)
        except httpx.RequestError:
            self.mensagem = "Não foi possível conectar à API de Pacientes."
            self.erro = True
            return

        if resposta.status_code == 401:
            self.mensagem = "Sessão não autenticada. O login será integrado pela change de autenticação."
            self.erro = True
            return
        if resposta.status_code == 403:
            self.mensagem = "Seu perfil não possui permissão para consultar Pacientes."
            self.erro = True
            return
        if resposta.status_code == 400:
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return

        paciente = resposta.json()
        if not paciente:
            self.cpf = cpf_consultado
            self.exibir_cadastro = True
            self.mensagem = "Paciente não encontrado. Complete o cadastro para continuar."
            return

        self._carregar_paciente(paciente)
        self.mensagem = "Paciente encontrado."

    def cadastrar(self) -> None:
        url = self._url("/pacientes")
        if not url:
            return
        self.mensagem = ""
        self.erro = False
        dados = {
            "cpf": self.cpf,
            "nome": self.nome,
            "data_nascimento": self.data_nascimento,
        }
        if self.telefone.strip():
            dados["telefone"] = self.telefone
        try:
            resposta = httpx.post(url, json=dados, timeout=10)
        except httpx.RequestError:
            self.mensagem = "Não foi possível conectar à API de Pacientes."
            self.erro = True
            return

        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return
        self._carregar_paciente(resposta.json())
        self.mensagem = "Paciente cadastrado."

    def atualizar(self) -> None:
        if not self.paciente_id:
            return
        url = self._url(f"/pacientes/{self.paciente_id}")
        if not url:
            return
        self.mensagem = ""
        self.erro = False
        dados = {
            "nome": self.nome,
            "data_nascimento": self.data_nascimento,
        }
        if self.telefone_alterado:
            dados["telefone"] = self.telefone
        try:
            resposta = httpx.patch(url, json=dados, timeout=10)
        except httpx.RequestError:
            self.mensagem = "Não foi possível conectar à API de Pacientes."
            self.erro = True
            return

        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return
        resultado = resposta.json()
        self.alterado = bool(resultado.get("alterado"))
        paciente = resultado.get("paciente") or {}
        self.nome = str(paciente.get("nome", self.nome))
        self.data_nascimento = str(paciente.get("data_nascimento", self.data_nascimento))
        self.telefone = str(paciente.get("telefone") or "")
        self.telefone_alterado = False
        self.mensagem = "Dados atualizados." if self.alterado else "Nenhuma alteração cadastral foi necessária."


def formulario_paciente() -> rx.Component:
    return rx.vstack(
        rx.input(value=PacienteState.nome, on_change=PacienteState.set_nome, placeholder="Nome completo", width="100%"),
        rx.input(type="date", value=PacienteState.data_nascimento, on_change=PacienteState.set_data_nascimento, width="100%"),
        rx.input(value=PacienteState.telefone, on_change=PacienteState.set_telefone, placeholder="Telefone (opcional)", width="100%"),
        spacing="3",
        width="100%",
    )


def recepcao_pacientes() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Identificação de Paciente", size="7"),
                rx.text("Recepção/Triagem — pesquise pelo CPF antes de cadastrar."),
                rx.hstack(
                    rx.input(value=PacienteState.cpf_busca, on_change=PacienteState.set_cpf_busca, placeholder="CPF com ou sem pontuação", width="100%"),
                    rx.button("Buscar", on_click=PacienteState.buscar),
                    width="100%",
                ),
                rx.cond(
                    PacienteState.mensagem != "",
                    rx.callout(PacienteState.mensagem, color_scheme=rx.cond(PacienteState.erro, "red", "blue")),
                ),
                rx.cond(
                    PacienteState.exibir_cadastro,
                    rx.vstack(
                        rx.heading("Cadastrar Paciente", size="5"),
                        rx.text("CPF informado: ", PacienteState.cpf),
                        formulario_paciente(),
                        rx.button("Cadastrar", on_click=PacienteState.cadastrar),
                        align="stretch",
                        width="100%",
                    ),
                ),
                rx.cond(
                    PacienteState.paciente_encontrado,
                    rx.vstack(
                        rx.heading("Paciente encontrado", size="5"),
                        rx.text("CPF: ", PacienteState.cpf),
                        formulario_paciente(),
                        rx.hstack(
                            rx.button("Salvar alterações", on_click=PacienteState.atualizar),
                            rx.button("Continuar", variant="soft"),
                        ),
                        rx.cond(
                            PacienteState.alterado == False,
                            rx.text("Nenhuma alteração foi enviada ao cadastro.", color_scheme="gray"),
                        ),
                        align="stretch",
                        width="100%",
                    ),
                ),
                spacing="4",
                width="min(100%, 42rem)",
            ),
            width="100%",
        ),
        padding="2rem",
    )


def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("PS Fila Prioritária", size="8"),
            rx.link("Abrir identificação de Paciente", href="/recepcao/pacientes"),
            spacing="4",
            padding="4rem",
        )
    )


app = rx.App()
app.add_page(index, route="/")
app.add_page(recepcao_pacientes, route="/recepcao/pacientes", title="Identificação de Paciente")

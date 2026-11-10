"""Estado da identificação e do cadastro de Paciente pela Recepção/Triagem."""

import os
from typing import Any

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import _mensagem_erro
from ps_fila_prioritaria.estados.autenticacao import AuthState


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
    abrindo_ficha: bool = False
    ticket_id: int = 0

    def set_cpf_busca(self, valor: str) -> None:
        self.cpf_busca = valor

    def set_nome(self, valor: str) -> None:
        self.nome = valor

    def set_data_nascimento(self, valor: str) -> None:
        self.data_nascimento = valor

    def set_telefone(self, valor: str) -> None:
        self.telefone = valor
        self.telefone_alterado = True

    async def _requisitar_pacientes(self, metodo: str, caminho: str, **kwargs: Any) -> tuple[httpx.Response | None, rx.event.EventSpec | None]:
        """Usa o token da sessão e centraliza 401/403 para as três operações de Paciente."""
        auth = await self.get_state(AuthState)
        try:
            resposta = api.requisitar(metodo, "XANO_API_URL", caminho, token=auth.token, **kwargs)
        except api.ConfiguracaoAusente:
            self.mensagem = "Configure XANO_API_URL para conectar a tela à API do PS."
            self.erro = True
            return None, None
        except httpx.RequestError:
            self.mensagem = "Não foi possível conectar à API de Pacientes."
            self.erro = True
            return None, None

        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
            return None, rx.redirect("/login")
        if resposta.status_code == 403:
            self.mensagem = "Seu perfil não possui permissão para consultar Pacientes."
            self.erro = True
            return None, None
        return resposta, None

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

    async def buscar(self) -> rx.event.EventSpec | None:
        """Busca somente por CPF; a validação definitiva é do backend Xano."""
        cpf_consultado = self.cpf_busca
        self._resetar_paciente_atual()
        if not cpf_consultado.strip():
            self.mensagem = "Informe o CPF para pesquisar."
            self.erro = True
            return

        resposta, redirecionamento = await self._requisitar_pacientes("GET", "/pacientes", params={"cpf": cpf_consultado})
        if redirecionamento is not None:
            return redirecionamento
        if resposta is None:
            return None
        if resposta.status_code == 400:
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return None
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return None

        paciente = resposta.json()
        if not paciente:
            self.cpf = cpf_consultado
            self.exibir_cadastro = True
            self.mensagem = "Paciente não encontrado — preencha o cadastro."
            return

        self._carregar_paciente(paciente)
        self.mensagem = "Paciente encontrado — confira e atualize os dados se necessário. O CPF não pode ser alterado."
        return None

    def cancelar(self) -> None:
        """Limpa a pesquisa e o formulário, sem chamar a API."""
        self._resetar_paciente_atual()
        self.cpf_busca = ""

    async def cadastrar(self) -> rx.event.EventSpec | None:
        self.mensagem = ""
        self.erro = False
        dados = {
            "cpf": self.cpf,
            "nome": self.nome,
            "data_nascimento": self.data_nascimento,
        }
        if self.telefone.strip():
            dados["telefone"] = self.telefone
        resposta, redirecionamento = await self._requisitar_pacientes("POST", "/pacientes", json=dados)
        if redirecionamento is not None:
            return redirecionamento
        if resposta is None:
            return None
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return None
        self._carregar_paciente(resposta.json())
        self.mensagem = "Paciente cadastrado."
        return None

    async def atualizar(self) -> rx.event.EventSpec | None:
        if not self.paciente_id:
            return None
        self.mensagem = ""
        self.erro = False
        dados = {
            "nome": self.nome,
            "data_nascimento": self.data_nascimento,
        }
        if self.telefone_alterado:
            dados["telefone"] = self.telefone
        resposta, redirecionamento = await self._requisitar_pacientes("PATCH", f"/pacientes/{self.paciente_id}", json=dados)
        if redirecionamento is not None:
            return redirecionamento
        if resposta is None:
            return None
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return None
        resultado = resposta.json()
        self.alterado = bool(resultado.get("alterado"))
        paciente = resultado.get("paciente") or {}
        self.nome = str(paciente.get("nome", self.nome))
        self.data_nascimento = str(paciente.get("data_nascimento", self.data_nascimento))
        self.telefone = str(paciente.get("telefone") or "")
        self.telefone_alterado = False
        self.mensagem = "Dados atualizados." if self.alterado else "Nenhuma alteração cadastral foi necessária."
        return None

    def iniciar_sem_ticket(self):
        self.ticket_id = 0
        self._resetar_paciente_atual()
        return rx.redirect("/recepcao/pacientes")

    async def continuar_atendimento(self) -> rx.event.EventSpec | None:
        """Abre a ficha do Paciente identificado e segue para sua edição."""
        if not self.paciente_id:
            self.mensagem = "Identifique um Paciente antes de abrir a ficha."
            self.erro = True
            return None

        base_url = os.getenv("XANO_TRIAGEM_API_URL", "").strip().rstrip("/")
        if not base_url:
            self.mensagem = "Configure XANO_TRIAGEM_API_URL para conectar a ficha à API do PS."
            self.erro = True
            return None

        self.abrindo_ficha = True
        self.mensagem = ""
        self.erro = False
        try:
            auth = await self.get_state(AuthState)
            dados = {"paciente_id": self.paciente_id}
            if self.ticket_id:
                dados["ticket_id"] = self.ticket_id
            resposta = api.requisitar("POST", "XANO_TRIAGEM_API_URL", "/fichas", token=auth.token, json=dados)
        except httpx.RequestError:
            self.mensagem = "Não foi possível conectar à API de Fichas."
            self.erro = True
            self.abrindo_ficha = False
            return None

        self.abrindo_ficha = False
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
            return rx.redirect("/login")
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return None

        ficha = resposta.json()
        self.ticket_id = 0
        try:
            ficha_id = int(ficha["id"])
        except (KeyError, TypeError, ValueError):
            self.mensagem = "A API de Fichas retornou uma resposta inválida."
            self.erro = True
            return None
        return rx.redirect(f"/recepcao/ficha/{ficha_id}")

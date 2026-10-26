"""Fluxo de identificação e cadastro de Paciente da Recepção/Triagem."""

import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx
import reflex as rx
from dotenv import load_dotenv

from ps_fila_prioritaria import api


ARQUIVO_ENV = Path(__file__).resolve().parents[1] / ".env"
# Fonte única do aviso de privacidade: a página mostra este arquivo sem alterá-lo (add-privacidade, D1).
ARQUIVO_AVISO_PRIVACIDADE = Path(__file__).resolve().parents[2] / "docs" / "aviso-de-privacidade.md"


def carregar_variaveis_ambiente() -> None:
    """Carrega o arquivo de ambiente do frontend sem depender do diretório atual."""
    load_dotenv(dotenv_path=ARQUIVO_ENV)


carregar_variaveis_ambiente()


def _mensagem_erro(resposta: httpx.Response) -> str:
    """Extrai a mensagem pública devolvida pela API sem expor detalhes internos."""
    try:
        corpo: Any = resposta.json()
    except ValueError:
        return "Não foi possível concluir a solicitação."

    if isinstance(corpo, dict):
        mensagem = corpo.get("message") or corpo.get("error") or corpo.get("code")
        if mensagem == "CPF_DUPLICADO":
            return "Já existe paciente com este CPF (CPF_DUPLICADO). Pesquise novamente para carregar o cadastro."
        if mensagem == "FICHA_SEM_SINTOMA_OU_OBSERVACAO":
            return "Informe ao menos um sintoma ou uma observação."
        if isinstance(mensagem, str):
            return mensagem
    return "Não foi possível concluir a solicitação."


# Área inicial de cada perfil (design D7).
AREA_POR_PERFIL = {
    "RECEPCAO_TRIAGEM": "/recepcao",
    "MEDICO": "/medico",
    "ADMINISTRADOR": "/admin",
}


def _postar_publico(estado: Any, caminho: str, corpo: dict[str, Any]) -> httpx.Response | None:
    """Chama um endpoint público de autenticação; em falha de conexão ou configuração, avisa e devolve None."""
    try:
        return api.requisitar("POST", "XANO_AUTH_API_URL", caminho, json=corpo)
    except api.ConfiguracaoAusente:
        estado.mensagem = "Configure XANO_AUTH_API_URL para conectar o login à API do PS."
    except httpx.RequestError:
        estado.mensagem = "Não foi possível conectar à API de autenticação."
    return None


def _segundos_reenvio(resposta: httpx.Response) -> int:
    return int(resposta.json().get("reenvio_em_segundos") or 60)


async def _contar_reenvio(estado: Any) -> None:
    """Contador do botão "Reenviar código"; um único contador por vez em cada estado."""
    async with estado:
        if estado.contando:
            return
        estado.contando = True
    while True:
        await asyncio.sleep(1)
        async with estado:
            estado.segundos_reenvio = max(estado.segundos_reenvio - 1, 0)
            if estado.segundos_reenvio == 0:
                estado.contando = False
                return


def _texto_reenvio(segundos: int) -> str:
    return f"Reenviar código em {segundos // 60}:{segundos % 60:02d}"


def _mascarar_email(email: str) -> str:
    """a***@ps.com.br, como no Figma (tela A2)."""
    usuario, _, dominio = email.partition("@")
    return f"{usuario[:1]}***@{dominio}" if dominio else email


def mascarar_cpf(valor: object) -> str:
    """***.456.789-** nas telas internas; CPF ausente ou sem 11 dígitos não aparece em parte (spec privacidade)."""
    digitos = "".join(c for c in str(valor or "") if c.isdigit())
    if len(digitos) != 11:
        return "—"
    return f"***.{digitos[3:6]}.{digitos[6:9]}-**"


class AuthState(rx.State):
    """Sessão da equipe no navegador. A autorização real é feita no Xano (design D3)."""

    token: str = rx.LocalStorage("", name="ps_token")
    nome: str = ""
    perfil: str = ""
    entrando: bool = False
    mensagem: str = ""
    aviso: str = ""
    email_pendente: str = ""
    segundos_reenvio: int = 0
    contando: bool = False
    # Vem do auth/me (INATIVIDADE_SEGUNDOS no Xano); 0 enquanto a sessão não foi conferida.
    inatividade_segundos: int = 0

    def _encerrar_sessao_local(self, mensagem: str = "") -> None:
        self.token = ""
        self.nome = ""
        self.perfil = ""
        self.mensagem = mensagem

    def _validar_sessao(self, perfil_exigido: str) -> rx.event.EventSpec | None:
        """Confere o token com auth/me; devolve o redirecionamento necessário ou None se pode seguir."""
        if not self.token:
            return rx.redirect("/login")
        try:
            resposta = api.requisitar("GET", "XANO_AUTH_API_URL", "/auth/me", token=self.token)
        except api.ConfiguracaoAusente:
            self.mensagem = "Configure XANO_AUTH_API_URL para conectar o login à API do PS."
            return rx.redirect("/login")
        except httpx.RequestError:
            self.mensagem = "Não foi possível conectar à API de autenticação."
            return rx.redirect("/login")

        if resposta.status_code == 401:
            self._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
            return rx.redirect("/login")
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return rx.redirect("/login")

        usuario = resposta.json()
        self.nome = str(usuario.get("nome", ""))
        self.perfil = str(usuario.get("perfil", ""))
        self.inatividade_segundos = int(usuario.get("inatividade_segundos") or 0)
        if perfil_exigido and self.perfil != perfil_exigido:
            return rx.redirect(AREA_POR_PERFIL.get(self.perfil, "/login"))
        return None

    @rx.var
    def email_exibido(self) -> str:
        return _mascarar_email(self.email_pendente)

    @rx.var
    def texto_reenvio(self) -> str:
        return _texto_reenvio(self.segundos_reenvio)

    def _postar(self, caminho: str, corpo: dict[str, Any]) -> httpx.Response | None:
        return _postar_publico(self, caminho, corpo)

    def _aguardar_reenvio(self, resposta: httpx.Response) -> None:
        self.segundos_reenvio = _segundos_reenvio(resposta)

    def entrar(self, dados: dict[str, Any]):
        """Primeira etapa: e-mail e senha. Com sucesso, o código segue por e-mail (design D13)."""
        self.mensagem = ""
        self.entrando = True
        yield
        email = str(dados.get("email", "")).strip().lower()
        resposta = self._postar("/auth/login", {"email": email, "senha": dados.get("senha", "")})
        self.entrando = False
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        # Só o e-mail fica guardado entre as etapas; a senha não.
        self.email_pendente = email
        self.aviso = ""
        self._aguardar_reenvio(resposta)
        yield rx.redirect("/login/codigo")
        yield AuthState.contar_reenvio

    def verificar_codigo(self, dados: dict[str, Any]):
        """Segunda etapa: com o código conferido, guarda o token e leva à área do perfil."""
        self.mensagem = ""
        self.aviso = ""
        self.entrando = True
        yield
        resposta = self._postar("/auth/login/verificar", {"email": self.email_pendente, "codigo": str(dados.get("codigo", "")).strip()})
        self.entrando = False
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        sessao = resposta.json()
        self.token = str(sessao["token"])
        self.nome = str(sessao.get("nome", ""))
        self.perfil = str(sessao.get("perfil", ""))
        self.email_pendente = ""
        self.segundos_reenvio = 0
        yield rx.redirect(AREA_POR_PERFIL.get(self.perfil, "/login"))

    def reenviar_codigo(self):
        self.mensagem = ""
        self.aviso = ""
        resposta = self._postar("/auth/login/reenviar", {"email": self.email_pendente})
        if resposta is None:
            return
        if resposta.status_code == 403:
            # Primeiro passo vencido: volta ao login para informar a senha de novo.
            self.email_pendente = ""
            self.mensagem = _mensagem_erro(resposta)
            yield rx.redirect("/login")
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        self.aviso = "Enviamos um novo código para o seu e-mail."
        self._aguardar_reenvio(resposta)
        yield AuthState.contar_reenvio

    @rx.event(background=True)
    async def contar_reenvio(self):
        await _contar_reenvio(self)

    def exigir_login_pendente(self) -> rx.event.EventSpec | None:
        """Guarda da tela do código: sem a primeira etapa feita, volta ao login."""
        if not self.email_pendente:
            return rx.redirect("/login")
        return None

    def voltar_ao_login(self) -> rx.event.EventSpec:
        self.email_pendente = ""
        self.mensagem = ""
        self.aviso = ""
        return rx.redirect("/login")

    def verificar_sessao(self, perfil_exigido: str = "") -> rx.event.EventSpec | None:
        """Guarda de rota usada no on_load das páginas internas."""
        return self._validar_sessao(perfil_exigido)

    def ir_para_inicio(self) -> rx.event.EventSpec:
        redirecionamento = self._validar_sessao("")
        if redirecionamento is not None:
            return redirecionamento
        return rx.redirect(AREA_POR_PERFIL.get(self.perfil, "/login"))

    def _sair(self, mensagem: str = "") -> rx.event.EventSpec:
        if self.token:
            try:
                api.requisitar("POST", "XANO_AUTH_API_URL", "/auth/logout", token=self.token)
            except (api.ConfiguracaoAusente, httpx.RequestError):
                pass  # O token é descartado mesmo se a API não responder.
        self._encerrar_sessao_local(mensagem)
        self.inatividade_segundos = 0
        return rx.redirect("/login")

    def sair(self) -> rx.event.EventSpec:
        return self._sair()

    def sair_por_inatividade(self) -> rx.event.EventSpec:
        """Chamado pela página /sair/inatividade quando o contador da tela estoura (add-privacidade, D5)."""
        return self._sair("Sua sessão foi encerrada por inatividade.")


class SenhaState(rx.State):
    """"Esqueci minha senha" (telas A1 a A4 do Figma). As regras do código ficam no Xano (design D12)."""

    email: str = ""
    codigo: str = ""
    enviando: bool = False
    mensagem: str = ""
    aviso: str = ""
    segundos_reenvio: int = 0
    contando: bool = False

    @rx.var
    def email_exibido(self) -> str:
        return _mascarar_email(self.email)

    @rx.var
    def texto_reenvio(self) -> str:
        return _texto_reenvio(self.segundos_reenvio)

    def _limpar(self) -> None:
        self.email = ""
        self.codigo = ""
        self.mensagem = ""
        self.aviso = ""

    def iniciar(self) -> None:
        self.mensagem = ""
        self.aviso = ""

    def solicitar_codigo(self, dados: dict[str, Any]):
        """A1: a resposta é a mesma para qualquer e-mail; só usuário ativo recebe o código."""
        self.mensagem = ""
        self.enviando = True
        yield
        email = str(dados.get("email", "")).strip().lower()
        resposta = _postar_publico(self, "/auth/senha/solicitar", {"email": email})
        self.enviando = False
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        self.email = email
        self.codigo = ""
        self.aviso = ""
        self.segundos_reenvio = _segundos_reenvio(resposta)
        yield rx.redirect("/senha/codigo")
        yield SenhaState.contar_reenvio

    def reenviar_codigo(self):
        self.mensagem = ""
        self.aviso = ""
        resposta = _postar_publico(self, "/auth/senha/solicitar", {"email": self.email})
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        self.aviso = "Se o e-mail estiver cadastrado, enviamos um novo código."
        self.segundos_reenvio = _segundos_reenvio(resposta)
        yield SenhaState.contar_reenvio

    @rx.event(background=True)
    async def contar_reenvio(self):
        await _contar_reenvio(self)

    def verificar_codigo(self, dados: dict[str, Any]):
        """A2: confere o código sem usá-lo; o uso definitivo é na troca da senha (A3)."""
        self.mensagem = ""
        self.aviso = ""
        self.enviando = True
        yield
        codigo = str(dados.get("codigo", "")).strip()
        resposta = _postar_publico(self, "/auth/senha/verificar", {"email": self.email, "codigo": codigo})
        self.enviando = False
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)  # A2b
            return

        self.codigo = codigo
        yield rx.redirect("/senha/nova")

    def redefinir(self, dados: dict[str, Any]):
        """A3: a confirmação é só da tela; o mínimo de 8 caracteres é validado no Xano."""
        self.mensagem = ""
        nova_senha = str(dados.get("nova_senha", ""))
        if nova_senha != str(dados.get("confirmacao", "")):
            self.mensagem = "As duas senhas devem ser iguais."
            return
        self.enviando = True
        yield
        resposta = _postar_publico(
            self, "/auth/senha/redefinir", {"email": self.email, "codigo": self.codigo, "nova_senha": nova_senha}
        )
        self.enviando = False
        if resposta is None:
            return
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return

        self._limpar()
        self.segundos_reenvio = 0
        yield rx.redirect("/senha/sucesso")

    def exigir_email(self) -> rx.event.EventSpec | None:
        """Guarda da tela A2: sem o pedido feito na A1, volta para ela."""
        if not self.email:
            return rx.redirect("/senha")
        return None

    def exigir_codigo(self) -> rx.event.EventSpec | None:
        """Guarda da tela A3: sem o código conferido na A2, volta para a A1."""
        if not self.email or not self.codigo:
            return rx.redirect("/senha")
        return None

    def voltar_ao_login(self) -> rx.event.EventSpec:
        self._limpar()
        return rx.redirect("/login")


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
            self.mensagem = "Paciente não encontrado — preencha o cadastro."
            return

        self._carregar_paciente(paciente)
        self.mensagem = "Paciente encontrado — confira e atualize os dados se necessário. O CPF não pode ser alterado."

    def cancelar(self) -> None:
        """Limpa a pesquisa e o formulário, sem chamar a API."""
        self._resetar_paciente_atual()
        self.cpf_busca = ""

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

    def continuar_atendimento(self) -> rx.event.EventSpec | None:
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
            resposta = httpx.post(f"{base_url}/fichas", json={"paciente_id": self.paciente_id}, timeout=10)
        except httpx.RequestError:
            self.mensagem = "Não foi possível conectar à API de Fichas."
            self.erro = True
            self.abrindo_ficha = False
            return None

        self.abrindo_ficha = False
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return None

        ficha = resposta.json()
        try:
            ficha_id = int(ficha["id"])
        except (KeyError, TypeError, ValueError):
            self.mensagem = "A API de Fichas retornou uma resposta inválida."
            self.erro = True
            return None
        return rx.redirect(f"/recepcao/ficha/{ficha_id}")


class FichaState(rx.State):
    """Estado da ficha de triagem, separado do cadastro de Paciente."""

    ficha_id: int = 0
    paciente: dict[str, Any] = {}
    catalogo_sintomas: list[dict[str, Any]] = []
    sintoma_ids_selecionados: list[int] = []
    observacao: str = ""
    sintomas_alterados: bool = False
    observacao_alterada: bool = False
    carregando: bool = False
    salvando: bool = False
    mensagem: str = ""
    erro: bool = False

    @rx.var
    def cpf_exibido(self) -> str:
        return mascarar_cpf(self.paciente.get("cpf"))

    def _url(self, caminho: str) -> str | None:
        base_url = os.getenv("XANO_TRIAGEM_API_URL", "").strip().rstrip("/")
        if not base_url:
            self.mensagem = "Configure XANO_TRIAGEM_API_URL para conectar a ficha à API do PS."
            self.erro = True
            return None
        return f"{base_url}{caminho}"

    def _limpar_feedback(self) -> None:
        self.mensagem = ""
        self.erro = False

    def _carregar_resposta_ficha(self, dados: dict[str, Any]) -> None:
        ficha = dados.get("ficha") or {}
        self.ficha_id = int(ficha.get("id", self.ficha_id))
        self.paciente = dict(dados.get("paciente") or {})
        self.observacao = str(ficha.get("observacao") or "")
        self.sintoma_ids_selecionados = sorted(int(sintoma["id"]) for sintoma in (dados.get("sintomas") or []))

    def carregar(self, ficha_id: str | int) -> None:
        """Recupera catálogo ativo e estado persistido para edição da ficha."""
        try:
            ficha_id_int = int(ficha_id)
        except (TypeError, ValueError):
            self.mensagem = "Ficha inválida."
            self.erro = True
            return

        url_ficha = self._url(f"/fichas/{ficha_id_int}")
        url_sintomas = self._url("/sintomas")
        if not url_ficha or not url_sintomas:
            return

        self.carregando = True
        self._limpar_feedback()
        try:
            resposta_ficha = httpx.get(url_ficha, timeout=10)
            resposta_sintomas = httpx.get(url_sintomas, timeout=10)
        except httpx.RequestError:
            self.mensagem = "Não foi possível conectar à API de Fichas."
            self.erro = True
            self.carregando = False
            return

        if not resposta_ficha.is_success:
            self.mensagem = _mensagem_erro(resposta_ficha)
            self.erro = True
            self.carregando = False
            return
        if not resposta_sintomas.is_success:
            self.mensagem = _mensagem_erro(resposta_sintomas)
            self.erro = True
            self.carregando = False
            return

        self._carregar_resposta_ficha(resposta_ficha.json())
        self.catalogo_sintomas = sorted(
            list(resposta_sintomas.json() or []),
            key=lambda sintoma: str(sintoma["nome"]).casefold(),
        )
        self.sintomas_alterados = False
        self.observacao_alterada = False
        self.carregando = False

    def carregar_da_rota(self) -> None:
        ficha_id = self.router.page.params.get("id", "")
        self.carregar(ficha_id)

    def set_observacao(self, valor: str) -> None:
        self.observacao = valor
        self.observacao_alterada = True

    def alternar_sintoma(self, sintoma_id: int, marcado: bool) -> None:
        selecionados = set(self.sintoma_ids_selecionados)
        if marcado:
            selecionados.add(int(sintoma_id))
        else:
            selecionados.discard(int(sintoma_id))
        self.sintoma_ids_selecionados = sorted(selecionados)
        self.sintomas_alterados = True

    async def salvar(self) -> AsyncIterator[None]:
        """Envia o estado final da coleção e a observação geral para validação do backend."""
        if self.salvando:
            return

        if not self.ficha_id:
            self.mensagem = "Nenhuma ficha foi carregada para salvar."
            self.erro = True
            self.salvando = False
            return

        if not self.sintoma_ids_selecionados and not self.observacao.strip():
            self.mensagem = "Informe ao menos um sintoma ou uma observação/queixa."
            self.erro = True
            self.salvando = False
            return

        url_ficha = self._url(f"/fichas/{self.ficha_id}")
        url_sintomas = self._url("/sintomas")
        if not url_ficha or not url_sintomas:
            self.salvando = False
            return

        self.salvando = True
        self._limpar_feedback()
        dados: dict[str, Any] = {}
        if self.sintomas_alterados:
            # Uma lista vazia é uma coleção final válida e não equivale a campo omitido.
            dados["sintoma_ids"] = self.sintoma_ids_selecionados
        if self.observacao_alterada:
            dados["observacao"] = self.observacao
        if not dados:
            self.salvando = False
            self.mensagem = "Nenhuma alteração para salvar."
            self.erro = False
            return

        # Entrega o loading antes das requisições de PATCH e GET.
        yield
        try:
            try:
                resposta = httpx.patch(url_ficha, json=dados, timeout=10)
            except httpx.RequestError:
                self.mensagem = "Não foi possível conectar à API de Fichas."
                self.erro = True
            else:
                if not resposta.is_success:
                    self.mensagem = _mensagem_erro(resposta)
                    self.erro = True
                else:
                    try:
                        resposta_ficha = httpx.get(url_ficha, timeout=10)
                        resposta_sintomas = httpx.get(url_sintomas, timeout=10)
                    except httpx.RequestError:
                        self.mensagem = "A ficha foi salva, mas não foi possível recarregá-la."
                        self.erro = True
                    else:
                        if not resposta_ficha.is_success:
                            self.mensagem = _mensagem_erro(resposta_ficha)
                            self.erro = True
                        elif not resposta_sintomas.is_success:
                            self.mensagem = _mensagem_erro(resposta_sintomas)
                            self.erro = True
                        else:
                            self._carregar_resposta_ficha(resposta_ficha.json())
                            self.catalogo_sintomas = sorted(
                                list(resposta_sintomas.json() or []),
                                key=lambda sintoma: str(sintoma["nome"]).casefold(),
                            )
                            self.sintomas_alterados = False
                            self.observacao_alterada = False
                            self.mensagem = "Ficha salva com sucesso."
                            self.erro = False
        finally:
            self.salvando = False


class SeletorSintomasState(rx.State):
    """Consulta efêmera da interface; a seleção continua pertencendo à FichaState."""

    busca: str = ""

    def set_busca(self, valor: str) -> None:
        self.busca = valor

    def limpar_busca(self) -> None:
        self.busca = ""


def sintomas_disponiveis(
    catalogo: list[dict[str, Any]], sintoma_ids_selecionados: list[int], busca: str
) -> list[dict[str, Any]]:
    """Deriva as opções sem alterar o catálogo nem a seleção persistida."""
    consulta = busca.strip().casefold()
    selecionados = set(sintoma_ids_selecionados)
    return sorted(
        (
            sintoma
            for sintoma in catalogo
            if int(sintoma["id"]) not in selecionados and consulta in str(sintoma["nome"]).casefold()
        ),
        key=lambda sintoma: str(sintoma["nome"]).casefold(),
    )


# Cores do protótipo no Figma (telas 3 e 3a–3e).
COR_MARINHO = "#123C6B"
COR_AZUL = "#1565C0"
COR_FUNDO = "#F3F5F7"
COR_BORDA = "#DDE3E8"
COR_TEXTO = "#1A2027"
COR_SECUNDARIA = "#66707A"
COR_SUCESSO = "#2E7D32"
COR_ERRO = "#C62828"


def sessao_no_cabecalho() -> rx.Component:
    return rx.hstack(
        rx.text(AuthState.nome, size="2", color="#CCDEF0"),
        rx.button("Sair", on_click=AuthState.sair, variant="outline", size="2", color="white", border_color="rgba(255, 255, 255, 0.4)"),
        align="center",
        spacing="3",
        padding_right="24px",
    )


def cabecalho(titulo: str, subtitulo: str, sigla: str) -> rx.Component:
    return rx.hstack(
        rx.center(
            rx.text(sigla, weight="bold", size="4", color="white"),
            width="48px",
            height="48px",
            border_radius="50%",
            background="rgba(255, 255, 255, 0.15)",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(titulo, weight="bold", size="5", color="white"),
            rx.text(subtitulo, size="2", color="#CCDEF0"),
            spacing="1",
        ),
        rx.spacer(),
        sessao_no_cabecalho(),
        rx.vstack(
            # Relógio do navegador, atualizado a cada segundo no fuso do PS.
            rx.moment(format="DD/MM/YYYY", interval=1000, tz="America/Sao_Paulo", color="#CCDEF0", font_size="14px", font_weight="500"),
            rx.moment(format="HH:mm:ss", interval=1000, tz="America/Sao_Paulo", color="white", font_size="26px", font_weight="700", font_variant_numeric="tabular-nums"),
            spacing="0",
            align="end",
        ),
        align="center",
        spacing="4",
        background=COR_MARINHO,
        padding="0 48px",
        height="96px",
        width="100%",
    )


def campo_rotulado(rotulo: str, campo: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(rotulo, size="1", weight="medium", color=COR_SECUNDARIA),
        campo,
        spacing="1",
        width="100%",
    )


def formulario_paciente() -> rx.Component:
    return rx.vstack(
        campo_rotulado(
            "NOME COMPLETO",
            rx.input(value=PacienteState.nome, on_change=PacienteState.set_nome, placeholder="Digite o nome completo", size="3", width="100%"),
        ),
        rx.hstack(
            campo_rotulado(
                "DATA DE NASCIMENTO",
                rx.input(type="date", value=PacienteState.data_nascimento, on_change=PacienteState.set_data_nascimento, size="3", width="100%"),
            ),
            campo_rotulado(
                "TELEFONE (OPCIONAL)",
                rx.input(value=PacienteState.telefone, on_change=PacienteState.set_telefone, placeholder="(00) 00000-0000", size="3", width="100%"),
            ),
            spacing="5",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def mensagem_identificacao() -> rx.Component:
    cor = rx.cond(PacienteState.erro, COR_ERRO, rx.cond(PacienteState.paciente_encontrado, COR_SUCESSO, COR_SECUNDARIA))
    return rx.cond(
        PacienteState.mensagem != "",
        rx.text(
            rx.cond(PacienteState.paciente_encontrado & ~PacienteState.erro, "✓ ", ""),
            PacienteState.mensagem,
            size="2",
            color=cor,
        ),
    )


def botao_secundario(texto: str, **props: Any) -> rx.Component:
    return rx.button(texto, variant="outline", color_scheme="gray", size="3", color=COR_TEXTO, **props)


def rodape_identificacao() -> rx.Component:
    return rx.cond(
        PacienteState.paciente_encontrado | PacienteState.exibir_cadastro,
        rx.vstack(
            rx.divider(color=COR_BORDA),
            rx.hstack(
                rx.spacer(),
                botao_secundario("Cancelar", on_click=PacienteState.cancelar),
                rx.cond(
                    PacienteState.paciente_encontrado,
                    rx.hstack(
                        botao_secundario("Salvar alterações", on_click=PacienteState.atualizar),
                        rx.button(
                            "Continuar",
                            on_click=PacienteState.continuar_atendimento,
                            loading=PacienteState.abrindo_ficha,
                            size="3",
                            background=COR_AZUL,
                            min_width="240px",
                        ),
                        spacing="3",
                    ),
                    rx.button("Salvar cadastro", on_click=PacienteState.cadastrar, size="3", background=COR_AZUL, min_width="240px"),
                ),
                align="center",
                spacing="3",
                width="100%",
                padding="16px 32px",
            ),
            spacing="0",
            width="100%",
        ),
    )


def recepcao_pacientes() -> rx.Component:
    return rx.box(
        cabecalho(
            "RECEPÇÃO/TRIAGEM — IDENTIFICAÇÃO DO PACIENTE",
            "Identifique o paciente pelo CPF antes de abrir a ficha",
            "R",
        ),
        rx.center(
            rx.vstack(
                rx.vstack(
                    rx.text("Identificação do paciente", weight="bold", size="5", color=COR_TEXTO),
                    rx.box(height="8px"),
                    campo_rotulado(
                        "CPF",
                        rx.hstack(
                            rx.input(
                                value=PacienteState.cpf_busca,
                                on_change=PacienteState.set_cpf_busca,
                                placeholder="000.000.000-00",
                                size="3",
                                width="100%",
                                max_width="342px",
                                color_scheme=rx.cond(PacienteState.erro, "red", "gray"),
                            ),
                            rx.button("Pesquisar", on_click=PacienteState.buscar, size="3", background=COR_AZUL, min_width="160px"),
                            spacing="4",
                            width="100%",
                        ),
                    ),
                    mensagem_identificacao(),
                    rx.cond(
                        PacienteState.paciente_encontrado | PacienteState.exibir_cadastro,
                        rx.box(formulario_paciente(), padding_top="12px", width="100%"),
                    ),
                    spacing="3",
                    padding="28px 32px",
                    width="100%",
                ),
                rodape_identificacao(),
                spacing="0",
                background="white",
                border=f"1px solid {COR_BORDA}",
                border_radius="12px",
                box_shadow="0 2px 8px rgba(18, 60, 107, 0.06)",
                width="min(100%, 772px)",
            ),
            padding="40px 16px",
            width="100%",
        ),
        background=COR_FUNDO,
        font_family="Inter, sans-serif",
        min_height="100vh",
        width="100%",
    )


def carregando() -> rx.Component:
    return rx.center(rx.spinner(size="3"), height="100vh", width="100%", background=COR_FUNDO)


# Contagem de inatividade no navegador (add-privacidade, D5). Instala os ouvintes uma única vez; só conta
# enquanto o marcador #ps-inatividade estiver na página, então as telas públicas não encerram nada.
SCRIPT_INATIVIDADE = """
(function () {
  if (window.__psInatividade) return;
  window.__psInatividade = true;
  var ultima = Date.now();
  ["mousemove", "mousedown", "keydown", "scroll", "touchstart"].forEach(function (evento) {
    window.addEventListener(evento, function () { ultima = Date.now(); }, { passive: true, capture: true });
  });
  setInterval(function () {
    var marcador = document.getElementById("ps-inatividade");
    if (!marcador) { ultima = Date.now(); return; }
    var limite = parseInt(marcador.getAttribute("data-inatividade-ms") || "0", 10);
    if (limite > 0 && Date.now() - ultima >= limite) {
      window.__psInatividade = false;
      window.location.href = "/sair/inatividade";
    }
  }, 1000);
})();
"""


def protegido(perfil: str, conteudo: rx.Component) -> rx.Component:
    """Só mostra a página ao perfil certo; enquanto a sessão é conferida, mostra o carregamento."""
    return rx.cond(
        AuthState.perfil == perfil,
        rx.fragment(
            conteudo,
            rx.el.div(id="ps-inatividade", custom_attrs={"data-inatividade-ms": AuthState.inatividade_segundos * 1000}, display="none"),
            rx.script(SCRIPT_INATIVIDADE),
        ),
        carregando(),
    )


def index() -> rx.Component:
    # A raiz só encaminha: para o login ou para a área do perfil logado.
    return carregando()


def logo_ps() -> rx.Component:
    return rx.center(
        rx.text("PS", weight="bold", size="5", color="white"),
        width="64px",
        height="64px",
        border_radius="50%",
        background=COR_MARINHO,
    )


def cartao_acesso(icone: rx.Component, titulo: str, subtitulo: rx.Component | str, *corpo: rx.Component, on_submit: Any = None) -> rx.Component:
    """Cartão centralizado das telas de acesso (login, código e redefinição de senha), como no Figma."""
    cartao = rx.vstack(
        icone,
        rx.text(titulo, weight="bold", size="5", color=COR_TEXTO),
        rx.text(subtitulo, size="2", color=COR_SECUNDARIA, text_align="center") if isinstance(subtitulo, str) else subtitulo,
        rx.box(height="8px"),
        *corpo,
        align="center",
        spacing="3",
        padding="40px 20px",
        background="white",
        border=f"1px solid {COR_BORDA}",
        border_radius="16px",
        box_shadow="0 2px 8px rgba(18, 60, 107, 0.06)",
        width="min(100%, 420px)",
    )
    return fundo_acesso(rx.form(cartao, on_submit=on_submit, width="min(100%, 420px)") if on_submit is not None else cartao)


def fundo_acesso(conteudo: rx.Component) -> rx.Component:
    """Fundo das páginas públicas, com o rodapé e o link do aviso de privacidade (add-privacidade, D2)."""
    return rx.center(
        rx.vstack(
            conteudo,
            rx.hstack(
                rx.text("Acesso restrito a profissionais autorizados do PS", size="1", color=COR_SECUNDARIA),
                rx.text("·", size="1", color=COR_SECUNDARIA),
                rx.link("Aviso de privacidade", href="/privacidade", size="1", color=COR_AZUL),
                spacing="2",
                wrap="wrap",
                justify="center",
            ),
            align="center",
            spacing="6",
            width="100%",
        ),
        background=COR_FUNDO,
        font_family="Inter, sans-serif",
        min_height="100vh",
        padding="24px 16px",
        width="100%",
    )


def mensagens_acesso(mensagem: rx.Var, aviso: rx.Var | None = None) -> rx.Component:
    erro = rx.cond(mensagem != "", rx.text(mensagem, size="2", color=COR_ERRO, width="100%"))
    if aviso is None:
        return erro
    return rx.fragment(erro, rx.cond(aviso != "", rx.text("✓ ", aviso, size="2", color=COR_SUCESSO, width="100%")))


def botao_principal(texto: str, ocupado: rx.Var) -> rx.Component:
    return rx.button(texto, type="submit", loading=ocupado, size="3", background=COR_AZUL, width="100%")


def link_acao(texto: str, **props: Any) -> rx.Component:
    return rx.button(texto, type="button", variant="ghost", size="2", color=COR_AZUL, **props)


def campo_codigo() -> rx.Component:
    return campo_rotulado(
        "CÓDIGO DE VERIFICAÇÃO",
        rx.input(
            name="codigo",
            placeholder="000000",
            max_length=6,
            input_mode="numeric",
            custom_attrs={"autoComplete": "one-time-code"},
            auto_focus=True,
            size="3",
            width="100%",
            text_align="center",
            letter_spacing="8px",
            font_size="22px",
        ),
    )


def bloco_reenvio(segundos: rx.Var, texto: rx.Var, ao_reenviar: Any) -> rx.Component:
    return rx.cond(
        segundos > 0,
        rx.text(texto, size="2", color=COR_SECUNDARIA),
        link_acao("Reenviar código", on_click=ao_reenviar),
    )


def login() -> rx.Component:
    return cartao_acesso(
        logo_ps(),
        "Sistema de Fila Prioritária",
        "Acesso da equipe — Recepção/Triagem, Médico e Administrador",
        campo_rotulado("E-MAIL", rx.input(name="email", type="email", placeholder="nome@ps.com.br", size="3", width="100%")),
        campo_rotulado("SENHA", rx.input(name="senha", type="password", placeholder="••••••••", size="3", width="100%")),
        mensagens_acesso(AuthState.mensagem),
        botao_principal("Entrar", AuthState.entrando),
        rx.link("Esqueci minha senha", href="/senha", size="2", color=COR_AZUL),
        on_submit=AuthState.entrar,
    )


def login_codigo() -> rx.Component:
    # Segunda etapa do login (design D13), no padrão da tela A2 do Figma.
    return cartao_acesso(
        logo_ps(),
        "Digite o código",
        rx.text(
            "Enviamos um código de 6 dígitos para ",
            AuthState.email_exibido,
            ". Digite-o abaixo para entrar.",
            size="2",
            color=COR_SECUNDARIA,
            text_align="center",
        ),
        campo_codigo(),
        mensagens_acesso(AuthState.mensagem, AuthState.aviso),
        botao_principal("Verificar código", AuthState.entrando),
        bloco_reenvio(AuthState.segundos_reenvio, AuthState.texto_reenvio, AuthState.reenviar_codigo),
        rx.text("Não recebeu? Confira a caixa de spam.", size="1", color=COR_SECUNDARIA),
        link_acao("Voltar ao login", on_click=AuthState.voltar_ao_login),
        on_submit=AuthState.verificar_codigo,
    )


def senha_email() -> rx.Component:
    # A1 — Esqueci minha senha (e-mail).
    return cartao_acesso(
        logo_ps(),
        "Redefinir senha",
        "Informe o e-mail cadastrado. Enviaremos um código de verificação.",
        campo_rotulado("E-MAIL", rx.input(name="email", type="email", placeholder="nome@ps.com.br", size="3", width="100%")),
        mensagens_acesso(SenhaState.mensagem),
        botao_principal("Enviar código", SenhaState.enviando),
        link_acao("Voltar ao login", on_click=SenhaState.voltar_ao_login),
        on_submit=SenhaState.solicitar_codigo,
    )


def senha_codigo() -> rx.Component:
    # A2 — Código enviado por e-mail; a A2b é esta tela com a mensagem "Código inválido ou expirado".
    return cartao_acesso(
        logo_ps(),
        "Digite o código",
        rx.text(
            "Se o e-mail estiver cadastrado, enviamos um código de 6 dígitos para ",
            SenhaState.email_exibido,
            ".",
            size="2",
            color=COR_SECUNDARIA,
            text_align="center",
        ),
        campo_codigo(),
        mensagens_acesso(SenhaState.mensagem, SenhaState.aviso),
        botao_principal("Verificar código", SenhaState.enviando),
        bloco_reenvio(SenhaState.segundos_reenvio, SenhaState.texto_reenvio, SenhaState.reenviar_codigo),
        rx.text("Não recebeu? Confira a caixa de spam.", size="1", color=COR_SECUNDARIA),
        link_acao("Voltar ao login", on_click=SenhaState.voltar_ao_login),
        on_submit=SenhaState.verificar_codigo,
    )


def senha_nova() -> rx.Component:
    # A3 — Nova senha.
    return cartao_acesso(
        logo_ps(),
        "Crie uma nova senha",
        "Código confirmado. Escolha a nova senha de acesso.",
        campo_rotulado("NOVA SENHA", rx.input(name="nova_senha", type="password", placeholder="••••••••", size="3", width="100%")),
        campo_rotulado("CONFIRMAR NOVA SENHA", rx.input(name="confirmacao", type="password", placeholder="••••••••", size="3", width="100%")),
        rx.text("Mínimo de 8 caracteres. As duas senhas devem ser iguais.", size="1", color=COR_SECUNDARIA, width="100%"),
        mensagens_acesso(SenhaState.mensagem),
        botao_principal("Salvar nova senha", SenhaState.enviando),
        on_submit=SenhaState.redefinir,
    )


def senha_sucesso() -> rx.Component:
    # A4 — Senha redefinida.
    return cartao_acesso(
        rx.center(rx.icon("check", size=28, color=COR_SUCESSO), width="64px", height="64px", border_radius="50%", background="#E8F5E9"),
        "Senha redefinida",
        "Sua senha foi alterada. A senha anterior deixou de funcionar; entre com a nova senha.",
        rx.link(rx.button("Ir para o login", size="3", background=COR_AZUL, width="100%"), href="/login", width="100%"),
    )


def carregar_aviso_privacidade() -> str:
    return ARQUIVO_AVISO_PRIVACIDADE.read_text(encoding="utf-8")


def privacidade() -> rx.Component:
    # Página pública do aviso: não exige login nem mexe na sessão aberta (spec privacidade).
    return fundo_acesso(
        rx.vstack(
            logo_ps(),
            rx.box(rx.markdown(carregar_aviso_privacidade()), color=COR_TEXTO, width="100%"),
            rx.link(rx.button("Voltar ao login", size="3", background=COR_AZUL), href="/login"),
            align="center",
            spacing="4",
            padding="40px 32px",
            background="white",
            border=f"1px solid {COR_BORDA}",
            border_radius="16px",
            box_shadow="0 2px 8px rgba(18, 60, 107, 0.06)",
            width="min(100%, 760px)",
        )
    )


def area_inicial(perfil: str, titulo: str, sigla: str, nome_perfil: str, conteudo: rx.Component) -> rx.Component:
    return protegido(
        perfil,
        rx.box(
            cabecalho(titulo, f"Área inicial — {nome_perfil}", sigla),
            rx.center(
                rx.vstack(
                    rx.text("Olá, ", AuthState.nome, weight="bold", size="5", color=COR_TEXTO),
                    rx.text(f"Perfil: {nome_perfil}", size="2", color=COR_SECUNDARIA),
                    conteudo,
                    spacing="3",
                    padding="28px 32px",
                    background="white",
                    border=f"1px solid {COR_BORDA}",
                    border_radius="12px",
                    width="min(100%, 772px)",
                ),
                padding="40px 16px",
                width="100%",
            ),
            background=COR_FUNDO,
            font_family="Inter, sans-serif",
            min_height="100vh",
            width="100%",
        ),
    )


def area_recepcao() -> rx.Component:
    return area_inicial(
        "RECEPCAO_TRIAGEM",
        "RECEPÇÃO/TRIAGEM",
        "R",
        "Recepção/Triagem",
        rx.link(rx.button("Identificar paciente", size="3", background=COR_AZUL), href="/recepcao/pacientes"),
    )


def area_medico() -> rx.Component:
    return area_inicial("MEDICO", "MÉDICO", "M", "Médico", rx.text("As funções do Médico ainda estão em construção.", size="2", color=COR_SECUNDARIA))


def area_admin() -> rx.Component:
    return area_inicial(
        "ADMINISTRADOR",
        "ADMINISTRADOR",
        "A",
        "Administrador",
        rx.text("As funções do Administrador ainda estão em construção.", size="2", color=COR_SECUNDARIA),
    )


def opcao_sintoma(sintoma: dict[str, Any]) -> rx.Component:
    return rx.button(
        sintoma["nome"],
        on_click=[FichaState.alternar_sintoma(sintoma["id"], True), SeletorSintomasState.limpar_busca],
        variant="ghost",
        color_scheme="gray",
        justify="start",
        white_space="normal",
        text_align="left",
        height="auto",
        min_height="2rem",
        padding="0.4rem 0.5rem",
        width="100%",
    )


def sintoma_selecionado(sintoma: dict[str, Any]) -> rx.Component:
    selecionado = FichaState.sintoma_ids_selecionados.contains(sintoma["id"])
    return rx.cond(
        selecionado,
        rx.hstack(
            rx.text(
                sintoma["nome"],
                min_width="0",
                white_space="normal",
                line_height="1.35",
            ),
            rx.spacer(),
            rx.button(
                "×",
                on_click=FichaState.alternar_sintoma(sintoma["id"], False),
                aria_label="Remover sintoma",
                variant="ghost",
                color_scheme="gray",
                size="2",
                flex_shrink="0",
            ),
            align="center",
            spacing="2",
            border="1px solid var(--gray-5)",
            border_radius="0.375rem",
            padding="0.35rem 0.5rem",
            width="100%",
        ),
    )


def recepcao_ficha() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Ficha de atendimento", size="7"),
                rx.cond(
                    FichaState.paciente != {},
                    rx.vstack(
                        rx.text("Paciente: ", FichaState.paciente["nome"], weight="medium"),
                        rx.text("CPF: ", FichaState.cpf_exibido, size="2", color_scheme="gray"),
                        spacing="1",
                        align="start",
                    ),
                ),
                rx.cond(
                    FichaState.mensagem != "",
                    rx.callout(FichaState.mensagem, color_scheme=rx.cond(FichaState.erro, "red", "blue")),
                ),
                rx.heading("Sintomas", size="5"),
                rx.text("Selecione um ou mais sintomas, ou informe a queixa geral abaixo.", size="2", color_scheme="gray"),
                rx.cond(
                    FichaState.carregando,
                    rx.spinner(),
                    rx.vstack(
                        rx.text("Adicionar sintoma", size="2", weight="medium"),
                        rx.popover.root(
                            rx.popover.trigger(
                                rx.button(
                                    "Pesquisar ou selecionar sintoma...",
                                    variant="soft",
                                    color_scheme="gray",
                                    justify="between",
                                    width="100%",
                                )
                            ),
                            rx.popover.content(
                                rx.vstack(
                                    rx.input(
                                        placeholder="Pesquisar por nome...",
                                        value=SeletorSintomasState.busca,
                                        on_change=SeletorSintomasState.set_busca,
                                        width="100%",
                                        auto_focus=True,
                                    ),
                                    rx.box(
                                        rx.vstack(
                                            rx.foreach(
                                                FichaState.catalogo_sintomas,
                                                lambda sintoma: rx.cond(
                                                    (~FichaState.sintoma_ids_selecionados.contains(sintoma["id"].to(int)))
                                                    & sintoma["nome"].to(str).lower().contains(
                                                        SeletorSintomasState.busca.strip().lower()
                                                    ),
                                                    opcao_sintoma(sintoma),
                                                ),
                                            ),
                                            spacing="1",
                                            align="stretch",
                                            width="100%",
                                        ),
                                        max_height="15rem",
                                        overflow_y="auto",
                                        width="100%",
                                    ),
                                    spacing="2",
                                    align="stretch",
                                    width="100%",
                                ),
                                width="min(34rem, calc(100vw - 3rem))",
                            ),
                        ),
                        rx.text("Sintomas selecionados", size="2", weight="medium", margin_top="2"),
                        rx.cond(
                            FichaState.sintoma_ids_selecionados.length() > 0,
                            rx.vstack(
                                rx.foreach(FichaState.catalogo_sintomas, sintoma_selecionado),
                                spacing="1",
                                align="stretch",
                                width="100%",
                            ),
                            rx.text("Nenhum sintoma selecionado.", size="2", color_scheme="gray"),
                        ),
                        spacing="2",
                        align="stretch",
                        width="100%",
                    ),
                ),
                rx.heading("Observação / queixa geral", size="5"),
                rx.text_area(
                    value=FichaState.observacao,
                    on_change=FichaState.set_observacao,
                    placeholder="Descreva a queixa geral do paciente (opcional se houver sintoma).",
                    width="100%",
                ),
                rx.button("Salvar ficha", on_click=FichaState.salvar, loading=FichaState.salvando),
                spacing="4",
                width="100%",
                align="stretch",
            ),
            width="100%",
            max_width="96rem",
        ),
        padding="2rem",
        width="100%",
    )


app = rx.App(stylesheets=["https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap"])
app.add_page(index, route="/", on_load=AuthState.ir_para_inicio)
app.add_page(login, route="/login", title="Login")
app.add_page(login_codigo, route="/login/codigo", title="Código de acesso", on_load=AuthState.exigir_login_pendente)
app.add_page(senha_email, route="/senha", title="Redefinir senha", on_load=SenhaState.iniciar)
app.add_page(senha_codigo, route="/senha/codigo", title="Redefinir senha", on_load=SenhaState.exigir_email)
app.add_page(senha_nova, route="/senha/nova", title="Nova senha", on_load=SenhaState.exigir_codigo)
app.add_page(senha_sucesso, route="/senha/sucesso", title="Senha redefinida")
app.add_page(privacidade, route="/privacidade", title="Aviso de privacidade")
app.add_page(carregando, route="/sair/inatividade", title="Sessão encerrada", on_load=AuthState.sair_por_inatividade)
app.add_page(area_recepcao, route="/recepcao", title="Recepção/Triagem", on_load=AuthState.verificar_sessao("RECEPCAO_TRIAGEM"))
app.add_page(area_medico, route="/medico", title="Médico", on_load=AuthState.verificar_sessao("MEDICO"))
app.add_page(area_admin, route="/admin", title="Administrador", on_load=AuthState.verificar_sessao("ADMINISTRADOR"))
def pagina_recepcao_pacientes() -> rx.Component:
    return protegido("RECEPCAO_TRIAGEM", recepcao_pacientes())


def pagina_recepcao_ficha() -> rx.Component:
    return protegido("RECEPCAO_TRIAGEM", recepcao_ficha())


app.add_page(
    pagina_recepcao_pacientes,
    route="/recepcao/pacientes",
    title="Identificação de Paciente",
    on_load=AuthState.verificar_sessao("RECEPCAO_TRIAGEM"),
)
app.add_page(
    pagina_recepcao_ficha,
    route="/recepcao/ficha/[id]",
    title="Ficha de atendimento",
    on_load=[AuthState.verificar_sessao("RECEPCAO_TRIAGEM"), FichaState.carregar_da_rota],
)

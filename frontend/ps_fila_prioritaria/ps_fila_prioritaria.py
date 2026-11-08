"""Fluxo de identificação e cadastro de Paciente da Recepção/Triagem."""

import asyncio
import os
import unicodedata
from datetime import datetime, timedelta, timezone
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


# Códigos da API da ficha e da classificação traduzidos para a Recepção/Triagem.
MENSAGENS_ERRO_API = {
    "FICHA_NAO_FINALIZADA_EXISTENTE": "Este paciente já está na fila de atendimento (ficha aguardando ou chamada). Não é possível abrir outra ficha.",
    "FICHA_FORA_DA_TRIAGEM": "Esta ficha já saiu da triagem e não pode mais ser alterada aqui.",
    "SINTOMA_LIVRE_DESCRICAO_INVALIDA": "Descreva o sintoma não listado com 3 a 80 caracteres.",
    "SINTOMA_LIVRE_PONTUACAO_INVALIDA": "Escolha a gravidade do sintoma não listado: 1, 2 ou 3.",
    "SINTOMA_LIVRE_DUPLICADO": "Há sintomas não listados repetidos.",
    "SINTOMA_LIVRE_EXISTE_NO_CATALOGO": "Um sintoma digitado já existe na lista: selecione-o na pesquisa.",
    "SINTOMAS_LIVRES_LIMITE": "Limite de 10 sintomas não listados por ficha.",
    "JUSTIFICATIVA_OBRIGATORIA": "A justificativa é obrigatória.",
    "PRIORIDADE_IGUAL_A_CALCULADA": "Essa já é a prioridade calculada. Escolha outra cor.",
    "PRIORIDADE_INVALIDA": "Escolha a prioridade.",
}
MENSAGEM_LIMITE_XANO ="O sistema recebeu muitos acessos ao mesmo tempo. Aguarde alguns segundos e tente novamente."


def _mensagem_erro(resposta: httpx.Response) -> str:
    """Extrai a mensagem pública devolvida pela API sem expor detalhes internos."""
    try:
        corpo: Any = resposta.json()
    except ValueError:
        return "Não foi possível concluir a solicitação."

    if isinstance(corpo, dict):
        mensagem = corpo.get("message") or corpo.get("error") or corpo.get("code")
        # Limite de requisições do plano gratuito do Xano (429, texto em inglês). Os 429 do nosso backend
        # ("Aguarde N segundos...") já vêm em português e seguem abaixo sem alteração.
        if getattr(resposta, "status_code", None) == 429 and isinstance(mensagem, str) and "requests per" in mensagem:
            return MENSAGEM_LIMITE_XANO
        if mensagem == "CPF_DUPLICADO":
            return "Já existe paciente com este CPF (CPF_DUPLICADO). Pesquise novamente para carregar o cadastro."
        if mensagem == "FICHA_SEM_SINTOMA_OU_OBSERVACAO":
            return "Informe ao menos um sintoma ou uma observação."
        if isinstance(mensagem, str) and mensagem.startswith("SINAL_VITAL_INVALIDO:"):
            campo = mensagem.split(":", 1)[1]
            return f"Valor fora do aceito em {NOME_SINAL_VITAL.get(campo, campo)}. Confira o número digitado."
        if isinstance(mensagem, str) and mensagem in MENSAGENS_ERRO_API:
            return MENSAGENS_ERRO_API[mensagem]
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


class TotemState(rx.State):
    """Tela pública do Totem (add-totem). Nenhum dado pessoal; a chave do dispositivo nunca vai ao navegador (D2)."""

    emitindo: bool = False
    codigo: str = ""
    tipo_emitido: str = ""
    erro: str = ""

    def emitir(self, tipo: str):
        self.erro = ""
        self.codigo = ""
        self.emitindo = True
        yield
        try:
            # A chave é lida aqui, no servidor, e não é guardada no estado (que é sincronizado com o navegador).
            resposta = api.requisitar(
                "POST",
                "XANO_TRIAGEM_API_URL",
                "/totem/tickets",
                json={"chave_dispositivo": os.getenv("TOTEM_CHAVE", ""), "tipo": tipo},
            )
        except (api.ConfiguracaoAusente, httpx.RequestError):
            resposta = None
        self.emitindo = False
        # Sem nova tentativa automática: repetir poderia emitir dois tickets (design, riscos).
        if resposta is None or not resposta.is_success:
            self.erro = "Não foi possível emitir o ticket."
            return
        dados = resposta.json()
        self.codigo = str(dados.get("codigo", ""))
        self.tipo_emitido = str(dados.get("tipo", ""))

    def concluir(self) -> None:
        self.codigo = ""
        self.tipo_emitido = ""
        self.erro = ""


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


def _timestamp_segundos(valor: Any) -> float | None:
    """Aceita timestamps Xano em milissegundos ou datas ISO."""
    if isinstance(valor, (int, float)):
        return valor / 1000 if valor > 100_000_000_000 else float(valor)
    if isinstance(valor, str):
        try:
            data = datetime.fromisoformat(valor.replace("Z", "+00:00"))
            return data.replace(tzinfo=timezone.utc).timestamp() if data.tzinfo is None else data.timestamp()
        except ValueError:
            return None
    return None


# Nome e cor de cada tipo na fila de pré-triagem (mesmas cores do Totem, tela 1/2 do Figma).
COR_SECUNDARIA_FILA = "#66707A"
APARENCIA_TIPO_TICKET = {
    "PEDIATRICO": ("Pediátrico", "#6554C0"),
    "PREFERENCIAL": ("Preferencial", "#ED8B00"),
    "NORMAL": ("Normal", "#1565C0"),
}
# O Brasil não tem horário de verão desde 2019: America/Sao_Paulo é sempre UTC-3. Evita depender do pacote tzdata no Windows.
FUSO_BRASILIA = timezone(timedelta(hours=-3))


def _hora_brasilia(valor: Any, segundos: bool = False) -> str:
    instante = _timestamp_segundos(valor)
    if instante is None:
        return "—"
    return datetime.fromtimestamp(instante, FUSO_BRASILIA).strftime("%H:%M:%S" if segundos else "%H:%M")


class FilaTicketsState(rx.State):
    tickets: list[dict[str, Any]] = []
    atualizado_em: str = ""
    mensagem: str = ""
    erro: bool = False
    monitorando: bool = False

    async def _requisitar(self, metodo: str, caminho: str, **kwargs: Any) -> httpx.Response | None:
        auth = await self.get_state(AuthState)
        try:
            resposta = api.requisitar(metodo, "XANO_TRIAGEM_API_URL", caminho, token=auth.token, **kwargs)
        except (api.ConfiguracaoAusente, httpx.RequestError):
            self.erro = True
            self.mensagem = "Não foi possível conectar à fila de pré-triagem."
            return None
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
        if not resposta.is_success:
            self.erro = True
            self.mensagem = _mensagem_erro(resposta)
            return None
        return resposta

    async def carregar(self) -> None:
        resposta = await self._requisitar("GET", "/tickets")
        if resposta is not None:
            corpo = resposta.json() or {}
            self.tickets = corpo.get("tickets", []) if isinstance(corpo, dict) else corpo
            agora = _timestamp_segundos(corpo.get("agora")) if isinstance(corpo, dict) else None
            parametros = corpo if isinstance(corpo, dict) else {}
            intervalo = int(parametros.get("intervalo_segundos") or 0)
            intervalo_repeticao = int(parametros.get("intervalo_repeticao_segundos") or 0)
            tentativas_maximas = int(parametros.get("tentativas_maximas") or 0)
            for ticket in self.tickets:
                ticket.setdefault("presente", False)
                tentativas = int(ticket.get("tentativas") or 0)
                # Chamada manual (chamada-manual-pre-triagem, D1): 30 s depois da 1ª chamada, 10 s depois das seguintes.
                espera = intervalo if tentativas <= 1 else intervalo_repeticao
                chamado = _timestamp_segundos(ticket.get("chamado_em"))
                ticket["segundos_restantes"] = max(0, int(chamado + espera - agora + 0.999)) if chamado is not None and agora is not None and espera > 0 else -1
                # Sem o limite configurado, a tela oferece o botão e o Xano decide (LIMITE_DE_CHAMADAS).
                ticket["pode_chamar_novamente"] = tentativas_maximas <= 0 or tentativas < tentativas_maximas
                prefixo = {"PEDIATRICO": "C", "PREFERENCIAL": "P", "NORMAL": "N"}.get(ticket.get("tipo"), "?")
                ticket["senha_exibida"] = f"{prefixo}-{int(ticket.get('numero') or 0):03d}"
                ticket["nome_tipo"], ticket["cor_tipo"] = APARENCIA_TIPO_TICKET.get(ticket.get("tipo"), ("—", COR_SECUNDARIA_FILA))
                ticket["emitido_hora"] = _hora_brasilia(ticket.get("emitido_em"))
            self.atualizado_em = _hora_brasilia(corpo.get("agora") if isinstance(corpo, dict) else None, segundos=True)

    @rx.var
    def chamados(self) -> list[dict[str, Any]]:
        return [ticket for ticket in self.tickets if ticket.get("status") == "CHAMADO"]

    @rx.var
    def aguardando(self) -> list[dict[str, Any]]:
        return [ticket for ticket in self.tickets if ticket.get("status") == "AGUARDANDO"]

    @rx.var
    def resumo_tipos(self) -> list[dict[str, Any]]:
        """Quantos tickets de cada tipo aguardam chamada, na ordem do Totem."""
        return [
            {"nome": nome, "cor": cor, "quantidade": sum(1 for t in self.tickets if t.get("status") == "AGUARDANDO" and t.get("tipo") == tipo)}
            for tipo, (nome, cor) in APARENCIA_TIPO_TICKET.items()
        ]

    @rx.event(background=True)
    async def monitorar(self):
        """Só atualiza a tela: recarrega do Xano a cada 10 s e desconta a contagem a cada 1 s. Nunca envia ação."""
        async with self:
            if self.monitorando:
                return
            self.monitorando = True
        try:
            ciclos = 0
            while True:
                await asyncio.sleep(1)
                async with self:
                    conexao = app.event_namespace
                    if (self.router.page.path != "/recepcao/fila" or conexao is None
                            or self.router.session.client_token not in conexao.token_to_sid):
                        return
                    ciclos += 1
                    if ciclos % 10 == 0:
                        await self.carregar()
                    else:
                        tickets = [dict(ticket) for ticket in self.tickets]
                        for ticket in tickets:
                            if ticket.get("status") == "CHAMADO" and not ticket.get("presente"):
                                restante = ticket.get("segundos_restantes", -1)
                                if restante > 0:
                                    ticket["segundos_restantes"] = restante - 1
                        self.tickets = tickets
        finally:
            async with self:
                self.monitorando = False

    async def proximo(self) -> None:
        self.erro = False
        self.mensagem = ""
        resposta = await self._requisitar("POST", "/tickets/proximo")
        if resposta is not None:
            self.mensagem = "Ticket chamado."
            await self.carregar()

    async def acao(self, ticket_id: int, acao: str) -> None:
        self.erro = False
        self.mensagem = ""
        resposta = await self._requisitar("POST", f"/tickets/{ticket_id}/acao", json={"acao": acao})
        if resposta is not None:
            self.mensagem = "Operação registrada."
            await self.carregar()

    async def chamar_novamente(self, ticket_id: int) -> None:
        await self.acao(ticket_id, "REPETIR")
        if not self.erro:
            self.mensagem = "Ticket chamado novamente."

    async def nao_compareceu(self, ticket_id: int) -> None:
        await self.acao(ticket_id, "AUSENCIA")
        if not self.erro:
            self.mensagem = "Não comparecimento registrado."

    async def identificar(self, ticket_id: int):
        paciente = await self.get_state(PacienteState)
        paciente._resetar_paciente_atual()
        paciente.ticket_id = ticket_id
        return rx.redirect("/recepcao/pacientes")


# Sinais vitais da ficha (add-classificacao-prioridade). A pontuação e a cor são calculadas no Xano.
CAMPOS_SINAIS_VITAIS = ["pa_sistolica", "fc", "fr", "temperatura", "spo2", "glicemia"]
NOME_SINAL_VITAL = {
    "pa_sistolica": "PA sistólica",
    "fc": "frequência cardíaca",
    "fr": "frequência respiratória",
    "temperatura": "temperatura",
    "spo2": "SpO2",
    "glicemia": "glicemia",
}
NOME_CONDICAO = {"NENHUMA": "Nenhuma", "IDOSO": "Idoso", "CRIANCA": "Criança", "GESTANTE": "Gestante"}
LIMITE_SINTOMAS_LIVRES = 10
_PENDENCIA_SINAL = {
    "PA_SISTOLICA_NAO_INFORMADO": "Informe a PA sistólica.",
    "FC_NAO_INFORMADO": "Informe a frequência cardíaca.",
    "FR_NAO_INFORMADO": "Informe a frequência respiratória.",
    "TEMPERATURA_NAO_INFORMADO": "Informe a temperatura.",
    "SPO2_NAO_INFORMADO": "Informe a SpO2.",
    "TABELA_ADULTA_NAO_APLICAVEL": "Menor de 16 anos ou gestante: a tabela adulta não se aplica. Defina a prioridade manualmente, com justificativa.",
    "SEM_SINTOMA_OU_OBSERVACAO": "Informe ao menos um sintoma ou uma observação.",
    "PARAMETRO_NAO_CONFIGURADO": "Os parâmetros da classificação não estão configurados.",
}


def _texto_pendencia(codigo: str) -> str:
    if codigo.startswith("FAIXA_NAO_CONFIGURADA:"):
        return f"Faixa de pontuação não configurada para {codigo.split(':', 1)[1]}."
    return _PENDENCIA_SINAL.get(codigo, codigo)


def _texto_sinal(valor: Any) -> str:
    """Mostra o número salvo no campo, com vírgula decimal; null vira campo vazio."""
    if valor is None or valor == "":
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return str(valor).replace(".", ",")


def _normalizar_texto(texto: str) -> str:
    """Compara nomes de sintomas sem diferenciar maiúsculas, acentos e espaços extras (como o Xano)."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sem_acento.casefold().split())


class FichaState(rx.State):
    """Estado da ficha de triagem, separado do cadastro de Paciente.

    A regra clínica (escore, cor, pendências) é calculada no Xano; aqui só ficam os valores digitados,
    o envio e a exibição do resultado (add-classificacao-prioridade, D7 e D8).
    """

    ficha_id: int = 0
    ficha: dict[str, Any] = {}
    paciente: dict[str, Any] = {}
    catalogo_sintomas: list[dict[str, Any]] = []
    sintoma_ids_selecionados: list[int] = []
    observacao: str = ""
    # Sintomas digitados pela Recepção/Triagem: [{descricao, pontuacao}] (D9).
    sintomas_livres: list[dict[str, Any]] = []
    # Sinais vitais como texto dos campos; vazio = não medido.
    sinais: dict[str, str] = {campo: "" for campo in CAMPOS_SINAIS_VITAIS}
    glicemia_gravidade: bool = False
    gestante: bool = False
    classificacao: dict[str, Any] = {}
    sintomas_alterados: bool = False
    observacao_alterada: bool = False
    livres_alterados: bool = False
    sinais_alterados: bool = False
    carregando: bool = False
    salvando: bool = False
    mensagem: str = ""
    erro: bool = False
    # Ajuste manual da prioridade (D6).
    ajuste_aberto: bool = False
    ajuste_prioridade: str = ""
    ajuste_justificativa: str = ""
    ajuste_erro: str = ""
    ajustando: bool = False

    @rx.var
    def cpf_exibido(self) -> str:
        return mascarar_cpf(self.paciente.get("cpf"))

    @rx.var
    def prioridade_exibida(self) -> str:
        """Prioridade atual gravada ou, sem ajuste salvo, a calculada agora pelo Xano."""
        return str(self.classificacao.get("prioridade_atual") or self.classificacao.get("prioridade_calculada") or "")

    @rx.var
    def prioridade_calculada(self) -> str:
        return str(self.classificacao.get("prioridade_calculada") or "")

    @rx.var
    def ajustada_manualmente(self) -> bool:
        return bool(self.classificacao.get("justificativa_ajuste"))

    @rx.var
    def resumo_escore(self) -> str:
        total = self.classificacao.get("escore_total")
        sintomas = self.classificacao.get("escore_sintomas")
        sinais = self.classificacao.get("escore_sinais")
        if total is None:
            return f"Escore incompleto (sintomas {sintomas or 0})"
        critico = " · item isolado de 3 pontos → Vermelha" if self.classificacao.get("item_critico") else ""
        return f"Escore total {total} (sintomas {sintomas or 0} · sinais vitais {sinais or 0}){critico}"

    @rx.var
    def pendencias_texto(self) -> list[str]:
        return [_texto_pendencia(str(p)) for p in (self.classificacao.get("pendencias") or [])]

    @rx.var
    def condicao_texto(self) -> str:
        return NOME_CONDICAO.get(str(self.classificacao.get("condicao_prioritaria") or "NENHUMA"), "Nenhuma")

    @rx.var
    def idade_texto(self) -> str:
        idade = self.paciente.get("idade")
        return f"{idade} anos" if idade is not None else "Idade não informada"

    def _limpar_feedback(self) -> None:
        self.mensagem = ""
        self.erro = False

    async def _requisitar(self, metodo: str, caminho: str, **kwargs: Any) -> httpx.Response | None:
        """Chama o grupo Triagem com o token da sessão; 401 encerra a sessão local (D7)."""
        auth = await self.get_state(AuthState)
        try:
            resposta = api.requisitar(metodo, "XANO_TRIAGEM_API_URL", caminho, token=auth.token, **kwargs)
        except api.ConfiguracaoAusente:
            self.mensagem = "Configure XANO_TRIAGEM_API_URL para conectar a ficha à API do PS."
            self.erro = True
            return None
        except httpx.RequestError:
            self.mensagem = "Não foi possível conectar à API de Fichas."
            self.erro = True
            return None
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return None
        return resposta

    def _carregar_resposta_ficha(self, dados: dict[str, Any]) -> None:
        ficha = dados.get("ficha") or {}
        self.ficha = dict(ficha)
        self.ficha_id = int(ficha.get("id", self.ficha_id))
        self.paciente = dict(dados.get("paciente") or {})
        self.observacao = str(ficha.get("observacao") or "")
        self.sintoma_ids_selecionados = sorted(int(sintoma["id"]) for sintoma in (dados.get("sintomas") or []))
        self.sintomas_livres = [
            {"descricao": str(livre.get("descricao") or ""), "pontuacao": int(livre.get("pontuacao") or 0)}
            for livre in (dados.get("sintomas_livres") or [])
        ]
        self.sinais = {campo: _texto_sinal(ficha.get(campo)) for campo in CAMPOS_SINAIS_VITAIS}
        self.glicemia_gravidade = bool(ficha.get("glicemia_sinais_gravidade"))
        self.gestante = bool(ficha.get("gestante"))
        self.classificacao = dict(dados.get("classificacao") or {})
        self.sintomas_alterados = False
        self.observacao_alterada = False
        self.livres_alterados = False
        self.sinais_alterados = False

    async def _recarregar(self) -> bool:
        resposta_ficha = await self._requisitar("GET", f"/fichas/{self.ficha_id}")
        if resposta_ficha is None:
            return False
        resposta_sintomas = await self._requisitar("GET", "/sintomas")
        if resposta_sintomas is None:
            return False
        self._carregar_resposta_ficha(resposta_ficha.json())
        self.catalogo_sintomas = sorted(
            list(resposta_sintomas.json() or []),
            key=lambda sintoma: str(sintoma["nome"]).casefold(),
        )
        return True

    async def carregar(self, ficha_id: str | int) -> None:
        """Recupera catálogo ativo e estado persistido para edição da ficha."""
        try:
            self.ficha_id = int(ficha_id)
        except (TypeError, ValueError):
            self.mensagem = "Ficha inválida."
            self.erro = True
            return
        self.carregando = True
        self._limpar_feedback()
        try:
            await self._recarregar()
        finally:
            self.carregando = False

    async def carregar_da_rota(self) -> None:
        ficha_id = self.router.page.params.get("id", "")
        await self.carregar(ficha_id)

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

    def set_sinal(self, campo: str, valor: str) -> None:
        if campo in CAMPOS_SINAIS_VITAIS:
            self.sinais = {**self.sinais, campo: valor}
            self.sinais_alterados = True

    def set_glicemia_gravidade(self, marcado: bool) -> None:
        self.glicemia_gravidade = bool(marcado)
        self.sinais_alterados = True

    def set_gestante(self, marcado: bool) -> None:
        self.gestante = bool(marcado)
        self.sinais_alterados = True

    def adicionar_sintoma_livre(self, descricao: str, pontuacao: int) -> None:
        """Valida na tela o que o Xano também valida, para avisar antes de salvar (D9)."""
        texto = " ".join(str(descricao or "").split())
        if not 3 <= len(texto) <= 80:
            self.mensagem = "Descreva o sintoma com 3 a 80 caracteres."
            self.erro = True
            return
        if int(pontuacao) not in (1, 2, 3):
            self.mensagem = "Escolha a gravidade do sintoma: 1, 2 ou 3."
            self.erro = True
            return
        chave = _normalizar_texto(texto)
        if any(_normalizar_texto(str(s.get("nome"))) == chave for s in self.catalogo_sintomas):
            self.mensagem = f"\"{texto}\" já está na lista de sintomas: selecione-o na pesquisa."
            self.erro = True
            return
        if any(_normalizar_texto(str(s.get("descricao"))) == chave for s in self.sintomas_livres):
            self.mensagem = f"\"{texto}\" já foi adicionado."
            self.erro = True
            return
        if len(self.sintomas_livres) >= LIMITE_SINTOMAS_LIVRES:
            self.mensagem = f"Limite de {LIMITE_SINTOMAS_LIVRES} sintomas não listados por ficha."
            self.erro = True
            return
        self.sintomas_livres = [*self.sintomas_livres, {"descricao": texto, "pontuacao": int(pontuacao)}]
        self.livres_alterados = True
        self._limpar_feedback()

    def remover_sintoma_livre(self, descricao: str) -> None:
        self.sintomas_livres = [s for s in self.sintomas_livres if s.get("descricao") != descricao]
        self.livres_alterados = True

    def _sinais_para_envio(self) -> dict[str, Any] | None:
        """Converte os campos em números; vazio vira null. Retorna None e avisa se algum não for número."""
        dados: dict[str, Any] = {"glicemia_sinais_gravidade": self.glicemia_gravidade, "gestante": self.gestante}
        for campo in CAMPOS_SINAIS_VITAIS:
            texto = str(self.sinais.get(campo) or "").strip().replace(",", ".")
            if not texto:
                dados[campo] = None
                continue
            try:
                numero = float(texto)
            except ValueError:
                self.mensagem = f"Valor inválido em {NOME_SINAL_VITAL[campo]}."
                self.erro = True
                return None
            dados[campo] = numero if campo == "temperatura" else (int(numero) if numero.is_integer() else numero)
        return dados

    async def salvar(self) -> AsyncIterator[None]:
        """Envia o estado final de sintomas, observação e sinais vitais; o Xano valida e recalcula a cor."""
        if self.salvando:
            return

        if not self.ficha_id:
            self.mensagem = "Nenhuma ficha foi carregada para salvar."
            self.erro = True
            return

        if not self.sintoma_ids_selecionados and not self.sintomas_livres and not self.observacao.strip():
            self.mensagem = "Informe ao menos um sintoma ou uma observação/queixa."
            self.erro = True
            return

        self._limpar_feedback()
        dados: dict[str, Any] = {}
        if self.sintomas_alterados:
            # Uma lista vazia é uma coleção final válida e não equivale a campo omitido.
            dados["sintoma_ids"] = self.sintoma_ids_selecionados
        if self.observacao_alterada:
            dados["observacao"] = self.observacao
        if self.livres_alterados:
            dados["sintomas_livres"] = self.sintomas_livres
        if self.sinais_alterados:
            sinais = self._sinais_para_envio()
            if sinais is None:
                return
            dados["sinais_vitais"] = sinais
        if not dados:
            self.mensagem = "Nenhuma alteração para salvar."
            return

        self.salvando = True
        # Entrega o loading antes das requisições de PATCH e GET.
        yield
        try:
            resposta = await self._requisitar("PATCH", f"/fichas/{self.ficha_id}", json=dados)
            if resposta is not None:
                if await self._recarregar():
                    self.mensagem = "Ficha salva. A prioridade foi recalculada."
                    self.erro = False
                elif not self.mensagem:
                    self.mensagem = "A ficha foi salva, mas não foi possível recarregá-la."
                    self.erro = True
        finally:
            self.salvando = False

    def abrir_ajuste(self) -> None:
        self.ajuste_prioridade = ""
        self.ajuste_justificativa = ""
        self.ajuste_erro = ""
        self.ajuste_aberto = True

    def fechar_ajuste(self) -> None:
        self.ajuste_aberto = False

    def set_ajuste_aberto(self, aberto: bool) -> None:
        self.ajuste_aberto = bool(aberto)

    def set_ajuste_prioridade(self, valor: str) -> None:
        self.ajuste_prioridade = valor

    def set_ajuste_justificativa(self, valor: str) -> None:
        self.ajuste_justificativa = valor

    async def confirmar_ajuste(self) -> None:
        """Ajuste manual ou classificação manual excepcional, sempre com justificativa (D6)."""
        if self.ajuste_prioridade not in ("VERMELHA", "AMARELA", "AZUL"):
            self.ajuste_erro = "Escolha a prioridade."
            return
        if not self.ajuste_justificativa.strip():
            self.ajuste_erro = "A justificativa é obrigatória."
            return
        if self.prioridade_calculada and self.ajuste_prioridade == self.prioridade_calculada:
            self.ajuste_erro = "Essa já é a prioridade calculada. Escolha outra cor."
            return
        if self.sintomas_alterados or self.observacao_alterada or self.livres_alterados or self.sinais_alterados:
            self.ajuste_erro = "Salve a ficha antes de ajustar a prioridade: salvar recalcula a cor e descarta ajustes."
            return
        self.ajuste_erro = ""
        self._limpar_feedback()
        self.ajustando = True
        try:
            resposta = await self._requisitar(
                "POST",
                f"/fichas/{self.ficha_id}/prioridade",
                json={"prioridade": self.ajuste_prioridade, "justificativa": self.ajuste_justificativa.strip()},
            )
            if resposta is None:
                self.ajuste_erro = self.mensagem
                self._limpar_feedback()
                return
            self.ajuste_aberto = False
            if await self._recarregar():
                self.mensagem = "Prioridade ajustada. A justificativa ficou registrada na auditoria."
                self.erro = False
        finally:
            self.ajustando = False


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


def cabecalho(titulo: str, subtitulo: str, com_sessao: bool = True) -> rx.Component:
    return rx.hstack(
        # Ícone Prioriza branco no lugar da sigla do perfil (Figma: Marca/Ícone Prioriza, versão branca).
        rx.image(src="/logo/icone-prioriza-branco.svg", alt="Prioriza", width="48px", height="48px", flex_shrink="0"),
        rx.vstack(
            rx.text(titulo, weight="bold", size="5", color="white"),
            *([rx.text(subtitulo, size="2", color="#CCDEF0")] if subtitulo else []),
            spacing="1",
        ),
        rx.spacer(),
        # Telas públicas (Totem) não têm sessão da equipe.
        *([sessao_no_cabecalho()] if com_sessao else []),
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
                rx.input(type="date", value=PacienteState.data_nascimento, on_change=PacienteState.set_data_nascimento, on_blur=PacienteState.set_data_nascimento, size="3", width="100%"),
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
    """Ícone Prioriza das telas de acesso (Figma: Marca/Ícone Prioriza, versão colorida)."""
    return rx.image(src="/logo/icone-prioriza.svg", alt="Prioriza", width="64px", height="64px")


def logo_prioriza_completo() -> rx.Component:
    """Logo com o nome, usado só no login (Figma: Marca/Logo Prioriza, versão colorida)."""
    return rx.image(src="/logo/logo-prioriza.svg", alt="Prioriza · Fila de atendimento", width="260px", height="80px")


def cartao_acesso(icone: rx.Component, titulo: str, subtitulo: rx.Component | str, *corpo: rx.Component, on_submit: Any = None) -> rx.Component:
    """Cartão centralizado das telas de acesso (login, código e redefinição de senha), como no Figma."""
    cartao = rx.vstack(
        icone,
        *([rx.text(titulo, weight="bold", size="5", color=COR_TEXTO)] if titulo else []),
        *([] if subtitulo == "" else [rx.text(subtitulo, size="2", color=COR_SECUNDARIA, text_align="center") if isinstance(subtitulo, str) else subtitulo]),
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
        logo_prioriza_completo(),
        "",
        "",
        campo_rotulado("E-MAIL", rx.input(name="email", type="email", placeholder="nome@ps.com.br", size="3", width="100%")),
        campo_rotulado("SENHA", rx.input(name="senha", type="password", placeholder="••••••••", size="3", width="100%")),
        mensagens_acesso(AuthState.mensagem),
        botao_principal("Entrar", AuthState.entrando),
        rx.link("Esqueci minha senha", href="/senha", size="2", color=COR_AZUL),
        rx.divider(color=COR_BORDA),
        # Só ida: o Totem é público e não tem caminho de volta ao login (decisão do PO, 08/11/2026).
        rx.link("Abrir o Totem de autoatendimento →", href="/totem", size="2", color=COR_SECUNDARIA),
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


# Tipos de ticket do Totem (add-totem D5), na ordem e com as cores da tela 1 do Figma.
TIPOS_TOTEM = [
    ("PEDIATRICO", "C", "Pediátrico", "#6554C0", "Crianças de até 11 anos."),
    ("PREFERENCIAL", "P", "Preferencial", "#ED8B00", "Pessoas com 60 anos ou mais, gestantes e demais pessoas com direito a atendimento preferencial."),
    ("NORMAL", "N", "Normal", COR_AZUL, "Todos os demais pacientes."),
]
NOME_TIPO_TOTEM = {tipo: nome for tipo, _, nome, _, _ in TIPOS_TOTEM}


def cartao_tipo_totem(tipo: str, letra: str, nome: str, cor: str, descricao: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.center(rx.text(letra, weight="bold", size="6", color=cor), width="64px", height="64px", border_radius="50%", background=f"{cor}1F"),
            rx.text(nome, weight="bold", size="7", color=COR_TEXTO),
            rx.text(descricao, size="3", color=COR_SECUNDARIA),
            rx.spacer(),
            rx.divider(color=COR_BORDA),
            rx.text("Toque para retirar", weight="bold", size="3", color=cor),
            spacing="3",
            align="start",
            height="100%",
            padding="28px",
        ),
        on_click=TotemState.emitir(tipo),
        cursor="pointer",
        background="white",
        border=f"1px solid {COR_BORDA}",
        border_top=f"6px solid {cor}",
        border_radius="12px",
        box_shadow="0 2px 8px rgba(18, 60, 107, 0.06)",
        min_height="320px",
        flex="1",
        _hover={"box_shadow": "0 6px 16px rgba(18, 60, 107, 0.14)"},
        aria_label=f"Retirar ticket {nome}",
    )


def aviso_totem() -> rx.Component:
    """Estados da emissão por cima da escolha: emitindo (1a), emitido (1b) e falha (1c)."""
    conteudo = rx.cond(
        TotemState.emitindo,
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Emitindo seu ticket…", weight="bold", size="6", color=COR_TEXTO),
            rx.text("Aguarde um instante.", size="3", color=COR_SECUNDARIA),
            align="center",
            spacing="4",
        ),
        rx.cond(
            TotemState.codigo != "",
            rx.vstack(
                rx.text("SEU TICKET", weight="medium", size="2", color=COR_SECUNDARIA),
                rx.text(TotemState.codigo, weight="bold", font_size="88px", line_height="1", color=COR_MARINHO),
                rx.match(TotemState.tipo_emitido, *[(t, rx.text(n, weight="medium", size="4", color=COR_TEXTO)) for t, n in NOME_TIPO_TOTEM.items()], rx.fragment()),
                rx.text(
                    "Aguarde a chamada da Recepção/Triagem e acompanhe o painel da sala de espera.",
                    size="3",
                    color=COR_SECUNDARIA,
                    text_align="center",
                ),
                rx.button("Concluir", on_click=TotemState.concluir, size="4", background=COR_AZUL, width="100%"),
                align="center",
                spacing="4",
            ),
            rx.vstack(
                rx.center(rx.text("!", weight="bold", size="7", color=COR_ERRO), width="72px", height="72px", border_radius="50%", background=f"{COR_ERRO}1F"),
                rx.text(TotemState.erro, weight="bold", size="6", color=COR_TEXTO, text_align="center"),
                rx.text("Toque em Voltar para tentar de novo ou procure a recepção.", size="3", color=COR_SECUNDARIA, text_align="center"),
                rx.button("Voltar", on_click=TotemState.concluir, size="4", background=COR_AZUL, width="100%"),
                align="center",
                spacing="4",
            ),
        ),
    )
    return rx.cond(
        TotemState.emitindo | (TotemState.codigo != "") | (TotemState.erro != ""),
        rx.center(
            rx.box(conteudo, background="white", border_radius="16px", padding="40px", width="min(100%, 480px)", box_shadow="0 8px 24px rgba(0, 0, 0, 0.18)"),
            position="fixed",
            inset="0",
            background="rgba(0, 0, 0, 0.45)",
            z_index="10",
            padding="16px",
        ),
    )


def totem() -> rx.Component:
    # Tela 1 do Figma: pública, sem login e sem pedir dado pessoal (spec totem).
    return rx.box(
        cabecalho("TOTEM DE AUTOATENDIMENTO", "", com_sessao=False),
        rx.vstack(
            rx.text("Bem-vindo ao Pronto-Socorro", weight="bold", size="8", color=COR_TEXTO),
            rx.text("Escolha o tipo de atendimento e toque para retirar seu ticket de chegada", size="3", color=COR_SECUNDARIA),
            rx.box(height="12px"),
            rx.flex(*[cartao_tipo_totem(*t) for t in TIPOS_TOTEM], gap="24px", width="100%", direction={"base": "column", "md": "row"}),
            spacing="2",
            padding="48px",
            width="100%",
            max_width="1280px",
            margin="0 auto",
        ),
        rx.center(
            rx.text("Em caso de dúvida, procure a recepção", size="2", color=COR_SECUNDARIA),
            border_top=f"1px solid {COR_BORDA}",
            padding="16px",
            width="100%",
        ),
        aviso_totem(),
        background=COR_FUNDO,
        font_family="Inter, sans-serif",
        min_height="100vh",
        width="100%",
    )


def area_inicial(perfil: str, titulo: str, nome_perfil: str, conteudo: rx.Component) -> rx.Component:
    return protegido(
        perfil,
        rx.box(
            cabecalho(titulo, f"Área inicial — {nome_perfil}"),
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
        "Recepção/Triagem",
        rx.vstack(
            rx.link(rx.button("Fila de pré-triagem", size="3", background=COR_AZUL), href="/recepcao/fila"),
            rx.button("Identificar paciente sem ticket", size="3", variant="outline", on_click=PacienteState.iniciar_sem_ticket),
        ),
    )


def chip_tipo_ticket(ticket: dict[str, Any]) -> rx.Component:
    """Chip colorido do tipo, como na tela 2 do Figma."""
    return rx.box(
        rx.text(ticket["nome_tipo"], size="2", weight="medium", color=ticket["cor_tipo"]),
        background=ticket["cor_tipo"].to(str) + "1F",
        border_radius="999px",
        padding="3px 14px",
        width="fit-content",
    )


def cartao_painel(*filhos: rx.Component, **props: Any) -> rx.Component:
    props.setdefault("width", "100%")
    return rx.box(
        *filhos,
        background="white",
        border=f"1px solid {COR_BORDA}",
        border_radius="12px",
        box_shadow="0 2px 8px rgba(18, 60, 107, 0.06)",
        **props,
    )


def cartao_chamado(ticket: dict[str, Any]) -> rx.Component:
    """Ticket em chamada: código grande, chamada atual, contagem e ações da Recepção (chamada manual, sem avanço automático)."""
    presente = ticket["presente"].to(bool)
    # Contagem em zero (ou desconhecida, -1) libera os botões; o Xano valida o prazo de qualquer forma.
    aguardando_intervalo = ticket["segundos_restantes"].to(int) > 0
    pode_chamar_novamente = ticket["pode_chamar_novamente"].to(bool)
    return cartao_painel(
        rx.hstack(
            rx.vstack(
                rx.text(rx.cond(presente, "PRESENTE — PRONTO PARA IDENTIFICAR", "CHAMANDO AGORA"), size="1", weight="medium",
                        color=rx.cond(presente, COR_SUCESSO, COR_SECUNDARIA)),
                rx.text(ticket["senha_exibida"], weight="bold", font_size="44px", line_height="1.1", color=ticket["cor_tipo"]),
                rx.hstack(
                    chip_tipo_ticket(ticket),
                    rx.text(ticket["tentativas"], "ª chamada", size="2", color=COR_TEXTO),
                    rx.cond(ticket["oportunidade"].to(int) > 1, rx.text("· 2ª oportunidade", size="2", color=COR_SECUNDARIA)),
                    rx.cond(~presente & aguardando_intervalo,
                            rx.text("· ", rx.cond(pode_chamar_novamente, "Chamar novamente e Não compareceu liberam", "Não compareceu libera"),
                                    " em ", ticket["segundos_restantes"], " s", size="2", color=COR_SECUNDARIA)),
                    align="center",
                    spacing="2",
                    wrap="wrap",
                ),
                spacing="2",
                align="start",
            ),
            rx.spacer(),
            rx.hstack(
                botao_secundario("Desistência", on_click=FilaTicketsState.acao(ticket["id"], "DESISTENCIA")),
                rx.cond(
                    ~presente,
                    rx.hstack(
                        rx.cond(
                            pode_chamar_novamente,
                            botao_secundario("Chamar novamente", on_click=FilaTicketsState.chamar_novamente(ticket["id"]), disabled=aguardando_intervalo),
                        ),
                        botao_secundario("Não compareceu", on_click=FilaTicketsState.nao_compareceu(ticket["id"]), disabled=aguardando_intervalo),
                        spacing="3",
                        wrap="wrap",
                    ),
                ),
                rx.cond(
                    presente,
                    rx.button("Identificar paciente", on_click=FilaTicketsState.identificar(ticket["id"]), size="3", background=COR_AZUL),
                    rx.button("Marcar presente", on_click=FilaTicketsState.acao(ticket["id"], "PRESENTE"), size="3", background=COR_SUCESSO),
                ),
                spacing="3",
                wrap="wrap",
            ),
            align="center",
            spacing="4",
            wrap="wrap",
            width="100%",
        ),
        border_left=rx.cond(presente, f"8px solid {COR_SUCESSO}", f"8px solid {COR_AZUL}"),
        padding="20px 28px",
    )


def linha_ticket_aguardando(ticket: dict[str, Any], indice: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(indice + 1, "º", size="2", color=COR_SECUNDARIA, width="48px"),
        rx.text(ticket["senha_exibida"], weight="bold", size="4", color=ticket["cor_tipo"], width="120px"),
        rx.box(chip_tipo_ticket(ticket), width="180px"),
        rx.text(ticket["emitido_hora"], size="3", color=COR_TEXTO, width="120px"),
        rx.text(rx.cond(ticket["oportunidade"].to(int) > 1, "2ª oportunidade", ""), size="2", color=COR_SECUNDARIA, flex="1"),
        rx.button("Desistência", on_click=FilaTicketsState.acao(ticket["id"], "DESISTENCIA"), variant="ghost", color_scheme="gray", size="2"),
        align="center",
        width="100%",
        padding="12px 16px",
        border_radius="8px",
        background=rx.cond(indice % 2 == 1, COR_FUNDO, "transparent"),
    )


def resumo_tipo(item: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.box(width="10px", height="10px", border_radius="50%", background=item["cor"]),
        rx.text(item["nome"], size="2", color=COR_TEXTO),
        rx.text(item["quantidade"], size="2", weight="bold", color=COR_TEXTO),
        align="center",
        spacing="2",
        padding="6px 14px",
        border=f"1px solid {COR_BORDA}",
        border_radius="999px",
        background="white",
    )


def pagina_fila_tickets() -> rx.Component:
    cabecalho_tabela = rx.hstack(
        *[rx.text(rotulo, size="1", weight="medium", color=COR_SECUNDARIA, **props) for rotulo, props in (
            ("ORDEM", {"width": "48px"}), ("TICKET", {"width": "120px"}), ("TIPO", {"width": "180px"}),
            ("RETIRADO ÀS", {"width": "120px"}), ("", {"flex": "1"}),
        )],
        width="100%",
        padding="0 16px 10px",
        border_bottom=f"1px solid {COR_BORDA}",
    )
    return protegido(
        "RECEPCAO_TRIAGEM",
        rx.box(
            cabecalho("RECEPÇÃO/TRIAGEM — FILA DE PRÉ-TRIAGEM", "Chame os tickets retirados no Totem e confirme a presença"),
            rx.center(
                rx.vstack(
                    rx.hstack(
                        rx.button("Chamar próximo", on_click=FilaTicketsState.proximo, size="3", background=COR_AZUL, min_width="200px"),
                        botao_secundario("Atualizar", on_click=FilaTicketsState.carregar),
                        rx.spacer(),
                        rx.foreach(FilaTicketsState.resumo_tipos, resumo_tipo),
                        align="center",
                        spacing="3",
                        wrap="wrap",
                        width="100%",
                    ),
                    rx.cond(
                        FilaTicketsState.mensagem != "",
                        rx.text(FilaTicketsState.mensagem, size="2", color=rx.cond(FilaTicketsState.erro, COR_ERRO, COR_SUCESSO)),
                    ),
                    rx.cond(
                        FilaTicketsState.chamados.length() > 0,
                        rx.vstack(rx.foreach(FilaTicketsState.chamados, cartao_chamado), spacing="3", width="100%"),
                    ),
                    rx.hstack(
                        rx.text("Aguardando chamada", weight="bold", size="5", color=COR_TEXTO),
                        rx.text("(ordem de chegada; a chamada alterna prioritários e normais)", size="2", color=COR_SECUNDARIA),
                        rx.spacer(),
                        rx.cond(FilaTicketsState.atualizado_em != "",
                                rx.text("Atualizado às ", FilaTicketsState.atualizado_em, size="1", color=COR_SECUNDARIA)),
                        align="baseline",
                        spacing="3",
                        wrap="wrap",
                        width="100%",
                        padding_top="8px",
                    ),
                    cartao_painel(
                        rx.cond(
                            FilaTicketsState.aguardando.length() == 0,
                            rx.text("Nenhum ticket aguardando. Os tickets retirados no Totem aparecem aqui automaticamente.",
                                    size="2", color=COR_SECUNDARIA, padding="8px 16px"),
                            rx.vstack(cabecalho_tabela, rx.foreach(FilaTicketsState.aguardando, linha_ticket_aguardando), spacing="1", width="100%"),
                        ),
                        padding="20px 16px",
                    ),
                    rx.link("← Voltar para a área inicial", href="/recepcao", size="2", color=COR_AZUL),
                    spacing="4",
                    width="min(100%, 1184px)",
                ),
                padding="28px 16px 40px",
                width="100%",
            ),
            background=COR_FUNDO,
            font_family="Inter, sans-serif",
            min_height="100vh",
            width="100%",
        ),
    )


def area_medico() -> rx.Component:
    return area_inicial("MEDICO", "MÉDICO", "Médico", rx.text("As funções do Médico ainda estão em construção.", size="2", color=COR_SECUNDARIA))


def area_admin() -> rx.Component:
    return area_inicial(
        "ADMINISTRADOR",
        "ADMINISTRADOR",
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


# Cores e textos das prioridades, como na tela 4 do Figma.
CORES_PRIORIDADE = [
    ("VERMELHA", "Vermelha", "Risco de morte", "#C62828"),
    ("AMARELA", "Amarela", "Urgente", "#ED8B00"),
    ("AZUL", "Azul", "Não urgente", "#1565C0"),
]


def rotulo_secao(texto: str) -> rx.Component:
    return rx.text(texto, size="1", weight="bold", color=COR_SECUNDARIA, letter_spacing="0.02em")


def campo_sinal(rotulo: str, campo: str, exemplo: str) -> rx.Component:
    return campo_rotulado(
        rotulo,
        rx.input(
            value=FichaState.sinais[campo],
            on_change=lambda valor: FichaState.set_sinal(campo, valor),
            placeholder=exemplo,
            input_mode="decimal",
            size="3",
            width="100%",
        ),
    )


def sinais_vitais_ficha() -> rx.Component:
    return rx.vstack(
        rotulo_secao("SINAIS VITAIS"),
        rx.grid(
            campo_sinal("PA SISTÓLICA (mmHg)", "pa_sistolica", "Ex.: 150"),
            campo_sinal("FREQUÊNCIA CARDÍACA (bpm)", "fc", "Ex.: 112"),
            campo_sinal("FREQUÊNCIA RESPIRATÓRIA (irpm)", "fr", "Ex.: 24"),
            campo_sinal("TEMPERATURA (°C)", "temperatura", "Ex.: 37,1"),
            campo_sinal("SpO2 (%)", "spo2", "Ex.: 96"),
            rx.vstack(
                campo_sinal("GLICEMIA (OPCIONAL, mg/dL)", "glicemia", "Ex.: 110"),
                rx.checkbox(
                    "glicemia com sinais de gravidade",
                    checked=FichaState.glicemia_gravidade,
                    on_change=FichaState.set_glicemia_gravidade,
                    size="2",
                ),
                spacing="2",
                width="100%",
            ),
            columns=rx.breakpoints(initial="1", sm="2", md="3"),
            spacing="4",
            width="100%",
        ),
        spacing="2",
        width="100%",
    )


def sintoma_livre_selecionado(livre: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.text(livre["descricao"], min_width="0", white_space="normal", line_height="1.35"),
        rx.badge("não listado · ", livre["pontuacao"], " pt(s)", color_scheme="gray", variant="soft"),
        rx.spacer(),
        rx.button(
            "×",
            on_click=FichaState.remover_sintoma_livre(livre["descricao"]),
            aria_label="Remover sintoma não listado",
            variant="ghost",
            color_scheme="gray",
            size="2",
            flex_shrink="0",
        ),
        align="center",
        spacing="2",
        border="1px dashed var(--gray-6)",
        border_radius="0.375rem",
        padding="0.35rem 0.5rem",
        width="100%",
    )


def adicionar_nao_listado() -> rx.Component:
    """Sintoma digitado (D9): a Recepção/Triagem escolhe a gravidade; vale só para esta ficha."""
    busca = SeletorSintomasState.busca.strip()
    return rx.cond(
        busca.length() >= 3,
        rx.vstack(
            rx.divider(),
            rx.text("Não encontrou? Adicionar \"", busca, "\" como sintoma não listado:", size="2", color=COR_SECUNDARIA),
            rx.hstack(
                *[
                    rx.button(
                        nome,
                        on_click=[FichaState.adicionar_sintoma_livre(busca, pontos), SeletorSintomasState.limpar_busca],
                        variant="outline",
                        color_scheme="gray",
                        size="2",
                    )
                    for pontos, nome in ((1, "Leve · 1 pt"), (2, "Moderado · 2 pts"), (3, "Grave · 3 pts"))
                ],
                spacing="2",
                wrap="wrap",
            ),
            spacing="2",
            width="100%",
        ),
    )


def sintomas_ficha() -> rx.Component:
    return rx.vstack(
        rotulo_secao("SINTOMAS (DA LISTA OU NÃO LISTADOS) E OBSERVAÇÃO"),
        rx.popover.root(
            rx.popover.trigger(
                rx.button("+ Pesquisar ou adicionar sintoma...", variant="soft", color_scheme="gray", justify="between", width="100%")
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
                                    & sintoma["nome"].to(str).lower().contains(SeletorSintomasState.busca.strip().lower()),
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
                    adicionar_nao_listado(),
                    spacing="2",
                    align="stretch",
                    width="100%",
                ),
                width="min(34rem, calc(100vw - 3rem))",
            ),
        ),
        rx.cond(
            (FichaState.sintoma_ids_selecionados.length() > 0) | (FichaState.sintomas_livres.length() > 0),
            rx.vstack(
                rx.foreach(FichaState.catalogo_sintomas, sintoma_selecionado),
                rx.foreach(FichaState.sintomas_livres, sintoma_livre_selecionado),
                spacing="1",
                align="stretch",
                width="100%",
            ),
            rx.text("Nenhum sintoma selecionado.", size="2", color=COR_SECUNDARIA),
        ),
        rx.text_area(
            value=FichaState.observacao,
            on_change=FichaState.set_observacao,
            placeholder="Observação / queixa geral (opcional se houver sintoma).",
            width="100%",
        ),
        spacing="2",
        align="stretch",
        width="100%",
    )


def cartao_prioridade(codigo: str, nome: str, descricao: str, cor: str) -> rx.Component:
    atual = FichaState.prioridade_exibida == codigo
    calculada_diferente = FichaState.ajustada_manualmente & (FichaState.prioridade_calculada == codigo)
    return rx.box(
        rx.text(nome, weight="bold", size="4", color=rx.cond(atual, cor, COR_TEXTO)),
        rx.text(descricao, size="2", color=COR_SECUNDARIA),
        rx.cond(atual & FichaState.ajustada_manualmente, rx.badge("ajuste manual", color_scheme="gray", margin_top="4px")),
        rx.cond(calculada_diferente, rx.badge("calculada", color_scheme="gray", variant="outline", margin_top="4px")),
        border=rx.cond(atual, f"2px solid {cor}", f"1px solid {COR_BORDA}"),
        border_left=f"6px solid {cor}",
        background=rx.cond(atual, f"{cor}14", "white"),
        border_radius="8px",
        padding="12px 16px",
        flex="1",
        min_width="140px",
    )


def classificacao_ficha() -> rx.Component:
    return rx.vstack(
        rotulo_secao("CLASSIFICAÇÃO"),
        rx.text(FichaState.resumo_escore, size="2", weight="medium", color=COR_TEXTO),
        rx.hstack(*[cartao_prioridade(*cor) for cor in CORES_PRIORIDADE], spacing="3", wrap="wrap", width="100%"),
        rx.cond(
            FichaState.ajustada_manualmente,
            rx.text("Justificativa do ajuste: ", FichaState.classificacao["justificativa_ajuste"], size="2", color=COR_SECUNDARIA),
        ),
        rx.cond(
            FichaState.pendencias_texto.length() > 0,
            rx.callout(
                rx.vstack(
                    rx.text("Classificação automática pendente:", weight="medium"),
                    rx.foreach(FichaState.pendencias_texto, lambda texto: rx.text("• ", texto, size="2")),
                    spacing="1",
                ),
                color_scheme="amber",
                width="100%",
            ),
        ),
        rx.checkbox(
            "Gestante — idoso e criança são identificados automaticamente pela data de nascimento",
            checked=FichaState.gestante,
            on_change=FichaState.set_gestante,
            size="2",
        ),
        rx.text(
            "Escala de simulação acadêmica (Azul 0–4, Amarela 5–9, Vermelha 10 ou mais; item de 3 pontos gera Vermelha). Não é protocolo clínico.",
            size="1",
            color=COR_SECUNDARIA,
        ),
        spacing="2",
        width="100%",
    )


def dialogo_ajuste_prioridade() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Ajustar prioridade"),
            rx.dialog.description(
                "A justificativa é obrigatória e fica na auditoria. Se sintomas ou sinais vitais mudarem depois, o ajuste é descartado e a cor é recalculada.",
                size="2",
            ),
            rx.vstack(
                rx.radio_group(
                    ["VERMELHA", "AMARELA", "AZUL"],
                    value=FichaState.ajuste_prioridade,
                    on_change=FichaState.set_ajuste_prioridade,
                    direction="row",
                    spacing="4",
                ),
                rx.text_area(
                    value=FichaState.ajuste_justificativa,
                    on_change=FichaState.set_ajuste_justificativa,
                    placeholder="Justificativa (obrigatória)",
                    width="100%",
                ),
                rx.cond(FichaState.ajuste_erro != "", rx.text(FichaState.ajuste_erro, size="2", color=COR_ERRO)),
                rx.hstack(
                    rx.dialog.close(botao_secundario("Cancelar")),
                    rx.button("Confirmar ajuste", on_click=FichaState.confirmar_ajuste, loading=FichaState.ajustando, size="3", background=COR_AZUL),
                    justify="end",
                    spacing="3",
                    width="100%",
                ),
                spacing="3",
                margin_top="12px",
                width="100%",
            ),
            max_width="480px",
        ),
        open=FichaState.ajuste_aberto,
        on_open_change=FichaState.set_ajuste_aberto,
    )


def cartao_paciente_ficha() -> rx.Component:
    return cartao_painel(
        rx.vstack(
            rotulo_secao("FICHA"),
            rx.badge(FichaState.ficha["status"], color_scheme="gray", size="2"),
            rx.divider(),
            rotulo_secao("NOME"),
            rx.text(FichaState.paciente["nome"], size="3", color=COR_TEXTO),
            rotulo_secao("CPF"),
            rx.text(FichaState.cpf_exibido, size="3", color=COR_TEXTO),
            rotulo_secao("IDADE · CONDIÇÃO PRIORITÁRIA"),
            rx.text(FichaState.idade_texto, " · ", FichaState.condicao_texto, size="3", color=COR_TEXTO),
            rx.text("A condição prioritária reordena dentro da mesma cor; não soma pontos.", size="1", color=COR_SECUNDARIA),
            spacing="2",
            align="start",
            width="100%",
        ),
        padding="24px",
        width=rx.breakpoints(initial="100%", md="320px"),
        flex_shrink="0",
    )


def recepcao_ficha() -> rx.Component:
    return rx.box(
        cabecalho("RECEPÇÃO/TRIAGEM — FICHA DE ATENDIMENTO", "Registre sintomas e sinais vitais — a cor é recalculada ao salvar"),
        rx.center(
            rx.cond(
                FichaState.carregando,
                rx.spinner(size="3"),
                rx.flex(
                    cartao_paciente_ficha(),
                    cartao_painel(
                        rx.vstack(
                            rx.text("Ficha de atendimento", weight="bold", size="5", color=COR_TEXTO),
                            rx.cond(
                                FichaState.mensagem != "",
                                rx.callout(FichaState.mensagem, color_scheme=rx.cond(FichaState.erro, "red", "green"), width="100%"),
                            ),
                            sinais_vitais_ficha(),
                            sintomas_ficha(),
                            classificacao_ficha(),
                            rx.divider(),
                            rx.flex(
                                botao_secundario("Ajustar prioridade (justificativa obrigatória)", on_click=FichaState.abrir_ajuste),
                                rx.button("Salvar ficha", on_click=FichaState.salvar, loading=FichaState.salvando, size="3", background=COR_AZUL, min_width="200px"),
                                justify="between",
                                gap="12px",
                                wrap="wrap",
                                width="100%",
                            ),
                            rx.link("← Voltar para a área inicial", href="/recepcao", size="2", color=COR_AZUL),
                            spacing="4",
                            width="100%",
                        ),
                        padding="28px",
                        flex="1",
                        min_width="0",
                    ),
                    direction=rx.breakpoints(initial="column", md="row"),
                    gap="24px",
                    align="start",
                    width="min(100%, 1184px)",
                ),
            ),
            padding="28px 16px 40px",
            width="100%",
        ),
        dialogo_ajuste_prioridade(),
        background=COR_FUNDO,
        font_family="Inter, sans-serif",
        min_height="100vh",
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
app.add_page(totem, route="/totem", title="Totem de autoatendimento", on_load=TotemState.concluir)
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

app.add_page(pagina_fila_tickets, route="/recepcao/fila", title="Fila de pré-triagem", on_load=[AuthState.verificar_sessao("RECEPCAO_TRIAGEM"), FilaTicketsState.carregar, FilaTicketsState.monitorar])

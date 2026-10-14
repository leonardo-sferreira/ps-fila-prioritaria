"""Fluxo de identificação e cadastro de Paciente da Recepção/Triagem."""

import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx
import reflex as rx
from dotenv import load_dotenv


ARQUIVO_ENV = Path(__file__).resolve().parents[1] / ".env"


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
            return "CPF_DUPLICADO: já existe um Paciente cadastrado com este CPF."
        if mensagem == "FICHA_SEM_SINTOMA_OU_OBSERVACAO":
            return "Informe ao menos um sintoma ou uma observação."
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
                            rx.button(
                                "Continuar",
                                variant="soft",
                                on_click=PacienteState.continuar_atendimento,
                                loading=PacienteState.abrindo_ficha,
                            ),
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
                        rx.text("CPF: ", FichaState.paciente["cpf"], size="2", color_scheme="gray"),
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


app = rx.App()
app.add_page(index, route="/")
app.add_page(recepcao_pacientes, route="/recepcao/pacientes", title="Identificação de Paciente")
app.add_page(recepcao_ficha, route="/recepcao/ficha/[id]", title="Ficha de atendimento", on_load=FichaState.carregar_da_rota)

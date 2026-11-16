"""Fila geral administrativa: o servidor ordena; o Reflex apresenta e consulta."""
from contextlib import aclosing
from datetime import datetime
from typing import Any

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import FUSO_BRASILIA, _mensagem_erro, _timestamp_segundos
from ps_fila_prioritaria.estados.autenticacao import AREA_POR_PERFIL, AuthState
from ps_fila_prioritaria.estados.equipe import EquipeState

ROTA = "/admin/acompanhamento"
CORES = {"VERMELHA": ("Vermelha", "var(--ps-clinica-vermelha)"),
         "AMARELA": ("Amarela", "var(--ps-clinica-amarela)"),
         "AZUL": ("Azul", "var(--ps-clinica-azul)")}
STATUS = {"EM_TRIAGEM": "Em triagem", "AGUARDANDO": "Aguardando", "CHAMADO": "Chamado"}
CONDICOES = {"NENHUMA": "—", "IDOSO": "Idoso", "CRIANCA": "Criança", "GESTANTE": "Gestante"}
AVISOS = {"PARAMETROS_NAO_CONFIGURADOS": "Parâmetros do ciclo não configurados.",
          "CICLO_FILA_INVALIDO": "Há ciclo de fila inválido; algumas posições estão indisponíveis."}


def parametros_consulta(especialidade: str, cor: str, status: str) -> dict[str, Any]:
    if not especialidade.isdigit() or cor not in ("TODAS", *CORES) or status not in ("TODOS", *STATUS):
        raise ValueError("Filtro inválido.")
    params: dict[str, Any] = {}
    if int(especialidade):
        params["especialidade_id"] = int(especialidade)
    if cor != "TODAS":
        params["cor"] = cor
    if status != "TODOS":
        params["status"] = status
    return params


def hora(valor: Any) -> str:
    segundos = _timestamp_segundos(valor)
    return datetime.fromtimestamp(segundos, FUSO_BRASILIA).strftime("%d/%m %H:%M:%S") if segundos is not None else "—"


def apresentar(corpo: Any) -> tuple[list[dict[str, str]], list[dict[str, str]], str, str]:
    """Consome a lista publicada; só ordena posições fornecidas pelo Xano.

    Reordena AGUARDANDO nos mesmos espaços de sua especialidade, sem comparar
    cores, chegada ou prioridade no Reflex e sem criar ranking entre filas.
    """
    if not isinstance(corpo, list):
        raise ValueError("Resposta inesperada.")
    fichas = list(corpo)
    ids, por_especialidade, opcoes, avisos = set(), {}, {}, []
    legado = False
    for indice, ficha in enumerate(fichas):
        if not isinstance(ficha, dict) or type(ficha.get("id")) is not int or ficha["id"] <= 0 or ficha.get("status") not in STATUS:
            raise ValueError("Ficha inválida.")
        if ficha["id"] in ids:
            raise ValueError("Ficha duplicada.")
        ids.add(ficha["id"])
        posicao = ficha.get("posicao")
        if posicao is not None and (type(posicao) is not int or posicao <= 0):
            raise ValueError("Posição inválida.")
        esp_id = ficha.get("especialidade_id")
        if esp_id is not None and (type(esp_id) is not int or esp_id <= 0):
            raise ValueError("Especialidade inválida.")
        if esp_id is not None:
            opcoes[str(esp_id)] = str(ficha.get("especialidade") or "Sem cadastro encontrado")
        if ficha["status"] == "AGUARDANDO" and esp_id is not None:
            por_especialidade.setdefault(esp_id, []).append(indice)
        avisos_item = ficha.get("avisos", [])
        if not isinstance(avisos_item, list) or not all(isinstance(v, str) for v in avisos_item):
            raise ValueError("Aviso inválido.")
        avisos.extend(avisos_item)
        legado |= "consultado_em" not in ficha
    for indices in por_especialidade.values():
        ordenadas = sorted((fichas[i] for i in indices),
                           key=lambda row: (row.get("posicao") is None, row.get("posicao") or 0))
        for indice, ficha in zip(indices, ordenadas):
            fichas[indice] = ficha
    linhas = []
    for ficha in fichas:
        cor, css = CORES.get(ficha.get("cor"), ("Sem cor", "var(--ps-secundaria)"))
        espera, ordem = ficha.get("espera_minutos"), ficha.get("posicao")
        chamado = ficha["status"] == "CHAMADO"
        linhas.append({
            "id": str(ficha["id"]), "senha": str(ficha.get("senha") or "—"),
            "status": STATUS[ficha["status"]], "cor": cor, "cor_css": css,
            "condicao": CONDICOES.get(ficha.get("condicao_prioritaria"), "—"),
            "especialidade": str(ficha.get("especialidade") or ("Sem cadastro encontrado" if ficha.get("especialidade_id") else "Sem especialidade")),
            "chegada": hora(ficha.get("chegada_em")),
            "espera": str(max(0, espera)) + " min" if type(espera) is int else "—",
            "ordem": str(ordem) if type(ordem) is int and ordem > 0 else "—",
            "medico": str(ficha.get("medico") or "—") if chamado else "—",
            "tentativa": str(ficha.get("tentativa") or "—") if chamado else "—",
        })
    aviso = " ".join(dict.fromkeys(AVISOS.get(v, "Há registros sem previsão disponível.") for v in avisos))
    if legado:
        aviso = (aviso + " A resposta publicada não informa metadados da previsão nem tempo de espera; posições após a vigésima podem estar indisponíveis.").strip()
    # Hora da consulta recebida pelo Reflex, nunca usada para calcular prioridade.
    atualizado = datetime.now(FUSO_BRASILIA).strftime("%d/%m %H:%M:%S")
    return linhas, [{"id": id, "nome": nome} for id, nome in sorted(opcoes.items(), key=lambda e: (e[1], int(e[0])))], atualizado, aviso


class FilaGeralState(rx.State):
    itens: list[dict[str, str]] = []
    especialidades: list[dict[str, str]] = []
    especialidade_id: str = "0"
    cor: str = "TODAS"
    status: str = "TODOS"
    carregando: bool = False
    ativa: bool = False
    erro: bool = False
    desatualizado: bool = False
    mensagem: str = ""
    aviso: str = ""
    atualizado_em: str = ""

    async def _consultar(self):
        if self.carregando or not self.ativa or self.router.url.path.rstrip("/") != ROTA:
            return
        self.carregando = True
        try:
            yield
            auth = await self.get_state(AuthState)
            if not auth.token or auth.perfil != "ADMINISTRADOR":
                self.itens = []
                self.ativa = False
                yield rx.redirect(AREA_POR_PERFIL.get(auth.perfil, "/login") if auth.token else "/login")
                return
            if not self.ativa or self.router.url.path.rstrip("/") != ROTA:
                return
            params = parametros_consulta(self.especialidade_id, self.cor, self.status)
            equipe = await self.get_state(EquipeState)
            try:
                await equipe.carregar()
            except (ValueError, TypeError, AttributeError, httpx.RequestError):
                equipe.mensagem = "Não foi possível atualizar a equipe."
            if not auth.token or auth.perfil != "ADMINISTRADOR":
                self.itens, self.ativa = [], False
                yield rx.redirect("/login")
                return
            if not self.ativa or self.router.url.path.rstrip("/") != ROTA:
                return
            try:
                resposta = api.requisitar("GET", "XANO_CADASTROS_API_URL", "/admin/fila-geral", token=auth.token, params=params)
            except api.ConfiguracaoAusente:
                raise ValueError("A API de cadastros não está configurada.")
            except httpx.TimeoutException:
                raise ValueError("Tempo de resposta excedido ao consultar a fila geral.")
            except httpx.RequestError:
                raise ValueError("Não foi possível conectar à consulta da fila geral.")
            if resposta.status_code == 401:
                auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
                self.itens, self.ativa = [], False
                yield rx.redirect("/login")
                return
            if resposta.status_code != 200:
                if resposta.status_code == 404:
                    raise ValueError("Fila geral indisponível: o GET /admin/fila-geral precisa estar publicado.")
                if resposta.status_code == 403:
                    raise ValueError("Acesso negado à fila geral administrativa.")
                if resposta.status_code >= 500 or 200 <= resposta.status_code < 300:
                    raise ValueError("O serviço não confirmou a consulta da fila geral.")
                raise ValueError(_mensagem_erro(resposta))
            try:
                itens, opcoes, atualizado, aviso = apresentar(resposta.json())
            except (ValueError, TypeError, OverflowError, OSError):
                raise ValueError("O serviço retornou uma resposta inesperada para a fila geral.")
            if not self.ativa:
                return
            self.itens = itens
            # Mantém opções já observadas quando o GET retorna somente um filtro.
            catalogo = {e["id"]: e for e in self.especialidades}
            catalogo.update({e["id"]: e for e in opcoes})
            self.especialidades = sorted(catalogo.values(), key=lambda e: (e["nome"], int(e["id"])))
            self.atualizado_em, self.aviso = atualizado, aviso
            self.erro, self.desatualizado, self.mensagem = False, False, ""
        except ValueError as exc:
            self.erro, self.desatualizado = True, bool(self.itens)
            self.mensagem = str(exc) + (" Dados anteriores preservados; não representam uma atualização confirmada." if self.itens else "")
        finally:
            self.carregando = False

    async def entrar(self):
        self.ativa = True
        async with aclosing(self._consultar()) as eventos:
            async for evento in eventos:
                yield evento

    def sair(self):
        self.ativa = False

    async def carregar(self):
        async with aclosing(self._consultar()) as eventos:
            async for evento in eventos:
                yield evento

    async def consultar_se_visivel(self, visivel: bool):
        if visivel is True:
            async with aclosing(self._consultar()) as eventos:
                async for evento in eventos:
                    yield evento

    async def filtrar(self, campo: str, valor: str):
        if self.carregando:
            return
        valores = {"especialidade_id": self.especialidade_id, "cor": self.cor, "status": self.status}
        if campo not in valores:
            return
        valores[campo] = valor
        try:
            parametros_consulta(valores["especialidade_id"], valores["cor"], valores["status"])
        except (ValueError, AttributeError):
            self.erro, self.mensagem = True, "Filtro inválido."
            return
        setattr(self, campo, valor)
        self.itens, self.atualizado_em, self.desatualizado = [], "", False
        async with aclosing(self._consultar()) as eventos:
            async for evento in eventos:
                yield evento

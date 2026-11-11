"""Painel do plantão na área inicial da Recepção: resumo do dia a partir da fila de pré-triagem e das fichas."""

from datetime import datetime
from typing import Any

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import FUSO_BRASILIA, _mensagem_erro, _timestamp_segundos, formatar_ticket
from ps_fila_prioritaria.estados.autenticacao import AuthState

# Cores clínicas (Rev. 2.1), com um tom para cada tema em assets/tema.css. O texto sobre o âmbar é escuro:
# branco não tem contraste nele.
CORES_CLINICAS = [
    ("VERMELHA", "Vermelha", "var(--ps-clinica-vermelha)", "#FFFFFF"),
    ("AMARELA", "Amarela", "var(--ps-clinica-amarela)", "#1A1A1A"),
    ("AZUL", "Azul", "var(--ps-clinica-azul)", "#FFFFFF"),
]
DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
HORAS_NO_GRAFICO = 12


def _minutos(desde: Any, agora: float) -> int | None:
    instante = _timestamp_segundos(desde)
    if instante is None:
        return None
    return max(0, int((agora - instante) // 60))


def _texto_espera(minutos: int) -> str:
    if minutos < 60:
        return f"{minutos} min"
    return f"{minutos // 60} h {minutos % 60:02d} min"


def resumir_plantao(fichas: list[dict[str, Any]], tickets: list[dict[str, Any]], agora: float) -> dict[str, Any]:
    """Números do painel. `agora` em segundos (epoch). Função pura: os testes a chamam com dados fixos."""
    por_status: dict[str, list[dict[str, Any]]] = {}
    for ficha in fichas:
        por_status.setdefault(str(ficha.get("status") or ""), []).append(ficha)
    aguardando = por_status.get("AGUARDANDO", [])
    tickets_aguardando = [t for t in tickets if t.get("status") == "AGUARDANDO"]
    tickets_chamados = [t for t in tickets if t.get("status") == "CHAMADO"]

    # Fichas na fila médica por cor (barra segmentada); a porcentagem dá a largura de cada bloco.
    cores = []
    for codigo, nome, cor, texto in CORES_CLINICAS:
        quantidade = sum(1 for f in aguardando if f.get("prioridade_atual") == codigo)
        percentual = round(100 * quantidade / len(aguardando), 1) if aguardando else 0.0
        cores.append({"codigo": codigo, "nome": nome, "cor": cor, "texto": texto, "quantidade": quantidade, "percentual": percentual,
                      "visivel": quantidade > 0,
                      # Dentro do bloco: número e nome quando cabem, só o número em bloco médio, nada em bloco estreito.
                      # A legenda e a dica sempre trazem os dois.
                      "rotulo": f"{quantidade} {nome}" if percentual >= 30 else (str(quantidade) if percentual >= 8 else ""),
                      "dica": f"{nome}: {quantidade} na fila médica"})

    # Espera mais longa: ficha na fila médica e ticket na pré-triagem.
    maior_ficha, maior_ticket = {"identificacao": "", "texto": ""}, {"identificacao": "", "texto": ""}
    minutos_ficha = minutos_ticket = -1
    for ficha in aguardando:
        minutos = _minutos(ficha.get("chegada_em"), agora)
        if minutos is not None and minutos > minutos_ficha:
            minutos_ficha = minutos
            maior_ficha = {"identificacao": str(ficha.get("senha") or "—"), "texto": _texto_espera(minutos)}
    for ticket in tickets_aguardando:
        minutos = _minutos(ticket.get("emitido_em"), agora)
        if minutos is not None and minutos > minutos_ticket:
            minutos_ticket = minutos
            maior_ticket = {"identificacao": formatar_ticket(ticket.get("tipo"), ticket.get("numero")), "texto": _texto_espera(minutos)}

    atendidas = len(por_status.get("ATENDIDO", []))
    encerradas = len(por_status.get("DESISTENCIA", [])) + len(por_status.get("CANCELADO", []))
    etapas = [
        {"rotulo": "Totem", "quantidade": len(tickets_aguardando) + len(tickets_chamados),
         "detalhe": f"{len(tickets_chamados)} em chamada" if tickets_chamados else "aguardando chamada", "rota": "/recepcao/fila"},
        {"rotulo": "Em triagem", "quantidade": len(por_status.get("EM_TRIAGEM", [])), "detalhe": "fichas abertas", "rota": "/recepcao/fichas"},
        {"rotulo": "Fila médica", "quantidade": len(aguardando), "detalhe": "com senha", "rota": "/recepcao/fichas"},
        {"rotulo": "Em chamada", "quantidade": len(por_status.get("CHAMADO", [])), "detalhe": "pelo médico", "rota": "/recepcao/fichas"},
        {"rotulo": "Concluídas", "quantidade": atendidas,
         "detalhe": f"+ {encerradas} encerrada(s)" if encerradas else "hoje", "rota": "/recepcao/fichas"},
    ]

    # Fila por especialidade (só fichas com senha), da maior para a menor; a barra é relativa à maior.
    contagem: dict[str, int] = {}
    for ficha in aguardando:
        nome = str(ficha.get("especialidade") or "Sem especialidade")
        contagem[nome] = contagem.get(nome, 0) + 1
    maior = max(contagem.values(), default=0)
    especialidades = [{"nome": nome, "quantidade": qtd, "largura": f"{round(100 * qtd / maior, 1)}%"}
                      for nome, qtd in sorted(contagem.items(), key=lambda item: (-item[1], item[0]))]

    # Chegadas por hora (fichas de hoje), nas últimas HORAS_NO_GRAFICO horas; a hora atual em destaque.
    agora_local = datetime.fromtimestamp(agora, FUSO_BRASILIA)
    inicio_dia = agora_local.replace(hour=0, minute=0, second=0, microsecond=0)
    por_hora = [0] * 24
    for ficha in fichas:
        instante = _timestamp_segundos(ficha.get("chegada_em"))
        if instante is None:
            continue
        local = datetime.fromtimestamp(instante, FUSO_BRASILIA)
        if local >= inicio_dia:
            por_hora[local.hour] += 1
    primeira = max(0, agora_local.hour - HORAS_NO_GRAFICO + 1)
    pico = max(por_hora[primeira:agora_local.hour + 1], default=0)
    chegadas = [{"hora": f"{h:02d}h", "quantidade": por_hora[h], "atual": h == agora_local.hour,
                 "altura": f"{round(100 * por_hora[h] / pico, 1) if pico else 0}%",
                 "altura_minima": "3px" if por_hora[h] else "0",
                 # Número só sobre a hora atual (rótulo seletivo); as demais horas ficam na dica.
                 "valor": str(por_hora[h]) if h == agora_local.hour and por_hora[h] else "",
                 "dica": f"{h:02d}h: {por_hora[h]} chegada(s)"} for h in range(primeira, agora_local.hour + 1)]

    # Indicadores do dia (dashboard do Administrador, add-acompanhamento-administrador D6).
    esperas = [m for m in (_minutos(f.get("chegada_em"), agora) for f in aguardando) if m is not None]
    media = round(sum(esperas) / len(esperas)) if esperas else None
    indicadores = [
        {"rotulo": "Atendidas", "valor": str(atendidas), "detalhe": "hoje"},
        {"rotulo": "Desistências", "valor": str(len(por_status.get("DESISTENCIA", []))), "detalhe": "hoje"},
        {"rotulo": "Canceladas", "valor": str(len(por_status.get("CANCELADO", []))), "detalhe": "hoje"},
        {"rotulo": "Espera média", "valor": _texto_espera(media) if media is not None else "—",
         "detalhe": f"de {len(esperas)} na fila médica agora" if esperas else "fila médica vazia"},
    ]

    return {
        "na_espera": len(tickets_aguardando) + len(aguardando),
        "indicadores": indicadores,
        "tickets_aguardando": len(tickets_aguardando),
        "fichas_aguardando": len(aguardando),
        "cores": cores,
        "maior_ficha": maior_ficha,
        "maior_ticket": maior_ticket,
        "etapas": etapas,
        "especialidades": especialidades,
        "chegadas": chegadas,
        "chegadas_hoje": sum(por_hora),
        "data_extenso": f"{DIAS_SEMANA[agora_local.weekday()].capitalize()}, {agora_local.day} de {MESES[agora_local.month - 1]}",
    }


class PlantaoState(rx.State):
    """Só consulta: o painel nunca altera fichas nem tickets."""

    na_espera: int = 0
    tickets_aguardando: int = 0
    fichas_aguardando: int = 0
    cores: list[dict[str, Any]] = []
    maior_ficha: dict[str, str] = {"identificacao": "", "texto": ""}
    maior_ticket: dict[str, str] = {"identificacao": "", "texto": ""}
    etapas: list[dict[str, Any]] = []
    especialidades: list[dict[str, Any]] = []
    chegadas: list[dict[str, Any]] = []
    indicadores: list[dict[str, str]] = []
    chegadas_hoje: int = 0
    data_extenso: str = ""
    carregado: bool = False
    atualizado_em: str = ""
    mensagem: str = ""

    async def _buscar(self, auth: AuthState, caminho: str) -> dict[str, Any] | None:
        try:
            resposta = api.requisitar("GET", "XANO_TRIAGEM_API_URL", caminho, token=auth.token)
        except (api.ConfiguracaoAusente, httpx.RequestError):
            self.mensagem = "Não foi possível atualizar o painel. Mostrando os últimos dados."
            return None
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return None
        corpo = resposta.json()
        return corpo if isinstance(corpo, dict) else {}

    async def carregar(self) -> None:
        auth = await self.get_state(AuthState)
        fichas = await self._buscar(auth, "/fichas")
        if fichas is None:
            return
        tickets = await self._buscar(auth, "/tickets")
        if tickets is None:
            return
        agora = _timestamp_segundos(fichas.get("agora")) or datetime.now(FUSO_BRASILIA).timestamp()
        resumo = resumir_plantao(list(fichas.get("fichas") or []), list(tickets.get("tickets") or []), agora)
        for campo, valor in resumo.items():
            setattr(self, campo, valor)
        self.atualizado_em = datetime.fromtimestamp(agora, FUSO_BRASILIA).strftime("%H:%M")
        self.carregado = True
        self.mensagem = ""

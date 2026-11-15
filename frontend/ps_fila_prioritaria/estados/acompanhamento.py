"""Fila geral e detalhe da ficha do Administrador, só leitura (add-acompanhamento-administrador, D3/D4, 2.1/2.2/3.2/3.3).

O Xano devolve as fichas abertas, com a posição prevista das AGUARDANDO pela regra da chamada; aqui se ordena para a
tela (chamadas primeiro, depois aguardando por especialidade e posição, depois em triagem) e se formata o tempo de
espera. Nenhuma ação altera a ficha.
"""

from datetime import datetime
from typing import Any

import reflex as rx

from ps_fila_prioritaria.comum import FUSO_BRASILIA, _id_da_rota, _timestamp_segundos
from ps_fila_prioritaria.estados.cadastros import chamar

NOME_STATUS_FICHA = {"EM_TRIAGEM": "Em triagem", "AGUARDANDO": "Aguardando", "CHAMADO": "Chamado", "ATENDIDO": "Atendido",
                     "DESISTENCIA": "Desistência", "CANCELADO": "Cancelado"}
NOME_COR = {"VERMELHA": "Vermelha", "AMARELA": "Amarela", "AZUL": "Azul"}
NOME_CONDICAO = {"IDOSO": "Idoso", "CRIANCA": "Criança", "GESTANTE": "Gestante", "PCD": "PcD"}
ORDEM_STATUS = {"CHAMADO": 0, "AGUARDANDO": 1, "EM_TRIAGEM": 2}
STATUS_FILTRO = [("TODOS", "Todos os status"), ("CHAMADO", "Chamado"), ("AGUARDANDO", "Aguardando"), ("EM_TRIAGEM", "Em triagem")]
CORES_FILTRO = [("TODAS", "Todas as cores"), ("VERMELHA", "Vermelha"), ("AMARELA", "Amarela"), ("AZUL", "Azul")]
NOME_TIPO_CHAMADA = {"CHAMADA": "Chamada", "COMPARECIMENTO": "Compareceu", "DESISTENCIA": "Desistiu"}


def _quando(instante: Any, formato: str = "%d/%m/%Y %H:%M") -> str:
    segundos = _timestamp_segundos(instante)
    return datetime.fromtimestamp(segundos, FUSO_BRASILIA).strftime(formato) if segundos is not None else "—"


def espera(chegada: Any, agora: datetime) -> str:
    """Tempo desde a chegada: "45 min" ou "2 h 05 min"."""
    segundos = _timestamp_segundos(chegada)
    if segundos is None:
        return "—"
    minutos = max(int((agora.timestamp() - segundos) // 60), 0)
    return f"{minutos} min" if minutos < 60 else f"{minutos // 60} h {minutos % 60:02d} min"


def linha_fila(ficha: dict[str, Any], agora: datetime) -> dict[str, Any]:
    status, cor = str(ficha.get("status") or ""), str(ficha.get("cor") or "")
    posicao, tentativa = ficha.get("posicao"), ficha.get("tentativa")
    condicao = str(ficha.get("condicao_prioritaria") or "NENHUMA")
    detalhe = ""
    if status == "CHAMADO":
        detalhe = f"{ficha.get('medico') or 'Médico'} · tentativa {tentativa or 1}"
    elif status == "AGUARDANDO":
        detalhe = f"{posicao}º na fila" if posicao else "depois da 20ª"
    return {
        "id": int(ficha.get("id") or 0),
        "senha": str(ficha.get("senha") or "—"),
        "status": status,
        "status_nome": NOME_STATUS_FICHA.get(status, status),
        "cor": cor,
        "cor_nome": NOME_COR.get(cor, "Sem cor"),
        "condicao": NOME_CONDICAO.get(condicao, ""),
        "especialidade": str(ficha.get("especialidade") or "—"),
        "espera": espera(ficha.get("chegada_em"), agora),
        "detalhe": detalhe,
        "_chegada": _timestamp_segundos(ficha.get("chegada_em")) or 0,
        "_posicao": int(posicao) if posicao else 9999,
    }


def ordenar_fila(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chamadas, depois aguardando por especialidade e posição prevista, depois em triagem; empate pela chegada."""
    return sorted(linhas, key=lambda l: (ORDEM_STATUS.get(l["status"], 9), l["especialidade"] if l["status"] == "AGUARDANDO" else "",
                                         l["_posicao"], l["_chegada"]))


def parametros_fila(especialidade_id: str, cor: str, status: str) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if especialidade_id.isdigit() and especialidade_id != "0":
        params["especialidade_id"] = int(especialidade_id)
    if cor not in ("", "TODAS"):
        params["cor"] = cor
    if status not in ("", "TODOS"):
        params["status"] = status
    return params


def _texto_valor(valor: Any) -> str:
    if valor in (None, "", {}, []):
        return "—"
    if isinstance(valor, dict):
        return " · ".join(f"{k}: {'—' if v is None else v}" for k, v in valor.items())
    return str(valor)


def detalhe_ficha(corpo: dict[str, Any]) -> dict[str, Any]:
    sinais = corpo.get("sinais") or {}
    rotulos = [("pa_sistolica", "PA sistólica", "mmHg"), ("fc", "FC", "bpm"), ("fr", "FR", "irpm"), ("temperatura", "Temperatura", "°C"),
               ("spo2", "SpO2", "%"), ("glicemia", "Glicemia", "mg/dL")]
    cor = str(corpo.get("cor") or "")
    calculada = str(corpo.get("cor_calculada") or "")
    return {
        "id": int(corpo.get("id") or 0),
        "senha": str(corpo.get("senha") or "—"),
        "senhas": ", ".join(corpo.get("senhas") or []) or "—",
        "status": NOME_STATUS_FICHA.get(str(corpo.get("status") or ""), str(corpo.get("status") or "")),
        "cor": NOME_COR.get(cor, "Sem cor"),
        "cor_codigo": cor,
        "ajuste": f"Ajustada de {NOME_COR.get(calculada, calculada)} para {NOME_COR.get(cor, cor)}: {corpo.get('justificativa_ajuste')}"
                  if corpo.get("justificativa_ajuste") else "",
        "escore": "—" if corpo.get("escore") is None else str(corpo.get("escore")),
        "condicao": NOME_CONDICAO.get(str(corpo.get("condicao_prioritaria") or ""), "Nenhuma"),
        "chegada": _quando(corpo.get("chegada_em")),
        "finalizada": _quando(corpo.get("finalizada_em")) if corpo.get("finalizada_em") else "",
        "sugerida": str(corpo.get("especialidade_sugerida") or "—"),
        "atribuida": str(corpo.get("especialidade_atribuida") or "—"),
        "medico": str(corpo.get("medico") or ""),
        "observacao": str(corpo.get("observacao") or ""),
        "sinais": [{"nome": nome, "valor": f"{sinais.get(chave)} {unidade}"} for chave, nome, unidade in rotulos if sinais.get(chave) is not None],
        "sintomas": [{"nome": str(s.get("nome") or "—"), "pontos": "—" if s.get("pontuacao") is None else str(s.get("pontuacao")),
                      "digitado": bool(s.get("digitado"))} for s in (corpo.get("sintomas") or [])],
        "chamadas": [{"quando": _quando(c.get("em"), "%d/%m %H:%M:%S"), "tipo": NOME_TIPO_CHAMADA.get(str(c.get("tipo")), str(c.get("tipo"))),
                      "medico": str(c.get("medico") or "—"), "tentativa": f"oportunidade {c.get('oportunidade') or 1}, tentativa {c.get('tentativa') or 1}"}
                     for c in (corpo.get("chamadas") or [])],
        "historico": [{"quando": _quando(h.get("em"), "%d/%m %H:%M:%S"), "evento": str(h.get("tipo_evento") or "").replace("_", " ").capitalize(),
                       "usuario": str(h.get("usuario") or "—"), "anterior": _texto_valor(h.get("valor_anterior")),
                       "novo": _texto_valor(h.get("valor_novo")), "justificativa": str(h.get("justificativa") or "")}
                      for h in (corpo.get("historico") or [])],
    }


class FilaGeralState(rx.State):
    itens: list[dict[str, Any]] = []
    especialidade_id: str = "0"
    cor: str = "TODAS"
    status: str = "TODOS"
    opcoes_especialidades: list[dict[str, str]] = []
    carregando: bool = False
    mensagem: str = ""
    erro: bool = False
    atualizado_em: str = ""

    @rx.var
    def resumo(self) -> str:
        contagem = {s: sum(1 for i in self.itens if i["status"] == s) for s in ORDEM_STATUS}
        return f"{contagem['CHAMADO']} chamada(s) · {contagem['AGUARDANDO']} aguardando · {contagem['EM_TRIAGEM']} em triagem"

    async def carregar(self) -> None:
        if not self.opcoes_especialidades:
            ok_e, especialidades = await chamar(self, "GET", "/especialidades")
            if ok_e:
                self.opcoes_especialidades = [{"id": str(e["id"]), "nome": str(e["nome"])} for e in (especialidades or []) if e.get("ativo", True)]
        await self.atualizar()

    async def atualizar(self, _=None) -> None:
        self.carregando = True
        try:
            ok, corpo = await chamar(self, "GET", "/admin/fila-geral", params=parametros_fila(self.especialidade_id, self.cor, self.status))
        finally:
            self.carregando = False
        if not ok:
            self.erro, self.mensagem = True, str(corpo)
            return
        agora = datetime.now(FUSO_BRASILIA)
        self.itens = ordenar_fila([linha_fila(f, agora) for f in (corpo or [])])
        self.erro, self.mensagem, self.atualizado_em = False, "", agora.strftime("%H:%M:%S")

    async def set_especialidade(self, valor: str) -> None:
        self.especialidade_id = valor
        await self.atualizar()

    async def set_cor(self, valor: str) -> None:
        self.cor = valor
        await self.atualizar()

    async def set_status(self, valor: str) -> None:
        self.status = valor
        await self.atualizar()


class FichaAdminState(rx.State):
    ficha: dict[str, Any] = {}
    carregando: bool = False
    mensagem: str = ""

    async def carregar_da_rota(self) -> None:
        ficha_id = _id_da_rota(self.router.url.path)
        self.ficha, self.mensagem, self.carregando = {}, "", True
        try:
            if not ficha_id.isdigit():
                self.mensagem = "Ficha não encontrada."
                return
            ok, corpo = await chamar(self, "GET", f"/admin/fichas/{ficha_id}")
        finally:
            self.carregando = False
        if not ok:
            self.mensagem = str(corpo)
            return
        self.ficha = detalhe_ficha(corpo or {})

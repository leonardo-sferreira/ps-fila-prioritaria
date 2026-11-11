"""Equipe com sessão ativa no dashboard do Administrador (add-acompanhamento-administrador, D6). Só consulta."""

from datetime import datetime
from typing import Any

import reflex as rx

from ps_fila_prioritaria.comum import FUSO_BRASILIA, _timestamp_segundos
from ps_fila_prioritaria.estados.cadastros import chamar

NOME_PERFIL = {"RECEPCAO_TRIAGEM": "Recepção/Triagem", "MEDICO": "Médico", "ADMINISTRADOR": "Administrador"}
# Status operacional: nome e cor do marcador (tokens de assets/tema.css).
STATUS = [
    ("DISPONIVEL", "Disponível", "var(--ps-sucesso)"),
    ("EM_ATENDIMENTO", "Em atendimento", "var(--ps-azul)"),
    ("PAUSA", "Pausa", "var(--ps-alerta)"),
    ("AUSENTE", "Ausente", "var(--ps-erro)"),
    ("", "Sem status", "var(--ps-secundaria)"),
]
NOME_STATUS = {codigo: (nome, cor) for codigo, nome, cor in STATUS}
ORDEM_PERFIL = {"MEDICO": 0, "RECEPCAO_TRIAGEM": 1, "ADMINISTRADOR": 2}


def resumir_equipe(equipe: list[dict[str, Any]]) -> dict[str, Any]:
    """Pessoas logadas (médicos primeiro, depois por nome) e médicos por status. Função pura para os testes."""
    pessoas = []
    for item in equipe:
        perfil = str(item.get("perfil") or "")
        codigo = str(item.get("status") or "") if perfil != "ADMINISTRADOR" else ""
        nome_status, cor = NOME_STATUS.get(codigo, NOME_STATUS[""])
        instante = _timestamp_segundos(item.get("login_em"))
        pessoas.append({
            "nome": str(item.get("nome") or "—"),
            "perfil": perfil,
            "perfil_nome": NOME_PERFIL.get(perfil, perfil),
            "status": nome_status if perfil != "ADMINISTRADOR" else "—",
            "cor": cor,
            "login": datetime.fromtimestamp(instante, FUSO_BRASILIA).strftime("%H:%M") if instante is not None else "—",
        })
    pessoas.sort(key=lambda p: (ORDEM_PERFIL.get(p["perfil"], 9), p["nome"].lower()))

    medicos = [str(i.get("status") or "") for i in equipe if i.get("perfil") == "MEDICO"]
    por_status = [{"nome": nome, "cor": cor, "quantidade": medicos.count(codigo)} for codigo, nome, cor in STATUS]
    return {
        "pessoas": pessoas,
        "medicos_por_status": por_status,
        "medicos_logados": len(medicos),
        "recepcao_logada": sum(1 for i in equipe if i.get("perfil") == "RECEPCAO_TRIAGEM"),
    }


class EquipeState(rx.State):
    pessoas: list[dict[str, str]] = []
    medicos_por_status: list[dict[str, Any]] = []
    medicos_logados: int = 0
    recepcao_logada: int = 0
    mensagem: str = ""

    async def carregar(self) -> None:
        ok, corpo = await chamar(self, "GET", "/admin/equipe")
        if not ok:
            self.mensagem = str(corpo)
            return
        for campo, valor in resumir_equipe(list((corpo or {}).get("equipe") or [])).items():
            setattr(self, campo, valor)
        self.mensagem = ""

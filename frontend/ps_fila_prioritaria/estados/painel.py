"""Painel público da sala de espera (add-painel-publico, D2 e D4). Sem login e só leitura.

O Xano devolve só campos permitidos (senha, cor, especialidade, Sala, tentativa e horários); aqui eles são
formatados para a TV. Uma chamada nova ou repetida é reconhecida pelo `chamada_id` da atual e pelo ticket e horário
da triagem: quando mudam, a tela destaca a senha e toca um aviso curto. Em falha de rede, mantém o último estado e
mostra "reconectando".
"""

from typing import Any

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import _hora_brasilia, formatar_ticket

NOME_COR = {"VERMELHA": "Vermelha", "AMARELA": "Amarela", "AZUL": "Azul"}

# Aviso de dois tons pela Web Audio API: sem arquivo de som. O navegador só libera o áudio depois de um toque
# na página, por isso o painel pede "Toque para ativar o som" na primeira vez (D2).
SCRIPT_SOM = """
(function(){
  var C = window.AudioContext || window.webkitAudioContext; if (!C) return;
  window.__psAudio = window.__psAudio || new C();
  var ctx = window.__psAudio; if (ctx.state === 'suspended') ctx.resume();
  [[880, 0], [1320, 0.28]].forEach(function(t){
    var o = ctx.createOscillator(), g = ctx.createGain();
    o.frequency.value = t[0]; o.connect(g); g.connect(ctx.destination);
    var i = ctx.currentTime + t[1];
    g.gain.setValueAtTime(0.0001, i); g.gain.exponentialRampToValueAtTime(0.4, i + 0.03);
    g.gain.exponentialRampToValueAtTime(0.0001, i + 0.25);
    o.start(i); o.stop(i + 0.26);
  });
})();
"""


def tentativa_texto(tentativa: Any) -> str:
    n = int(tentativa or 1)
    return f"{n}ª chamada" if n > 1 else ""


def destino(chamada: dict[str, Any]) -> str:
    """Para onde ir: "Cardiologia — Sala 2", ou só a especialidade quando o médico não tem Sala (D3)."""
    especialidade = str(chamada.get("especialidade") or "")
    sala = str(chamada.get("sala") or "").strip()
    if not sala:
        return especialidade
    rotulo = sala if sala.lower().startswith("sala") else f"Sala {sala}"
    return f"{especialidade} — {rotulo}" if especialidade else rotulo


def chave_novidade(corpo: dict[str, Any]) -> str:
    """Muda a cada chamada médica nova ou repetida e a cada chamada ou rechamada de ticket na triagem."""
    atual, triagem = corpo.get("atual") or {}, corpo.get("triagem") or {}
    return f"{atual.get('chamada_id', '')}|{triagem.get('ticket_id', '')}:{triagem.get('chamado_em', '')}"


def montar_painel(corpo: dict[str, Any]) -> dict[str, Any]:
    atual = corpo.get("atual")
    triagem = corpo.get("triagem")
    return {
        "atual": None if not atual else {
            "senha": str(atual.get("senha") or "—"),
            "cor": str(atual.get("cor") or ""),
            "cor_nome": NOME_COR.get(str(atual.get("cor") or ""), ""),
            "destino": destino(atual),
            "tentativa": tentativa_texto(atual.get("tentativa")),
            "hora": _hora_brasilia(atual.get("chamado_em")),
        },
        "ultimas": [{"senha": str(u.get("senha") or "—"), "cor": str(u.get("cor") or ""), "destino": destino(u),
                     "hora": _hora_brasilia(u.get("chamado_em"))} for u in (corpo.get("ultimas") or [])[:4]],
        "triagem": None if not triagem else {
            "ticket": formatar_ticket(triagem.get("tipo"), triagem.get("numero")),
            "tentativa": tentativa_texto(triagem.get("tentativa")),
            "hora": _hora_brasilia(triagem.get("chamado_em")),
        },
        "previsoes": [{"especialidade": str(p.get("especialidade") or ""), "sigla": str(p.get("sigla") or ""),
                       "senhas": [{"senha": str(s.get("senha") or ""), "cor": str(s.get("cor") or "")} for s in (p.get("senhas") or [])]}
                      for p in (corpo.get("previsoes") or [])],
    }


def siglas_do_filtro(valor: Any) -> str:
    """?especialidades=car, ort → "CAR,ORT"; vazio = todas as especialidades ativas."""
    return ",".join(s.strip().upper() for s in str(valor or "").split(",") if s.strip())


class PainelState(rx.State):
    atual: dict[str, str] = {}
    ultimas: list[dict[str, str]] = []
    triagem: dict[str, str] = {}
    previsoes: list[dict[str, Any]] = []
    carregado: bool = False
    reconectando: bool = False
    aviso: str = ""
    som_ativo: bool = False
    # Incrementa a cada novidade; a página usa o valor na `key` do destaque para reiniciar a animação.
    destaques: int = 0
    _chave: str = ""

    async def atualizar(self, _=None):
        filtro = siglas_do_filtro(self.router.url.query_parameters.get("especialidades", ""))
        try:
            resposta = api.requisitar("GET", "XANO_FILA_API_URL", "/painel", params={"especialidades": filtro} if filtro else None)
        except (api.ConfiguracaoAusente, httpx.RequestError):
            self.reconectando = True
            return
        if resposta.status_code == 400:
            self.reconectando, self.aviso = False, "Nenhuma especialidade ativa corresponde ao filtro do endereço."
            return
        if not resposta.is_success:
            self.reconectando = True
            return
        corpo = resposta.json() or {}
        painel = montar_painel(corpo)
        self.atual = painel["atual"] or {}
        self.ultimas = painel["ultimas"]
        self.triagem = painel["triagem"] or {}
        self.previsoes = painel["previsoes"]
        self.reconectando, self.aviso = False, ""
        chave = chave_novidade(corpo)
        novidade = self.carregado and chave != self._chave
        self._chave, self.carregado = chave, True
        if novidade:
            self.destaques += 1
            if self.som_ativo:
                yield rx.call_script(SCRIPT_SOM)

    def ativar_som(self):
        self.som_ativo = True
        return rx.call_script(SCRIPT_SOM)

"""Painéis públicos da sala de espera (add-painel-publico, D2, D4 e D6). Sem login e só leitura.

Duas telas (decisão do PO, 20/11/2026): /painel/medico, com a senha chamada pelo médico e as últimas chamadas, e
/painel/triagem, com o ticket chamado pela Recepção/Triagem e os últimos tickets. As duas usam o mesmo GET painel.

O Xano devolve só campos permitidos (senha, cor, especialidade, Sala, tentativa e horários); aqui eles são
formatados para a TV. Decisão do PO (20/11/2026): a tela não mostra a previsão das próximas senhas. Uma chamada nova ou repetida é reconhecida pelo `chamada_id` da atual e pelo ticket e horário
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
    return f"{int(tentativa or 1)}ª chamada"


def sala_texto(chamada: dict[str, Any]) -> str:
    """Sala vinculada ao médico que chamou ("Sala 2"), ou vazio quando ele não tem Sala (D3)."""
    sala = str(chamada.get("sala") or "").strip()
    if not sala:
        return ""
    return sala if sala.lower().startswith("sala") else f"Sala {sala}"


def destino(chamada: dict[str, Any]) -> str:
    """Para onde ir: "Cardiologia · Sala 2", ou só a especialidade quando o médico não tem Sala (D3)."""
    especialidade, sala = str(chamada.get("especialidade") or ""), sala_texto(chamada)
    return " · ".join(p for p in (especialidade, sala) if p)


def tela_da_rota(caminho: str) -> str:
    """/painel/triagem → "triagem"; /painel/medico → "medico"."""
    return "triagem" if str(caminho or "").rstrip("/").endswith("/triagem") else "medico"


def chave_novidade(corpo: dict[str, Any], tela: str) -> str:
    """Muda a cada chamada nova ou repetida da própria tela: médico (chamada_id) ou triagem (ticket e horário)."""
    if tela == "triagem":
        triagem = corpo.get("triagem") or {}
        return f"{triagem.get('ticket_id', '')}:{triagem.get('chamado_em', '')}"
    return str((corpo.get("atual") or {}).get("chamada_id", ""))


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
        "ultimas": [{"senha": str(u.get("senha") or "—"), "cor": str(u.get("cor") or ""), "especialidade": str(u.get("especialidade") or "—"),
                     "sala": sala_texto(u) or "—", "hora": _hora_brasilia(u.get("chamado_em"))} for u in (corpo.get("ultimas") or [])[:4]],
        "triagem": None if not triagem else {
            "ticket": formatar_ticket(triagem.get("tipo"), triagem.get("numero")),
            "tentativa": tentativa_texto(triagem.get("tentativa")),
            "hora": _hora_brasilia(triagem.get("chamado_em")),
        },
        "triagem_ultimas": [{"ticket": formatar_ticket(t.get("tipo"), t.get("numero")), "hora": _hora_brasilia(t.get("chamado_em"))}
                            for t in (corpo.get("triagem_ultimas") or [])[:4]],
    }


def siglas_do_filtro(valor: Any) -> str:
    """?especialidades=car, ort → "CAR,ORT"; vazio = todas as especialidades ativas."""
    return ",".join(s.strip().upper() for s in str(valor or "").split(",") if s.strip())


class PainelState(rx.State):
    atual: dict[str, str] = {}
    ultimas: list[dict[str, str]] = []
    triagem: dict[str, str] = {}
    triagem_ultimas: list[dict[str, str]] = []
    carregado: bool = False
    reconectando: bool = False
    aviso: str = ""
    som_ativo: bool = False
    # Incrementa a cada novidade; a página usa o valor na `key` do destaque para reiniciar a animação.
    destaques: int = 0
    _chave: str = ""

    async def atualizar(self, _=None):
        tela = tela_da_rota(self.router.url.path)
        # O filtro por especialidade só vale para o painel dos médicos; a triagem é comum a todas.
        filtro = siglas_do_filtro(self.router.url.query_parameters.get("especialidades", "")) if tela == "medico" else ""
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
        self.triagem_ultimas = painel["triagem_ultimas"]
        self.reconectando, self.aviso = False, ""
        chave = chave_novidade(corpo, tela)
        novidade = self.carregado and chave != self._chave
        self._chave, self.carregado = chave, True
        if novidade:
            self.destaques += 1
            if self.som_ativo:
                yield rx.call_script(SCRIPT_SOM)

    async def abrir(self):
        """Ao abrir uma das telas, recomeça a detecção de novidade (a outra tela pode ter deixado outra chave)."""
        self.carregado, self._chave, self.destaques = False, "", 0
        self.atual, self.ultimas, self.triagem, self.triagem_ultimas = {}, [], {}, []
        async for evento in self.atualizar():
            yield evento

    def ativar_som(self):
        self.som_ativo = True
        return rx.call_script(SCRIPT_SOM)

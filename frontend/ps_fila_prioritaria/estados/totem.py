"""Estado do Totem de autoatendimento (emissão de tickets)."""

import os

import httpx
import reflex as rx

from ps_fila_prioritaria import api


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

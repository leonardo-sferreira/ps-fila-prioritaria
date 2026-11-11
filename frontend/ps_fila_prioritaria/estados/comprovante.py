"""Estado do comprovante de senha impresso para o paciente."""

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import _data_hora_brasilia, _id_da_rota, _mensagem_erro
from ps_fila_prioritaria.estados.autenticacao import AuthState


NOME_PRIORIDADE = {"VERMELHA": "Vermelha", "AMARELA": "Amarela", "AZUL": "Azul"}


class ComprovanteState(rx.State):
    """Comprovante de 80 mm da senha (add-direcionamento-senha, D6): só senha, cor, especialidade e entrada."""

    ficha_id: int = 0
    senha: str = ""
    prioridade: str = ""
    especialidade: str = ""
    entrada: str = ""
    carregando: bool = False
    mensagem: str = ""

    async def carregar(self, ficha_id: str | int):
        try:
            self.ficha_id = int(ficha_id)
        except (TypeError, ValueError):
            self.mensagem = "Ficha inválida."
            return None
        auth = await self.get_state(AuthState)
        self.carregando = True
        self.mensagem = ""
        try:
            resposta = api.requisitar("GET", "XANO_TRIAGEM_API_URL", f"/fichas/{self.ficha_id}/comprovante", token=auth.token)
        except (api.ConfiguracaoAusente, httpx.RequestError):
            self.mensagem = "Não foi possível carregar o comprovante."
            return None
        finally:
            self.carregando = False
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
            return rx.redirect("/login")
        if not resposta.is_success:
            self.mensagem = _mensagem_erro(resposta)
            return None
        dados = resposta.json() or {}
        self.senha = str(dados.get("senha") or "")
        self.prioridade = NOME_PRIORIDADE.get(str(dados.get("prioridade")), "")
        self.especialidade = str((dados.get("especialidade") or {}).get("nome") or "")
        self.entrada = _data_hora_brasilia(dados.get("chegada_em"))
        # Abre a caixa de impressão do navegador (impressora térmica de 80 mm configurada no sistema).
        return rx.call_script("setTimeout(function(){window.print()}, 300)")

    async def carregar_da_rota(self):
        return await self.carregar(_id_da_rota(self.router.url.path))

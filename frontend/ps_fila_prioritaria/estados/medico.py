"""Estados do Médico: fila e chamada (add-fila-chamada-medico) e impressão da ficha atribuída."""

from typing import Any

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import _codigo_erro, _mensagem_erro
from ps_fila_prioritaria.estados.autenticacao import AuthState


class MedicoState(rx.State):
    """Consulta a fila e executa somente ações sobre a ficha atribuída pelo Xano."""

    filas: list[dict[str, Any]] = []
    ficha_atual: dict[str, Any] = {}
    historico: list[dict[str, Any]] = []
    apto: bool = False
    plantao_vigente: bool = False
    status_operacional: str = ""
    tem_ficha: bool = False
    mensagem: str = ""
    erro: bool = False
    confirmando_desistencia: bool = False
    ocupado: bool = False

    async def _requisitar(self, metodo: str, caminho: str, **kwargs: Any) -> httpx.Response | None:
        auth = await self.get_state(AuthState)
        try:
            resposta = api.requisitar(metodo, "XANO_FILA_API_URL", caminho, token=auth.token, **kwargs)
        except (api.ConfiguracaoAusente, httpx.RequestError):
            self.erro = True
            self.mensagem = "Não foi possível conectar à fila médica. Confira XANO_FILA_API_URL."
            return None
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
        if not resposta.is_success:
            self.erro = True
            codigo = _codigo_erro(resposta)
            if "FICHA_PENDENTE" in codigo:
                self.mensagem = "Confirme o comparecimento ou registre a desistência da ficha atual."
            elif "MEDICO_INDISPONIVEL" in codigo:
                self.mensagem = "Você não está disponível para chamar neste momento."
            elif "AGUARDE_INTERVALO:" in codigo:
                self.mensagem = f"Aguarde {codigo.split('AGUARDE_INTERVALO:', 1)[1].split()[0]} segundos para repetir a chamada."
            else:
                self.mensagem = _mensagem_erro(resposta)
            return None
        return resposta

    async def carregar(self) -> None:
        resposta = await self._requisitar("GET", "/medico/filas")
        if resposta is None:
            return
        dados = resposta.json() or {}
        self.filas = dados.get("filas") or []
        self.ficha_atual = dados.get("ficha_atual") or {}
        self.historico = dados.get("historico") or []
        self.tem_ficha = bool(self.ficha_atual)
        medico = dados.get("medico") or {}
        self.apto = bool(medico.get("apto"))
        self.plantao_vigente = bool(medico.get("plantao_vigente"))
        self.status_operacional = str(medico.get("status") or "INDISPONÍVEL")

    async def definir_status(self, status: str) -> None:
        if self.ocupado:
            return
        self.ocupado = True
        self.erro = False
        self.mensagem = ""
        try:
            auth = await self.get_state(AuthState)
            try:
                resposta = api.requisitar("PATCH", "XANO_AUTH_API_URL", "/me/status", token=auth.token, json={"status": status})
            except (api.ConfiguracaoAusente, httpx.RequestError):
                self.erro = True
                self.mensagem = "Não foi possível alterar o status. Confira a conexão."
                return
            if resposta.status_code == 401:
                auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
            if not resposta.is_success:
                self.erro = True
                self.mensagem = _mensagem_erro(resposta)
                return
            await self.carregar()
            self.mensagem = "Status atualizado."
        finally:
            self.ocupado = False

    async def chamar(self) -> None:
        if self.ocupado:
            return
        self.ocupado = True
        self.erro = False
        self.mensagem = ""
        try:
            resposta = await self._requisitar("POST", "/medico/chamar-proximo", json={})
            if resposta is not None:
                dados = resposta.json() or {}
                self.mensagem = "Nenhum paciente aguardando nas filas disponíveis." if dados.get("fila_vazia") else "Ficha chamada."
                await self.carregar()
        finally:
            self.ocupado = False

    async def _agir(self, acao: str) -> None:
        if self.ocupado or not self.tem_ficha:
            return
        self.ocupado = True
        self.erro = False
        self.mensagem = ""
        try:
            resposta = await self._requisitar("POST", f"/medico/fichas/{self.ficha_atual['id']}/acao", json={"acao": acao})
            if resposta is not None:
                dados = resposta.json() or {}
                if acao == "REPETIR":
                    self.mensagem = "Ficha chamada novamente." if dados.get("status") == "CHAMADO" else "Oportunidade encerrada; ficha devolvida à fila ou encerrada."
                elif acao == "COMPARECEU":
                    self.mensagem = "Comparecimento confirmado."
                else:
                    self.mensagem = "Desistência registrada."
                await self.carregar()
        finally:
            self.ocupado = False

    async def repetir(self) -> None:
        await self._agir("REPETIR")

    async def compareceu(self) -> None:
        await self._agir("COMPARECEU")

    def pedir_desistencia(self) -> None:
        self.confirmando_desistencia = True

    def cancelar_desistencia(self) -> None:
        self.confirmando_desistencia = False

    async def desistiu(self) -> None:
        self.confirmando_desistencia = False
        await self._agir("DESISTENCIA")


class ImpressaoMedicoState(rx.State):
    tem_dados: bool = False
    mensagem: str = ""
    senha: str = ""
    especialidade: str = ""
    nome: str = ""
    idade: str = ""
    prioridade: str = ""
    condicao: str = ""
    escore: str = ""
    classificacao: str = ""
    sintomas: list[str] = []
    observacao: str = ""
    pa_sistolica: str = ""
    fc: str = ""
    fr: str = ""
    temperatura: str = ""
    spo2: str = ""
    glicemia: str = ""

    async def carregar_da_rota(self):
        partes = str(self.router.url.path or "").rstrip("/").split("/")
        ficha_id = partes[-2] if len(partes) >= 2 and partes[-1] == "imprimir" else ""
        self.tem_dados = False
        self.mensagem = ""
        if not ficha_id.isdigit():
            self.mensagem = "Ficha inválida para impressão."
            return None
        auth = await self.get_state(AuthState)
        try:
            resposta = api.requisitar("GET", "XANO_FILA_API_URL", f"/fichas/{ficha_id}/impressao", token=auth.token)
        except (api.ConfiguracaoAusente, httpx.RequestError):
            self.mensagem = "Não foi possível carregar a ficha para impressão."
            return None
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
            return rx.redirect("/login")
        if not resposta.is_success:
            self.mensagem = "Você não pode imprimir esta ficha." if resposta.status_code in (403, 404) else _mensagem_erro(resposta)
            return None
        dados = resposta.json() or {}
        ficha = dados.get("ficha") or {}
        paciente = dados.get("paciente") or {}
        mostrar = lambda valor: "—" if valor is None or valor == "" else str(valor)
        self.senha = mostrar(ficha.get("senha"))
        self.especialidade = mostrar((ficha.get("especialidade") or {}).get("nome"))
        self.nome = mostrar(paciente.get("nome"))
        self.idade = mostrar(paciente.get("idade"))
        self.prioridade = mostrar(ficha.get("prioridade_atual"))
        self.condicao = mostrar(ficha.get("condicao_prioritaria"))
        self.escore = mostrar(ficha.get("escore_risco"))
        self.classificacao = mostrar(ficha.get("classificacao_risco"))
        self.sintomas = [str(item.get("nome")) for item in dados.get("sintomas") or []] + [str(item) for item in dados.get("sintomas_livres") or []]
        self.observacao = mostrar(ficha.get("observacao"))
        self.pa_sistolica = mostrar(ficha.get("pa_sistolica"))
        self.fc = mostrar(ficha.get("fc"))
        self.fr = mostrar(ficha.get("fr"))
        self.temperatura = mostrar(ficha.get("temperatura"))
        self.spo2 = mostrar(ficha.get("spo2"))
        self.glicemia = mostrar(ficha.get("glicemia"))
        self.tem_dados = True
        return rx.call_script("setTimeout(function(){window.print()}, 300)")

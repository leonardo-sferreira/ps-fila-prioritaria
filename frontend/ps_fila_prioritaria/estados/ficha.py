"""Estado da ficha de atendimento: sintomas, sinais vitais, classificação e direcionamento."""

import unicodedata
from collections.abc import AsyncIterator
from typing import Any

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import (
    NOME_SINAL_VITAL,
    _codigo_erro,
    _id_da_rota,
    _mensagem_erro,
    mascarar_cpf,
)
from ps_fila_prioritaria.estados.autenticacao import AuthState


# Sinais vitais da ficha (add-classificacao-prioridade). A pontuação e a cor são calculadas no Xano.
CAMPOS_SINAIS_VITAIS = ["pa_sistolica", "fc", "fr", "temperatura", "spo2", "glicemia"]


NOME_CONDICAO = {"NENHUMA": "Nenhuma", "IDOSO": "Idoso", "CRIANCA": "Criança", "GESTANTE": "Gestante"}


LIMITE_SINTOMAS_LIVRES = 10


_PENDENCIA_SINAL = {
    "PA_SISTOLICA_NAO_INFORMADO": "Informe a PA sistólica.",
    "FC_NAO_INFORMADO": "Informe a frequência cardíaca.",
    "FR_NAO_INFORMADO": "Informe a frequência respiratória.",
    "TEMPERATURA_NAO_INFORMADO": "Informe a temperatura.",
    "SPO2_NAO_INFORMADO": "Informe a SpO2.",
    "TABELA_ADULTA_NAO_APLICAVEL": "Menor de 16 anos ou idade não informada: defina a prioridade manualmente.",
    "SEM_SINTOMA_OU_OBSERVACAO": "Informe ao menos um sintoma ou uma observação.",
    "PARAMETRO_NAO_CONFIGURADO": "Os parâmetros da classificação não estão configurados.",
}


def _texto_pendencia(codigo: str) -> str:
    if codigo.startswith("FAIXA_NAO_CONFIGURADA:"):
        return f"Faixa de pontuação não configurada para {codigo.split(':', 1)[1]}."
    return _PENDENCIA_SINAL.get(codigo, codigo)


# Faixas de referência (as de 0 ponto, configuradas no Xano) mostradas ao lado de cada sinal vital.
CAMPO_DO_PARAMETRO = {
    "PA_SISTOLICA": "pa_sistolica",
    "FC": "fc",
    "FR": "fr",
    "TEMPERATURA": "temperatura",
    "SPO2": "spo2",
    "GLICEMIA": "glicemia",
}


def _referencias_sinais(faixas: Any) -> dict[str, str]:
    """Monta "Ref.: 111–219" por campo a partir das faixas sem pontos; sem faixa, o campo fica sem referência."""
    trechos: dict[str, list[str]] = {}
    for faixa in faixas or []:
        campo = CAMPO_DO_PARAMETRO.get(str(faixa.get("parametro")))
        if campo is None:
            continue
        minimo, maximo = _texto_sinal(faixa.get("minimo")), _texto_sinal(faixa.get("maximo"))
        if minimo and maximo:
            trecho = f"{minimo}–{maximo}"
        elif minimo:
            trecho = f"≥ {minimo}"
        elif maximo:
            trecho = f"≤ {maximo}"
        else:
            continue
        trechos.setdefault(campo, []).append(trecho)
    return {campo: ("Ref.: " + " ou ".join(trechos[campo])) if campo in trechos else "" for campo in CAMPOS_SINAIS_VITAIS}


def _texto_sinal(valor: Any) -> str:
    """Mostra o número salvo no campo, com vírgula decimal; null vira campo vazio."""
    if valor is None or valor == "":
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return str(valor).replace(".", ",")


def _normalizar_texto(texto: str) -> str:
    """Compara nomes de sintomas sem diferenciar maiúsculas, acentos e espaços extras (como o Xano)."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sem_acento.casefold().split())


class FichaState(rx.State):
    """Estado da ficha de triagem, separado do cadastro de Paciente.

    A regra clínica (escore, cor, pendências) é calculada no Xano; aqui só ficam os valores digitados,
    o envio e a exibição do resultado (add-classificacao-prioridade, D7 e D8).
    """

    ficha_id: int = 0
    ficha: dict[str, Any] = {}
    paciente: dict[str, Any] = {}
    catalogo_sintomas: list[dict[str, Any]] = []
    sintoma_ids_selecionados: list[int] = []
    observacao: str = ""
    # Sintomas digitados pela Recepção/Triagem: [{descricao, pontuacao}] (D9).
    sintomas_livres: list[dict[str, Any]] = []
    # Sinais vitais como texto dos campos; vazio = não medido.
    sinais: dict[str, str] = {campo: "" for campo in CAMPOS_SINAIS_VITAIS}
    # Valores como vieram do Xano, para marcar o que foi alterado e ainda não salvo.
    sinais_salvos: dict[str, str] = {campo: "" for campo in CAMPOS_SINAIS_VITAIS}
    referencias_sinais: dict[str, str] = {campo: "" for campo in CAMPOS_SINAIS_VITAIS}
    glicemia_gravidade: bool = False
    gestante: bool = False
    classificacao: dict[str, Any] = {}
    sintomas_alterados: bool = False
    observacao_alterada: bool = False
    livres_alterados: bool = False
    sinais_alterados: bool = False
    carregando: bool = False
    salvando: bool = False
    mensagem: str = ""
    erro: bool = False
    # Ajuste manual da prioridade (D6).
    ajuste_aberto: bool = False
    ajuste_prioridade: str = ""
    ajuste_justificativa: str = ""
    ajuste_erro: str = ""
    ajustando: bool = False
    # Direcionamento: especialidade prevista enquanto EM_TRIAGEM (add-direcionamento-senha, D7).
    destino_previsto: dict[str, Any] = {}
    confirmando: bool = False
    # Reavaliação em AGUARDANDO (add-reavaliacao-ficha-aguardando, D6): aviso fixo quando a senha muda e
    # código do último erro da API, para reagir à ficha que ficaria sem cor.
    aviso_senha: str = ""
    ultimo_erro: str = ""

    @rx.var
    def cpf_exibido(self) -> str:
        return mascarar_cpf(self.paciente.get("cpf"))

    @rx.var
    def prioridade_exibida(self) -> str:
        """Prioridade atual gravada ou, sem ajuste salvo, a calculada agora pelo Xano."""
        return str(self.classificacao.get("prioridade_atual") or self.classificacao.get("prioridade_calculada") or "")

    @rx.var
    def prioridade_calculada(self) -> str:
        return str(self.classificacao.get("prioridade_calculada") or "")

    @rx.var
    def ajustada_manualmente(self) -> bool:
        return bool(self.classificacao.get("justificativa_ajuste"))

    @rx.var
    def resumo_escore(self) -> str:
        total = self.classificacao.get("escore_total")
        sintomas = self.classificacao.get("escore_sintomas")
        sinais = self.classificacao.get("escore_sinais")
        if total is None:
            return f"Escore incompleto (sintomas {sintomas or 0})"
        critico = " · item isolado de 3 pontos → Vermelha" if self.classificacao.get("item_critico") else ""
        return f"Escore total {total} (sintomas {sintomas or 0} · sinais vitais {sinais or 0}){critico}"

    @rx.var
    def situacao_sinais(self) -> dict[str, str]:
        """Por campo: "vazio" (não preenchido), "alterado" (mudou e falta salvar) ou "salvo"."""
        situacao = {}
        for campo in CAMPOS_SINAIS_VITAIS:
            atual = str(self.sinais.get(campo) or "").strip()
            if atual != str(self.sinais_salvos.get(campo) or "").strip():
                situacao[campo] = "alterado"
            else:
                situacao[campo] = "salvo" if atual else "vazio"
        return situacao

    @rx.var
    def aviso_classificacao(self) -> str:
        """Pendências da classificação numa linha só; gestante tem aviso próprio."""
        textos = []
        for codigo in self.classificacao.get("pendencias") or []:
            if codigo == "TABELA_ADULTA_NAO_APLICAVEL" and self.classificacao.get("condicao_prioritaria") == "GESTANTE":
                textos.append("Gestante: a tabela adulta não se aplica, defina a prioridade manualmente.")
            else:
                textos.append(_texto_pendencia(str(codigo)))
        return " ".join(textos)

    @rx.var
    def condicao_texto(self) -> str:
        return NOME_CONDICAO.get(str(self.classificacao.get("condicao_prioritaria") or "NENHUMA"), "Nenhuma")

    @rx.var
    def em_triagem(self) -> bool:
        return self.ficha.get("status") == "EM_TRIAGEM"

    @rx.var
    def aguardando(self) -> bool:
        return self.ficha.get("status") == "AGUARDANDO"

    @rx.var
    def destino_texto(self) -> str:
        especialidade = (self.destino_previsto or {}).get("especialidade") or {}
        if not especialidade:
            return "Destino ainda indisponível (calculado ao confirmar)."
        motivo = {"PEDIATRIA": " (até 11 anos)", "PADRAO": " (sem sintoma da lista)"}.get(str(self.destino_previsto.get("motivo")), "")
        return f"{especialidade.get('nome')}{motivo}"

    @rx.var
    def senha_ficha(self) -> str:
        return str(self.ficha.get("senha") or "")

    @rx.var
    def especialidade_ficha(self) -> str:
        return str((self.ficha.get("especialidade") or {}).get("nome") or "")

    @rx.var
    def idade_texto(self) -> str:
        idade = self.paciente.get("idade")
        return f"{idade} anos" if idade is not None else "Idade não informada"

    def _limpar_feedback(self) -> None:
        self.mensagem = ""
        self.erro = False

    async def _requisitar(self, metodo: str, caminho: str, **kwargs: Any) -> httpx.Response | None:
        """Chama o grupo Triagem com o token da sessão; 401 encerra a sessão local (D7)."""
        auth = await self.get_state(AuthState)
        try:
            resposta = api.requisitar(metodo, "XANO_TRIAGEM_API_URL", caminho, token=auth.token, **kwargs)
        except api.ConfiguracaoAusente:
            self.mensagem = "Configure XANO_TRIAGEM_API_URL para conectar a ficha à API do PS."
            self.erro = True
            return None
        except httpx.RequestError:
            self.mensagem = "Não foi possível conectar à API de Fichas."
            self.erro = True
            return None
        if resposta.status_code == 401:
            auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
        self.ultimo_erro = ""
        if not resposta.is_success:
            self.ultimo_erro = _codigo_erro(resposta)
            self.mensagem = _mensagem_erro(resposta)
            self.erro = True
            return None
        return resposta

    def _alteracoes_pendentes(self) -> bool:
        return self.sintomas_alterados or self.observacao_alterada or self.livres_alterados or self.sinais_alterados

    def _registrar_senha(self, resultado: dict[str, Any]) -> None:
        """Guarda o aviso de reimpressão quando a reavaliação troca a senha (D6)."""
        if resultado.get("senha_alterada"):
            self.aviso_senha = (
                f"Senha alterada de {resultado.get('senha_anterior')} para {resultado.get('senha')}: "
                "reimprima o comprovante."
            )

    def _carregar_resposta_ficha(self, dados: dict[str, Any]) -> None:
        ficha = dados.get("ficha") or {}
        self.ficha = dict(ficha)
        self.ficha_id = int(ficha.get("id", self.ficha_id))
        self.paciente = dict(dados.get("paciente") or {})
        self.observacao = str(ficha.get("observacao") or "")
        self.sintoma_ids_selecionados = sorted(int(sintoma["id"]) for sintoma in (dados.get("sintomas") or []))
        self.sintomas_livres = [
            {"descricao": str(livre.get("descricao") or ""), "pontuacao": int(livre.get("pontuacao") or 0)}
            for livre in (dados.get("sintomas_livres") or [])
        ]
        self.sinais = {campo: _texto_sinal(ficha.get(campo)) for campo in CAMPOS_SINAIS_VITAIS}
        self.sinais_salvos = dict(self.sinais)
        self.referencias_sinais = _referencias_sinais(dados.get("referencias_sinais"))
        self.glicemia_gravidade = bool(ficha.get("glicemia_sinais_gravidade"))
        self.gestante = bool(ficha.get("gestante"))
        self.classificacao = dict(dados.get("classificacao") or {})
        self.destino_previsto = dict(dados.get("destino_previsto") or {})
        self.sintomas_alterados = False
        self.observacao_alterada = False
        self.livres_alterados = False
        self.sinais_alterados = False

    async def _recarregar(self) -> bool:
        resposta_ficha = await self._requisitar("GET", f"/fichas/{self.ficha_id}")
        if resposta_ficha is None:
            return False
        resposta_sintomas = await self._requisitar("GET", "/sintomas")
        if resposta_sintomas is None:
            return False
        self._carregar_resposta_ficha(resposta_ficha.json())
        self.catalogo_sintomas = sorted(
            list(resposta_sintomas.json() or []),
            key=lambda sintoma: str(sintoma["nome"]).casefold(),
        )
        return True

    async def carregar(self, ficha_id: str | int) -> None:
        """Recupera catálogo ativo e estado persistido para edição da ficha."""
        try:
            self.ficha_id = int(ficha_id)
        except (TypeError, ValueError):
            self.mensagem = "Ficha inválida."
            self.erro = True
            return
        self.carregando = True
        self._limpar_feedback()
        # O aviso de reimpressão vale para a ficha salva agora, não para outra ficha aberta depois.
        self.aviso_senha = ""
        try:
            await self._recarregar()
        finally:
            self.carregando = False

    async def carregar_da_rota(self) -> None:
        ficha_id = _id_da_rota(self.router.url.path)
        await self.carregar(ficha_id)

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

    def set_sinal(self, campo: str, valor: str) -> None:
        if campo in CAMPOS_SINAIS_VITAIS:
            self.sinais = {**self.sinais, campo: valor}
            self.sinais_alterados = True

    def set_glicemia_gravidade(self, marcado: bool) -> None:
        self.glicemia_gravidade = bool(marcado)
        self.sinais_alterados = True

    def set_gestante(self, marcado: bool) -> None:
        self.gestante = bool(marcado)
        self.sinais_alterados = True

    def adicionar_sintoma_livre(self, descricao: str, pontuacao: int) -> None:
        """Valida na tela o que o Xano também valida, para avisar antes de salvar (D9)."""
        texto = " ".join(str(descricao or "").split())
        if not 3 <= len(texto) <= 80:
            self.mensagem = "Descreva o sintoma com 3 a 80 caracteres."
            self.erro = True
            return
        if int(pontuacao) not in (1, 2, 3):
            self.mensagem = "Escolha a gravidade do sintoma: 1, 2 ou 3."
            self.erro = True
            return
        chave = _normalizar_texto(texto)
        if any(_normalizar_texto(str(s.get("nome"))) == chave for s in self.catalogo_sintomas):
            self.mensagem = f"\"{texto}\" já está na lista de sintomas: selecione-o na pesquisa."
            self.erro = True
            return
        if any(_normalizar_texto(str(s.get("descricao"))) == chave for s in self.sintomas_livres):
            self.mensagem = f"\"{texto}\" já foi adicionado."
            self.erro = True
            return
        if len(self.sintomas_livres) >= LIMITE_SINTOMAS_LIVRES:
            self.mensagem = f"Limite de {LIMITE_SINTOMAS_LIVRES} sintomas não listados por ficha."
            self.erro = True
            return
        self.sintomas_livres = [*self.sintomas_livres, {"descricao": texto, "pontuacao": int(pontuacao)}]
        self.livres_alterados = True
        self._limpar_feedback()

    def remover_sintoma_livre(self, descricao: str) -> None:
        self.sintomas_livres = [s for s in self.sintomas_livres if s.get("descricao") != descricao]
        self.livres_alterados = True

    def _sinais_para_envio(self) -> dict[str, Any] | None:
        """Converte os campos em números; vazio vira null. Retorna None e avisa se algum não for número."""
        dados: dict[str, Any] = {"glicemia_sinais_gravidade": self.glicemia_gravidade, "gestante": self.gestante}
        for campo in CAMPOS_SINAIS_VITAIS:
            texto = str(self.sinais.get(campo) or "").strip().replace(",", ".")
            if not texto:
                dados[campo] = None
                continue
            try:
                numero = float(texto)
            except ValueError:
                self.mensagem = f"Valor inválido em {NOME_SINAL_VITAL[campo]}."
                self.erro = True
                return None
            dados[campo] = numero if campo == "temperatura" else (int(numero) if numero.is_integer() else numero)
        return dados

    async def salvar(self) -> AsyncIterator[None]:
        """Envia o estado final de sintomas, observação e sinais vitais; o Xano valida e recalcula a cor."""
        if self.salvando:
            return

        if not self.ficha_id:
            self.mensagem = "Nenhuma ficha foi carregada para salvar."
            self.erro = True
            return

        if not self.sintoma_ids_selecionados and not self.sintomas_livres and not self.observacao.strip():
            self.mensagem = "Informe ao menos um sintoma ou uma observação/queixa."
            self.erro = True
            return

        self._limpar_feedback()
        dados = self._dados_alterados()
        if dados is None:
            return
        if not dados:
            self.mensagem = "Nenhuma alteração para salvar."
            return

        self.salvando = True
        # Entrega o loading antes das requisições de PATCH e GET.
        yield
        try:
            await self._enviar_alteracoes(dados)
        finally:
            self.salvando = False

    def _dados_alterados(self) -> dict[str, Any] | None:
        """Monta o PATCH só com o que mudou; None quando um sinal vital digitado é inválido."""
        dados: dict[str, Any] = {}
        if self.sintomas_alterados:
            # Uma lista vazia é uma coleção final válida e não equivale a campo omitido.
            dados["sintoma_ids"] = self.sintoma_ids_selecionados
        if self.observacao_alterada:
            dados["observacao"] = self.observacao
        if self.livres_alterados:
            dados["sintomas_livres"] = self.sintomas_livres
        if self.sinais_alterados:
            sinais = self._sinais_para_envio()
            if sinais is None:
                return None
            dados["sinais_vitais"] = sinais
        return dados

    async def _enviar_alteracoes(self, dados: dict[str, Any]) -> bool:
        """Envia o PATCH; em AGUARDANDO o Xano também refaz destino e senha (D3)."""
        resposta = await self._requisitar("PATCH", f"/fichas/{self.ficha_id}", json=dados)
        if resposta is None:
            if self.ultimo_erro == "FICHA_SEM_PRIORIDADE" and self.ficha.get("status") == "AGUARDANDO":
                # A ficha não pode ficar na fila sem cor: o ajuste vai junto com as alterações (D2).
                self.mensagem = (
                    "Com essas alterações a cor não pode ser calculada. Escolha a prioridade com justificativa "
                    "para salvar tudo junto."
                )
                self.abrir_ajuste()
            return False
        self._registrar_senha(resposta.json() or {})
        if await self._recarregar():
            self.mensagem = "Ficha salva. A prioridade foi recalculada."
            self.erro = False
        elif not self.mensagem:
            self.mensagem = "A ficha foi salva, mas não foi possível recarregá-la."
            self.erro = True
        return True

    def abrir_ajuste(self) -> None:
        self.ajuste_prioridade = ""
        self.ajuste_justificativa = ""
        self.ajuste_erro = ""
        self.ajuste_aberto = True

    def fechar_ajuste(self) -> None:
        self.ajuste_aberto = False

    def set_ajuste_aberto(self, aberto: bool) -> None:
        self.ajuste_aberto = bool(aberto)

    def set_ajuste_prioridade(self, valor: str) -> None:
        self.ajuste_prioridade = valor

    def set_ajuste_justificativa(self, valor: str) -> None:
        self.ajuste_justificativa = valor

    async def confirmar_triagem(self):
        """Confirma a triagem: o Xano define o destino, gera a senha e leva a ficha a AGUARDANDO (D5)."""
        if self.confirmando or not self.ficha_id:
            return None
        if self.sintomas_alterados or self.observacao_alterada or self.livres_alterados or self.sinais_alterados:
            self.mensagem = "Salve a ficha antes de confirmar."
            self.erro = True
            return None
        if not self.classificacao.get("prioridade_atual"):
            self.mensagem = "Defina a cor antes de confirmar: salve os sinais vitais ou ajuste a prioridade manualmente."
            self.erro = True
            return None
        self._limpar_feedback()
        self.confirmando = True
        try:
            resposta = await self._requisitar("POST", f"/fichas/{self.ficha_id}/confirmar-triagem")
        finally:
            self.confirmando = False
        if resposta is None:
            return None
        return rx.redirect(f"/recepcao/comprovante/{self.ficha_id}")

    def reimprimir(self):
        return rx.redirect(f"/recepcao/comprovante/{self.ficha_id}")

    async def confirmar_ajuste(self) -> None:
        """Ajuste manual ou classificação manual excepcional, sempre com justificativa (D6)."""
        if self.ajuste_prioridade not in ("VERMELHA", "AMARELA", "AZUL"):
            self.ajuste_erro = "Escolha a prioridade."
            return
        if not self.ajuste_justificativa.strip():
            self.ajuste_erro = "A justificativa é obrigatória."
            return
        pendentes = self._alteracoes_pendentes()
        if pendentes and self.ficha.get("status") == "AGUARDANDO":
            # Com alterações pendentes, a cor calculada mostrada ainda é a antiga: o Xano valida contra a nova.
            await self._ajustar_com_alteracoes()
            return
        if self.prioridade_calculada and self.ajuste_prioridade == self.prioridade_calculada:
            self.ajuste_erro = "Essa já é a prioridade calculada. Escolha outra cor."
            return
        if pendentes:
            self.ajuste_erro = "Salve a ficha antes de ajustar a prioridade: salvar recalcula a cor e descarta ajustes."
            return
        self.ajuste_erro = ""
        self._limpar_feedback()
        self.ajustando = True
        try:
            resposta = await self._requisitar(
                "POST",
                f"/fichas/{self.ficha_id}/prioridade",
                json={"prioridade": self.ajuste_prioridade, "justificativa": self.ajuste_justificativa.strip()},
            )
            if resposta is None:
                self.ajuste_erro = self.mensagem
                self._limpar_feedback()
                return
            self.ajuste_aberto = False
            self._registrar_senha(resposta.json() or {})
            if await self._recarregar():
                self.mensagem = "Prioridade ajustada. A justificativa ficou registrada na auditoria."
                self.erro = False
        finally:
            self.ajustando = False

    async def _ajustar_com_alteracoes(self) -> None:
        """Ficha AGUARDANDO: alterações clínicas e ajuste no mesmo PATCH, para não ficar sem cor (D2)."""
        dados = self._dados_alterados()
        if dados is None:
            self.ajuste_erro = self.mensagem
            self._limpar_feedback()
            return
        dados["prioridade_ajuste"] = self.ajuste_prioridade
        dados["justificativa_ajuste"] = self.ajuste_justificativa.strip()
        self.ajuste_erro = ""
        self._limpar_feedback()
        self.ajustando = True
        try:
            if await self._enviar_alteracoes(dados):
                self.ajuste_aberto = False
                self.mensagem = "Ficha salva com a prioridade ajustada. A justificativa ficou registrada na auditoria."
            else:
                self.ajuste_erro = self.mensagem
                self._limpar_feedback()
        finally:
            self.ajustando = False

    def fechar_aviso_senha(self) -> None:
        self.aviso_senha = ""


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

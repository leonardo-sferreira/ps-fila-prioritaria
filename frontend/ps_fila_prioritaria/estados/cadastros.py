"""Estados das telas de cadastro do Administrador (add-cadastros-administrador, D9).

`CadastroBase` é um mixin: cada tela herda lista, filtro, busca, diálogo de edição, salvar e ativar/desativar,
com os próprios dados. As regras e a validação ficam no Xano; aqui só se monta o corpo e se mostra o erro.
"""

from datetime import datetime
from typing import Any, ClassVar

import httpx
import reflex as rx

from ps_fila_prioritaria import api
from ps_fila_prioritaria.comum import FUSO_BRASILIA, _mensagem_erro, _timestamp_segundos
from ps_fila_prioritaria.estados.autenticacao import AuthState
from ps_fila_prioritaria.estados.ficha import _normalizar_texto as _normalizar_busca

VARIAVEL_API = "XANO_CADASTROS_API_URL"
GRUPOS_SINTOMA = [
    ("CARDIOVASCULAR", "Cardiovascular"),
    ("RESPIRATORIO", "Respiratório"),
    ("NEUROLOGICO", "Neurológico"),
    ("GASTROINTESTINAL", "Gastrointestinal"),
    ("TRAUMATICO_ORTOPEDICO", "Traumático/ortopédico"),
    ("TRAUMATICO_NEUROLOGICO", "Traumático/neurológico"),
    ("GERAL", "Geral"),
]
NOME_GRUPO = dict(GRUPOS_SINTOMA)


async def chamar(estado: Any, metodo: str, caminho: str, **kwargs: Any) -> tuple[bool, Any]:
    """Chama o grupo Cadastros com o token da sessão. Devolve (ok, corpo ou mensagem de erro)."""
    auth = await estado.get_state(AuthState)
    try:
        resposta = api.requisitar(metodo, VARIAVEL_API, caminho, token=auth.token, **kwargs)
    except api.ConfiguracaoAusente:
        return False, "Configure XANO_CADASTROS_API_URL no frontend/.env."
    except httpx.RequestError:
        return False, "Não foi possível conectar à API de cadastros."
    if resposta.status_code == 401:
        auth._encerrar_sessao_local("Sua sessão expirou. Faça login novamente.")
    if not resposta.is_success:
        return False, _mensagem_erro(resposta)
    return True, resposta.json()


def filtrar(itens: list[dict[str, Any]], filtro: str, busca: str, campos: tuple[str, ...]) -> list[dict[str, Any]]:
    """Filtro de situação (ATIVOS/INATIVOS/TODOS) e busca sem acento em alguns campos de texto."""
    termo = _normalizar_busca(busca)
    resultado = []
    for item in itens:
        ativo = bool(item.get("ativo"))
        if (filtro == "ATIVOS" and not ativo) or (filtro == "INATIVOS" and ativo):
            continue
        if termo and not any(termo in _normalizar_busca(str(item.get(c) or "")) for c in campos):
            continue
        resultado.append(item)
    return resultado


class CadastroBase(rx.State, mixin=True):
    """Comportamento comum das telas de cadastro; as subclasses dizem o caminho e como montar o formulário."""

    CAMINHO: ClassVar[str] = ""
    CAMPOS_BUSCA: ClassVar[tuple[str, ...]] = ("nome",)

    itens: list[dict[str, Any]] = []
    filtro: str = "ATIVOS"
    busca: str = ""
    carregando: bool = False
    mensagem: str = ""
    erro: bool = False
    dialogo_aberto: bool = False
    editando_id: int = 0
    form: dict[str, Any] = {}
    erro_form: str = ""
    salvando: bool = False

    @rx.var
    def itens_filtrados(self) -> list[dict[str, Any]]:
        return filtrar(self.itens, self.filtro, self.busca, self.CAMPOS_BUSCA)

    @rx.var
    def editando(self) -> bool:
        return self.editando_id != 0

    def set_filtro(self, valor: str | list[str]) -> None:
        self.filtro = valor[0] if isinstance(valor, list) and valor else str(valor or "ATIVOS")

    def set_busca(self, valor: str) -> None:
        self.busca = valor

    def set_dialogo_aberto(self, aberto: bool) -> None:
        self.dialogo_aberto = bool(aberto)

    def set_campo(self, campo: str, valor: Any) -> None:
        self.form = {**self.form, campo: valor}

    def alternar_especialidade(self, especialidade_id: int) -> None:
        """Marca/desmarca uma especialidade na lista ordenada do formulário (destinos ou especialidades próprias)."""
        ids = list(self.form.get("especialidade_ids") or [])
        especialidade_id = int(especialidade_id)
        self.form = {**self.form, "especialidade_ids": [i for i in ids if i != especialidade_id] if especialidade_id in ids else ids + [especialidade_id]}

    # Ganchos das subclasses.
    def _form_vazio(self) -> dict[str, Any]:
        return {}

    def _form_de(self, item: dict[str, Any]) -> dict[str, Any]:
        return dict(item)

    def _corpo(self) -> dict[str, Any]:
        return dict(self.form)

    async def _carregar_extras(self) -> None:
        """Opções dos formulários (especialidades, salas), quando a tela precisa."""

    async def carregar(self) -> None:
        self.carregando = True
        try:
            ok, corpo = await chamar(self, "GET", self.CAMINHO)
            if ok:
                self.itens = list(corpo or [])
                self.erro, self.mensagem = False, ""
                await self._carregar_extras()
            else:
                self.erro, self.mensagem = True, str(corpo)
        finally:
            self.carregando = False

    def abrir_novo(self) -> None:
        self.editando_id, self.form, self.erro_form, self.dialogo_aberto = 0, self._form_vazio(), "", True

    def abrir_edicao(self, item: dict[str, Any]) -> None:
        self.editando_id, self.form, self.erro_form, self.dialogo_aberto = int(item.get("id") or 0), self._form_de(item), "", True

    async def salvar(self) -> None:
        if self.salvando:
            return
        self.salvando, self.erro_form = True, ""
        try:
            if self.editando_id:
                ok, corpo = await chamar(self, "PATCH", f"{self.CAMINHO}/{self.editando_id}", json=self._corpo())
            else:
                ok, corpo = await chamar(self, "POST", self.CAMINHO, json=self._corpo())
        finally:
            self.salvando = False
        if not ok:
            self.erro_form = str(corpo)
            return
        self.dialogo_aberto = False
        await self.carregar()
        self.erro, self.mensagem = False, "Alteração salva."

    async def alternar_ativo(self, item_id: int, ativo: bool) -> None:
        ok, corpo = await chamar(self, "PATCH", f"{self.CAMINHO}/{int(item_id)}/ativo", json={"ativo": bool(ativo)})
        if not ok:
            self.erro, self.mensagem = True, str(corpo)
            return
        await self.carregar()
        self.erro, self.mensagem = False, "Ativado." if ativo else "Desativado."


class OpcoesEspecialidades(rx.State, mixin=True):
    """Especialidades ativas para escolher em formulários."""

    opcoes_especialidades: list[dict[str, Any]] = []

    async def _carregar_especialidades(self) -> None:
        ok, corpo = await chamar(self, "GET", "/especialidades")
        if ok:
            self.opcoes_especialidades = [{"id": int(e["id"]), "nome": str(e["nome"]), "sigla": str(e.get("sigla") or "")}
                                          for e in (corpo or []) if e.get("ativo", True)]


class EspecialidadesState(CadastroBase, rx.State):
    CAMINHO: ClassVar[str] = "/especialidades"
    CAMPOS_BUSCA: ClassVar[tuple[str, ...]] = ("nome", "sigla")

    def _form_vazio(self) -> dict[str, Any]:
        return {"nome": "", "sigla": "", "descricao": ""}

    def _form_de(self, item: dict[str, Any]) -> dict[str, Any]:
        return {"nome": item.get("nome") or "", "sigla": item.get("sigla") or "", "descricao": item.get("descricao") or ""}

    def _corpo(self) -> dict[str, Any]:
        corpo = {"nome": self.form.get("nome", ""), "descricao": self.form.get("descricao") or None}
        if not self.editando_id:
            corpo["sigla"] = str(self.form.get("sigla", "")).upper()
        return corpo


class SintomasState(CadastroBase, OpcoesEspecialidades, rx.State):
    CAMINHO: ClassVar[str] = "/sintomas"
    CAMPOS_BUSCA: ClassVar[tuple[str, ...]] = ("nome", "grupo_nome")

    @rx.var
    def ordem_destinos(self) -> str:
        """Destinos marcados, na ordem de preferência (a ordem em que foram marcados)."""
        nomes = {int(e["id"]): e["nome"] for e in self.opcoes_especialidades}
        ordem = [nomes.get(int(i), "?") for i in self.form.get("especialidade_ids") or []]
        return " → ".join(ordem) if ordem else "Nenhum destino marcado"

    async def carregar(self) -> None:
        await CadastroBase.carregar(self)
        self.itens = [{**s, "grupo_nome": NOME_GRUPO.get(str(s.get("grupo")), str(s.get("grupo") or "")),
                       "destinos": " → ".join(s.get("especialidades") or [])} for s in self.itens]

    async def _carregar_extras(self) -> None:
        await self._carregar_especialidades()

    def _form_vazio(self) -> dict[str, Any]:
        return {"nome": "", "descricao": "", "grupo": "GERAL", "pontuacao": "1", "especialidade_ids": []}

    def _form_de(self, item: dict[str, Any]) -> dict[str, Any]:
        return {"nome": item.get("nome") or "", "descricao": item.get("descricao") or "", "grupo": item.get("grupo") or "GERAL",
                "pontuacao": str(item.get("pontuacao") or 1), "especialidade_ids": [int(i) for i in item.get("especialidade_ids") or []]}

    def _corpo(self) -> dict[str, Any]:
        return {"nome": self.form.get("nome", ""), "descricao": self.form.get("descricao") or None, "grupo": self.form.get("grupo", "GERAL"),
                "pontuacao": int(self.form.get("pontuacao") or 0), "especialidade_ids": list(self.form.get("especialidade_ids") or [])}


class SalasState(CadastroBase, rx.State):
    CAMINHO: ClassVar[str] = "/salas"

    def _form_vazio(self) -> dict[str, Any]:
        return {"nome": "", "descricao": ""}

    def _form_de(self, item: dict[str, Any]) -> dict[str, Any]:
        return {"nome": item.get("nome") or "", "descricao": item.get("descricao") or ""}

    def _corpo(self) -> dict[str, Any]:
        return {"nome": self.form.get("nome", ""), "descricao": self.form.get("descricao") or None}


class MedicosState(CadastroBase, OpcoesEspecialidades, rx.State):
    CAMINHO: ClassVar[str] = "/medicos"
    CAMPOS_BUSCA: ClassVar[tuple[str, ...]] = ("nome", "email", "crm")

    opcoes_salas: list[dict[str, Any]] = []

    async def carregar(self) -> None:
        await CadastroBase.carregar(self)
        self.itens = [{**m, "lista_especialidades": ", ".join(m.get("especialidades") or []), "sala": m.get("sala") or "—"} for m in self.itens]

    async def _carregar_extras(self) -> None:
        await self._carregar_especialidades()
        ok, corpo = await chamar(self, "GET", "/salas")
        if ok:
            self.opcoes_salas = [{"id": str(s["id"]), "nome": str(s["nome"])} for s in (corpo or []) if s.get("ativo")]

    def _form_vazio(self) -> dict[str, Any]:
        return {"nome": "", "email": "", "senha": "", "crm": "", "especialidade_ids": [], "sala_id": ""}

    def _form_de(self, item: dict[str, Any]) -> dict[str, Any]:
        return {"nome": item.get("nome") or "", "email": item.get("email") or "", "senha": "", "crm": item.get("crm") or "",
                "especialidade_ids": [int(i) for i in item.get("especialidade_ids") or []],
                "sala_id": str(item.get("sala_id") or "")}

    def _corpo(self) -> dict[str, Any]:
        sala = str(self.form.get("sala_id") or "")
        corpo = {"nome": self.form.get("nome", ""), "email": self.form.get("email", ""), "crm": self.form.get("crm", ""),
                 "especialidade_ids": list(self.form.get("especialidade_ids") or []), "sala_id": int(sala) if sala.isdigit() else None}
        if not self.editando_id:
            corpo["senha"] = self.form.get("senha", "")
        return corpo


class RecepcaoState(CadastroBase, OpcoesEspecialidades, rx.State):
    CAMINHO: ClassVar[str] = "/recepcao"
    CAMPOS_BUSCA: ClassVar[tuple[str, ...]] = ("nome", "email")

    async def carregar(self) -> None:
        await CadastroBase.carregar(self)
        self.itens = [{**r, "cpf_exibido": _cpf_mascarado(r.get("cpf")), "especialidade_referencia": r.get("especialidade_referencia") or "—"}
                      for r in self.itens]

    async def _carregar_extras(self) -> None:
        await self._carregar_especialidades()

    def _form_vazio(self) -> dict[str, Any]:
        return {"nome": "", "email": "", "senha": "", "cpf": "", "especialidade_referencia_id": ""}

    def _form_de(self, item: dict[str, Any]) -> dict[str, Any]:
        return {"nome": item.get("nome") or "", "email": item.get("email") or "", "senha": "", "cpf": item.get("cpf") or "",
                "especialidade_referencia_id": str(item.get("especialidade_referencia_id") or "")}

    def _corpo(self) -> dict[str, Any]:
        referencia = str(self.form.get("especialidade_referencia_id") or "")
        corpo = {"nome": self.form.get("nome", ""), "email": self.form.get("email", ""), "cpf": self.form.get("cpf", ""),
                 "especialidade_referencia_id": int(referencia) if referencia.isdigit() else None}
        if not self.editando_id:
            corpo["senha"] = self.form.get("senha", "")
        return corpo


def _cpf_mascarado(cpf: Any) -> str:
    digitos = "".join(c for c in str(cpf or "") if c.isdigit())
    return f"***.{digitos[3:6]}.{digitos[6:9]}-**" if len(digitos) == 11 else "—"


def _hora(instante: Any) -> str:
    segundos = _timestamp_segundos(instante)
    return datetime.fromtimestamp(segundos, FUSO_BRASILIA).strftime("%H:%M") if segundos is not None else "—"


def _data(instante: Any) -> str:
    segundos = _timestamp_segundos(instante)
    return datetime.fromtimestamp(segundos, FUSO_BRASILIA).strftime("%Y-%m-%d") if segundos is not None else ""


def linha_plantao(plantao: dict[str, Any]) -> dict[str, Any]:
    """Plantão da API com horários em Brasília e a situação para a tela."""
    inicio, fim = plantao.get("inicio"), plantao.get("fim")
    vira_dia = _data(inicio) != _data(fim)
    situacao = "Encerrado" if plantao.get("encerrado_em") else ("Em andamento" if plantao.get("em_andamento") else ("Concluído" if plantao.get("iniciado") else "Agendado"))
    return {
        "id": int(plantao.get("id") or 0),
        "medico_id": int(plantao.get("medico_id") or 0),
        "medico": str(plantao.get("medico") or "—"),
        "sala": str(plantao.get("sala") or "—"),
        "especialidades": " · ".join(plantao.get("especialidades") or []),
        "data": _data(inicio),
        "hora_inicio": _hora(inicio),
        "hora_fim": _hora(fim),
        "horario": f"{_hora(inicio)} – {_hora(fim)}" + (" (+1 dia)" if vira_dia else ""),
        "situacao": situacao,
        "iniciado": bool(plantao.get("iniciado")),
    }


class PlantoesState(rx.State):
    """Plantões por dia (add-cadastros-administrador, D6)."""

    data: str = ""
    plantoes: list[dict[str, Any]] = []
    opcoes_medicos: list[dict[str, Any]] = []
    carregando: bool = False
    mensagem: str = ""
    erro: bool = False
    dialogo_aberto: bool = False
    editando_id: int = 0
    editando_iniciado: bool = False
    form: dict[str, Any] = {}
    erro_form: str = ""
    salvando: bool = False

    def set_data(self, valor: str) -> None:
        self.data = valor

    def set_dialogo_aberto(self, aberto: bool) -> None:
        self.dialogo_aberto = bool(aberto)

    def set_campo(self, campo: str, valor: Any) -> None:
        self.form = {**self.form, campo: valor}

    async def carregar(self) -> None:
        if not self.data:
            self.data = datetime.now(FUSO_BRASILIA).strftime("%Y-%m-%d")
        self.carregando = True
        try:
            ok, corpo = await chamar(self, "GET", "/disponibilidade", params={"data": self.data})
            if not ok:
                self.erro, self.mensagem = True, str(corpo)
                return
            self.plantoes = [linha_plantao(p) for p in (corpo or {}).get("plantoes") or []]
            ok_medicos, medicos = await chamar(self, "GET", "/medicos")
            if ok_medicos:
                self.opcoes_medicos = [{"id": str(m["id"]), "nome": f"{m.get('nome')} — {', '.join(m.get('especialidades') or [])}"}
                                       for m in (medicos or []) if m.get("ativo")]
            self.erro, self.mensagem = False, ""
        finally:
            self.carregando = False

    async def mudar_dia(self, valor: str) -> None:
        self.data = valor
        await self.carregar()

    def abrir_novo(self) -> None:
        self.editando_id, self.editando_iniciado, self.erro_form, self.dialogo_aberto = 0, False, "", True
        self.form = {"medico_id": "", "data": self.data, "hora_inicio": "07:00", "hora_fim": "19:00", "repetir": False, "data_fim": ""}

    def abrir_edicao(self, plantao: dict[str, Any]) -> None:
        self.editando_id, self.editando_iniciado, self.erro_form, self.dialogo_aberto = int(plantao["id"]), bool(plantao.get("iniciado")), "", True
        self.form = {"medico_id": str(plantao.get("medico_id") or ""), "data": plantao.get("data") or self.data,
                     "hora_inicio": plantao.get("hora_inicio") or "", "hora_fim": plantao.get("hora_fim") or ""}

    async def salvar(self) -> None:
        if self.salvando:
            return
        medico = str(self.form.get("medico_id") or "")
        if not self.editando_id and not medico.isdigit():
            self.erro_form = "Escolha o médico."
            return
        if not self.editando_id and self.form.get("repetir") and not self.form.get("data_fim"):
            self.erro_form = "Informe até quando vai a escala."
            return
        corpo = {"data": self.form.get("data", ""), "hora_inicio": self.form.get("hora_inicio", ""), "hora_fim": self.form.get("hora_fim", "")}
        self.salvando, self.erro_form = True, ""
        try:
            if self.editando_id:
                ok, resposta = await chamar(self, "PATCH", f"/disponibilidade/{self.editando_id}", json=corpo)
            else:
                novo = {**corpo, "medico_id": int(medico)}
                if self.form.get("repetir"):
                    novo["data_fim"] = str(self.form.get("data_fim") or "")
                ok, resposta = await chamar(self, "POST", "/disponibilidade", json=novo)
        finally:
            self.salvando = False
        if not ok:
            self.erro_form = str(resposta)
            return
        self.dialogo_aberto = False
        await self.carregar()
        criados = int((resposta or {}).get("criados") or 1) if isinstance(resposta, dict) else 1
        self.mensagem = f"{criados} plantões criados na escala 12x36." if criados > 1 else "Plantão salvo."

    async def remover(self, plantao_id: int) -> None:
        ok, resposta = await chamar(self, "DELETE", f"/disponibilidade/{int(plantao_id)}")
        if not ok:
            self.erro, self.mensagem = True, str(resposta)
            return
        await self.carregar()
        self.mensagem = "Plantão removido."


def linha_parametro(parametro: dict[str, Any]) -> dict[str, Any]:
    minimo, maximo = parametro.get("minimo"), parametro.get("maximo")
    limites = f"{minimo} a {maximo} {parametro.get('unidade') or ''}".strip() if minimo is not None and maximo is not None else ""
    valor = str(parametro.get("valor") or "")
    return {"chave": str(parametro.get("chave")), "valor": valor, "edicao": valor, "rotulo": str(parametro.get("rotulo") or parametro.get("chave")),
            "limites": limites, "tipo": str(parametro.get("tipo") or "INTEIRO"), "editavel": bool(parametro.get("editavel"))}


NOME_SINAL = {"PA_SISTOLICA": "PA sistólica (mmHg)", "FC": "Frequência cardíaca (bpm)", "FR": "Frequência respiratória (irpm)",
              "TEMPERATURA": "Temperatura (°C)", "SPO2": "SpO2 (%)", "GLICEMIA": "Glicemia (mg/dL)"}


def _numero(valor: Any) -> str:
    if valor is None or valor == "":
        return ""
    numero = float(valor)
    return str(int(numero)) if numero.is_integer() else str(numero).replace(".", ",")


def linha_faixa(faixa: dict[str, Any]) -> dict[str, Any]:
    minimo, maximo = _numero(faixa.get("minimo")), _numero(faixa.get("maximo"))
    intervalo = f"{minimo} a {maximo}" if minimo and maximo else (f"≥ {minimo}" if minimo else f"≤ {maximo}")
    condicao = faixa.get("condicao_gravidade")
    return {"id": int(faixa.get("id") or 0), "parametro": str(faixa.get("parametro")), "sinal": NOME_SINAL.get(str(faixa.get("parametro")), str(faixa.get("parametro"))),
            "minimo": minimo, "maximo": maximo, "intervalo": intervalo, "pontos": str(faixa.get("pontos")),
            "condicao": "" if condicao is None else ("com sinais de gravidade" if condicao else "sem sinais de gravidade")}


class ParametrosState(rx.State):
    """Parâmetros e faixas (add-cadastros-administrador, D7 e D8)."""

    parametros: list[dict[str, Any]] = []
    faixas: list[dict[str, Any]] = []
    opcoes_especialidades: list[dict[str, Any]] = []
    mensagem: str = ""
    erro: bool = False
    faixa_aberta: bool = False
    faixa_form: dict[str, Any] = {}
    erro_faixa: str = ""

    async def carregar(self) -> None:
        ok, corpo = await chamar(self, "GET", "/parametros")
        if not ok:
            self.erro, self.mensagem = True, str(corpo)
            return
        self.parametros = [linha_parametro(p) for p in (corpo or []) if p.get("editavel")]
        ok_faixas, faixas = await chamar(self, "GET", "/faixas")
        if ok_faixas:
            self.faixas = [linha_faixa(f) for f in (faixas or [])]
        ok_esp, especialidades = await chamar(self, "GET", "/especialidades")
        if ok_esp:
            self.opcoes_especialidades = [{"id": str(e["id"]), "nome": str(e["nome"])} for e in (especialidades or []) if e.get("ativo", True)]

    def set_valor(self, chave: str, valor: str) -> None:
        """Valor em edição fica na própria linha (o Reflex não indexa dicionário do estado com item do laço)."""
        self.parametros = [{**p, "edicao": valor} if p["chave"] == chave else p for p in self.parametros]

    async def salvar_parametro(self, chave: str) -> None:
        texto = str(next((p["edicao"] for p in self.parametros if p["chave"] == chave), "")).strip()
        if not texto.lstrip("-").isdigit():
            self.erro, self.mensagem = True, "Informe um número inteiro."
            return
        ok, corpo = await chamar(self, "PATCH", f"/parametros/{chave}", json={"valor": int(texto)})
        if not ok:
            self.erro, self.mensagem = True, str(corpo)
            return
        await self.carregar()
        self.erro, self.mensagem = False, "Parâmetro salvo."

    def abrir_faixa(self, faixa: dict[str, Any]) -> None:
        self.faixa_form = {"id": faixa["id"], "sinal": faixa["sinal"], "condicao": faixa["condicao"],
                           "minimo": faixa["minimo"], "maximo": faixa["maximo"], "pontos": faixa["pontos"]}
        self.erro_faixa, self.faixa_aberta = "", True

    def set_faixa_aberta(self, aberta: bool) -> None:
        self.faixa_aberta = bool(aberta)

    def set_campo_faixa(self, campo: str, valor: str) -> None:
        self.faixa_form = {**self.faixa_form, campo: valor}

    async def salvar_faixa(self) -> None:
        def numero(texto: Any) -> float | None:
            texto = str(texto or "").strip().replace(",", ".")
            return float(texto) if texto else None
        try:
            corpo = {"minimo": numero(self.faixa_form.get("minimo")), "maximo": numero(self.faixa_form.get("maximo")),
                     "pontos": int(str(self.faixa_form.get("pontos") or "0"))}
        except ValueError:
            self.erro_faixa = "Use números nos limites e nos pontos."
            return
        ok, resposta = await chamar(self, "PATCH", f"/faixas/{int(self.faixa_form['id'])}", json=corpo)
        if not ok:
            self.erro_faixa = str(resposta)
            return
        self.faixa_aberta = False
        await self.carregar()
        self.erro, self.mensagem = False, "Faixa salva."


class MeusPlantoesState(rx.State):
    """Plantões do próprio Médico, só leitura (add-cadastros-administrador, D1)."""

    plantoes: list[dict[str, Any]] = []
    mensagem: str = ""

    async def carregar(self) -> None:
        ok, corpo = await chamar(self, "GET", "/medicos/me/disponibilidade")
        if not ok:
            self.mensagem = str(corpo)
            return
        self.plantoes = [{**linha_plantao(p), "dia": datetime.strptime(_data(p.get("inicio")), "%Y-%m-%d").strftime("%d/%m") if _data(p.get("inicio")) else ""}
                         for p in (corpo or {}).get("plantoes") or []]
        self.mensagem = ""

"""Gestão de usuários do Administrador (add-autenticacao-perfis, D9/D14; revisão de 14/11/2026).

Lista todos os usuários e, para qualquer perfil, cria (escolhendo o perfil), edita (nome, e-mail e os dados do perfil:
CRM, especialidades e sala do Médico; CPF e especialidade de referência da Recepção/Triagem), ativa e desativa. A troca
de perfil, inclusive para Administrador, vale para todos menos o próprio usuário. As regras (próprio usuário, último
administrador, médico com ficha chamada) ficam no Xano; aqui só se monta o corpo e se mostra o erro.
"""

from typing import Any, ClassVar

import reflex as rx

from ps_fila_prioritaria.estados.cadastros import CadastroBase, OpcoesEspecialidades, chamar, filtrar

NOME_PERFIL = {"RECEPCAO_TRIAGEM": "Recepção/Triagem", "MEDICO": "Médico", "ADMINISTRADOR": "Administrador"}
PERFIS = list(NOME_PERFIL.items())


def filtrar_usuarios(itens: list[dict[str, Any]], filtro: str, busca: str, perfil: str) -> list[dict[str, Any]]:
    """Situação e busca como nos cadastros, mais o filtro de perfil (TODOS ou um perfil)."""
    lista = filtrar(itens, filtro, busca, UsuariosState.CAMPOS_BUSCA)
    return lista if perfil in ("", "TODOS") else [u for u in lista if u.get("perfil") == perfil]


def linha_usuario(usuario: dict[str, Any]) -> dict[str, Any]:
    """Usuário da API com o nome do perfil; `pendente` marca Médico ou Recepção sem o cadastro do perfil."""
    perfil = str(usuario.get("perfil") or "")
    pendente = (perfil == "MEDICO" and not usuario.get("medico_id")) or (perfil == "RECEPCAO_TRIAGEM" and not usuario.get("recepcao_id"))
    return {**usuario, "perfil_nome": NOME_PERFIL.get(perfil, perfil), "admin": perfil == "ADMINISTRADOR",
            "proprio": bool(usuario.get("proprio")), "pendente": pendente}


def _id_ou_none(valor: Any) -> int | None:
    texto = str(valor or "")
    return int(texto) if texto.isdigit() and texto != "0" else None


def dados_perfil(perfil: str, form: dict[str, Any]) -> dict[str, Any]:
    """Só os dados que o perfil exige: CRM, especialidades e sala (Médico); CPF e referência (Recepção/Triagem)."""
    if perfil == "MEDICO":
        return {"crm": str(form.get("crm") or ""), "especialidade_ids": list(form.get("especialidade_ids") or []),
                "sala_id": _id_ou_none(form.get("sala_id"))}
    if perfil == "RECEPCAO_TRIAGEM":
        return {"cpf": str(form.get("cpf") or ""), "especialidade_referencia_id": _id_ou_none(form.get("especialidade_referencia_id"))}
    return {}


def corpo_troca(form: dict[str, Any]) -> dict[str, Any]:
    """Corpo de PATCH usuarios/{id}/perfil: o perfil novo e os dados que ele exige."""
    perfil = str(form.get("perfil") or "")
    return {"perfil": perfil, **dados_perfil(perfil, form)}


def form_do_usuario(usuario: dict[str, Any]) -> dict[str, Any]:
    """Formulário preenchido com o login e o cadastro atual do perfil."""
    return {"nome": usuario.get("nome") or "", "email": usuario.get("email") or "", "senha": "",
            "perfil": str(usuario.get("perfil") or "ADMINISTRADOR"), "crm": usuario.get("crm") or "",
            "especialidade_ids": [int(i) for i in (usuario.get("especialidade_ids") or [])],
            "sala_id": str(usuario.get("sala_id") or ""), "cpf": usuario.get("cpf") or "",
            "especialidade_referencia_id": str(usuario.get("especialidade_referencia_id") or "")}


class UsuariosState(CadastroBase, OpcoesEspecialidades, rx.State):
    CAMINHO: ClassVar[str] = "/usuarios"
    CAMPOS_BUSCA: ClassVar[tuple[str, ...]] = ("nome", "email")

    filtro_perfil: str = "TODOS"
    opcoes_salas: list[dict[str, Any]] = []
    troca_aberta: bool = False
    troca_usuario: dict[str, Any] = {}
    erro_troca: str = ""

    @rx.var
    def itens_filtrados(self) -> list[dict[str, Any]]:
        return filtrar_usuarios(self.itens, self.filtro, self.busca, self.filtro_perfil)

    @rx.var
    def opcoes_perfil_troca(self) -> list[list[str]]:
        """Perfis para os quais o usuário escolhido pode ir (todos menos o atual, Administrador incluído)."""
        atual = self.troca_usuario.get("perfil")
        return [[valor, nome] for valor, nome in PERFIS if valor != atual]

    def set_filtro_perfil(self, valor: str | list[str]) -> None:
        self.filtro_perfil = valor[0] if isinstance(valor, list) and valor else str(valor or "TODOS")

    def set_troca_aberta(self, aberta: bool) -> None:
        self.troca_aberta = bool(aberta)

    async def carregar(self) -> None:
        await CadastroBase.carregar(self)
        self.itens = [linha_usuario(u) for u in self.itens]

    async def _carregar_extras(self) -> None:
        await self._carregar_especialidades()
        ok, corpo = await chamar(self, "GET", "/salas")
        if ok:
            self.opcoes_salas = [{"id": str(s["id"]), "nome": str(s["nome"])} for s in (corpo or []) if s.get("ativo")]

    # Criar/editar (o diálogo comum dos cadastros). Na criação o perfil é escolhido; na edição ele é o atual.
    def _form_vazio(self) -> dict[str, Any]:
        return form_do_usuario({"perfil": "RECEPCAO_TRIAGEM"})

    def _form_de(self, item: dict[str, Any]) -> dict[str, Any]:
        return form_do_usuario(item)

    def _corpo(self) -> dict[str, Any]:
        perfil = str(self.form.get("perfil") or "ADMINISTRADOR")
        corpo = {"nome": self.form.get("nome", ""), "email": self.form.get("email", ""), **dados_perfil(perfil, self.form)}
        if not self.editando_id:
            corpo.update(senha=self.form.get("senha", ""), perfil=perfil)
        return corpo

    # Trocar perfil.
    def abrir_troca(self, usuario: dict[str, Any]) -> None:
        destino = next((v for v, _ in PERFIS if v != usuario.get("perfil")), "")
        self.troca_usuario, self.erro_troca, self.troca_aberta = dict(usuario), "", True
        self.form = {**form_do_usuario(usuario), "perfil": destino}

    def set_perfil_troca(self, valor: str) -> None:
        self.form = {**self.form, "perfil": valor}

    async def trocar_perfil(self) -> None:
        if self.salvando:
            return
        usuario_id = int(self.troca_usuario.get("id") or 0)
        self.salvando, self.erro_troca = True, ""
        try:
            ok, corpo = await chamar(self, "PATCH", f"{self.CAMINHO}/{usuario_id}/perfil", json=corpo_troca(self.form))
        finally:
            self.salvando = False
        if not ok:
            self.erro_troca = str(corpo)
            return
        self.troca_aberta = False
        await self.carregar()
        nome = NOME_PERFIL.get(str(self.form.get("perfil")), "")
        self.erro, self.mensagem = False, f"Perfil alterado para {nome}. Vale no próximo acesso do usuário."

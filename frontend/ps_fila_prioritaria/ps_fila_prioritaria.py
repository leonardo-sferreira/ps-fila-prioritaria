"""App Reflex do Prioriza: cria o app e registra as rotas. Estados e páginas ficam nos módulos de cada funcionalidade."""

import reflex as rx

from ps_fila_prioritaria.componentes import carregando
from ps_fila_prioritaria.estados.autenticacao import AuthState, SenhaState
from ps_fila_prioritaria.estados.comprovante import ComprovanteState
from ps_fila_prioritaria.estados.ficha import FichaState
from ps_fila_prioritaria.estados.fila_pre_triagem import FilaTicketsState
from ps_fila_prioritaria.estados.totem import TotemState
from ps_fila_prioritaria.paginas.areas import area_admin, area_medico, area_recepcao
from ps_fila_prioritaria.paginas.autenticacao import (
    index,
    login,
    login_codigo,
    senha_codigo,
    senha_email,
    senha_nova,
    senha_sucesso,
)
from ps_fila_prioritaria.paginas.comprovante import pagina_comprovante
from ps_fila_prioritaria.paginas.ficha import pagina_recepcao_ficha
from ps_fila_prioritaria.paginas.fila_pre_triagem import pagina_fila_tickets
from ps_fila_prioritaria.paginas.pacientes import pagina_recepcao_pacientes
from ps_fila_prioritaria.paginas.privacidade import privacidade
from ps_fila_prioritaria.paginas.totem import totem


app = rx.App(stylesheets=["https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap"])
app.add_page(index, route="/", on_load=AuthState.ir_para_inicio)
app.add_page(login, route="/login", title="Login")
app.add_page(login_codigo, route="/login/codigo", title="Código de acesso", on_load=AuthState.exigir_login_pendente)
app.add_page(senha_email, route="/senha", title="Redefinir senha", on_load=SenhaState.iniciar)
app.add_page(senha_codigo, route="/senha/codigo", title="Redefinir senha", on_load=SenhaState.exigir_email)
app.add_page(senha_nova, route="/senha/nova", title="Nova senha", on_load=SenhaState.exigir_codigo)
app.add_page(senha_sucesso, route="/senha/sucesso", title="Senha redefinida")
app.add_page(privacidade, route="/privacidade", title="Aviso de privacidade")
app.add_page(totem, route="/totem", title="Totem de autoatendimento", on_load=TotemState.concluir)
app.add_page(carregando, route="/sair/inatividade", title="Sessão encerrada", on_load=AuthState.sair_por_inatividade)
app.add_page(area_recepcao, route="/recepcao", title="Recepção/Triagem", on_load=AuthState.verificar_sessao("RECEPCAO_TRIAGEM"))
app.add_page(area_medico, route="/medico", title="Médico", on_load=AuthState.verificar_sessao("MEDICO"))
app.add_page(area_admin, route="/admin", title="Administrador", on_load=AuthState.verificar_sessao("ADMINISTRADOR"))
app.add_page(
    pagina_recepcao_pacientes,
    route="/recepcao/pacientes",
    title="Identificação de Paciente",
    on_load=AuthState.verificar_sessao("RECEPCAO_TRIAGEM"),
)
app.add_page(
    pagina_recepcao_ficha,
    route="/recepcao/ficha/[id]",
    title="Ficha de atendimento",
    on_load=[AuthState.verificar_sessao("RECEPCAO_TRIAGEM"), FichaState.carregar_da_rota],
)
app.add_page(
    pagina_comprovante,
    route="/recepcao/comprovante/[id]",
    title="Comprovante da senha",
    on_load=[AuthState.verificar_sessao("RECEPCAO_TRIAGEM"), ComprovanteState.carregar_da_rota],
)
app.add_page(pagina_fila_tickets, route="/recepcao/fila", title="Fila de pré-triagem", on_load=[AuthState.verificar_sessao("RECEPCAO_TRIAGEM"), FilaTicketsState.carregar, FilaTicketsState.monitorar])

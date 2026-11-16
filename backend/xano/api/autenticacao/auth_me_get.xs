query "auth/me" verb=GET {
  api_group = "Autenticacao"
  description = "Devolve o usuário do token, recarregado do banco (usado pelo Reflex para proteger as rotas)."
  auth = "usuario"

  input {
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $auth.id,
        perfis_permitidos: ["RECEPCAO_TRIAGEM", "MEDICO", "ADMINISTRADOR"]
      }
    } as $usuario

    // Status operacional da sessão ativa (status-equipe, add-acompanhamento-administrador D5); null para Administrador.
    db.query sessao {
      where = $db.sessao.usuario_id == $usuario.id && $db.sessao.logout_em == null && $db.sessao.expira_em > now
      sort = {login_em: "desc"}
      return = {type: "single"}
    } as $sessao_atual
  }

  // inatividade_segundos: tempo sem uso até a tela encerrar a sessão (add-privacidade, D4).
  response = {
    id                  : $usuario.id
    nome                : $usuario.nome
    email               : $usuario.email
    perfil              : $usuario.perfil
    inatividade_segundos: $env.INATIVIDADE_SEGUNDOS|to_int
    status_operacional  : ($sessao_atual == null) ? null : $sessao_atual.status_operacional
  }
  guid = "nT4cvJFnCLpa3B6ijMw3TEyYfBw"
}

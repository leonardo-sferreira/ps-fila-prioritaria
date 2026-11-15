// Consulta somente o status da própria sessão ativa; não altera sessão ou plantão.
query "me/status" verb=GET {
  api_group = "Autenticacao"
  auth = "usuario"
  input {
  }
  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["MEDICO", "RECEPCAO_TRIAGEM"]}
    } as $usuario
    db.query sessao {
      where = $db.sessao.usuario_id == $usuario.id && $db.sessao.logout_em == null && $db.sessao.expira_em > now
      sort = {login_em: "desc"}
      return = {type: "single"}
    } as $sessao
    precondition ($sessao != null) {
      error_type = "unauthorized"
      error = "Sessão expirada. Faça login novamente."
    }
  }
  response = {status: $sessao.status_operacional}
}

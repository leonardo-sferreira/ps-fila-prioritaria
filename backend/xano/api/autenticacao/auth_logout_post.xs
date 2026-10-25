query "auth/logout" verb=POST {
  api_group = "Autenticacao"
  description = "Encerra a sessão aberta mais recente do usuário do token."
  auth = "usuario"

  input {
  }

  stack {
    db.query sessao {
      where = $db.sessao.usuario_id == $auth.id && $db.sessao.logout_em == null
      sort = {login_em: "desc"}
      return = {type: "single"}
    } as $sessao_aberta

    conditional {
      if ($sessao_aberta != null) {
        db.edit sessao {
          field_name = "id"
          field_value = $sessao_aberta.id
          data = {logout_em: now}
        }
      }
    }
  }

  response = {encerrada: true}
  guid = "RKidC2dthtvWWxHyv0kj_kA_irI"
}

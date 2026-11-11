query "auth/logout" verb=POST {
  api_group = "Autenticacao"
  description = "Encerra a sessão aberta mais recente do usuário do token."
  auth = "usuario"

  input {
  }

  stack {
    db.get usuario {
      field_name = "id"
      field_value = $auth.id
    } as $usuario

    precondition ($usuario != null) {
      error_type = "unauthorized"
      error = "Sessão inválida. Faça login novamente."
    }

    db.transaction {
      stack {
        conditional {
          if ($usuario.perfil == "MEDICO") {
            db.edit usuario {
              field_name = "id"
              field_value = $usuario.id
              data = {ativo: $usuario.ativo}
            } as $usuario_travado
          }
        }

        db.query sessao {
          where = $db.sessao.usuario_id == $usuario.id && $db.sessao.logout_em == null && $db.sessao.expira_em > now
          sort = {login_em: "desc"}
          return = {type: "list"}
        } as $sessoes_ativas

        conditional {
          if ($usuario.perfil == "MEDICO") {
            foreach ($sessoes_ativas) {
              each as $sessao {
                db.edit sessao {
                  field_name = "id"
                  field_value = $sessao.id
                  data = {logout_em: now}
                } as $encerrada
              }
            }
          }

          elseif (($sessoes_ativas|count) > 0) {
            db.edit sessao {
              field_name = "id"
              field_value = ($sessoes_ativas|first).id
              data = {logout_em: now}
            } as $encerrada
          }
        }
      }
    }
  }

  response = {encerrada: true}
  guid = "RKidC2dthtvWWxHyv0kj_kA_irI"
}

// Migração idempotente: preenche apenas sessões ativas da Recepção/Triagem sem status.
function "manutencao/inicializar_status_sessoes" {
  input {
  }

  stack {
    var $atualizadas {
      value = 0
    }

    db.transaction {
      stack {
        db.query sessao {
          where = $db.sessao.logout_em == null && $db.sessao.expira_em > now && $db.sessao.status_operacional == null
          return = {type: "list"}
        } as $sessoes

        foreach ($sessoes) {
          each as $sessao {
            db.get usuario {
              field_name = "id"
              field_value = $sessao.usuario_id
            } as $usuario

            conditional {
              if ($usuario != null && $usuario.perfil == "RECEPCAO_TRIAGEM") {
                db.edit sessao {
                  field_name = "id"
                  field_value = $sessao.id
                  data = {status_operacional: "DISPONIVEL"}
                } as $atualizada

                var.update $atualizadas {
                  value = $atualizadas + 1
                }
              }
            }
          }
        }
      }
    }
  }

  response = {atualizadas: $atualizadas}
  guid = "DpVN-j4pfuT60XJwklFy9zaGUms"
}

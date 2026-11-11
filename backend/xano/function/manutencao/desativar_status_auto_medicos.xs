// Revisão do PO: sessões médicas antigas não foram ativadas manualmente.
// Executar antes de liberar PATCH me/status; preservar PAUSA, AUSENTE e EM_ATENDIMENTO.
function "manutencao/desativar_status_auto_medicos" {
  input {
  }

  stack {
    var $atualizadas {
      value = 0
    }

    db.transaction {
      stack {
        db.query sessao {
          where = $db.sessao.logout_em == null && $db.sessao.expira_em > now && $db.sessao.status_operacional == "DISPONIVEL"
          return = {type: "list"}
        } as $sessoes

        foreach ($sessoes) {
          each as $sessao {
            db.get usuario {
              field_name = "id"
              field_value = $sessao.usuario_id
            } as $usuario

            conditional {
              if ($usuario != null && $usuario.perfil == "MEDICO") {
                db.edit sessao {
                  field_name = "id"
                  field_value = $sessao.id
                  data = {status_operacional: null}
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
  guid = "OxXT7715rgReU3IhtIE_VRCBGdM"
}

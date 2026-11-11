// Ativa ou desativa a sala. Ao desativar, desfaz o vínculo dos médicos que a tinham como sala atual
// (add-cadastros-administrador, D4).
query "salas/{sala_id}/ativo" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int sala_id
    bool ativo
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get sala {
      field_name = "id"
      field_value = $input.sala_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Sala não encontrada."
    }

    var $desvinculados { value = [] }

    db.transaction {
      stack {
        db.edit sala {
          field_name = "id"
          field_value = $anterior.id
          data = {ativo: $input.ativo}
        } as $sala

        conditional {
          if (!$input.ativo) {
            db.query medico {
              where = $db.medico.sala_id == $anterior.id
              return = {type: "list"}
            } as $medicos_na_sala
            foreach ($medicos_na_sala) {
              each as $medico {
                db.edit medico {
                  field_name = "id"
                  field_value = $medico.id
                  data = {sala_id: null}
                } as $sem_sala
                var.update $desvinculados { value = $desvinculados|push:$medico.id }
              }
            }
          }
        }

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: ($input.ativo ? "SALA_ATIVADA" : "SALA_DESATIVADA"), entidade: "SALA", registro_id: $anterior.id, valor_anterior: {ativo: $anterior.ativo}, valor_novo: {ativo: $input.ativo, medicos_desvinculados: $desvinculados}}
        } as $auditoria
      }
    }
  }

  response = {id: $sala.id, ativo: $sala.ativo, medicos_desvinculados: $desvinculados}
}

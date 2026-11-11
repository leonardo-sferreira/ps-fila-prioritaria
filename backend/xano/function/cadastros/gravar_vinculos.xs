// Substitui os vínculos de um sintoma (destinos, com ordem) ou de um médico (especialidades próprias)
// (add-cadastros-administrador, D4). Vínculo não tem histórico próprio: apaga os antigos e grava os novos.
// Deve ser chamada dentro da transação do endpoint; os IDs já vêm validados por cadastros/especialidades_validas.
function "cadastros/gravar_vinculos" {
  description = "tipo SINTOMA grava sintoma_especialidade com ordem 1..n; tipo MEDICO grava medico_especialidade."

  input {
    text tipo filters=trim|upper
    int dono_id
    json especialidade_ids
  }

  stack {
    precondition ($input.tipo == "SINTOMA" || $input.tipo == "MEDICO") {
      error_type = "inputerror"
      error = "Tipo de vínculo inválido."
    }

    conditional {
      if ($input.tipo == "SINTOMA") {
        db.query sintoma_especialidade {
          where = $db.sintoma_especialidade.sintoma_id == $input.dono_id
          return = {type: "list"}
        } as $antigos_sintoma
        foreach ($antigos_sintoma) {
          each as $vinculo_sintoma {
            db.del sintoma_especialidade {
              field_name = "id"
              field_value = $vinculo_sintoma.id
            }
          }
        }
        var $ordem { value = 0 }
        foreach ($input.especialidade_ids) {
          each as $destino {
            var.update $ordem { value = $ordem + 1 }
            db.add sintoma_especialidade {
              data = {sintoma_id: $input.dono_id, especialidade_id: $destino, ordem: $ordem}
            } as $novo_destino
          }
        }
      }
      else {
        db.query medico_especialidade {
          where = $db.medico_especialidade.medico_id == $input.dono_id
          return = {type: "list"}
        } as $antigos_medico
        foreach ($antigos_medico) {
          each as $vinculo_medico {
            db.del medico_especialidade {
              field_name = "id"
              field_value = $vinculo_medico.id
            }
          }
        }
        foreach ($input.especialidade_ids) {
          each as $propria {
            db.add medico_especialidade {
              data = {medico_id: $input.dono_id, especialidade_id: $propria}
            } as $novo_vinculo
          }
        }
      }
    }
  }

  response = $input.especialidade_ids
}

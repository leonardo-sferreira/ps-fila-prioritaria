query "fichas" verb=POST {
  api_group = "Triagem"
  description = "Abre ficha vazia em EM_TRIAGEM para paciente ativo, sem depender de ticket ou autenticação nesta fatia."

  input {
    int paciente_id
    int? ticket_id?
  }

  stack {
    db.transaction {
      stack {
        db.get paciente {
          field_name = "id"
          field_value = $input.paciente_id
        } as $paciente

        precondition ($paciente != null && $paciente.ativo == true) {
          error_type = "inputerror"
          error = "PACIENTE_INEXISTENTE_OU_INATIVO"
        }

        db.query ficha_atendimento {
          where = $db.ficha_atendimento.paciente_id == $input.paciente_id && $db.ficha_atendimento.status in ["EM_TRIAGEM", "AGUARDANDO", "CHAMADO"]
          return = { type: "single" }
        } as $ficha_nao_finalizada

        precondition ($ficha_nao_finalizada == null) {
          error_type = "inputerror"
          error = "FICHA_NAO_FINALIZADA_EXISTENTE"
        }

        var $ficha { value = null }
        conditional {
          if ($input.ticket_id != null) {
            db.add ficha_atendimento {
              data = {
                paciente_id: $input.paciente_id,
                ticket_id: $input.ticket_id,
                chegada_em: now,
                status: "EM_TRIAGEM"
              }
            } as $ficha_com_ticket
            var.update $ficha {
              value = $ficha_com_ticket
            }
          }
          else {
            db.add ficha_atendimento {
              data = {
                paciente_id: $input.paciente_id,
                chegada_em: now,
                status: "EM_TRIAGEM"
              }
            } as $ficha_sem_ticket
            var.update $ficha {
              value = $ficha_sem_ticket
            }
          }
        }
      }
    }
  }

  response = $ficha
  guid = "7AzpsrORCc-N5u5PuR5rPmVraO8"
}

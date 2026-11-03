query "fichas" verb=POST {
  api_group = "Triagem"
  description = "Abre ficha vazia em EM_TRIAGEM para paciente ativo, com ticket opcional e auditoria."

  auth = "usuario"

  input {
    int paciente_id
    int? ticket_id?
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM"]}
    } as $usuario

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
            db.get ticket_pre_triagem {
              field_name = "id"
              field_value = $input.ticket_id
            } as $ticket
            precondition ($ticket != null && $ticket.status == "CHAMADO" && $ticket.presente == true) {
              error_type = "inputerror"
              error = "TICKET_INVALIDO"
            }
            db.add ficha_atendimento {
              data = {
                paciente_id: $input.paciente_id,
                ticket_id: $input.ticket_id,
                aberta_por: $usuario.id,
                chegada_em: now,
                status: "EM_TRIAGEM"
              }
            } as $ficha_com_ticket
            db.edit ticket_pre_triagem {
              field_name = "id"
              field_value = $ticket.id
              data = {status: "ATENDIDO", paciente_id: $input.paciente_id}
            } as $ticket_atendido
            function.run "registrar_alteracao" {
              input = {usuario_id: $usuario.id, tipo_evento: "ATENDIMENTO", entidade: "TICKET_PRE_TRIAGEM", registro_id: $ticket.id, valor_anterior: {status: $ticket.status}, valor_novo: {status: "ATENDIDO", paciente_id: $input.paciente_id}}
            } as $auditoria_ticket
            var.update $ficha {
              value = $ficha_com_ticket
            }
          }
          else {
            db.add ficha_atendimento {
              data = {
                paciente_id: $input.paciente_id,
                aberta_por: $usuario.id,
                chegada_em: now,
                status: "EM_TRIAGEM"
              }
            } as $ficha_sem_ticket
            var.update $ficha {
              value = $ficha_sem_ticket
            }
          }
        }
        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "CADASTRO", entidade: "FICHA_ATENDIMENTO", registro_id: $ficha.id, valor_novo: {paciente_id: $input.paciente_id, ticket_id: $input.ticket_id, status: "EM_TRIAGEM", chegada_em: $ficha.chegada_em}}
        } as $auditoria_ficha
      }
    }
  }

  response = $ficha
  guid = "7AzpsrORCc-N5u5PuR5rPmVraO8"
}

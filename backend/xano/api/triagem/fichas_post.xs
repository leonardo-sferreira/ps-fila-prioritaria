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

        var $ficha { value = null }
        var $ja_existente { value = false }
        conditional {
          // RN03: não cria segunda ficha. A ficha ainda EM_TRIAGEM é reaberta para continuar a triagem
          // (decisão do PO, 08/11/2026); ficha já na fila (AGUARDANDO/CHAMADO) ou chegada com ticket é recusada.
          if ($ficha_nao_finalizada != null) {
            precondition ($ficha_nao_finalizada.status == "EM_TRIAGEM" && $input.ticket_id == null) {
              error_type = "inputerror"
              error = "FICHA_NAO_FINALIZADA_EXISTENTE"
            }
            var.update $ficha {
              value = $ficha_nao_finalizada
            }
            var.update $ja_existente {
              value = true
            }
          }
          elseif ($input.ticket_id != null) {
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
        conditional {
          if (!$ja_existente) {
        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "CADASTRO", entidade: "FICHA_ATENDIMENTO", registro_id: $ficha.id, valor_novo: {paciente_id: $input.paciente_id, ticket_id: $input.ticket_id, status: "EM_TRIAGEM", chegada_em: $ficha.chegada_em}}
        } as $auditoria_ficha
          }
        }
      }
    }
  }

  response = {id: $ficha.id, paciente_id: $ficha.paciente_id, ticket_id: $ficha.ticket_id, status: $ficha.status, chegada_em: $ficha.chegada_em, ja_existente: $ja_existente}
  guid = "7AzpsrORCc-N5u5PuR5rPmVraO8"
}

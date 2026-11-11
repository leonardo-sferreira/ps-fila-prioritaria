// Expiração (add-expiracao-24h, D2–D5): encerra como DESISTENCIA as fichas EM_TRIAGEM/AGUARDANDO/CHAMADO e os tickets
// AGUARDANDO/CHAMADO que passaram de HORAS_EXPIRACAO horas desde a chegada/emissão. Registros finais não entram na
// consulta. Cada encerramento grava EXPIRACAO no histórico sem usuário (ação do sistema), na mesma transação.
// Chamada pela tarefa "expirar_registros" a cada hora; também pode ser rodada pelo CLI:
// xano function run manutencao/expirar_registros --branch v1 --no-input-check
function "manutencao/expirar_registros" {
  description = "Encerra como desistência fichas e tickets não concluídos dentro de HORAS_EXPIRACAO horas e registra no histórico."

  input {}

  stack {
    db.get parametro {
      field_name = "chave"
      field_value = "HORAS_EXPIRACAO"
    } as $parametro

    var $horas { value = null }
    conditional {
      if ($parametro != null) {
        var.update $horas { value = $parametro.valor|to_int }
      }
    }

    var $agora { value = now }
    var $fichas_expiradas { value = [] }
    var $tickets_expirados { value = [] }
    var $motivo { value = null }
    var $justificativa { value = "Encerrada após o prazo de expiração sem conclusão (HORAS_EXPIRACAO)." }

    conditional {
      if ($horas == null || $horas <= 0) {
        var.update $motivo { value = "HORAS_EXPIRACAO não configurado como inteiro positivo; nada foi alterado." }
      }
      else {
        db.query ficha_atendimento {
          where = $db.ficha_atendimento.status in ["EM_TRIAGEM", "AGUARDANDO", "CHAMADO"]
          return = {type: "list"}
        } as $fichas_ativas

        db.query ticket_pre_triagem {
          where = $db.ticket_pre_triagem.status in ["AGUARDANDO", "CHAMADO"]
          return = {type: "list"}
        } as $tickets_ativos

        db.transaction {
          stack {
            foreach ($fichas_ativas) {
              each as $ficha {
                function.run "manutencao/expirou" {
                  input = {horario: $ficha.chegada_em, agora: $agora, horas: $horas}
                } as $ficha_expirou

                conditional {
                  if ($ficha_expirou) {
                    db.patch ficha_atendimento {
                      field_name = "id"
                      field_value = $ficha.id
                      data = {status: "DESISTENCIA"}
                    } as $ficha_encerrada

                    db.add historico_alteracao {
                      data = {tipo_evento: "EXPIRACAO", entidade: "FICHA_ATENDIMENTO", registro_id: $ficha.id, valor_anterior: {status: $ficha.status}, valor_novo: {status: "DESISTENCIA"}, justificativa: $justificativa, usuario_id: null}
                    } as $historico_ficha

                    var.update $fichas_expiradas { value = $fichas_expiradas|push:$ficha.id }
                  }
                }
              }
            }

            foreach ($tickets_ativos) {
              each as $ticket {
                function.run "manutencao/expirou" {
                  input = {horario: $ticket.emitido_em, agora: $agora, horas: $horas}
                } as $ticket_expirou

                conditional {
                  if ($ticket_expirou) {
                    db.patch ticket_pre_triagem {
                      field_name = "id"
                      field_value = $ticket.id
                      data = {status: "DESISTENCIA"}
                    } as $ticket_encerrado

                    db.add historico_alteracao {
                      data = {tipo_evento: "EXPIRACAO", entidade: "TICKET_PRE_TRIAGEM", registro_id: $ticket.id, valor_anterior: {status: $ticket.status}, valor_novo: {status: "DESISTENCIA"}, justificativa: $justificativa, usuario_id: null}
                    } as $historico_ticket

                    var.update $tickets_expirados { value = $tickets_expirados|push:$ticket.id }
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  response = {
    horas_expiracao  : $horas
    fichas_expiradas : $fichas_expiradas
    tickets_expirados: $tickets_expirados
    motivo           : $motivo
  }
}

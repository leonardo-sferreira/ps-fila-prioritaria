// Dispensa por prazo (add-expiracao-24h, D2–D5): lista as fichas EM_TRIAGEM/AGUARDANDO/CHAMADO e os tickets
// AGUARDANDO/CHAMADO parados há mais de HORAS_EXPIRACAO horas desde a chegada/emissão. Sem `aplicar`, só devolve a
// prévia; com `aplicar`, encerra cada um como DESISTENCIA e audita EXPIRACAO em nome de `usuario_id` (Administrador),
// na mesma transação. Registros finais não entram na consulta.
function "manutencao/expirar_registros" {
  description = "Prévia ou dispensa (aplicar=true) de fichas e tickets parados há mais de HORAS_EXPIRACAO horas, com auditoria."

  input {
    bool aplicar?=false
    // Administrador que dispensa; obrigatório com aplicar=true (registrar_alteracao exige usuário ativo).
    int? usuario_id?
  }

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
    var $fichas { value = [] }
    var $tickets { value = [] }
    var $motivo { value = null }
    var $aplicado { value = false }

    conditional {
      if ($horas == null || $horas <= 0) {
        var.update $motivo { value = "HORAS_EXPIRACAO não configurado como inteiro positivo; nada foi alterado." }
      }
      else {
        db.query ficha_atendimento {
          where = $db.ficha_atendimento.status in ["EM_TRIAGEM", "AGUARDANDO", "CHAMADO"]
          sort = {chegada_em: "asc", id: "asc"}
          return = {type: "list"}
        } as $fichas_ativas

        db.query ticket_pre_triagem {
          where = $db.ticket_pre_triagem.status in ["AGUARDANDO", "CHAMADO"]
          sort = {emitido_em: "asc", id: "asc"}
          return = {type: "list"}
        } as $tickets_ativos

        foreach ($fichas_ativas) {
          each as $ficha {
            function.run "manutencao/expirou" {
              input = {horario: $ficha.chegada_em, agora: $agora, horas: $horas}
            } as $ficha_expirou
            conditional {
              if ($ficha_expirou) {
                var.update $fichas {
                  value = $fichas|push:{id: $ficha.id, senha: $ficha.senha, status: $ficha.status, chegada_em: $ficha.chegada_em}
                }
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
                var.update $tickets {
                  value = $tickets|push:{id: $ticket.id, tipo: $ticket.tipo, numero: $ticket.numero, status: $ticket.status, emitido_em: $ticket.emitido_em}
                }
              }
            }
          }
        }

        conditional {
          if ($input.aplicar) {
            precondition ($input.usuario_id != null) {
              error_type = "inputerror"
              error = "USUARIO_OBRIGATORIO"
            }

            var $justificativa {
              value = "Dispensada pelo Administrador: parada há mais de " ~ $horas ~ " h sem conclusão."
            }

            db.transaction {
              stack {
                foreach ($fichas) {
                  each as $item_ficha {
                    db.patch ficha_atendimento {
                      field_name = "id"
                      field_value = $item_ficha.id
                      data = {status: "DESISTENCIA"}
                    } as $ficha_encerrada

                    function.run "registrar_alteracao" {
                      input = {usuario_id: $input.usuario_id, tipo_evento: "EXPIRACAO", entidade: "FICHA_ATENDIMENTO", registro_id: $item_ficha.id, valor_anterior: {status: $item_ficha.status}, valor_novo: {status: "DESISTENCIA"}, justificativa: $justificativa}
                    } as $auditoria_ficha
                  }
                }

                foreach ($tickets) {
                  each as $item_ticket {
                    db.patch ticket_pre_triagem {
                      field_name = "id"
                      field_value = $item_ticket.id
                      data = {status: "DESISTENCIA"}
                    } as $ticket_encerrado

                    function.run "registrar_alteracao" {
                      input = {usuario_id: $input.usuario_id, tipo_evento: "EXPIRACAO", entidade: "TICKET_PRE_TRIAGEM", registro_id: $item_ticket.id, valor_anterior: {status: $item_ticket.status}, valor_novo: {status: "DESISTENCIA"}, justificativa: $justificativa}
                    } as $auditoria_ticket
                  }
                }
              }
            }

            var.update $aplicado { value = true }
          }
        }
      }
    }
  }

  response = {
    horas_expiracao: $horas
    aplicado       : $aplicado
    fichas         : $fichas
    tickets        : $tickets
    motivo         : $motivo
  }
}

query "tickets/{ticket_id}/acao" verb=POST {
  api_group = "Triagem"
  auth = "usuario"
  input {
    int ticket_id
    text acao filters=trim
  }
  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM"]}
    } as $usuario
    var $resultado { value = null }
    db.transaction {
      stack {
        function.run "inicializar_parametros_fila" { input = {} } as $inicializados
        db.get ticket_pre_triagem {
          field_name = "id"
          field_value = $input.ticket_id
        } as $ticket
        precondition ($ticket != null && ($ticket.status == "AGUARDANDO" || $ticket.status == "CHAMADO")) {
          error_type = "inputerror"
          error = "TICKET_INDISPONIVEL"
        }
        precondition ($input.acao == "REPETIR" || $input.acao == "AUSENCIA" || $input.acao == "DESISTENCIA" || $input.acao == "PRESENTE" || $input.acao == "AVANCAR") {
          error_type = "inputerror"
          error = "ACAO_INVALIDA"
        }
        var $dados { value = {} }
        conditional {
          if ($input.acao == "DESISTENCIA") {
            var.update $dados { value = {status: "DESISTENCIA"} }
          }
          elseif ($input.acao == "PRESENTE") {
            precondition ($ticket.status == "CHAMADO" && $ticket.presente != true) {
              error_type = "inputerror"
              error = "TICKET_INDISPONIVEL"
            }
            var.update $dados { value = {presente: true} }
          }
          else {
            precondition ($ticket.presente != true) {
              error_type = "inputerror"
              error = "PRESENCA_CONFIRMADA"
            }
            db.get parametro {
              field_name = "chave"
              field_value = "INTERVALO_CHAMADA_SEGUNDOS"
            } as $intervalo
            db.get parametro {
              field_name = "chave"
              field_value = "TENTATIVAS_CHAMADA"
            } as $limite
            precondition ($intervalo != null && $limite != null && ($intervalo.valor|to_int) > 0 && ($limite.valor|to_int) > 0) {
              error_type = "inputerror"
              error = "PARAMETROS_NAO_CONFIGURADOS"
            }
            precondition ($ticket.status == "CHAMADO" && $ticket.chamado_em != null) {
              error_type = "inputerror"
              error = "TICKET_NAO_CHAMADO"
            }
            var $proxima_chamada { value = $ticket.chamado_em|add_secs_to_timestamp:($intervalo.valor|to_int) }
            var $agora_ms { value = now|to_ms }
            precondition ($agora_ms >= $proxima_chamada) {
              error_type = "inputerror"
              error = "AGUARDE_INTERVALO"
            }
            conditional {
              if ($input.acao == "REPETIR" || ($input.acao == "AVANCAR" && $ticket.tentativas < ($limite.valor|to_int))) {
                precondition ($ticket.tentativas < ($limite.valor|to_int)) {
                  error_type = "inputerror"
                  error = "LIMITE_DE_CHAMADAS"
                }
                var.update $dados { value = {tentativas: $ticket.tentativas + 1, chamado_em: now, chamado_por: $usuario.id} }
              }
              else {
                precondition ($ticket.tentativas == ($limite.valor|to_int)) {
                  error_type = "inputerror"
                  error = "TENTATIVAS_NAO_ESGOTADAS"
                }
                conditional {
                  if ($ticket.oportunidade == 1) {
                    var.update $dados { value = {status: "AGUARDANDO", oportunidade: 2, tentativas: 0, fila_em: now} }
                  }
                  else {
                    var.update $dados { value = {status: "NAO_COMPARECEU"} }
                  }
                }
              }
            }
          }
        }
        db.patch ticket_pre_triagem {
          field_name = "id"
          field_value = $ticket.id
          data = $dados
        } as $atualizado
        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "CHAMADA", entidade: "TICKET_PRE_TRIAGEM", registro_id: $ticket.id, valor_anterior: {status: $ticket.status, tentativas: $ticket.tentativas, oportunidade: $ticket.oportunidade, presente: $ticket.presente}, valor_novo: {status: $atualizado.status, tentativas: $atualizado.tentativas, oportunidade: $atualizado.oportunidade, presente: $atualizado.presente}}
        } as $auditoria
        var.update $resultado { value = $atualizado }
      }
    }
  }
  response = $resultado
  guid = "g_pUlR25aJpnmQb8XUe2Z2ItEDY"
}

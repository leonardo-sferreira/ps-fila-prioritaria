query "tickets/proximo" verb=POST {
  api_group = "Triagem"
  auth = "usuario"
  input {}
  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM"]}
    } as $usuario
    var $resultado { value = null }
    db.transaction {
      stack {
        function.run "inicializar_parametros_fila" { input = {} } as $inicializados
        db.get parametro {
          field_name = "chave"
          field_value = "CICLO_PRE_TRIAGEM_PRIORITARIOS"
        } as $prioritarios
        db.get parametro {
          field_name = "chave"
          field_value = "CICLO_PRE_TRIAGEM_NORMAIS"
        } as $normais
        db.get parametro {
          field_name = "chave"
          field_value = "POSICAO_CICLO_PRE_TRIAGEM"
        } as $ciclo
        precondition ($prioritarios != null && $normais != null && $ciclo != null) {
          error_type = "inputerror"
          error = "PARAMETROS_NAO_CONFIGURADOS"
        }
        var $p { value = $prioritarios.valor|to_int }
        var $n { value = $normais.valor|to_int }
        var $posicao { value = $ciclo.valor|to_int }
        precondition ($p > 0 && $n > 0 && $posicao >= 0 && $posicao < ($p + $n)) {
          error_type = "inputerror"
          error = "PARAMETROS_INVALIDOS"
        }
        db.query ticket_pre_triagem {
          where = $db.ticket_pre_triagem.status == "AGUARDANDO"
          return = {type: "list"}
        } as $aguardando
        var $pediatrico { value = null }
        var $preferencial { value = null }
        var $normal { value = null }
        var $tempo_pediatrico { value = null }
        var $tempo_preferencial { value = null }
        var $tempo_normal { value = null }
        foreach ($aguardando) {
          each as $item {
            var $tempo { value = $item.emitido_em }
            conditional {
              if ($item.fila_em != null) {
                var.update $tempo { value = $item.fila_em }
              }
            }
            conditional {
              if ($item.tipo == "PEDIATRICO" && ($pediatrico == null || $tempo < $tempo_pediatrico || ($tempo == $tempo_pediatrico && $item.id < $pediatrico.id))) {
                var.update $pediatrico { value = $item }
                var.update $tempo_pediatrico { value = $tempo }
              }
              elseif ($item.tipo == "PREFERENCIAL" && ($preferencial == null || $tempo < $tempo_preferencial || ($tempo == $tempo_preferencial && $item.id < $preferencial.id))) {
                var.update $preferencial { value = $item }
                var.update $tempo_preferencial { value = $tempo }
              }
              elseif ($item.tipo == "NORMAL" && ($normal == null || $tempo < $tempo_normal || ($tempo == $tempo_normal && $item.id < $normal.id))) {
                var.update $normal { value = $item }
                var.update $tempo_normal { value = $tempo }
              }
            }
          }
        }
        var $prioritario { value = $pediatrico }
        conditional {
          if ($prioritario == null) {
            var.update $prioritario { value = $preferencial }
          }
        }
        var $ticket { value = null }
        var $avancar { value = false }
        conditional {
          if ($posicao < $p) {
            conditional {
              if ($prioritario != null) {
                var.update $ticket { value = $prioritario }
                var.update $avancar { value = true }
              }
              else {
                var.update $ticket { value = $normal }
              }
            }
          }
          else {
            conditional {
              if ($normal != null) {
                var.update $ticket { value = $normal }
                var.update $avancar { value = true }
              }
              else {
                var.update $ticket { value = $prioritario }
              }
            }
          }
        }
        precondition ($ticket != null) {
          error_type = "inputerror"
          error = "FILA_VAZIA"
        }
        db.get ticket_pre_triagem {
          field_name = "id"
          field_value = $ticket.id
        } as $atual
        precondition ($atual != null && $atual.status == "AGUARDANDO") {
          error_type = "inputerror"
          error = "TICKET_INDISPONIVEL"
        }
        db.edit ticket_pre_triagem {
          field_name = "id"
          field_value = $atual.id
          data = {status: "CHAMADO", tentativas: 1, presente: false, chamado_em: now, chamado_por: $usuario.id}
        } as $chamado
        conditional {
          if ($avancar) {
            db.edit parametro {
              field_name = "id"
              field_value = $ciclo.id
              data = {valor: (($posicao + 1) % ($p + $n))|to_text}
            } as $ciclo_atualizado
          }
        }
        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "CHAMADA", entidade: "TICKET_PRE_TRIAGEM", registro_id: $atual.id, valor_anterior: {status: $atual.status}, valor_novo: {status: "CHAMADO", tentativas: 1}}
        } as $auditoria
        var.update $resultado { value = $chamado }
      }
    }
  }
  response = $resultado
  guid = "p7l1pZ1ebKTEZe-6P3EVqWiqAGE"
}

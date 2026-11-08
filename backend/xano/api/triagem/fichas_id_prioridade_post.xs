// Ajuste manual da prioridade pela Recepção/Triagem (add-classificacao-prioridade, D6).
// Também é a classificação manual excepcional quando o cálculo automático está bloqueado
// (menor de 16 anos, gestante ou dado pendente). Justificativa obrigatória e auditada.
query "fichas/{ficha_id}/prioridade" verb=POST {
  api_group = "Triagem"
  description = "Define a prioridade atual da ficha EM_TRIAGEM com justificativa obrigatória e auditoria PRIORIDADE_ALTERADA."

  auth = "usuario"

  input {
    int ficha_id
    text prioridade? filters=trim|upper
    text justificativa? filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM"]}
    } as $usuario

    precondition (["VERMELHA", "AMARELA", "AZUL"]|in:$input.prioridade) {
      error_type = "inputerror"
      error = "PRIORIDADE_INVALIDA"
    }

    precondition ($input.justificativa != null && ($input.justificativa|strlen) > 0) {
      error_type = "inputerror"
      error = "JUSTIFICATIVA_OBRIGATORIA"
    }

    db.transaction {
      stack {
        function.run "classificacao/inicializar_classificacao" {
          input = {}
        } as $classificacao_inicializada

        db.get ficha_atendimento {
          field_name = "id"
          field_value = $input.ficha_id
        } as $ficha

        precondition ($ficha != null) {
          error_type = "notfound"
          error = "FICHA_NAO_ENCONTRADA"
        }

        precondition ($ficha.status == "EM_TRIAGEM") {
          error_type = "inputerror"
          error = "FICHA_FORA_DA_TRIAGEM"
        }

        // Compara com a classificação vigente, não com um valor gravado antigo.
        function.run "classificacao/avaliar_ficha" {
          input = {ficha_id: $ficha.id}
        } as $avaliacao

        var $prioridade_calculada {
          value = $avaliacao.classificacao.prioridade_calculada
        }

        precondition ($prioridade_calculada == null || $prioridade_calculada != $input.prioridade) {
          error_type = "inputerror"
          error = "PRIORIDADE_IGUAL_A_CALCULADA"
        }

        db.patch ficha_atendimento {
          field_name = "id"
          field_value = $ficha.id
          data = {prioridade_calculada: $prioridade_calculada, prioridade_atual: $input.prioridade, justificativa_ajuste: $input.justificativa}
        } as $ficha_ajustada

        function.run "registrar_alteracao" {
          input = {
            usuario_id    : $usuario.id
            tipo_evento   : "PRIORIDADE_ALTERADA"
            entidade      : "FICHA_ATENDIMENTO"
            registro_id   : $ficha.id
            valor_anterior: {prioridade_calculada: $ficha.prioridade_calculada, prioridade_atual: $ficha.prioridade_atual, justificativa_ajuste: $ficha.justificativa_ajuste}
            valor_novo    : {prioridade_calculada: $prioridade_calculada, prioridade_atual: $input.prioridade}
            justificativa : $input.justificativa
          }
        } as $auditoria
      }
    }
  }

  response = {
    id                  : $input.ficha_id
    prioridade_calculada: $prioridade_calculada
    prioridade_atual    : $input.prioridade
    justificativa_ajuste: $input.justificativa
  }
  guid = "x3yrP4otR-fp0fb9tsb5QL-Tj-8"
}

// Grava a trilha imutável da operação autenticada. O chamador DEVE passar
// $auth.id após verificar_acesso e executá-la na mesma db.transaction da
// escrita de domínio.
function "registrar_alteracao" {
  description = "Registra a alteração da operação autenticada em historico_alteracao; não expõe endpoint próprio."

  input {
    int usuario_id
    text tipo_evento filters=trim
    text entidade filters=trim
    int registro_id
    json? valor_anterior?
    json? valor_novo?
    text? justificativa? filters=trim
  }

  stack {
    db.get usuario {
      field_name = "id"
      field_value = $input.usuario_id
    } as $usuario

    precondition ($usuario != null && $usuario.ativo) {
      error_type = "unauthorized"
      error = "Sessão inválida. Faça login novamente."
    }

    precondition ($input.tipo_evento != "") {
      error_type = "inputerror"
      error = "Tipo de evento obrigatório."
    }

    precondition ($input.entidade != "") {
      error_type = "inputerror"
      error = "Entidade obrigatória."
    }

    precondition ($input.registro_id > 0) {
      error_type = "inputerror"
      error = "Identificador do registro inválido."
    }

    // Criações não têm valor anterior e remoções não têm valor novo; uma
    // alteração relevante sempre precisa informar ao menos um dos dois.
    precondition ($input.valor_anterior != null || $input.valor_novo != null) {
      error_type = "inputerror"
      error = "Informe o valor anterior ou o valor novo."
    }

    db.add historico_alteracao {
      data = {
        tipo_evento   : $input.tipo_evento,
        entidade      : $input.entidade,
        registro_id   : $input.registro_id,
        valor_anterior: $input.valor_anterior,
        valor_novo    : $input.valor_novo,
        justificativa : $input.justificativa,
        usuario_id    : $usuario.id
      }
    } as $registro
  }

  response = $registro
  guid = "T4-yFsuf4ffw6AcSqail44GR3t8"
}

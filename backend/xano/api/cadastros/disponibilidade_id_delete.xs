// Remove um plantão que ainda não começou: desfaz um registro feito por engano (add-cadastros-administrador, D2/D6).
// Plantão iniciado nunca é removido.
query "disponibilidade/{disponibilidade_id}" verb=DELETE {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int disponibilidade_id
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get disponibilidade_medico {
      field_name = "id"
      field_value = $input.disponibilidade_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Plantão não encontrado."
    }

    precondition ($anterior.inicio > now) {
      error_type = "inputerror"
      error = "PLANTAO_INICIADO"
    }

    db.transaction {
      stack {
        db.del disponibilidade_medico {
          field_name = "id"
          field_value = $anterior.id
        }

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "PLANTAO_REMOVIDO", entidade: "DISPONIBILIDADE_MEDICO", registro_id: $anterior.id, valor_anterior: {medico_id: $anterior.medico_id, inicio: $anterior.inicio, fim: $anterior.fim}, valor_novo: null}
        } as $auditoria
      }
    }
  }

  response = {id: $anterior.id, removido: true}
}

// Registra um plantão de médico ativo, sem sobreposição (add-cadastros-administrador, D6).
query disponibilidade verb=POST {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int medico_id
    text data filters=trim
    text hora_inicio filters=trim
    text hora_fim filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get medico {
      field_name = "id"
      field_value = $input.medico_id
    } as $medico

    precondition ($medico != null && $medico.ativo == true) {
      error_type = "inputerror"
      error = "Médico inexistente ou inativo."
    }

    function.run "cadastros/periodo_plantao" {
      input = {data: $input.data, hora_inicio: $input.hora_inicio, hora_fim: $input.hora_fim}
    } as $periodo

    precondition ($periodo.valido) {
      error_type = "inputerror"
      error = "Data ou horário inválido."
    }

    function.run "cadastros/plantao_sobreposto" {
      input = {medico_id: $medico.id, inicio: $periodo.inicio, fim: $periodo.fim}
    } as $sobreposto

    precondition (!$sobreposto) {
      error_type = "inputerror"
      error = "PLANTAO_SOBREPOSTO"
    }

    db.transaction {
      stack {
        db.add disponibilidade_medico {
          data = {medico_id: $medico.id, inicio: $periodo.inicio, fim: $periodo.fim}
        } as $plantao

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "PLANTAO_CRIADO", entidade: "DISPONIBILIDADE_MEDICO", registro_id: $plantao.id, valor_anterior: null, valor_novo: {medico_id: $medico.id, inicio: $plantao.inicio, fim: $plantao.fim}}
        } as $auditoria
      }
    }
  }

  response = {id: $plantao.id, medico_id: $plantao.medico_id, inicio: $plantao.inicio, fim: $plantao.fim}
  guid = "oPCOzfyZ0vKB8-1pqP4GtO6PZvY"
}

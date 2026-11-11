// Altera um plantão (add-cadastros-administrador, D6). Não iniciado: data e horários livres.
// Já iniciado: o início não muda; só o fim pode ser estendido ou antecipado, desde que fique no futuro.
query "disponibilidade/{disponibilidade_id}" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int disponibilidade_id
    text data filters=trim
    text hora_inicio filters=trim
    text hora_fim filters=trim
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

    precondition ($anterior.encerrado_em == null) {
      error_type = "inputerror"
      error = "Plantão já encerrado pelo médico."
    }

    function.run "cadastros/periodo_plantao" {
      input = {data: $input.data, hora_inicio: $input.hora_inicio, hora_fim: $input.hora_fim}
    } as $periodo

    precondition ($periodo.valido) {
      error_type = "inputerror"
      error = "Data ou horário inválido."
    }

    var $agora { value = now }
    conditional {
      if ($anterior.inicio <= $agora) {
        precondition ($periodo.inicio == $anterior.inicio && $periodo.fim > $agora) {
          error_type = "inputerror"
          error = "PLANTAO_INICIADO"
        }
      }
    }

    function.run "cadastros/plantao_sobreposto" {
      input = {medico_id: $anterior.medico_id, inicio: $periodo.inicio, fim: $periodo.fim, ignorar_id: $anterior.id}
    } as $sobreposto

    precondition (!$sobreposto) {
      error_type = "inputerror"
      error = "PLANTAO_SOBREPOSTO"
    }

    db.transaction {
      stack {
        db.edit disponibilidade_medico {
          field_name = "id"
          field_value = $anterior.id
          data = {inicio: $periodo.inicio, fim: $periodo.fim}
        } as $plantao

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "PLANTAO_ALTERADO", entidade: "DISPONIBILIDADE_MEDICO", registro_id: $anterior.id, valor_anterior: {inicio: $anterior.inicio, fim: $anterior.fim}, valor_novo: {inicio: $plantao.inicio, fim: $plantao.fim}}
        } as $auditoria
      }
    }
  }

  response = {id: $plantao.id, medico_id: $plantao.medico_id, inicio: $plantao.inicio, fim: $plantao.fim}
}

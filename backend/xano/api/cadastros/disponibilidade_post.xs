// Registra um plantão de médico ativo, sem sobreposição (add-cadastros-administrador, D6).
// Com data_fim, registra a escala 12x36 até essa data: um plantão a cada 48 h, tudo ou nada (add-plantao-12x36).
query disponibilidade verb=POST {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int medico_id
    text data filters=trim
    text hora_inicio filters=trim
    text hora_fim filters=trim
    text data_fim? filters=trim
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

    // Sem data_fim: um plantão só. Com data_fim: 12x36, o mesmo horário a cada 2 dias até data_fim (máx. 90 dias).
    var $quantidade { value = 1 }
    conditional {
      if ($input.data_fim != null && $input.data_fim != "") {
        function.run "cadastros/periodo_plantao" {
          input = {data: $input.data_fim, hora_inicio: $input.hora_inicio, hora_fim: $input.hora_fim}
        } as $ultimo

        precondition ($ultimo.valido && $ultimo.inicio >= $periodo.inicio) {
          error_type = "inputerror"
          error = "Data final inválida ou anterior à data inicial."
        }

        precondition ($ultimo.inicio - $periodo.inicio <= 7776000000) {
          error_type = "inputerror"
          error = "A escala pode ter no máximo 90 dias."
        }

        var.update $quantidade {
          value = (($ultimo.inicio - $periodo.inicio) / 172800000)|floor|add:1
        }
      }
    }

    var $periodos { value = [] }
    foreach (0|range:0:($quantidade - 1)) {
      each as $indice {
        var $inicio { value = $periodo.inicio + ($indice * 172800000) }
        var $fim { value = $periodo.fim + ($indice * 172800000) }

        function.run "cadastros/plantao_sobreposto" {
          input = {medico_id: $medico.id, inicio: $inicio, fim: $fim}
        } as $sobreposto

        precondition (!$sobreposto) {
          error_type = "inputerror"
          error = "PLANTAO_SOBREPOSTO"
        }

        var.update $periodos { value = $periodos|push:{inicio: $inicio, fim: $fim} }
      }
    }

    var $criados { value = [] }
    db.transaction {
      stack {
        foreach ($periodos) {
          each as $item {
            db.add disponibilidade_medico {
              data = {medico_id: $medico.id, inicio: $item.inicio, fim: $item.fim}
            } as $plantao

            function.run "registrar_alteracao" {
              input = {usuario_id: $usuario.id, tipo_evento: "PLANTAO_CRIADO", entidade: "DISPONIBILIDADE_MEDICO", registro_id: $plantao.id, valor_anterior: null, valor_novo: {medico_id: $medico.id, inicio: $plantao.inicio, fim: $plantao.fim}}
            } as $auditoria

            var.update $criados { value = $criados|push:$plantao }
          }
        }
      }
    }

    var $primeiro { value = $criados|first }
  }

  response = {id: $primeiro.id, medico_id: $primeiro.medico_id, inicio: $primeiro.inicio, fim: $primeiro.fim, criados: $criados|count}
  guid = "oPCOzfyZ0vKB8-1pqP4GtO6PZvY"
}

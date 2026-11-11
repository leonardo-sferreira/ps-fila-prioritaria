// Altera mínimo, máximo e pontos (0–3) de uma faixa, sem sobrepor outra do mesmo parâmetro e condição
// (add-cadastros-administrador, D8). Limite vazio = extremo aberto. Faixas não são criadas nem apagadas aqui.
query "faixas/{faixa_id}" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int faixa_id
    decimal? minimo?
    decimal? maximo?
    int pontos
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get faixa_sinal_vital {
      field_name = "id"
      field_value = $input.faixa_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Faixa não encontrada."
    }

    precondition ($input.pontos >= 0 && $input.pontos <= 3) {
      error_type = "inputerror"
      error = "Os pontos devem ficar entre 0 e 3."
    }

    precondition ($input.minimo != null || $input.maximo != null) {
      error_type = "inputerror"
      error = "Informe ao menos um dos limites."
    }

    precondition ($input.minimo == null || $input.maximo == null || $input.minimo <= $input.maximo) {
      error_type = "inputerror"
      error = "O mínimo deve ser menor ou igual ao máximo."
    }

    db.query faixa_sinal_vital {
      where = $db.faixa_sinal_vital.parametro == $anterior.parametro && $db.faixa_sinal_vital.id != $anterior.id
      return = {type: "list"}
    } as $outras

    function.run "cadastros/faixa_sobrepoe" {
      input = {faixa: {minimo: $input.minimo, maximo: $input.maximo, condicao_gravidade: $anterior.condicao_gravidade}, outras: $outras}
    } as $sobrepoe

    precondition (!$sobrepoe) {
      error_type = "inputerror"
      error = "FAIXA_SOBREPOSTA"
    }

    db.transaction {
      stack {
        db.edit faixa_sinal_vital {
          field_name = "id"
          field_value = $anterior.id
          data = {minimo: $input.minimo, maximo: $input.maximo, pontos: $input.pontos}
        } as $faixa

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "FAIXA_ALTERADA", entidade: "FAIXA_SINAL_VITAL", registro_id: $anterior.id, valor_anterior: {parametro: $anterior.parametro, minimo: $anterior.minimo, maximo: $anterior.maximo, pontos: $anterior.pontos}, valor_novo: {parametro: $faixa.parametro, minimo: $faixa.minimo, maximo: $faixa.maximo, pontos: $faixa.pontos}}
        } as $auditoria
      }
    }
  }

  response = {id: $faixa.id, parametro: $faixa.parametro, minimo: $faixa.minimo, maximo: $faixa.maximo, pontos: $faixa.pontos, condicao_gravidade: $faixa.condicao_gravidade}
}

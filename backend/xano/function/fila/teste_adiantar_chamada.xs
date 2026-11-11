// Apoio aos testes da change: altera apenas fichas sintéticas criadas por teste_criar_cenario.
function "fila/teste_adiantar_chamada" {
  input {
    int ficha_id
    text marcador filters=trim
  }

  stack {
    db.get ficha_atendimento {
      field_name = "id"
      field_value = $input.ficha_id
    } as $ficha

    precondition ($ficha != null && $ficha.status == "CHAMADO") {
      error_type = "accessdenied"
      error = "FICHA_DE_TESTE_INVALIDA"
    }

    db.get paciente {
      field_name = "id"
      field_value = $ficha.paciente_id
    } as $paciente

    precondition ($paciente != null && ($paciente.nome == "Paciente Fictício Fila Um" || $paciente.nome == "Paciente Fictício Fila Dois") && $ficha.senha == ("V-CAR-"|concat:$input.marcador)) {
      error_type = "accessdenied"
      error = "FICHA_DE_TESTE_INVALIDA"
    }

    db.edit ficha_atendimento {
      field_name = "id"
      field_value = $ficha.id
      data = {chamada_em: now|add_secs_to_timestamp:-31}
    } as $atualizada
  }

  response = {
    ficha_id : $atualizada.id
    tentativa: $atualizada.tentativas_chamada
  }

  guid = "-rrCmH3yZdBZMxzDeQbitBMXM-8"
}

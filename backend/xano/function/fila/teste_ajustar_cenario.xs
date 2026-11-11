// Ajusta somente registros fictícios identificados pelo marcador do teste.
function "fila/teste_ajustar_cenario" {
  input {
    text marcador
    int medico_um
    int medico_dois
    int ficha_dois
    int vinculo_neu
    int vinculo_cli
  }

  stack {
    db.get medico {
      field_name = "id"
      field_value = $input.medico_um
    } as $um

    db.get medico {
      field_name = "id"
      field_value = $input.medico_dois
    } as $dois

    db.get ficha_atendimento {
      field_name = "id"
      field_value = $input.ficha_dois
    } as $ficha

    db.get medico_especialidade {
      field_name = "id"
      field_value = $input.vinculo_neu
    } as $neu

    db.get medico_especialidade {
      field_name = "id"
      field_value = $input.vinculo_cli
    } as $cli

    db.get especialidade {
      field_name = "sigla"
      field_value = "CAR"
    } as $cardiologia

    precondition ($um != null && $dois != null && $ficha != null && $neu != null && $cli != null && $cardiologia != null && $um.registro_profissional == ("TESTE-UM-" ~ $input.marcador) && $dois.registro_profissional == ("TESTE-DOIS-" ~ $input.marcador) && $neu.medico_id == $um.id && $cli.medico_id == $dois.id && $ficha.status == "AGUARDANDO" && $ficha.senha == ("A-CAR-" ~ $input.marcador)) {
      error_type = "accessdenied"
      error = "CENARIO_TESTE_INVALIDO"
    }

    db.transaction {
      stack {
        db.del medico_especialidade {
          field_name = "id"
          field_value = $neu.id
        }

        db.del medico_especialidade {
          field_name = "id"
          field_value = $cli.id
        }

        db.add medico_especialidade {
          data = {medico_id: $dois.id, especialidade_id: $cardiologia.id}
        } as $novo_vinculo

        db.edit ficha_atendimento {
          field_name = "id"
          field_value = $ficha.id
          data = {
            prioridade_atual: "VERMELHA"
            senha           : "V-CAR-" ~ $input.marcador
          }
        } as $atualizada
      }
    }
  }

  response = {ficha_id: $atualizada.id, vinculo_id: $novo_vinculo.id}
  guid = "2BpRcNkpijYQZgC84VJ-Nh6MGKg"
}

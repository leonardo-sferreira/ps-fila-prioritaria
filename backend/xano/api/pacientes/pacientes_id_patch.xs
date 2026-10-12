query "pacientes/{paciente_id}" verb=PATCH {
  api_group = "Pacientes"
  description = "Atualiza parcialmente os dados cadastrais de um Paciente. Autorização e auditoria serão integradas pelas changes dependentes."

  input {
    int paciente_id
    // Os defaults internos distinguem campo omitido de null explícito no JSON.
    text? cpf?="__CPF_AUSENTE__" filters=trim
    text? nome?="__NOME_AUSENTE__" filters=trim
    date? data_nascimento?="0001-01-01"
    // Sem trim aqui: texto vazio é a intenção explícita de limpar o telefone.
    text? telefone?="__TELEFONE_AUSENTE__"
  }

  stack {
    precondition ($input.cpf == "__CPF_AUSENTE__") {
      error_type = "inputerror"
      error = "CPF não pode ser alterado"
    }

    db.get paciente {
      field_name = "id"
      field_value = $input.paciente_id
      mock = {
        "limpa telefone com null": {
          id: 1,
          cpf: "52998224725",
          nome: "Paciente de teste",
          data_nascimento: "1990-01-01",
          telefone: "11999999999",
          ativo: true
        },
        "limpa telefone com texto vazio": {
          id: 1,
          cpf: "52998224725",
          nome: "Paciente de teste",
          data_nascimento: "1990-01-01",
          telefone: "11999999999",
          ativo: true
        },
        "telefone vazio já está ausente": {
          id: 1,
          cpf: "52998224725",
          nome: "Paciente de teste",
          data_nascimento: "1990-01-01",
          telefone: null,
          ativo: true
        }
      }
    } as $paciente_atual

    precondition ($paciente_atual != null) {
      error_type = "notfound"
      error = "Paciente não encontrado"
    }

    var $atualizacoes { value = {} }
    conditional {
      if ($input.nome != "__NOME_AUSENTE__") {
        precondition ($input.nome != null && ($input.nome|strlen) > 0) {
          error_type = "inputerror"
          error = "Nome inválido"
        }
        var.update $atualizacoes { value = $atualizacoes|set:"nome":$input.nome }
      }
    }
    conditional {
      if ($input.data_nascimento != "0001-01-01") {
        var $hoje { value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo" }
        var $data_minima { value = now|transform_timestamp:"-130 years"|format_timestamp:"Y-m-d":"America/Sao_Paulo" }
        precondition ($input.data_nascimento != null && $input.data_nascimento <= $hoje && $input.data_nascimento >= $data_minima) {
          error_type = "inputerror"
          error = "Data de nascimento inválida"
        }
        var.update $atualizacoes { value = $atualizacoes|set:"data_nascimento":$input.data_nascimento }
      }
    }
    conditional {
      if ($input.telefone != "__TELEFONE_AUSENTE__") {
        // O formulário envia texto vazio ao apagar; no banco, telefone ausente é null.
        var $telefone_normalizado { value = $input.telefone }
        conditional {
          if ($telefone_normalizado == "") {
            var.update $telefone_normalizado { value = null }
          }
        }
        var.update $atualizacoes { value = $atualizacoes|set:"telefone":$telefone_normalizado }
      }
    }

    precondition (($atualizacoes|is_empty) == false) {
      error_type = "inputerror"
      error = "Nenhum campo atualizável informado"
    }

    var $houve_alteracao { value = false }
    var $paciente_resultado { value = $paciente_atual }
    conditional {
      if ($input.nome != "__NOME_AUSENTE__") {
        conditional {
          if ($atualizacoes.nome != $paciente_atual.nome) {
            var.update $houve_alteracao { value = true }
          }
        }
      }
    }
    conditional {
      if ($input.data_nascimento != "0001-01-01") {
        conditional {
          if ($atualizacoes.data_nascimento != $paciente_atual.data_nascimento) {
            var.update $houve_alteracao { value = true }
          }
        }
      }
    }
    conditional {
      if ($input.telefone != "__TELEFONE_AUSENTE__") {
        conditional {
          if ($atualizacoes.telefone != $paciente_atual.telefone) {
            var.update $houve_alteracao { value = true }
          }
        }
      }
    }

    conditional {
      if ($houve_alteracao) {
        db.patch paciente {
          field_name = "id"
          field_value = $paciente_atual.id
          data = $atualizacoes
          mock = {
            "limpa telefone com null": {
              id: 1,
              cpf: "52998224725",
              nome: "Paciente de teste",
              data_nascimento: "1990-01-01",
              telefone: null,
              ativo: true
          },
          "limpa telefone com texto vazio": {
            id: 1,
            cpf: "52998224725",
            nome: "Paciente de teste",
            data_nascimento: "1990-01-01",
            telefone: null,
            ativo: true
            }
          }
        } as $paciente_atualizado

        var.update $paciente_resultado { value = $paciente_atualizado }
      }
    }
  }

  response = {
    alterado: $houve_alteracao,
    paciente: $paciente_resultado
  }

  test "rejeita CPF nulo no payload" {
    input = { paciente_id: 1, cpf: null }
    expect.to_throw
  }

  test "limpa telefone com null" {
    input = { paciente_id: 1, telefone: null }
    expect.to_be_true ($response.alterado)
    expect.to_be_null ($response.paciente.telefone)
  }

  test "limpa telefone com texto vazio" {
    input = { paciente_id: 1, telefone: "" }
    expect.to_be_true ($response.alterado)
    expect.to_be_null ($response.paciente.telefone)
  }

  test "telefone vazio já está ausente" {
    input = { paciente_id: 1, telefone: "" }
    expect.to_be_false ($response.alterado)
    expect.to_be_null ($response.paciente.telefone)
  }
  guid = "Czt7H4l1idB6xF-IjV6_ujuuUAU"
}

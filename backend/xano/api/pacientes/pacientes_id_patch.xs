query "pacientes/{paciente_id}" verb=PATCH {
  api_group = "Pacientes"
  description = "Atualiza parcialmente os dados cadastrais de um Paciente para Recepção/Triagem, com auditoria atômica."
  auth = "usuario"

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
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $auth.id,
        perfis_permitidos: ["RECEPCAO_TRIAGEM"]
      }
    } as $usuario

    precondition ($input.cpf == "__CPF_AUSENTE__") {
      error_type = "inputerror"
      error = "CPF não pode ser alterado"
    }

    db.get paciente {
      field_name = "id"
      field_value = $input.paciente_id
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
        // O formulário envia texto vazio ao apagar; no banco, telefone ausente é null (regra testada na função).
        function.run "pacientes/normalizar_telefone" {
          input = {telefone: $input.telefone, atual: $paciente_atual.telefone}
        } as $telefone
        var.update $atualizacoes { value = $atualizacoes|set:"telefone":$telefone.valor }
      }
    }

    precondition (($atualizacoes|is_empty) == false) {
      error_type = "inputerror"
      error = "Nenhum campo atualizável informado"
    }

    var $houve_alteracao { value = false }
    var $valor_anterior { value = {} }
    var $paciente_resultado { value = $paciente_atual }
    conditional {
      if ($input.nome != "__NOME_AUSENTE__") {
        conditional {
          if ($atualizacoes.nome != $paciente_atual.nome) {
            var.update $houve_alteracao { value = true }
            var.update $valor_anterior { value = $valor_anterior|set:"nome":$paciente_atual.nome }
          }
        }
      }
    }
    conditional {
      if ($input.data_nascimento != "0001-01-01") {
        conditional {
          if ($atualizacoes.data_nascimento != $paciente_atual.data_nascimento) {
            var.update $houve_alteracao { value = true }
            var.update $valor_anterior { value = $valor_anterior|set:"data_nascimento":$paciente_atual.data_nascimento }
          }
        }
      }
    }
    conditional {
      if ($input.telefone != "__TELEFONE_AUSENTE__") {
        conditional {
          if ($telefone.alterado) {
            var.update $houve_alteracao { value = true }
            var.update $valor_anterior { value = $valor_anterior|set:"telefone":$paciente_atual.telefone }
          }
        }
      }
    }

    conditional {
      if ($houve_alteracao) {
        db.transaction {
          stack {
            db.patch paciente {
              field_name = "id"
              field_value = $paciente_atual.id
              data = $atualizacoes
            } as $paciente_atualizado

            function.run "registrar_alteracao" {
              input = {
                usuario_id    : $usuario.id,
                tipo_evento   : "ALTERACAO",
                entidade      : "PACIENTE",
                registro_id   : $paciente_atual.id,
                valor_anterior: $valor_anterior,
                valor_novo    : $atualizacoes
              }
            }
            var.update $paciente_resultado { value = $paciente_atualizado }
          }
        }
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

  guid = "Czt7H4l1idB6xF-IjV6_ujuuUAU"
}

query "pacientes" verb=POST {
  api_group = "Pacientes"
  description = "Cadastra um Paciente com CPF normalizado e único para Recepção/Triagem, com auditoria atômica."
  auth = "usuario"

  input {
    text cpf filters=trim
    text? nome? filters=trim
    date data_nascimento
    text? telefone? filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $auth.id,
        perfis_permitidos: ["RECEPCAO_TRIAGEM"]
      }
    } as $usuario

    function.run "pacientes/normalizar_cpf" {
      input = { cpf: $input.cpf }
    } as $cpf_normalizado

    precondition ($input.nome != null && ($input.nome|strlen) > 0) {
      error_type = "inputerror"
      error = "Nome inválido"
    }

    var $hoje { value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo" }
    var $data_minima { value = now|transform_timestamp:"-130 years"|format_timestamp:"Y-m-d":"America/Sao_Paulo" }
    precondition ($input.data_nascimento <= $hoje && $input.data_nascimento >= $data_minima) {
      error_type = "inputerror"
      error = "Data de nascimento inválida"
    }

    var $paciente { value = null }
    db.transaction {
      stack {
        db.has "paciente" {
          field_name = "cpf"
          field_value = $cpf_normalizado
        } as $cpf_ja_cadastrado

        precondition ($cpf_ja_cadastrado == false) {
          error_type = "inputerror"
          error = "CPF_DUPLICADO"
        }

        db.add "paciente" {
          data = {
            cpf: $cpf_normalizado,
            nome: $input.nome,
            data_nascimento: $input.data_nascimento,
            telefone: $input.telefone,
            ativo: true
          }
        } as $paciente_criado

        function.run "registrar_alteracao" {
          input = {
            usuario_id    : $usuario.id,
            tipo_evento   : "CADASTRO",
            entidade      : "PACIENTE",
            registro_id   : $paciente_criado.id,
            valor_anterior: null,
            valor_novo    : {
              cpf: $paciente_criado.cpf,
              nome: $paciente_criado.nome,
              data_nascimento: $paciente_criado.data_nascimento,
              telefone: $paciente_criado.telefone,
              ativo: $paciente_criado.ativo
            }
          }
        } as $auditoria

        var.update $paciente { value = $paciente_criado }
      }
    }
  }

  response = $paciente

  test "recusa nome vazio após trim" {
    input = {
      cpf: "529.982.247-25",
      nome: "   ",
      data_nascimento: "1990-01-01"
    }
    expect.to_throw
  }
  guid = "fNmEk5-0_JQmBsqzh-d5ic65BzE"
}

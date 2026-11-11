// Cria o login (perfil RECEPCAO_TRIAGEM) e o cadastro juntos, com CPF válido e único
// (add-cadastros-administrador, D3 e D5). A senha nunca vai para a auditoria nem para a resposta.
query recepcao verb=POST {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    text nome filters=trim
    text email filters=trim|lower
    text senha {
      sensitive = true
    }
    text cpf filters=trim
    int? especialidade_referencia_id?
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    precondition (($input.nome|strlen) >= 3) {
      error_type = "inputerror"
      error = "Informe o nome."
    }

    precondition (($input.senha|strlen) >= 8) {
      error_type = "inputerror"
      error = "A senha inicial deve ter 8 ou mais caracteres."
    }

    function.run "pacientes/normalizar_cpf" {
      input = {cpf: $input.cpf}
    } as $cpf

    db.get recepcao_triagem {
      field_name = "cpf"
      field_value = $cpf
    } as $cpf_existente

    precondition ($cpf_existente == null) {
      error_type = "inputerror"
      error = "CPF já cadastrado."
    }

    function.run "cadastros/email_livre" {
      input = {email: $input.email}
    } as $email

    var $referencia { value = ($input.especialidade_referencia_id == null || $input.especialidade_referencia_id == 0) ? null : $input.especialidade_referencia_id }
    conditional {
      if ($referencia != null) {
        function.run "cadastros/especialidades_validas" {
          input = {especialidade_ids: [$referencia]}
        } as $referencia_ok
      }
    }

    db.transaction {
      stack {
        db.add usuario {
          data = {nome: $input.nome, email: $email, password: $input.senha, perfil: "RECEPCAO_TRIAGEM", ativo: true}
        } as $login

        db.add recepcao_triagem {
          data = {usuario_id: $login.id, cpf: $cpf, especialidade_referencia_id: $referencia, ativo: true}
        } as $cadastro

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "RECEPCAO_CRIADA", entidade: "RECEPCAO_TRIAGEM", registro_id: $cadastro.id, valor_anterior: null, valor_novo: {nome: $login.nome, email: $login.email, especialidade_referencia_id: $referencia}}
        } as $auditoria
      }
    }
  }

  response = {id: $cadastro.id, usuario_id: $login.id, nome: $login.nome, email: $login.email, cpf: $cpf, especialidade_referencia_id: $referencia, ativo: true}
  guid = "aAZV6SlevjXICywpvMm7wYSK6tg"
}

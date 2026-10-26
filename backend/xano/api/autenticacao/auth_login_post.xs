query "auth/login" verb=POST {
  api_group = "Autenticacao"
  description = "Primeira etapa do login: confere e-mail, senha e usuário ativo e envia o código de verificação por e-mail."

  input {
    text email? filters=trim|lower
    text senha? {
      sensitive = true
    }
  }

  stack {
    precondition ($input.email != null && $input.email != "") {
      error_type = "inputerror"
      error = "Informe o e-mail."
    }

    precondition ($input.senha != null && $input.senha != "") {
      error_type = "inputerror"
      error = "Informe a senha."
    }

    db.get usuario {
      field_name = "email"
      field_value = $input.email
    } as $usuario

    // Mesma mensagem para e-mail inexistente e senha errada, sem revelar qual dado falhou.
    precondition ($usuario != null) {
      error_type = "unauthorized"
      error = "E-mail ou senha inválidos"
    }

    security.check_password {
      text_password = $input.senha
      hash_password = $usuario.password
    } as $senha_confere

    precondition ($senha_confere) {
      error_type = "unauthorized"
      error = "E-mail ou senha inválidos"
    }

    precondition ($usuario.ativo) {
      error_type = "accessdenied"
      error = "Usuário inativo. Procure o administrador."
    }

    // Senha conferida: o token só sai em auth/login/verificar, com o código enviado por e-mail (D13).
    function.run "auth/emitir_codigo" {
      input = {
        usuario_id : $usuario.id
        nome       : $usuario.nome
        email      : $usuario.email
        finalidade : "LOGIN"
        iniciado_em: now
      }
    } as $emitido
  }

  response = {
    codigo_enviado     : true
    mensagem           : "Enviamos um código de 6 dígitos para o seu e-mail."
    reenvio_em_segundos: $env.CODIGO_REENVIO_SEGUNDOS|to_int
  }
  guid = "E83kmLVAho4jK6rRpAtlgdt0V_c"
}

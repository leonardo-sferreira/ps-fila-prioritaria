query "auth/login" verb=POST {
  api_group = "Autenticacao"
  description = "Autentica a equipe por e-mail e senha, registra a sessão e devolve token, nome e perfil."

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

    var $ttl {
      value = $env.TOKEN_TTL_SEGUNDOS|to_int
    }

    precondition ($ttl > 0) {
      error_type = "standard"
      error = "Variável de ambiente TOKEN_TTL_SEGUNDOS não configurada."
    }

    security.create_auth_token {
      table = "usuario"
      id = $usuario.id
      extras = {}
      expiration = $ttl
    } as $token

    db.add sessao {
      data = {
        usuario_id: $usuario.id,
        login_em  : now,
        expira_em : now|add_secs_to_timestamp:$ttl
      }
    }
  }

  response = {
    token : $token
    nome  : $usuario.nome
    perfil: $usuario.perfil
  }
  guid = "E83kmLVAho4jK6rRpAtlgdt0V_c"
}

query "auth/login/verificar" verb=POST {
  api_group = "Autenticacao"
  description = "Segunda etapa do login: confere o código enviado por e-mail, registra a sessão e devolve token, nome e perfil."

  input {
    text email? filters=trim|lower
    text codigo? filters=trim {
      sensitive = true
    }
  }

  stack {
    precondition ($input.email != null && $input.email != "") {
      error_type = "inputerror"
      error = "Informe o e-mail."
    }

    precondition ($input.codigo != null && $input.codigo != "") {
      error_type = "inputerror"
      error = "Informe o código."
    }

    db.get usuario {
      field_name = "email"
      field_value = $input.email
    } as $usuario

    precondition ($usuario != null) {
      error_type = "unauthorized"
      error = "Código inválido ou expirado"
    }

    // Desativado entre as etapas: não entra, mesmo com o código certo.
    precondition ($usuario.ativo) {
      error_type = "accessdenied"
      error = "Usuário inativo. Procure o administrador."
    }

    function.run "auth/conferir_codigo" {
      input = {
        usuario_id: $usuario.id
        finalidade: "LOGIN"
        codigo    : $input.codigo
      }
    } as $conferido

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
  guid = "X_VRttyjLTrwK2LilJgLc7HDBy8"
}

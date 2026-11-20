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

    // Primeiro confere sem consumir: o código errado conta tentativa fora da transação (não é desfeito).
    function.run "auth/conferir_codigo" {
      input = {
        usuario_id: $usuario.id
        finalidade: "LOGIN"
        codigo    : $input.codigo
        consumir  : false
      }
    } as $conferido

    var $ttl {
      value = $env.TOKEN_TTL_SEGUNDOS|to_int
    }

    precondition ($ttl > 0) {
      error_type = "standard"
      error = "Variável de ambiente TOKEN_TTL_SEGUNDOS não configurada."
    }

    db.query codigo_verificacao {
      where = $db.codigo_verificacao.usuario_id == $usuario.id && $db.codigo_verificacao.finalidade == "LOGIN" && $db.codigo_verificacao.usado_em == null
      sort = {criado_em: "desc"}
      return = {type: "single"}
    } as $conferido_aberto

    precondition ($conferido_aberto != null && $conferido_aberto.codigo_hash == ($input.codigo|hmac_sha256:("ps-codigo:" ~ ($usuario.id|to_text)))) {
      error_type = "unauthorized"
      error = "Código inválido ou expirado"
    }

    // Consumo atômico. A primeira escrita muda de fato a linha do código (tentativas + 1) e a trava até o fim da
    // transação; uma verificação simultânea do mesmo código espera aqui, relê o código já usado e é recusada (a
    // transação dela é desfeita). Ao consumir, as tentativas voltam ao valor anterior.
    db.transaction {
      stack {
        db.edit codigo_verificacao {
          field_name = "id"
          field_value = $conferido_aberto.id
          data = {tentativas: $conferido_aberto.tentativas + 1}
        } as $codigo_travado

        db.get codigo_verificacao {
          field_name = "id"
          field_value = $conferido_aberto.id
        } as $aberto

        precondition ($aberto != null && $aberto.usado_em == null && $aberto.expira_em > now) {
          error_type = "unauthorized"
          error = "Código inválido ou expirado"
        }

        db.edit codigo_verificacao {
          field_name = "id"
          field_value = $aberto.id
          data = {usado_em: now, tentativas: $conferido_aberto.tentativas}
        } as $consumido

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
            expira_em : now|add_secs_to_timestamp:$ttl,
            status_operacional: ($usuario.perfil == "RECEPCAO_TRIAGEM") ? "DISPONIVEL" : null
          }
        }
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

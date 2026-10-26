query "auth/senha/redefinir" verb=POST {
  api_group = "Autenticacao"
  description = "Troca a senha com o código de redefinição, usa o código e encerra as sessões abertas do usuário."

  input {
    text email? filters=trim|lower
    text codigo? filters=trim {
      sensitive = true
    }
    text nova_senha? {
      sensitive = true
    }
  }

  stack {
    // Senha curta é recusada antes de usar o código, para a pessoa poder tentar de novo.
    precondition ($input.nova_senha != null && ($input.nova_senha|strlen) >= 8) {
      error_type = "inputerror"
      error = "A nova senha deve ter pelo menos 8 caracteres."
    }

    db.get usuario {
      field_name = "email"
      field_value = $input.email
    } as $usuario

    precondition ($usuario != null) {
      error_type = "unauthorized"
      error = "Código inválido ou expirado"
    }

    // Desativado depois de pedir o código: a redefinição não libera o acesso.
    precondition ($usuario.ativo) {
      error_type = "accessdenied"
      error = "Usuário inativo. Procure o administrador."
    }

    function.run "auth/conferir_codigo" {
      input = {
        usuario_id: $usuario.id
        finalidade: "REDEFINICAO_SENHA"
        codigo    : $input.codigo
      }
    } as $conferido

    db.edit usuario {
      field_name = "id"
      field_value = $usuario.id
      data = {password: $input.nova_senha}
    }

    db.query sessao {
      where = $db.sessao.usuario_id == $usuario.id && $db.sessao.logout_em == null
    } as $abertas

    foreach ($abertas) {
      each as $aberta {
        db.edit sessao {
          field_name = "id"
          field_value = $aberta.id
          data = {logout_em: now}
        }
      }
    }
  }

  response = {senha_redefinida: true}
  guid = "PKxhcMGmB4D19iRtcuxi4ACDYII"
}

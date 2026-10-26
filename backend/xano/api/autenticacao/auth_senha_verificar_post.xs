query "auth/senha/verificar" verb=POST {
  api_group = "Autenticacao"
  description = "Confere o código de redefinição sem usá-lo, para liberar a tela da nova senha; o uso definitivo é em auth/senha/redefinir."

  input {
    text email? filters=trim|lower
    text codigo? filters=trim {
      sensitive = true
    }
  }

  stack {
    precondition ($input.codigo != null && $input.codigo != "") {
      error_type = "inputerror"
      error = "Informe o código."
    }

    db.get usuario {
      field_name = "email"
      field_value = $input.email
    } as $usuario

    precondition ($usuario != null && $usuario.ativo) {
      error_type = "unauthorized"
      error = "Código inválido ou expirado"
    }

    function.run "auth/conferir_codigo" {
      input = {
        usuario_id: $usuario.id
        finalidade: "REDEFINICAO_SENHA"
        codigo    : $input.codigo
        consumir  : false
      }
    } as $conferido
  }

  response = {codigo_valido: true}
  guid = "oZfkALPDlhMefueBxyGnsUNiBuk"
}

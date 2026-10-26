query "auth/senha/solicitar" verb=POST {
  api_group = "Autenticacao"
  description = "Esqueci minha senha: envia o código de redefinição a usuário ativo, com a mesma resposta para qualquer e-mail."

  input {
    text email? filters=trim|lower
  }

  stack {
    precondition ($input.email != null && $input.email != "") {
      error_type = "inputerror"
      error = "Informe o e-mail."
    }

    var $intervalo {
      value = $env.CODIGO_REENVIO_SEGUNDOS|to_int
    }

    precondition ($intervalo > 0) {
      error_type = "standard"
      error = "Variável de ambiente CODIGO_REENVIO_SEGUNDOS não configurada."
    }

    db.get usuario {
      field_name = "email"
      field_value = $input.email
    } as $usuario

    // E-mail inexistente ou de usuário inativo: nada é enviado, e a resposta é a mesma.
    conditional {
      if ($usuario != null && $usuario.ativo) {
        db.query codigo_verificacao {
          where = $db.codigo_verificacao.usuario_id == $usuario.id && $db.codigo_verificacao.finalidade == "REDEFINICAO_SENHA" && $db.codigo_verificacao.usado_em == null
          sort = {criado_em: "desc"}
          return = {type: "single"}
        } as $anterior

        conditional {
          if ($anterior != null) {
            var $falta_ms {
              value = (($anterior.criado_em|add_secs_to_timestamp:$intervalo)|to_ms) - ("now"|to_ms)
            }

            precondition ($falta_ms <= 0) {
              error_type = "toomanyrequests"
              error = "Aguarde " ~ (($falta_ms / 1000)|ceil|to_text) ~ " segundos para pedir um novo código."
            }
          }
        }

        function.run "auth/emitir_codigo" {
          input = {
            usuario_id : $usuario.id
            nome       : $usuario.nome
            email      : $usuario.email
            finalidade : "REDEFINICAO_SENHA"
            iniciado_em: now
          }
        } as $emitido
      }
    }
  }

  response = {
    mensagem           : "Se o e-mail estiver cadastrado, enviamos um código"
    reenvio_em_segundos: $intervalo
  }
  guid = "52kB9oi_SGL4qDXvIM9fE2LpmAo"
}

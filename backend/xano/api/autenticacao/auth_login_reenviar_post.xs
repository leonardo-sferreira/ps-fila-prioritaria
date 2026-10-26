query "auth/login/reenviar" verb=POST {
  api_group = "Autenticacao"
  description = "Reenvia o código do login sem pedir a senha de novo, dentro da validade do primeiro passo e após o intervalo de reenvio."

  input {
    text email? filters=trim|lower
  }

  stack {
    var $ttl {
      value = $env.CODIGO_TTL_SEGUNDOS|to_int
    }

    var $intervalo {
      value = $env.CODIGO_REENVIO_SEGUNDOS|to_int
    }

    precondition ($ttl > 0 && $intervalo > 0) {
      error_type = "standard"
      error = "Variáveis de ambiente CODIGO_TTL_SEGUNDOS e CODIGO_REENVIO_SEGUNDOS não configuradas."
    }

    db.get usuario {
      field_name = "email"
      field_value = $input.email
    } as $usuario

    var $pendente {
      value = null
    }

    conditional {
      if ($usuario != null && $usuario.ativo) {
        db.query codigo_verificacao {
          where = $db.codigo_verificacao.usuario_id == $usuario.id && $db.codigo_verificacao.finalidade == "LOGIN" && $db.codigo_verificacao.usado_em == null
          sort = {criado_em: "desc"}
          return = {type: "single"}
        } as $aberto

        var.update $pendente {
          value = $aberto
        }
      }
    }

    // Sem login pendente, ou com o primeiro passo vencido, é preciso informar a senha de novo.
    precondition ($pendente != null && ($pendente.iniciado_em|add_secs_to_timestamp:$ttl) > now) {
      error_type = "accessdenied"
      error = "Não foi possível reenviar o código. Faça login novamente."
    }

    var $falta_ms {
      value = (($pendente.criado_em|add_secs_to_timestamp:$intervalo)|to_ms) - ("now"|to_ms)
    }

    precondition ($falta_ms <= 0) {
      error_type = "toomanyrequests"
      error = "Aguarde " ~ (($falta_ms / 1000)|ceil|to_text) ~ " segundos para pedir um novo código."
    }

    function.run "auth/emitir_codigo" {
      input = {
        usuario_id : $usuario.id
        nome       : $usuario.nome
        email      : $usuario.email
        finalidade : "LOGIN"
        iniciado_em: $pendente.iniciado_em
      }
    } as $emitido
  }

  response = {
    codigo_enviado     : true
    mensagem           : "Enviamos um novo código para o seu e-mail."
    reenvio_em_segundos: $intervalo
  }
  guid = "sLuhmTRZXA4RgTH0aAgH3bCmLoo"
}

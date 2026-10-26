// Confere o código de verificação aberto do usuário e o marca como usado quando confere (design D12/D13).
function "auth/conferir_codigo" {
  description = "Recusa código inexistente, expirado, com tentativas esgotadas ou incorreto (contando a tentativa); se confere e consumir=true, marca como usado."

  input {
    int usuario_id
    enum finalidade {
      values = ["LOGIN", "REDEFINICAO_SENHA"]
    }
    text codigo {
      sensitive = true
    }
    // false só confere (tela de código da redefinição); o uso definitivo acontece ao trocar a senha.
    bool consumir?=true
  }

  stack {
    var $limite {
      value = $env.CODIGO_TENTATIVAS|to_int
    }

    precondition ($limite > 0) {
      error_type = "standard"
      error = "Variável de ambiente CODIGO_TENTATIVAS não configurada."
    }

    db.query codigo_verificacao {
      where = $db.codigo_verificacao.usuario_id == $input.usuario_id && $db.codigo_verificacao.finalidade == $input.finalidade && $db.codigo_verificacao.usado_em == null
      sort = {criado_em: "desc"}
      return = {type: "single"}
    } as $aberto

    // Com as tentativas esgotadas, nem o código correto é aceito até pedir outro.
    precondition ($aberto != null && $aberto.expira_em > now && $aberto.tentativas < $limite) {
      error_type = "unauthorized"
      error = "Código inválido ou expirado"
    }

    conditional {
      if (($input.codigo|hmac_sha256:("ps-codigo:" ~ ($input.usuario_id|to_text))) != $aberto.codigo_hash) {
        db.edit codigo_verificacao {
          field_name = "id"
          field_value = $aberto.id
          data = {tentativas: $aberto.tentativas + 1}
        }

        precondition (false) {
          error_type = "unauthorized"
          error = "Código inválido ou expirado"
        }
      }
    }

    conditional {
      if ($input.consumir) {
        db.edit codigo_verificacao {
          field_name = "id"
          field_value = $aberto.id
          data = {usado_em: now}
        }
      }
    }
  }

  response = {conferido: true}
  guid = "FPAeQPa3pfn3g_QbBd8dTD8MluY"
}

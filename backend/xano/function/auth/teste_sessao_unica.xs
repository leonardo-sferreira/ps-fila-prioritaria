// Cenário sintético executado somente pelo CLI; não possui endpoint público.
function "auth/teste_sessao_unica" {
  input {
    enum acao {
      values = ["CRIAR", "CODIGO", "PAUSA", "AUSENTE", "EXPIRAR", "ENCERRAR", "CONSULTAR"]
    }
    text marcador filters=trim
    text? codigo filters=trim
    password? senha
  }

  stack {
    var $email {
      value = "teste-sessao-" ~ $input.marcador ~ "@example.invalid"
    }

    db.get usuario {
      field_name = "email"
      field_value = $email
    } as $usuario

    conditional {
      if ($input.acao == "CRIAR") {
        precondition ($usuario == null && $input.senha != null) {
          error_type = "inputerror"
          error = "CENARIO_INVALIDO"
        }

        db.add usuario {
          data = {
            nome    : "Teste Sessão Única"
            email   : $email
            password: $input.senha
            perfil  : "MEDICO"
            ativo   : true
          }
        } as $criado

        var.update $usuario {
          value = $criado
        }

        db.add medico {
          data = {
            usuario_id           : $criado.id
            registro_profissional: "TESTE-SESSAO-" ~ $input.marcador
            ativo                : true
          }
        } as $medico_criado

        db.add disponibilidade_medico {
          data = {
            medico_id: $medico_criado.id
            inicio   : now|add_secs_to_timestamp:-3600
            fim      : now|add_secs_to_timestamp:3600
          }
        } as $plantao_criado
      }

      else {
        precondition ($usuario != null && $usuario.nome == "Teste Sessão Única" && $usuario.perfil == "MEDICO") {
          error_type = "accessdenied"
          error = "CENARIO_INVALIDO"
        }
      }
    }

    conditional {
      if ($input.acao == "CRIAR" || $input.acao == "CODIGO") {
        precondition ($input.codigo != null && $input.codigo != "") {
          error_type = "inputerror"
          error = "CODIGO_OBRIGATORIO"
        }

        db.query codigo_verificacao {
          where = $db.codigo_verificacao.usuario_id == $usuario.id && $db.codigo_verificacao.finalidade == "LOGIN" && $db.codigo_verificacao.usado_em == null
          return = {type: "list"}
        } as $anteriores

        foreach ($anteriores) {
          each as $anterior {
            db.edit codigo_verificacao {
              field_name = "id"
              field_value = $anterior.id
              data = {usado_em: now}
            } as $invalidado
          }
        }

        db.add codigo_verificacao {
          data = {
            usuario_id : $usuario.id
            finalidade: "LOGIN"
            codigo_hash: $input.codigo|hmac_sha256:("ps-codigo:" ~ ($usuario.id|to_text))
            iniciado_em: now
            criado_em  : now
            expira_em  : now|add_secs_to_timestamp:600
            tentativas : 0
          }
        } as $codigo_criado
      }
    }

    db.query sessao {
      where = $db.sessao.usuario_id == $usuario.id && $db.sessao.logout_em == null && $db.sessao.expira_em > now
      sort = {login_em: "desc"}
      return = {type: "list"}
    } as $sessoes

    conditional {
      if ($input.acao == "PAUSA" || $input.acao == "AUSENTE") {
        precondition (($sessoes|count) > 0) {
          error_type = "inputerror"
          error = "SEM_SESSAO"
        }

        db.edit sessao {
          field_name = "id"
          field_value = ($sessoes|first).id
          data = {status_operacional: $input.acao}
        } as $alterada
      }

      elseif ($input.acao == "EXPIRAR") {
        foreach ($sessoes) {
          each as $sessao {
            db.edit sessao {
              field_name = "id"
              field_value = $sessao.id
              data = {expira_em: now|add_secs_to_timestamp:-1}
            } as $expirada
          }
        }
      }

      elseif ($input.acao == "ENCERRAR") {
        foreach ($sessoes) {
          each as $sessao {
            db.edit sessao {
              field_name = "id"
              field_value = $sessao.id
              data = {logout_em: now}
            } as $encerrada
          }
        }

        db.edit usuario {
          field_name = "id"
          field_value = $usuario.id
          data = {ativo: false}
        } as $desativado

        db.get medico {
          field_name = "usuario_id"
          field_value = $usuario.id
        } as $medico

        conditional {
          if ($medico != null && $medico.registro_profissional == ("TESTE-SESSAO-" ~ $input.marcador)) {
            db.query disponibilidade_medico {
              where = $db.disponibilidade_medico.medico_id == $medico.id && $db.disponibilidade_medico.encerrado_em == null
              return = {type: "list"}
            } as $periodos

            foreach ($periodos) {
              each as $periodo {
                db.edit disponibilidade_medico {
                  field_name = "id"
                  field_value = $periodo.id
                  data = {encerrado_em: now}
                } as $periodo_encerrado
              }
            }

            db.edit medico {
              field_name = "id"
              field_value = $medico.id
              data = {ativo: false}
            } as $medico_encerrado
          }
        }
      }
    }

    db.query sessao {
      where = $db.sessao.usuario_id == $usuario.id && $db.sessao.logout_em == null && $db.sessao.expira_em > now
      sort = {login_em: "desc"}
      return = {type: "list"}
    } as $vigentes
  }

  response = {
    email            : $email
    usuario_id       : $usuario.id
    sessoes_ativas   : $vigentes|count
    status_atual     : (($vigentes|count) == 0) ? null : ($vigentes|first).status_operacional
    status_sessoes   : $vigentes|map:$$.status_operacional
  }
  guid = "z7avw3PTcMsAGBbshxulOJvHeVg"
}

// A alteração das quantidades do ciclo reinicia a posição de todas as especialidades.
query "parametros/{chave}" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    text chave filters=trim
    int valor
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $auth.id
        perfis_permitidos: ["ADMINISTRADOR"]
      }
    } as $usuario

    precondition ($input.chave == "amarelas_por_ciclo" || $input.chave == "azuis_por_ciclo" || $input.chave == "tamanho_previsao") {
      error_type = "inputerror"
      error = "PARAMETRO_NAO_EDITAVEL_AQUI"
    }

    var $maximo {
      value = ($input.chave == "tamanho_previsao") ? 20 : 10
    }

    precondition ($input.valor >= 1 && $input.valor <= $maximo) {
      error_type = "inputerror"
      error = "PARAMETRO_FORA_DOS_LIMITES"
    }

    var $resultado {
      value = null
    }

    db.transaction {
      stack {
        db.get parametro {
          field_name = "chave"
          field_value = $input.chave
        } as $anterior

        precondition ($anterior != null) {
          error_type = "notfound"
          error = "PARAMETRO_NAO_CONFIGURADO"
        }

        conditional {
          if ($anterior.valor != ($input.valor|to_text)) {
            db.edit parametro {
              field_name = "id"
              field_value = $anterior.id
              data = {valor: $input.valor|to_text}
            } as $atualizado

            conditional {
              if ($input.chave != "tamanho_previsao") {
                db.query ciclo_fila {
                  return = {type: "list"}
                } as $ciclos

                foreach ($ciclos) {
                  each as $ciclo {
                    db.edit ciclo_fila {
                      field_name = "id"
                      field_value = $ciclo.id
                      data = {posicao: 1}
                    } as $reiniciado
                  }
                }
              }
            }

            function.run registrar_alteracao {
              input = {
                usuario_id    : $usuario.id
                tipo_evento   : "PARAMETRO_ALTERADO"
                entidade      : "PARAMETRO"
                registro_id   : $anterior.id
                valor_anterior: {chave: $anterior.chave, valor: $anterior.valor}
                valor_novo    : {chave: $anterior.chave, valor: $atualizado.valor}
              }
            } as $auditoria

            var.update $resultado {
              value = {chave: $atualizado.chave, valor: $atualizado.valor}
            }
          }

          else {
            var.update $resultado {
              value = {chave: $anterior.chave, valor: $anterior.valor}
            }
          }
        }
      }
    }
  }

  response = $resultado
  guid = "WpCoQrBr6eU_Bo10xcsyVpKmP-c"
}

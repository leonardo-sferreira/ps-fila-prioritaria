// Repete a chamada ou conclui a ficha atribuída ao médico autenticado.
function "fila/agir_chamada" {
  input {
    int usuario_id
    int ficha_id
    text acao filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $input.usuario_id
        perfis_permitidos: ["MEDICO"]
      }
    } as $usuario

    db.get medico {
      field_name = "usuario_id"
      field_value = $usuario.id
    } as $medico

    precondition ($medico != null && $medico.ativo) {
      error_type = "accessdenied"
      error = "MEDICO_INATIVO"
    }

    precondition ($input.acao == "REPETIR" || $input.acao == "COMPARECEU" || $input.acao == "DESISTENCIA") {
      error_type = "inputerror"
      error = "ACAO_INVALIDA"
    }

    var $resultado {
      value = null
    }

    db.transaction {
      stack {
        db.get ficha_atendimento {
          field_name = "id"
          field_value = $input.ficha_id
        } as $anterior

        precondition ($anterior != null && $anterior.status == "CHAMADO" && $anterior.medico_chamada_id == $medico.id) {
          error_type = "accessdenied"
          error = "FICHA_NAO_ATRIBUIDA"
        }

        // Serializa ações da mesma ficha, inclusive cliques repetidos.
        db.edit ficha_atendimento {
          field_name = "id"
          field_value = $anterior.id
          data = {oportunidade: $anterior.oportunidade ?? 1}
        } as $travada

        db.get ficha_atendimento {
          field_name = "id"
          field_value = $anterior.id
        } as $ficha

        precondition ($ficha.status == "CHAMADO" && $ficha.medico_chamada_id == $medico.id) {
          error_type = "accessdenied"
          error = "FICHA_NAO_ATRIBUIDA"
        }

        var $oportunidade {
          value = $ficha.oportunidade ?? 1
        }

        var $tentativa {
          value = $ficha.tentativas_chamada ?? 1
        }

        conditional {
          if ($input.acao == "REPETIR") {
            db.get parametro {
              field_name = "chave"
              field_value = "INTERVALO_CHAMADA_SEGUNDOS"
            } as $intervalo

            db.get parametro {
              field_name = "chave"
              field_value = "TENTATIVAS_CHAMADA"
            } as $limite

            precondition ($intervalo != null && $limite != null && ($intervalo.valor|to_int) > 0 && ($limite.valor|to_int) > 0) {
              error_type = "inputerror"
              error = "PARAMETROS_NAO_CONFIGURADOS"
            }

            precondition ($tentativa < ($limite.valor|to_int)) {
              error_type = "inputerror"
              error = "LIMITE_DE_CHAMADAS"
            }

            var $liberada_em {
              value = $ficha.chamada_em
                |add_secs_to_timestamp:($intervalo.valor|to_int)
            }

            var $restante {
              value = (($liberada_em - (now|to_ms) + 999) / 1000)|ceil
            }

            precondition ($restante <= 0) {
              error_type = "inputerror"
              error = "AGUARDE_INTERVALO:"|concat:($restante|to_text)
            }

            var.update $tentativa {
              value = $tentativa + 1
            }

            db.add chamada {
              data = {
                ficha_id    : $ficha.id
                medico_id   : $medico.id
                oportunidade: $oportunidade
                tentativa   : $tentativa
                tipo        : "CHAMADA"
                created_at  : now
              }
            } as $evento

            conditional {
              if ($tentativa >= ($limite.valor|to_int)) {
                conditional {
                  if ($oportunidade == 1) {
                    db.edit ficha_atendimento {
                      field_name = "id"
                      field_value = $ficha.id
                      data = {
                        status            : "AGUARDANDO"
                        oportunidade      : 2
                        tentativas_chamada: 0
                        medico_chamada_id : null
                        fila_em           : now
                        chamada_em        : now
                      }
                    } as $atualizada
                  }

                  else {
                    db.edit ficha_atendimento {
                      field_name = "id"
                      field_value = $ficha.id
                      data = {
                        status            : "DESISTENCIA"
                        tentativas_chamada: $tentativa
                        finalizada_em     : now
                      }
                    } as $atualizada

                    db.add chamada {
                      data = {
                        ficha_id    : $ficha.id
                        medico_id   : $medico.id
                        oportunidade: $oportunidade
                        tentativa   : $tentativa
                        tipo        : "DESISTENCIA"
                        created_at  : now
                      }
                    } as $desistencia
                  }
                }
              }

              else {
                db.edit ficha_atendimento {
                  field_name = "id"
                  field_value = $ficha.id
                  data = {tentativas_chamada: $tentativa, chamada_em: now}
                } as $atualizada
              }
            }
          }

          else {
            var $novo_status {
              value = ($input.acao == "COMPARECEU") ? "ATENDIDO" : "DESISTENCIA"
            }

            var $tipo_evento {
              value = ($input.acao == "COMPARECEU") ? "COMPARECIMENTO" : "DESISTENCIA"
            }

            db.edit ficha_atendimento {
              field_name = "id"
              field_value = $ficha.id
              data = {status: $novo_status, finalizada_em: now}
            } as $atualizada

            db.add chamada {
              data = {
                ficha_id    : $ficha.id
                medico_id   : $medico.id
                oportunidade: $oportunidade
                tentativa   : $tentativa
                tipo        : $tipo_evento
                created_at  : now
              }
            } as $evento
          }
        }

        function.run registrar_alteracao {
          input = {
            usuario_id    : $usuario.id
            tipo_evento   : "CHAMADA"
            entidade      : "FICHA_ATENDIMENTO"
            registro_id   : $ficha.id
            valor_anterior: {
            status      : $ficha.status
            oportunidade: $oportunidade
            tentativa   : $ficha.tentativas_chamada
          }
            valor_novo    : {
            status      : $atualizada.status
            oportunidade: $atualizada.oportunidade
            tentativa   : $atualizada.tentativas_chamada
          }
          }
        } as $auditoria

        var.update $resultado {
          value = {
            ficha_id     : $ficha.id
            senha        : $ficha.senha
            status       : $atualizada.status
            oportunidade : $atualizada.oportunidade
            tentativa    : $atualizada.tentativas_chamada
            chamada_em   : $atualizada.chamada_em
            finalizada_em: $atualizada.finalizada_em
          }
        }
      }
    }
  }

  response = $resultado
  guid = "FRboAfGyRyELEbZ8gWLiDvUUz1M"
}

query "fichas/{ficha_id}" verb=PATCH {
  api_group = "Triagem"
  description = "Atualiza parcialmente a observação geral e a coleção final de sintomas, validando RN04 no estado resultante."

  input {
    int ficha_id
    // Texto vazio, whitespace e coleção vazia precisam ser preservados como
    // intenções explícitas de edição; apenas a ausência do campo não altera
    // aquele componente da ficha.
    text observacao? = "__OMITTED__"
    json sintoma_ids? = "__OMITTED__"
  }

  stack {
    var $altera_observacao {
      value = $input.observacao != "__OMITTED__"
    }

    var $altera_sintomas {
      value = $input.sintoma_ids != "__OMITTED__"
    }

    precondition ($altera_observacao || $altera_sintomas) {
      error_type = "inputerror"
      error = "NENHUM_CAMPO_ATUALIZAVEL_INFORMADO"
    }

    db.transaction {
      stack {
        db.get ficha_atendimento {
          field_name = "id"
          field_value = $input.ficha_id
        } as $ficha

        precondition ($ficha != null) {
          error_type = "notfound"
          error = "FICHA_NAO_ENCONTRADA"
        }

        db.query ficha_sintoma {
          where = $db.ficha_sintoma.ficha_id == $ficha.id
          return = {type: "list"}
        } as $vinculos_atuais

        var $ids_atuais {
          value = $vinculos_atuais|map:$$.sintoma_id
        }

        var $ids_resultantes {
          value = $ids_atuais
        }

        conditional {
          if ($altera_sintomas) {
            precondition ($input.sintoma_ids|is_array) {
              error_type = "inputerror"
              error = "SINTOMA_IDS_INVALIDO"
            }

            foreach ($input.sintoma_ids) {
              each as $sintoma_id {
                precondition ($sintoma_id|is_int) {
                  error_type = "inputerror"
                  error = "SINTOMA_IDS_INVALIDO"
                }
              }
            }

            var.update $ids_resultantes {
              value = $input.sintoma_ids|unique
            }

            db.query sintoma {
              where = $db.sintoma.id in $ids_resultantes && $db.sintoma.ativo == true
              return = {type: "list"}
            } as $sintomas_ativos

            precondition (($sintomas_ativos|count) == ($ids_resultantes|count)) {
              error_type = "inputerror"
              error = "SINTOMA_INEXISTENTE_OU_INATIVO"
            }
          }
        }

        var $observacao_resultante {
          value = $ficha.observacao ?? ""
        }

        conditional {
          if ($altera_observacao) {
            var.update $observacao_resultante {
              value = $input.observacao|trim
            }
          }
        }

        precondition ((($ids_resultantes|count) > 0) || (($observacao_resultante|strlen) > 0)) {
          error_type = "inputerror"
          error = "FICHA_SEM_SINTOMA_OU_OBSERVACAO"
        }

        conditional {
          if ($altera_observacao) {
            db.patch ficha_atendimento {
              field_name = "id"
              field_value = $ficha.id
              data = {observacao: $observacao_resultante}
            } as $ficha_atualizada
          }
        }

        conditional {
          if ($altera_sintomas) {
            var $ids_para_remover {
              value = $ids_atuais|diff:$ids_resultantes
            }

            var $ids_para_adicionar {
              value = $ids_resultantes|diff:$ids_atuais
            }

            conditional {
              if (($ids_para_remover|count) > 0) {
                db.bulk.delete ficha_sintoma {
                  where = $db.ficha_sintoma.ficha_id == $ficha.id && $db.ficha_sintoma.sintoma_id in $ids_para_remover
                } as $vinculos_removidos
              }
            }

            foreach ($ids_para_adicionar) {
              each as $sintoma_id {
                db.add ficha_sintoma {
                  data = {ficha_id: $ficha.id, sintoma_id: $sintoma_id}
                } as $vinculo_criado
              }
            }
          }
        }
      }
    }
  }

  response = {
    id         : $input.ficha_id
    observacao : $observacao_resultante
    sintoma_ids: $ids_resultantes
  }

  guid = "XJ6U5MqK_6-Cg2920GUm4eZWp80"
}

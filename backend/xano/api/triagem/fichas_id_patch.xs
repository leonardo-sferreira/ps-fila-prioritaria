query "fichas/{ficha_id}" verb=PATCH {
  api_group = "Triagem"
  description = "Atualiza observação, sintomas do catálogo, sintomas digitados e sinais vitais da ficha EM_TRIAGEM ou AGUARDANDO, valida RN04, recalcula a classificação (descartando o ajuste manual), aplica o ajuste opcional, reavalia destino e senha em AGUARDANDO e audita."

  auth = "usuario"

  input {
    int ficha_id
    // Texto vazio, whitespace e coleção vazia precisam ser preservados como
    // intenções explícitas de edição; apenas a ausência do campo não altera
    // aquele componente da ficha.
    text observacao? = "__OMITTED__"
    json sintoma_ids? = "__OMITTED__"
    // Conjunto final: pa_sistolica, fc, fr, temperatura, spo2, glicemia,
    // glicemia_sinais_gravidade e gestante. Campo ausente ou vazio = não medido (add-classificacao-prioridade, D5).
    json sinais_vitais? = "__OMITTED__"
    // Lista final de {descricao, pontuacao} digitados pela Recepção/Triagem (D9).
    json sintomas_livres? = "__OMITTED__"
    // Ajuste manual opcional aplicado depois do recálculo, para a ficha não ficar sem cor
    // (add-reavaliacao-ficha-aguardando, D2).
    text prioridade_ajuste? filters=trim|upper
    text justificativa_ajuste? filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM"]}
    } as $usuario

    var $altera_observacao {
      value = $input.observacao != "__OMITTED__"
    }

    var $altera_sintomas {
      value = $input.sintoma_ids != "__OMITTED__"
    }

    var $altera_sinais {
      value = $input.sinais_vitais != "__OMITTED__"
    }

    var $altera_livres {
      value = $input.sintomas_livres != "__OMITTED__"
    }

    precondition ($altera_observacao || $altera_sintomas || $altera_sinais || $altera_livres) {
      error_type = "inputerror"
      error = "NENHUM_CAMPO_ATUALIZAVEL_INFORMADO"
    }

    db.transaction {
      stack {
        function.run "classificacao/inicializar_classificacao" {
          input = {}
        } as $classificacao_inicializada

        db.get ficha_atendimento {
          field_name = "id"
          field_value = $input.ficha_id
        } as $ficha

        precondition ($ficha != null) {
          error_type = "notfound"
          error = "FICHA_NAO_ENCONTRADA"
        }

        // AGUARDANDO também é editável (RF12); CHAMADO e os finais não.
        precondition (["EM_TRIAGEM", "AGUARDANDO"]|in:$ficha.status) {
          error_type = "inputerror"
          error = "FICHA_FORA_DA_TRIAGEM"
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

        // Sintomas digitados (D9): só valem para esta ficha.
        db.query ficha_sintoma_livre {
          where = $db.ficha_sintoma_livre.ficha_id == $ficha.id
          sort = {id: "asc"}
          return = {type: "list"}
        } as $livres_atuais

        var $livres_anteriores {
          value = $livres_atuais|map:{descricao: $$.descricao, pontuacao: $$.pontuacao}
        }

        var $livres_resultantes {
          value = $livres_anteriores
        }

        conditional {
          if ($altera_livres) {
            precondition ($input.sintomas_livres|is_array) {
              error_type = "inputerror"
              error = "SINTOMAS_LIVRES_INVALIDO"
            }

            precondition (($input.sintomas_livres|count) <= 10) {
              error_type = "inputerror"
              error = "SINTOMAS_LIVRES_LIMITE"
            }

            db.query sintoma {
              return = {type: "list"}
            } as $catalogo

            var $nomes_catalogo {
              value = $catalogo|map:(($$.nome ?? "")|trim|to_lower|unaccent)
            }

            var $normalizados { value = [] }
            var.update $livres_resultantes { value = [] }

            foreach ($input.sintomas_livres) {
              each as $item {
                var $descricao {
                  value = (($item|get:"descricao":"") ?? "")|to_text|trim
                }

                precondition (($descricao|strlen) >= 3 && ($descricao|strlen) <= 80) {
                  error_type = "inputerror"
                  error = "SINTOMA_LIVRE_DESCRICAO_INVALIDA"
                }

                var $pontuacao {
                  value = $item|get:"pontuacao":null
                }

                precondition ($pontuacao != null && ([1, 2, 3]|in:$pontuacao)) {
                  error_type = "inputerror"
                  error = "SINTOMA_LIVRE_PONTUACAO_INVALIDA"
                }

                var $normalizado {
                  value = $descricao|to_lower|unaccent
                }

                precondition (!($normalizados|in:$normalizado)) {
                  error_type = "inputerror"
                  error = "SINTOMA_LIVRE_DUPLICADO"
                }

                precondition (!($nomes_catalogo|in:$normalizado)) {
                  error_type = "inputerror"
                  error = "SINTOMA_LIVRE_EXISTE_NO_CATALOGO"
                }

                var.update $normalizados {
                  value = $normalizados|push:$normalizado
                }

                var.update $livres_resultantes {
                  value = $livres_resultantes|push:{descricao: $descricao, pontuacao: $pontuacao|to_int}
                }
              }
            }
          }
        }

        // Sinais vitais (D5): conjunto final, com limites de digitação (não são faixas de pontuação).
        var $sinais_anteriores {
          value = {
            pa_sistolica             : $ficha.pa_sistolica
            fc                       : $ficha.fc
            fr                       : $ficha.fr
            temperatura              : $ficha.temperatura
            spo2                     : $ficha.spo2
            glicemia                 : $ficha.glicemia
            glicemia_sinais_gravidade: $ficha.glicemia_sinais_gravidade == true
            gestante                 : $ficha.gestante == true
          }
        }

        var $sinais_resultantes {
          value = $sinais_anteriores
        }

        conditional {
          if ($altera_sinais) {
            precondition ($input.sinais_vitais != null && !($input.sinais_vitais|is_array)) {
              error_type = "inputerror"
              error = "SINAIS_VITAIS_INVALIDO"
            }

            var.update $sinais_resultantes {
              value = {
                glicemia_sinais_gravidade: ($input.sinais_vitais|get:"glicemia_sinais_gravidade":false) == true
                gestante                 : ($input.sinais_vitais|get:"gestante":false) == true
              }
            }

            foreach ([{campo: "pa_sistolica", minimo: 40, maximo: 300, decimal: false}, {campo: "fc", minimo: 20, maximo: 250, decimal: false}, {campo: "fr", minimo: 4, maximo: 80, decimal: false}, {campo: "temperatura", minimo: 25, maximo: 45, decimal: true}, {campo: "spo2", minimo: 50, maximo: 100, decimal: false}, {campo: "glicemia", minimo: 10, maximo: 1500, decimal: false}]) {
              each as $regra {
                var $bruto {
                  value = $input.sinais_vitais|get:$regra.campo:null
                }

                var $valor { value = null }

                conditional {
                  if ($bruto != null && $bruto != "") {
                    var $numero {
                      value = $bruto|to_decimal
                    }

                    precondition ($numero >= $regra.minimo && $numero <= $regra.maximo) {
                      error_type = "inputerror"
                      error = "SINAL_VITAL_INVALIDO:" ~ $regra.campo
                    }

                    conditional {
                      if ($regra.decimal) {
                        // Temperatura com no máximo uma casa decimal.
                        precondition (((($numero * 10) - (($numero * 10)|round:0))|abs) < 0.001) {
                          error_type = "inputerror"
                          error = "SINAL_VITAL_INVALIDO:" ~ $regra.campo
                        }

                        var.update $valor {
                          value = ($numero|round:1)
                        }
                      }
                      else {
                        precondition (($numero|floor) == $numero) {
                          error_type = "inputerror"
                          error = "SINAL_VITAL_INVALIDO:" ~ $regra.campo
                        }

                        var.update $valor {
                          value = $numero|to_int
                        }
                      }
                    }
                  }
                }

                var.update $sinais_resultantes {
                  value = $sinais_resultantes|set:$regra.campo:$valor
                }
              }
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

        // RN04: sintoma do catálogo, sintoma digitado ou observação.
        precondition ((($ids_resultantes|count) > 0) || (($livres_resultantes|count) > 0) || (($observacao_resultante|strlen) > 0)) {
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

        conditional {
          if ($altera_livres) {
            conditional {
              if (($livres_atuais|count) > 0) {
                db.bulk.delete ficha_sintoma_livre {
                  where = $db.ficha_sintoma_livre.ficha_id == $ficha.id
                } as $livres_removidos
              }
            }

            foreach ($livres_resultantes) {
              each as $livre {
                db.add ficha_sintoma_livre {
                  data = {ficha_id: $ficha.id, descricao: $livre.descricao, pontuacao: $livre.pontuacao, criado_por: $usuario.id}
                } as $livre_criado
              }
            }
          }
        }

        conditional {
          if ($altera_sinais) {
            db.patch ficha_atendimento {
              field_name = "id"
              field_value = $ficha.id
              data = $sinais_resultantes
            } as $ficha_com_sinais
          }
        }

        // Recálculo: a prioridade atual volta a ser a calculada e o ajuste manual é descartado (decisão do PO, 08/11/2026).
        function.run "classificacao/avaliar_ficha" {
          input = {ficha_id: $ficha.id}
        } as $avaliacao

        var $prioridade_calculada {
          value = $avaliacao.classificacao.prioridade_calculada
        }

        var $classificacao_risco { value = null }

        conditional {
          if ($prioridade_calculada == "VERMELHA") {
            var.update $classificacao_risco { value = "ALTO" }
          }
          elseif ($prioridade_calculada == "AMARELA") {
            var.update $classificacao_risco { value = "MODERADO" }
          }
          elseif ($prioridade_calculada == "AZUL") {
            var.update $classificacao_risco { value = "BAIXO" }
          }
        }

        db.patch ficha_atendimento {
          field_name = "id"
          field_value = $ficha.id
          data = {
            escore_risco        : $avaliacao.classificacao.escore_total
            parametro_critico   : $avaliacao.classificacao.item_critico
            classificacao_risco : $classificacao_risco
            prioridade_calculada: $prioridade_calculada
            prioridade_atual    : $prioridade_calculada
            justificativa_ajuste: null
            condicao_prioritaria: $avaliacao.classificacao.condicao_prioritaria
          }
        } as $ficha_recalculada

        var $prioridade_final { value = $prioridade_calculada }

        conditional {
          if ($input.prioridade_ajuste != null && $input.prioridade_ajuste != "") {
            function.run "classificacao/aplicar_ajuste" {
              input = {ficha_id: $ficha.id, usuario_id: $usuario.id, prioridade: $input.prioridade_ajuste, justificativa: $input.justificativa_ajuste}
            } as $ajuste
            var.update $prioridade_final { value = $ajuste.prioridade_atual }
          }
        }

        var $reavaliacao { value = null }

        conditional {
          if ($ficha.status == "AGUARDANDO") {
            function.run "direcionamento/reavaliar_senha" {
              input = {ficha_id: $ficha.id, prioridade_anterior: $ficha.prioridade_atual, refazer_destino: true}
            } as $reavaliacao_feita
            var.update $reavaliacao { value = $reavaliacao_feita }
          }
        }

        var $tipo_evento { value = "SINAIS_VITAIS_ALTERADOS" }

        conditional {
          if ($altera_sintomas || $altera_livres || $altera_observacao) {
            var.update $tipo_evento { value = "SINTOMAS_ALTERADOS" }
          }
        }

        function.run "registrar_alteracao" {
          input = {
            usuario_id    : $usuario.id
            tipo_evento   : $tipo_evento
            entidade      : "FICHA_ATENDIMENTO"
            registro_id   : $ficha.id
            valor_anterior: {observacao: $ficha.observacao, sintoma_ids: $ids_atuais, sintomas_livres: $livres_anteriores, sinais_vitais: $sinais_anteriores, prioridade_calculada: $ficha.prioridade_calculada, prioridade_atual: $ficha.prioridade_atual, justificativa_ajuste: $ficha.justificativa_ajuste, especialidade_id: $ficha.especialidade_atribuida_id, senha: $ficha.senha}
            valor_novo    : {observacao: $observacao_resultante, sintoma_ids: $ids_resultantes, sintomas_livres: $livres_resultantes, sinais_vitais: $sinais_resultantes, prioridade_calculada: $prioridade_calculada, prioridade_atual: $prioridade_final, especialidade_id: ($reavaliacao == null) ? $ficha.especialidade_atribuida_id : $reavaliacao.especialidade.id, senha: ($reavaliacao == null) ? $ficha.senha : $reavaliacao.senha}
          }
        } as $auditoria
      }
    }
  }

  response = {
    id             : $input.ficha_id
    observacao     : $observacao_resultante
    sintoma_ids    : $ids_resultantes
    sintomas_livres: $livres_resultantes
    sinais_vitais  : $sinais_resultantes
    classificacao  : $avaliacao.classificacao
    prioridade_atual: $prioridade_final
    especialidade  : ($reavaliacao == null) ? null : $reavaliacao.especialidade
    senha_anterior : ($reavaliacao == null) ? null : $reavaliacao.senha_anterior
    senha          : ($reavaliacao == null) ? null : $reavaliacao.senha
    senha_alterada : ($reavaliacao == null) ? false : $reavaliacao.senha_alterada
  }

  guid = "XJ6U5MqK_6-Cg2920GUm4eZWp80"
}

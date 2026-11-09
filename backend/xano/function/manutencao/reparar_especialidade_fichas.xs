// Reparo único após a migração de `especialidade` na v1 (PR #30): a migração apagou as especialidades e a carga do
// direcionamento as recriou com IDs novos. Fichas confirmadas antes ficaram apontando para IDs que não existem mais,
// fora de qualquer fila. Este reparo reaponta cada ficha para a especialidade de mesma sigla, lida da senha
// (COR-ESP-NNN). Sem `aplicar`, só relata o que encontrou; com `aplicar`, corrige e audita em nome de `email`.
// Rodar pelo terminal: xano function run manutencao/reparar_especialidade_fichas (ver README do PR).
function "manutencao/reparar_especialidade_fichas" {
  description = "Lista (ou corrige, com aplicar=true) fichas, ligações e parâmetro que apontam para especialidades inexistentes."

  input {
    bool aplicar?=false
    // E-mail de um usuário ativo, para a auditoria das correções (obrigatório com aplicar=true).
    text email? filters=trim|lower
  }

  stack {
    db.query especialidade {
      return = {type: "list"}
    } as $especialidades

    var $ids_validos {
      value = $especialidades|map:$$.id
    }

    db.query ficha_atendimento {
      where = $db.ficha_atendimento.status in ["EM_TRIAGEM", "AGUARDANDO", "CHAMADO"] && ($db.ficha_atendimento.especialidade_atribuida_id != null || $db.ficha_atendimento.especialidade_sugerida_id != null)
      return = {type: "list"}
    } as $fichas

    var $afetadas { value = [] }

    foreach ($fichas) {
      each as $ficha {
        var $atribuida_valida {
          value = $ficha.especialidade_atribuida_id == null || ($ids_validos|in:$ficha.especialidade_atribuida_id)
        }
        var $sugerida_valida {
          value = $ficha.especialidade_sugerida_id == null || ($ids_validos|in:$ficha.especialidade_sugerida_id)
        }
        conditional {
          if (!$atribuida_valida || !$sugerida_valida) {
            var $partes {
              value = ($ficha.senha ?? "")|split:"-"
            }
            var $sigla {
              value = (($partes|count) == 3) ? ($partes|get:1:"") : ""
            }
            var $especialidade {
              value = $especialidades|find:($$.sigla == $sigla)
            }
            var $nova_id {
              value = ($especialidade == null) ? null : $especialidade.id
            }
            var.update $afetadas {
              value = $afetadas|push:{ficha_id: $ficha.id, status: $ficha.status, senha: $ficha.senha, atribuida_antiga: $ficha.especialidade_atribuida_id, sugerida_antiga: $ficha.especialidade_sugerida_id, sigla: $sigla, nova_especialidade_id: $nova_id}
            }
          }
        }
      }
    }

    // Ligações sintoma → especialidade e parâmetro padrão que apontem para IDs apagados (só relatório).
    db.query sintoma_especialidade {
      return = {type: "list"}
    } as $ligacoes

    var $ligacoes_orfas {
      value = $ligacoes|filter:(!($ids_validos|in:$$.especialidade_id))
    }

    db.get parametro {
      field_name = "chave"
      field_value = "ESPECIALIDADE_PADRAO"
    } as $parametro_padrao

    var $padrao_valido {
      value = $parametro_padrao != null && ($ids_validos|in:($parametro_padrao.valor|to_int))
    }

    var $sem_destino {
      value = $afetadas|filter:($$.nova_especialidade_id == null)
    }

    var $corrigidas { value = 0 }

    conditional {
      if ($input.aplicar) {
        precondition ($input.email != null && $input.email != "") {
          error_type = "inputerror"
          error = "Informe o e-mail de um usuário ativo para a auditoria (email=...)."
        }

        db.get usuario {
          field_name = "email"
          field_value = $input.email
        } as $usuario

        precondition ($usuario != null && $usuario.ativo) {
          error_type = "inputerror"
          error = "Usuário da auditoria não encontrado ou inativo."
        }

        db.transaction {
          stack {
            foreach ($afetadas) {
              each as $item {
                conditional {
                  if ($item.nova_especialidade_id != null) {
                    db.patch ficha_atendimento {
                      field_name = "id"
                      field_value = $item.ficha_id
                      data = {especialidade_atribuida_id: $item.nova_especialidade_id, especialidade_sugerida_id: $item.nova_especialidade_id}
                    } as $ficha_reparada

                    function.run "registrar_alteracao" {
                      input = {
                        usuario_id    : $usuario.id
                        tipo_evento   : "ESPECIALIDADE_REPARADA"
                        entidade      : "FICHA_ATENDIMENTO"
                        registro_id   : $item.ficha_id
                        valor_anterior: {especialidade_atribuida_id: $item.atribuida_antiga, especialidade_sugerida_id: $item.sugerida_antiga}
                        valor_novo    : {especialidade_atribuida_id: $item.nova_especialidade_id, especialidade_sugerida_id: $item.nova_especialidade_id}
                        justificativa : "Reparo após a migração de especialidade (PR #30): reapontada pela sigla da senha."
                      }
                    } as $auditoria

                    var.update $corrigidas { value = $corrigidas + 1 }
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  response = {
    aplicado                 : $input.aplicar == true
    fichas_afetadas          : $afetadas
    fichas_corrigidas        : $corrigidas
    fichas_sem_sigla_valida  : $sem_destino
    ligacoes_orfas           : $ligacoes_orfas|count
    especialidade_padrao_ok  : $padrao_valido
    especialidades_existentes: $especialidades|map:{id: $$.id, sigla: $$.sigla, nome: $$.nome}
  }
}

// Lê o estado de todas as filas e aplica as duas etapas da seleção sem reservar ficha.
// Obtém uma candidata por especialidade e escolhe a próxima para o médico.
function "fila/selecionar_atual" {
  input {
    int medico_id
  }

  stack {
    function.run "fila/cobertura_atual" as $cobertura
    var $medico {
      value = $cobertura.medicos|find:$$.id == $input.medico_id
    }

    precondition ($medico != null) {
      error_type = "inputerror"
      error = "MEDICO_INDISPONIVEL"
    }

    db.get parametro {
      field_name = "chave"
      field_value = "amarelas_por_ciclo"
    } as $param_amarelas

    db.get parametro {
      field_name = "chave"
      field_value = "azuis_por_ciclo"
    } as $param_azuis

    precondition ($param_amarelas != null && $param_azuis != null) {
      error_type = "inputerror"
      error = "PARAMETROS_NAO_CONFIGURADOS"
    }

    db.query especialidade {
      return = {type: "list"}
    } as $especialidades

    db.query ficha_atendimento {
      where = $db.ficha_atendimento.status == "AGUARDANDO"
      return = {type: "list"}
    } as $fichas

    db.query ciclo_fila {
      return = {type: "list"}
    } as $ciclos

    var $candidatas {
      value = []
    }

    foreach ($especialidades) {
      each as $especialidade {
        var $da_fila {
          value = $fichas|filter:$$.especialidade_atribuida_id == $especialidade.id
        }

        var $ciclo {
          value = $ciclos|find:$$.especialidade_id == $especialidade.id
        }

        var $posicao {
          value = ($ciclo == null) ? 1 : $ciclo.posicao
        }

        function.run "fila/proxima_ficha" {
          input = {
            fichas  : $da_fila
            posicao : $posicao
            amarelas: $param_amarelas.valor|to_int
            azuis   : $param_azuis.valor|to_int
          }
        } as $proxima

        conditional {
          if ($proxima.ficha != null) {
            var.update $candidatas {
              value = $candidatas
                |push:{especialidade_id: $especialidade.id, especialidade_nome: $especialidade.nome, descoberta: !($cobertura.especialidade_ids|some:$$ == $especialidade.id), ficha: $proxima.ficha, avanca_ciclo: $proxima.avancar_ciclo, proxima_posicao: $proxima.proxima_posicao, ciclo_id: ($ciclo == null) ? null : $ciclo.id}
            }
          }
        }
      }
    }

    db.query chamada {
      where = $db.chamada.medico_id == $medico.id && $db.chamada.tipo == "CHAMADA"
      sort = {created_at: "desc"}
      return = {type: "list"}
    } as $historico

    var $ultima_propria {
      value = null
    }

    foreach ($historico) {
      each as $evento {
        conditional {
          if ($ultima_propria == null) {
            db.get ficha_atendimento {
              field_name = "id"
              field_value = $evento.ficha_id
            } as $ficha_historica

            conditional {
              if ($ficha_historica != null && $medico.especialidade_ids|some:$$ == $ficha_historica.especialidade_atribuida_id) {
                var.update $ultima_propria {
                  value = $ficha_historica.especialidade_atribuida_id
                }
              }
            }
          }
        }
      }
    }

    function.run "fila/selecionar_entre_filas" {
      input = {
        candidatas             : $candidatas
        especialidades_proprias: $medico.especialidade_ids
        ultima_propria         : $ultima_propria
      }
    } as $selecao
  }

  response = {
    selecao   : $selecao
    medico    : $medico
    candidatas: $candidatas
  }

  guid = "ABkVoZGYPgF578TQweGh4vHL8BY"
}

// Destino atual da ficha (add-direcionamento-senha, D3): lê idade e sintomas do catálogo via avaliar_ficha,
// as ligações sintoma → especialidade ativa, a fila AGUARDANDO das candidatas, Pediatria e a especialidade padrão,
// e chama a regra pura escolher_destino. Só leitura: usada na prévia (GET) e na confirmação.
function "direcionamento/destino_da_ficha" {
  description = "Calcula a especialidade de destino da ficha e devolve também a avaliação da classificação."

  input {
    int ficha_id
  }

  stack {
    function.run "classificacao/avaliar_ficha" {
      input = {ficha_id: $input.ficha_id}
    } as $avaliacao

    db.query especialidade {
      where = $db.especialidade.ativo == true
      return = {type: "list"}
    } as $ativas

    var $ids_ativas {
      value = $ativas|map:$$.id
    }

    var $sintoma_ids {
      value = $avaliacao.sintomas|map:$$.id
    }

    db.query sintoma_especialidade {
      where = $db.sintoma_especialidade.sintoma_id in $sintoma_ids && $db.sintoma_especialidade.especialidade_id in $ids_ativas
      return = {type: "list"}
    } as $ligacoes

    var $sintomas_destino { value = [] }

    foreach ($avaliacao.sintomas) {
      each as $sintoma {
        var $ligadas {
          value = $ligacoes|filter:($$.sintoma_id == $sintoma.id)
        }
        conditional {
          if (($ligadas|count) > 0) {
            var $ids_ligados {
              value = $ligadas|map:$$.especialidade_id
            }
            var.update $sintomas_destino {
              value = $sintomas_destino|push:{pontuacao: $sintoma.pontuacao, especialidade_ids: $ids_ligados}
            }
          }
        }
      }
    }

    var $candidatas {
      value = ($ligacoes|map:$$.especialidade_id)|unique
    }

    db.query ficha_atendimento {
      where = $db.ficha_atendimento.status == "AGUARDANDO" && $db.ficha_atendimento.especialidade_atribuida_id in $candidatas
      return = {type: "list"}
    } as $aguardando

    var $filas { value = [] }

    foreach ($candidatas) {
      each as $especialidade_id {
        var $na_fila {
          value = $aguardando|filter:($$.especialidade_atribuida_id == $especialidade_id)
        }
        var $quantidade {
          value = $na_fila|count
        }
        var.update $filas {
          value = $filas|push:{especialidade_id: $especialidade_id, aguardando: $quantidade}
        }
      }
    }

    var $pediatria {
      value = $ativas|find:($$.sigla == "PED")
    }

    db.get parametro {
      field_name = "chave"
      field_value = "IDADE_MAXIMA_CRIANCA"
    } as $parametro_crianca

    db.get parametro {
      field_name = "chave"
      field_value = "ESPECIALIDADE_PADRAO"
    } as $parametro_padrao

    var $padrao { value = null }

    conditional {
      if ($parametro_padrao != null) {
        var.update $padrao {
          value = $ativas|find:($$.id == ($parametro_padrao.valor|to_int))
        }
      }
    }

    function.run "direcionamento/escolher_destino" {
      input = {
        idade               : $avaliacao.idade
        idade_maxima_crianca: ($parametro_crianca == null) ? null : ($parametro_crianca.valor|to_int)
        pediatria_id        : ($pediatria == null) ? null : $pediatria.id
        padrao_id           : ($padrao == null) ? null : $padrao.id
        sintomas            : $sintomas_destino
        filas               : $filas
      }
    } as $escolha

    var $especialidade {
      value = ($escolha.especialidade_id == null) ? null : ($ativas|find:($$.id == $escolha.especialidade_id))
    }
  }

  response = {
    especialidade_id: $escolha.especialidade_id
    motivo          : $escolha.motivo
    especialidade   : ($especialidade == null) ? null : {id: $especialidade.id, nome: $especialidade.nome, sigla: $especialidade.sigla}
    avaliacao       : $avaliacao
  }
  guid = "hSkE7BqK7a2hyJQeYDZRP20mqcU"
}

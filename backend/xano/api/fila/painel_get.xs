// Painel público da sala de espera (add-painel-publico, D2 e D3). Sem sessão e só de leitura: a resposta é montada
// campo a campo, sem nome, CPF, sintomas, sinais vitais ou identificação do Médico (RNF06, RN35). A Sala é a atual
// do Médico que chamou (sem mudança de schema). chamada_id e ticket_id são identificadores técnicos para o painel
// detectar chamada nova ou repetida.
// Chamada atual, últimas chamadas, ticket chamado na triagem e previsão por especialidade, para o painel público.
query painel verb=GET {
  api_group = "Fila"

  input {
    // Siglas separadas por vírgula (ex.: "CAR,CLI"); vazio = todas as especialidades ativas.
    text especialidades? filters=trim
  }

  stack {
    db.query especialidade {
      where = $db.especialidade.ativo == true
      sort = {id: "asc"}
      return = {type: "list"}
    } as $ativas

    var $siglas {
      value = []
    }

    conditional {
      if (($input.especialidades ?? "") != "") {
        var.update $siglas {
          value = ($input.especialidades|split:",")|map:($$|trim|to_upper)
        }
      }
    }

    // Siglas inexistentes ou inativas são ignoradas; nenhuma válida é erro, para o painel avisar.
    var $selecionadas {
      value = (($siglas|count) == 0) ? $ativas : ($ativas|filter:($siglas|in:$$.sigla))
    }

    precondition (($selecionadas|count) > 0) {
      error_type = "inputerror"
      error = "FILTRO_SEM_ESPECIALIDADE_ATIVA"
    }

    var $ids_especialidades {
      value = $selecionadas|map:$$.id
    }

    // Chamadas médicas mais recentes das especialidades exibidas; 30 bastam para achar 5 senhas distintas.
    // Com join, só o que está no eval vem com certeza; a ordem usa o horário da chamada, não o da ficha.
    db.query chamada {
      join = {
        ficha_atendimento: {
          table: "ficha_atendimento"
          where: $db.chamada.ficha_id == $db.ficha_atendimento.id
        }
      }

      where = $db.chamada.tipo == "CHAMADA" && $db.ficha_atendimento.especialidade_atribuida_id in $ids_especialidades
      sort = {chamado_em: "desc"}
      eval = {
        senha           : $db.ficha_atendimento.senha
        cor             : $db.ficha_atendimento.prioridade_atual
        especialidade_id: $db.ficha_atendimento.especialidade_atribuida_id
        tentativa       : $db.chamada.tentativa
        chamado_em      : $db.chamada.created_at
      }

      return = {
        type  : "list"
        paging: {page: 1, per_page: 30, metadata: false}
      }
    } as $chamadas

    var $ids_medicos {
      value = ($chamadas|map:$$.medico_id)|unique
    }

    db.query medico {
      where = $db.medico.id in $ids_medicos
      return = {type: "list"}
    } as $medicos

    var $ids_salas {
      value = ($medicos|map:$$.sala_id)|unique
    }

    db.query sala {
      where = $db.sala.id in $ids_salas && $db.sala.ativo == true
      return = {type: "list"}
    } as $salas

    // A primeira é a chamada atual (inclusive repetição); as seguintes, sem repetir senha, são as últimas.
    var $vistas {
      value = []
    }

    var $itens {
      value = []
    }

    foreach ($chamadas) {
      each as $c {
        conditional {
          if (($itens|count) < 5 && !($vistas|in:$c.senha)) {
            var $medico_c {
              value = $medicos|find:($$.id == $c.medico_id)
            }

            var $sala_c {
              value = ($medico_c == null || $medico_c.sala_id == null) ? null : ($salas|find:($$.id == $medico_c.sala_id))
            }

            var $especialidade_c {
              value = $selecionadas|find:($$.id == $c.especialidade_id)
            }

            // Ternário fora do objeto: dentro dele, as chaves seguintes se perdiam na resposta.
            var $nome_sala {
              value = ($sala_c == null) ? null : $sala_c.nome
            }

            var.update $itens {
              value = $itens
                |push:```
                  {
                    chamada_id   : $c.id
                    senha        : $c.senha
                    cor          : $c.cor
                    especialidade: $especialidade_c.nome
                    sigla        : $especialidade_c.sigla
                    sala         : $nome_sala
                    tentativa    : $c.tentativa
                    chamado_em   : $c.chamado_em
                  }
                  ```
            }

            var.update $vistas {
              value = $vistas|push:$c.senha
            }
          }
        }
      }
    }

    var $atual {
      value = (($itens|count) == 0) ? null : ($itens|first)
    }

    var $ultimas {
      value = ($itens|slice:1:4)|map:{senha: $$.senha, cor: $$.cor, especialidade: $$.especialidade, sigla: $$.sigla, sala: $$.sala, chamado_em: $$.chamado_em}
    }

    // A triagem é comum a todas as especialidades: o último ticket chamado aparece em qualquer painel.
    db.query ticket_pre_triagem {
      where = $db.ticket_pre_triagem.chamado_em != null
      sort = {chamado_em: "desc"}
      return = {type: "single"}
    } as $ticket

    var $previsoes {
      value = []
    }

    foreach ($selecionadas) {
      each as $esp {
        function.run "fila/previsao_especialidade" {
          input = {especialidade_id: $esp.id}
        } as $senhas

        var.update $previsoes {
          value = $previsoes
            |push:{especialidade: $esp.nome, sigla: $esp.sigla, senhas: $senhas}
        }
      }
    }
  }

  response = {
    atual    : $atual
    ultimas  : $ultimas
    triagem  : ($ticket == null) ? null : {ticket_id: $ticket.id, tipo: $ticket.tipo, numero: $ticket.numero, tentativa: $ticket.tentativas, chamado_em: $ticket.chamado_em}
    previsoes: $previsoes
    gerado_em: now
  }

  guid = "pdRVkMNt9YzGyxp63l08kPNasYg"
}
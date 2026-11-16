// Correção local do GET existente (remoto 4128628); não criar outra rota.
// Consulta administrativa: nenhuma escrita, reserva ou avanço persistido de ciclo.
query "admin/fila-geral" verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int? especialidade_id?
    text? cor? filters=trim|upper
    text? status? filters=trim|upper
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    var $agora { value = now }
    var $cor { value = $input.cor ?? "" }
    var $status { value = $input.status ?? "" }
    precondition (["", "VERMELHA", "AMARELA", "AZUL"]|in:$cor) {
      error_type = "inputerror"
      error = "COR_INVALIDA"
    }
    precondition (["", "EM_TRIAGEM", "AGUARDANDO", "CHAMADO"]|in:$status) {
      error_type = "inputerror"
      error = "STATUS_INVALIDO"
    }
    precondition ($input.especialidade_id == null || $input.especialidade_id >= 0) {
      error_type = "inputerror"
      error = "ESPECIALIDADE_INVALIDA"
    }

    db.query ficha_atendimento {
      where = $db.ficha_atendimento.status in ["EM_TRIAGEM", "AGUARDANDO", "CHAMADO"]
      sort = {chegada_em: "asc", id: "asc"}
      return = {type: "list"}
    } as $fichas

    // Inclui inativas com fichas preservadas; projeção mantém o contrato publicado.
    db.query especialidade {
      sort = {nome: "asc", id: "asc"}
      return = {type: "list"}
    } as $especialidades

    var $medico_ids {
      value = $fichas|filter:($$.status == "CHAMADO" && $$.medico_chamada_id != null)|map:$$.medico_chamada_id|unique
    }
    var $medicos { value = [] }
    conditional {
      if (($medico_ids|count) > 0) {
        db.query medico {
          where = $db.medico.id in $medico_ids
          return = {type: "list"}
        } as $medicos_encontrados
        var.update $medicos { value = $medicos_encontrados }
      }
    }
    var $usuario_ids { value = $medicos|map:$$.usuario_id|unique }
    var $usuarios { value = [] }
    conditional {
      if (($usuario_ids|count) > 0) {
        db.query usuario {
          where = $db.usuario.id in $usuario_ids
          return = {type: "list"}
        } as $usuarios_encontrados
        var.update $usuarios { value = $usuarios_encontrados }
      }
    }
    var $especialidade_ids { value = $fichas|map:$$.especialidade_atribuida_id|unique }
    db.query ciclo_fila {
      where = $db.ciclo_fila.especialidade_id in $especialidade_ids
      return = {type: "list"}
    } as $ciclos

    db.get parametro {
      field_name = "chave"
      field_value = "amarelas_por_ciclo"
    } as $param_amarelas
    db.get parametro {
      field_name = "chave"
      field_value = "azuis_por_ciclo"
    } as $param_azuis
    var $amarelas { value = ($param_amarelas == null) ? 0 : ($param_amarelas.valor|to_int) }
    var $azuis { value = ($param_azuis == null) ? 0 : ($param_azuis.valor|to_int) }
    var $avisos { value = [] }
    conditional {
      if ($param_amarelas == null || $param_azuis == null) {
        var.update $avisos { value = $avisos|push:"PARAMETROS_NAO_CONFIGURADOS" }
      }
      elseif ($amarelas <= 0 || $azuis <= 0) {
        var.update $avisos { value = $avisos|push:"CICLO_FILA_INVALIDO" }
      }
    }

    var $ordenadas { value = [] }
    foreach ($especialidades) {
      each as $esp {
        var $aguardando {
          value = $fichas|filter:($$.status == "AGUARDANDO" && $$.especialidade_atribuida_id == $esp.id)
        }
        var $ciclo { value = $ciclos|find:($$.especialidade_id == $esp.id) }
        // Mesmo ponto de partida da previsão publicada; nunca grava ciclo.
        var $posicao { value = ($ciclo == null) ? 1 : $ciclo.posicao }
        conditional {
          if ($amarelas > 0 && $azuis > 0 && $posicao != null && $posicao >= 1 && $posicao <= ($amarelas + $azuis)) {
            // Não entregar cor nula à seleção (null == null poderia escolhê-la).
            // A inclusão de segurança preserva os dados inconsistentes sem posição.
            var $restantes {
              value = $aguardando|filter:($$.prioridade_atual == "VERMELHA" || $$.prioridade_atual == "AMARELA" || $$.prioridade_atual == "AZUL")
            }
            var $ordem { value = 0 }
            // Itera o conjunto original, não um limite de 20 nem a lista mutável.
            foreach ($aguardando) {
              each as $ignorado {
                conditional {
                  if (($restantes|count) > 0) {
                    function.run "fila/proxima_ficha" {
                      input = {fichas: $restantes, posicao: $posicao, amarelas: $amarelas, azuis: $azuis}
                    } as $escolha
                    conditional {
                      if ($escolha.ficha != null) {
                        var.update $ordem { value = $ordem + 1 }
                        var.update $ordenadas {
                          value = $ordenadas|push:{ficha: $escolha.ficha, ordem_prevista: $ordem}
                        }
                        var.update $restantes { value = $restantes|filter:($$.id != $escolha.ficha.id) }
                        var.update $posicao { value = $escolha.proxima_posicao }
                      }
                      else {
                        // Dado sem cor elegível: a inclusão de segurança abaixo o preserva.
                        var.update $restantes { value = [] }
                      }
                    }
                  }
                }
              }
            }
          }
          elseif (($aguardando|count) > 0) {
            var.update $avisos { value = $avisos|push:"CICLO_FILA_INVALIDO" }
          }
        }
      }
    }

    // Inclui exatamente uma vez TODAS as fichas ainda não previstas: triagem,
    // chamadas, sem catálogo correspondente e aguardando com dados inconsistentes.
    foreach ($fichas) {
      each as $ficha {
        var $incluida { value = $ordenadas|find:($$.ficha.id == $ficha.id) }
        conditional {
          if ($incluida == null) {
            var.update $ordenadas { value = $ordenadas|push:{ficha: $ficha, ordem_prevista: null} }
          }
        }
      }
    }

    var $lista { value = [] }
    foreach ($ordenadas) {
      each as $entrada {
        var $ficha { value = $entrada.ficha }
        // Filtrar DEPOIS da previsão não muda as posições do ciclo completo.
        conditional {
          if (($input.especialidade_id == null || $input.especialidade_id == 0 || $ficha.especialidade_atribuida_id == $input.especialidade_id) && ($cor == "" || $ficha.prioridade_atual == $cor) && ($status == "" || $ficha.status == $status)) {
            var $esp { value = $especialidades|find:($$.id == $ficha.especialidade_atribuida_id) }
            var $medico {
              value = ($ficha.status == "CHAMADO") ? ($medicos|find:($$.id == $ficha.medico_chamada_id)) : null
            }
            var $pessoa { value = ($medico == null) ? null : ($usuarios|find:($$.id == $medico.usuario_id)) }
            var $minutos { value = ($ficha.chegada_em == null) ? null : ((($agora - $ficha.chegada_em) / 60000)|to_int) }
            var.update $lista {
              value = $lista|push:{
                id: $ficha.id,
                status: $ficha.status,
                senha: $ficha.senha,
                cor: $ficha.prioridade_atual,
                condicao_prioritaria: $ficha.condicao_prioritaria,
                especialidade_id: $ficha.especialidade_atribuida_id,
                especialidade: ($esp == null) ? null : $esp.nome,
                chegada_em: $ficha.chegada_em,
                espera_minutos: ($minutos != null && $minutos < 0) ? 0 : $minutos,
                posicao: $entrada.ordem_prevista,
                consultado_em: $agora,
                avisos: $avisos|unique,
                medico: ($pessoa == null) ? null : $pessoa.nome,
                medico_id: ($ficha.status == "CHAMADO") ? $ficha.medico_chamada_id : null,
                tentativa: ($ficha.status == "CHAMADO") ? $ficha.tentativas_chamada : null,
                oportunidade: ($ficha.status == "CHAMADO") ? $ficha.oportunidade : null
              }
            }
          }
        }
      }
    }
  }

  // Mantém a lista simples e os campos publicados; metadados por item são aditivos.
  response = $lista
}

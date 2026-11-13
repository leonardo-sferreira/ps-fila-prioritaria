// Recebe uma candidata já ordenada internamente por especialidade.
// A cobertura e a lista de especialidades próprias são calculadas pelo backend antes desta função.
// Escolhe entre própria, descoberta e outra coberta pela política da Rev. 2.1.
function "fila/selecionar_entre_filas" {
  input {
    json candidatas
    json especialidades_proprias
    int? ultima_propria?
  }

  stack {
    var $vermelha_propria {
      value = null
    }

    var $propria_rodizio {
      value = null
    }

    var $propria_inicio {
      value = null
    }

    var $descoberta {
      value = null
    }

    var $coberta {
      value = null
    }

    foreach ($input.candidatas) {
      each as $candidata {
        conditional {
          if ($candidata.ficha != null) {
            var $eh_propria {
              value = $input.especialidades_proprias|some:$$ == $candidata.especialidade_id
            }

            var $cor {
              value = $candidata.ficha.prioridade_atual
            }

            var $grau {
              value = ($cor == "VERMELHA") ? 3 : (($cor == "AMARELA") ? 2 : 1)
            }

            var $prioritaria {
              value = $candidata.ficha.condicao_prioritaria != null && $candidata.ficha.condicao_prioritaria != "NENHUMA"
            }

            var $ordem {
              value = $candidata.ficha.fila_em ?? $candidata.ficha.chegada_em
            }

            conditional {
              if ($eh_propria && $cor == "VERMELHA") {
                conditional {
                  if ($vermelha_propria == null || $candidata.ficha.chegada_em < $vermelha_propria.ficha.chegada_em || ($candidata.ficha.chegada_em == $vermelha_propria.ficha.chegada_em && $candidata.ficha.id < $vermelha_propria.ficha.id)) {
                    var.update $vermelha_propria {
                      value = $candidata
                    }
                  }
                }
              }

              elseif ($eh_propria) {
                conditional {
                  if ($propria_inicio == null || $candidata.especialidade_id < $propria_inicio.especialidade_id) {
                    var.update $propria_inicio {
                      value = $candidata
                    }
                  }
                }

                conditional {
                  if (($input.ultima_propria == null || $candidata.especialidade_id > $input.ultima_propria) && ($propria_rodizio == null || $candidata.especialidade_id < $propria_rodizio.especialidade_id)) {
                    var.update $propria_rodizio {
                      value = $candidata
                    }
                  }
                }
              }

              elseif ($candidata.descoberta) {
                var $melhor_grau {
                  value = ($descoberta == null) ? 0 : (($descoberta.ficha.prioridade_atual == "VERMELHA") ? 3 : (($descoberta.ficha.prioridade_atual == "AMARELA") ? 2 : 1))
                }

                var $melhor_prioritaria {
                  value = ($descoberta != null) && $descoberta.ficha.condicao_prioritaria != null && $descoberta.ficha.condicao_prioritaria != "NENHUMA"
                }

                var $melhor_ordem {
                  value = ($descoberta == null) ? null : ($descoberta.ficha.fila_em ?? $descoberta.ficha.chegada_em)
                }

                conditional {
                  if ($descoberta == null || $grau > $melhor_grau || ($grau == $melhor_grau && $prioritaria && !$melhor_prioritaria) || ($grau == $melhor_grau && $prioritaria == $melhor_prioritaria && ($ordem < $melhor_ordem || ($ordem == $melhor_ordem && $candidata.ficha.id < $descoberta.ficha.id)))) {
                    var.update $descoberta {
                      value = $candidata
                    }
                  }
                }
              }

              else {
                var $melhor_grau {
                  value = ($coberta == null) ? 0 : (($coberta.ficha.prioridade_atual == "VERMELHA") ? 3 : (($coberta.ficha.prioridade_atual == "AMARELA") ? 2 : 1))
                }

                var $melhor_prioritaria {
                  value = ($coberta != null) && $coberta.ficha.condicao_prioritaria != null && $coberta.ficha.condicao_prioritaria != "NENHUMA"
                }

                var $melhor_ordem {
                  value = ($coberta == null) ? null : ($coberta.ficha.fila_em ?? $coberta.ficha.chegada_em)
                }

                conditional {
                  if ($coberta == null || $grau > $melhor_grau || ($grau == $melhor_grau && $prioritaria && !$melhor_prioritaria) || ($grau == $melhor_grau && $prioritaria == $melhor_prioritaria && ($ordem < $melhor_ordem || ($ordem == $melhor_ordem && $candidata.ficha.id < $coberta.ficha.id)))) {
                    var.update $coberta {
                      value = $candidata
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    var $propria {
      value = $vermelha_propria ?? $propria_rodizio ?? $propria_inicio
    }

    var $escolha {
      value = $propria
    }

    var $origem {
      value = ($propria == null) ? null : "PROPRIA"
    }

    var $grau_propria {
      value = ($propria == null) ? 0 : (($propria.ficha.prioridade_atual == "VERMELHA") ? 3 : (($propria.ficha.prioridade_atual == "AMARELA") ? 2 : 1))
    }

    var $grau_descoberta {
      value = ($descoberta == null) ? 0 : (($descoberta.ficha.prioridade_atual == "VERMELHA") ? 3 : (($descoberta.ficha.prioridade_atual == "AMARELA") ? 2 : 1))
    }

    conditional {
      if ($descoberta != null && ($propria == null || $grau_descoberta > $grau_propria)) {
        var.update $escolha {
          value = $descoberta
        }

        var.update $origem {
          value = "DESCOBERTA"
        }
      }

      elseif ($propria == null && $coberta != null) {
        var.update $escolha {
          value = $coberta
        }

        var.update $origem {
          value = "COBERTA"
        }
      }
    }
  }

  response = {candidata: $escolha, origem: $origem}
  guid = "PvBEMV23CxS2PbRNmuYDx1Nwe4Q"
}

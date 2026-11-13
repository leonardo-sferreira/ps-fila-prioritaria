// Seleção pura dentro de uma especialidade. A chamada e a previsão usam esta mesma função.
// Escolhe a próxima ficha AGUARDANDO e informa se o ciclo amarelo/azul avança.
function "fila/proxima_ficha" {
  input {
    json fichas
    int posicao
    int amarelas
    int azuis
  }

  stack {
    precondition ($input.amarelas > 0 && $input.azuis > 0 && $input.posicao >= 1 && $input.posicao <= ($input.amarelas + $input.azuis)) {
      error_type = "inputerror"
      error = "CICLO_FILA_INVALIDO"
    }

    var $vermelha {
      value = false
    }

    var $amarela {
      value = false
    }

    var $azul {
      value = false
    }

    foreach ($input.fichas) {
      each as $item {
        conditional {
          if ($item.status == "AGUARDANDO" && $item.prioridade_atual == "VERMELHA") {
            var.update $vermelha {
              value = true
            }
          }

          elseif ($item.status == "AGUARDANDO" && $item.prioridade_atual == "AMARELA") {
            var.update $amarela {
              value = true
            }
          }

          elseif ($item.status == "AGUARDANDO" && $item.prioridade_atual == "AZUL") {
            var.update $azul {
              value = true
            }
          }
        }
      }
    }

    var $prevista {
      value = ($input.posicao <= $input.amarelas) ? "AMARELA" : "AZUL"
    }

    var $cor {
      value = null
    }

    conditional {
      if ($vermelha) {
        var.update $cor {
          value = "VERMELHA"
        }
      }

      elseif ($prevista == "AMARELA" && $amarela) {
        var.update $cor {
          value = "AMARELA"
        }
      }

      elseif ($prevista == "AZUL" && $azul) {
        var.update $cor {
          value = "AZUL"
        }
      }

      elseif ($amarela) {
        var.update $cor {
          value = "AMARELA"
        }
      }

      elseif ($azul) {
        var.update $cor {
          value = "AZUL"
        }
      }
    }

    var $melhor {
      value = null
    }

    var $melhor_prioritaria {
      value = false
    }

    var $melhor_ordem {
      value = null
    }

    foreach ($input.fichas) {
      each as $item {
        conditional {
          if ($item.status == "AGUARDANDO" && $item.prioridade_atual == $cor) {
            var $prioritaria {
              value = $item.condicao_prioritaria != null && $item.condicao_prioritaria != "NENHUMA"
            }

            var $ordem {
              value = $item.fila_em ?? $item.chegada_em
            }

            conditional {
              if ($melhor == null || ($prioritaria && !$melhor_prioritaria) || ($prioritaria == $melhor_prioritaria && ($ordem < $melhor_ordem || ($ordem == $melhor_ordem && $item.id < $melhor.id)))) {
                var.update $melhor {
                  value = $item
                }

                var.update $melhor_prioritaria {
                  value = $prioritaria
                }

                var.update $melhor_ordem {
                  value = $ordem
                }
              }
            }
          }
        }
      }
    }

    var $avancar {
      value = $melhor != null && $cor != "VERMELHA" && $cor == $prevista
    }

    var $proxima_posicao {
      value = $input.posicao
    }

    conditional {
      if ($avancar) {
        var.update $proxima_posicao {
          value = ($input.posicao % ($input.amarelas + $input.azuis)) + 1
        }
      }
    }
  }

  response = {
    ficha          : $melhor
    cor            : $cor
    avancar_ciclo  : $avancar
    proxima_posicao: $proxima_posicao
  }

  test "vermelha tardia precede amarela sem avançar ciclo" {
    input = {
      fichas  : [{id: 1, status: "AGUARDANDO", prioridade_atual: "AMARELA", condicao_prioritaria: "NENHUMA", chegada_em: 100, fila_em: 100}, {id: 2, status: "AGUARDANDO", prioridade_atual: "VERMELHA", condicao_prioritaria: "NENHUMA", chegada_em: 200, fila_em: 200}]
      posicao : 2
      amarelas: 2
      azuis   : 1
    }

    expect.to_equal ($response.ficha.id) {
      value = 2
    }

    expect.to_equal ($response.proxima_posicao) {
      value = 2
    }
  }

  test "cor alternativa não avança ciclo" {
    input = {
      fichas  : [{id: 1, status: "AGUARDANDO", prioridade_atual: "AZUL", condicao_prioritaria: "NENHUMA", chegada_em: 100, fila_em: 100}]
      posicao : 1
      amarelas: 2
      azuis   : 1
    }

    expect.to_equal ($response.ficha.id) {
      value = 1
    }

    expect.to_equal ($response.proxima_posicao) {
      value = 1
    }
  }

  test "condição prioritária vence chegada dentro da cor" {
    input = {
      fichas  : [{id: 1, status: "AGUARDANDO", prioridade_atual: "AZUL", condicao_prioritaria: "NENHUMA", chegada_em: 100, fila_em: 100}, {id: 2, status: "AGUARDANDO", prioridade_atual: "AZUL", condicao_prioritaria: "IDOSO", chegada_em: 200, fila_em: 200}]
      posicao : 3
      amarelas: 2
      azuis   : 1
    }

    expect.to_equal ($response.ficha.id) {
      value = 2
    }
  }

  test "reentrada usa ordem efetiva" {
    input = {
      fichas  : [{id: 1, status: "AGUARDANDO", prioridade_atual: "AMARELA", condicao_prioritaria: "NENHUMA", chegada_em: 100, fila_em: 300}, {id: 2, status: "AGUARDANDO", prioridade_atual: "AMARELA", condicao_prioritaria: "NENHUMA", chegada_em: 200, fila_em: 200}]
      posicao : 1
      amarelas: 2
      azuis   : 1
    }

    expect.to_equal ($response.ficha.id) {
      value = 2
    }
  }

  guid = "ZonecTuQitotWnsqXlUsS-6gaJk"
}

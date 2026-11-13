// Simula chamadas sem alterar ficha, ciclo ou histórico.
// Prevê as próximas senhas pela mesma seleção usada na chamada real.
function "fila/prever_fila" {
  input {
    json fichas
    int posicao
    int amarelas
    int azuis
    int limite
  }

  stack {
    precondition ($input.limite >= 1 && $input.limite <= 20) {
      error_type = "inputerror"
      error = "TAMANHO_PREVISAO_INVALIDO"
    }

    var $restantes {
      value = $input.fichas
    }

    var $posicao {
      value = $input.posicao
    }

    var $itens {
      value = []
    }

    foreach ((1..$input.limite)) {
      each as $indice {
        function.run "fila/proxima_ficha" {
          input = {
            fichas  : $restantes
            posicao : $posicao
            amarelas: $input.amarelas
            azuis   : $input.azuis
          }
        } as $escolha

        conditional {
          if ($escolha.ficha != null) {
            var.update $itens {
              value = $itens
                |push:{senha: $escolha.ficha.senha, cor: $escolha.cor}
            }

            var.update $restantes {
              value = $restantes|filter:$$.id != $escolha.ficha.id
            }

            var.update $posicao {
              value = $escolha.proxima_posicao
            }
          }
        }
      }
    }
  }

  response = $itens

  test "três fichas retornam três senhas sem dados pessoais" {
    input = {
      fichas  : [{id: 1, status: "AGUARDANDO", prioridade_atual: "AMARELA", condicao_prioritaria: "NENHUMA", chegada_em: 1, senha: "A-CAR-001", nome: "Privado"}, {id: 2, status: "AGUARDANDO", prioridade_atual: "AMARELA", condicao_prioritaria: "NENHUMA", chegada_em: 2, senha: "A-CAR-002"}, {id: 3, status: "AGUARDANDO", prioridade_atual: "AZUL", condicao_prioritaria: "NENHUMA", chegada_em: 3, senha: "B-CAR-003"}]
      posicao : 1
      amarelas: 2
      azuis   : 1
      limite  : 5
    }

    expect.to_equal ($response) {
      value = [
        {senha: "A-CAR-001", cor: "AMARELA"}
        {senha: "A-CAR-002", cor: "AMARELA"}
        {senha: "B-CAR-003", cor: "AZUL"}
      ]
    }
  }

  test "limite um retorna apenas a proxima senha" {
    input = {
      fichas: [{id: 1, status: "AGUARDANDO", prioridade_atual: "AMARELA", condicao_prioritaria: "NENHUMA", chegada_em: 1, fila_em: 1, senha: "A-CAR-001"}, {id: 2, status: "AGUARDANDO", prioridade_atual: "AMARELA", condicao_prioritaria: "NENHUMA", chegada_em: 2, fila_em: 2, senha: "A-CAR-002"}, {id: 3, status: "AGUARDANDO", prioridade_atual: "AZUL", condicao_prioritaria: "NENHUMA", chegada_em: 3, fila_em: 3, senha: "B-CAR-003"}]
      posicao: 1
      amarelas: 2
      azuis: 1
      limite: 1
    }
    expect.to_equal ($response) {
      value = [{senha: "A-CAR-001", cor: "AMARELA"}]
    }
  }

  test "nova Vermelha aparece primeiro sem perder ciclo" {
    input = {
      fichas: [{id: 1, status: "AGUARDANDO", prioridade_atual: "AMARELA", condicao_prioritaria: "NENHUMA", chegada_em: 1, fila_em: 1, senha: "A-CAR-001"}, {id: 2, status: "AGUARDANDO", prioridade_atual: "VERMELHA", condicao_prioritaria: "NENHUMA", chegada_em: 2, fila_em: 2, senha: "V-CAR-002"}]
      posicao: 2
      amarelas: 2
      azuis: 1
      limite: 2
    }
    expect.to_equal ($response) {
      value = [{senha: "V-CAR-002", cor: "VERMELHA"}, {senha: "A-CAR-001", cor: "AMARELA"}]
    }
  }

  test "limite zero e recusado" {
    input = {fichas: [], posicao: 1, amarelas: 2, azuis: 1, limite: 0}
    expect.to_throw
  }

  test "limite vinte e um e recusado" {
    input = {fichas: [], posicao: 1, amarelas: 2, azuis: 1, limite: 21}
    expect.to_throw
  }

  guid = "2GHWqk9TvNgi-M_2t0mGbZwZxm4"
}

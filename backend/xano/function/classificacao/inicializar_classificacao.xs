// Carga idempotente dos parâmetros e das faixas de sinais vitais da classificação
// (add-classificacao-prioridade, D2). Faixas da Rev. 2.1, §21.2 e §21.3: extremos inclusivos,
// null = limite aberto. Faixas só são inseridas com a tabela vazia, para não sobrescrever ajustes do ADM.
function "classificacao/inicializar_classificacao" {
  description = "Cria os parâmetros e as faixas de sinais vitais da classificação, se ainda não existirem."
  input {}
  stack {
    foreach ([{chave: "LIMIAR_AMARELA", valor: "5"}, {chave: "LIMIAR_VERMELHA", valor: "10"}, {chave: "IDADE_MINIMA_TABELA_ADULTA", valor: "16"}, {chave: "IDADE_MINIMA_IDOSO", valor: "60"}, {chave: "IDADE_MAXIMA_CRIANCA", valor: "11"}]) {
      each as $padrao {
        db.get parametro {
          field_name = "chave"
          field_value = $padrao.chave
        } as $existente
        conditional {
          if ($existente == null) {
            db.add parametro {
              data = {chave: $padrao.chave, valor: $padrao.valor, tipo: "INTEIRO"}
            } as $criado
          }
        }
      }
    }

    db.query faixa_sinal_vital {
      return = {type: "count"}
    } as $faixas_existentes

    conditional {
      if ($faixas_existentes == 0) {
        function.run "classificacao/faixas_padrao" {
          input = {}
        } as $padrao
        foreach ($padrao.faixas) {
          each as $faixa {
            db.add faixa_sinal_vital {
              data = {parametro: $faixa.parametro, minimo: $faixa.minimo, maximo: $faixa.maximo, pontos: $faixa.pontos, condicao_gravidade: $faixa.condicao_gravidade}
            } as $faixa_criada
          }
        }
      }
    }

    db.query faixa_sinal_vital {
      return = {type: "count"}
    } as $total_faixas
  }
  response = {faixas: $total_faixas}

  test "carrega as 30 faixas da Rev. 2.1 sem duplicar" {
    input = {}
    expect.to_equal ($response.faixas) {
      value = 30
    }
  }
  guid = "mnJzdEWpYvdieFzRJEb9b_yrlrw"
}

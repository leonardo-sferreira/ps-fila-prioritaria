// Regra pura da classificação (add-classificacao-prioridade, D3): não acessa o banco.
// Escore = soma dos sintomas distintos (catálogo + digitados, 1–3) + pontos dos sinais vitais (0–3) pelas faixas.
// Vermelha se qualquer item tiver 3 pontos; senão Azul abaixo de LIMIAR_AMARELA, Amarela abaixo de LIMIAR_VERMELHA,
// Vermelha a partir dele. Dado ausente não vira zero: entra em `pendencias` e a prioridade fica null.
// Tabela adulta só para idade >= IDADE_MINIMA_TABELA_ADULTA e não gestante (Rev. 2.1, §21.1).
function "classificacao/pontuar" {
  description = "Calcula pontos dos sinais vitais, escore, item crítico, prioridade calculada, condição prioritária e pendências."

  input {
    // pa_sistolica, fc, fr, temperatura, spo2, glicemia, glicemia_sinais_gravidade (null = não medido).
    json sinais
    bool gestante?=false
    // Idade na data de chegada; null quando desconhecida.
    int? idade?
    // Pontos de cada sintoma distinto da ficha (catálogo e digitados).
    json? pontos_sintomas?
    bool tem_observacao?=false
    // LIMIAR_AMARELA, LIMIAR_VERMELHA, IDADE_MINIMA_TABELA_ADULTA, IDADE_MINIMA_IDOSO, IDADE_MAXIMA_CRIANCA.
    json parametros
    // Faixas de faixa_sinal_vital. Lista vazia bloqueia o cálculo (FAIXA_NAO_CONFIGURADA).
    json? faixas?
    // Só para os testes: usa faixas_padrao no lugar de `faixas`. O Xano converte [] em null,
    // então "faixas ausentes" não pode significar "usar o padrão".
    bool faixas_padrao?=false
  }

  stack {
    var $pendencias { value = [] }
    var $sinais { value = $input.sinais }
    var $pontos_sintomas { value = $input.pontos_sintomas ?? [] }

    var $faixas { value = $input.faixas ?? [] }
    conditional {
      if ($input.faixas_padrao) {
        function.run "classificacao/faixas_padrao" {
          input = {}
        } as $faixas_padrao
        var.update $faixas { value = $faixas_padrao.faixas }
      }
    }

    var $limiar_amarela { value = $input.parametros|get:"LIMIAR_AMARELA":null }
    var $limiar_vermelha { value = $input.parametros|get:"LIMIAR_VERMELHA":null }
    var $idade_adulta { value = $input.parametros|get:"IDADE_MINIMA_TABELA_ADULTA":null }
    var $idade_idoso { value = $input.parametros|get:"IDADE_MINIMA_IDOSO":null }
    var $idade_crianca { value = $input.parametros|get:"IDADE_MAXIMA_CRIANCA":null }

    conditional {
      if ($limiar_amarela == null || $limiar_vermelha == null || $idade_adulta == null || $idade_idoso == null || $idade_crianca == null) {
        var.update $pendencias { value = $pendencias|push:"PARAMETRO_NAO_CONFIGURADO" }
      }
    }

    // Condição prioritária: gestante, depois idoso, depois criança. Não soma pontos nem muda a cor.
    var $condicao { value = "NENHUMA" }
    conditional {
      if ($input.gestante) {
        var.update $condicao { value = "GESTANTE" }
      }
      elseif ($input.idade != null && $idade_idoso != null && $input.idade >= $idade_idoso) {
        var.update $condicao { value = "IDOSO" }
      }
      elseif ($input.idade != null && $idade_crianca != null && $input.idade <= $idade_crianca) {
        var.update $condicao { value = "CRIANCA" }
      }
    }

    var $escore_sintomas { value = $pontos_sintomas|reduce:$$ + $result:0 }
    var $critico { value = $pontos_sintomas|some:$$ == 3 }

    conditional {
      if (($pontos_sintomas|count) == 0 && !$input.tem_observacao) {
        var.update $pendencias { value = $pendencias|push:"SEM_SINTOMA_OU_OBSERVACAO" }
      }
    }

    var $tabela_adulta { value = !$input.gestante && $input.idade != null && $idade_adulta != null && $input.idade >= $idade_adulta }
    conditional {
      if (!$tabela_adulta) {
        var.update $pendencias { value = $pendencias|push:"TABELA_ADULTA_NAO_APLICAVEL" }
      }
    }

    var $pontos_sinais { value = {PA_SISTOLICA: null, FC: null, FR: null, TEMPERATURA: null, SPO2: null, GLICEMIA: null} }
    var $escore_sinais { value = 0 }

    conditional {
      if ($tabela_adulta) {
        foreach ([{parametro: "PA_SISTOLICA", campo: "pa_sistolica"}, {parametro: "FC", campo: "fc"}, {parametro: "FR", campo: "fr"}, {parametro: "TEMPERATURA", campo: "temperatura"}, {parametro: "SPO2", campo: "spo2"}]) {
          each as $item {
            var $valor { value = $sinais|get:$item.campo:null }
            conditional {
              if ($valor == null) {
                var.update $pendencias { value = $pendencias|push:($item.parametro ~ "_NAO_INFORMADO") }
              }
              else {
                var $faixa {
                  value = $faixas|find:($$.parametro == $item.parametro && ($$.minimo == null || $valor >= $$.minimo) && ($$.maximo == null || $valor <= $$.maximo))
                }
                conditional {
                  if ($faixa == null) {
                    var.update $pendencias { value = $pendencias|push:("FAIXA_NAO_CONFIGURADA:" ~ $item.parametro) }
                  }
                  else {
                    var.update $pontos_sinais { value = $pontos_sinais|set:$item.parametro:$faixa.pontos }
                    var.update $escore_sinais { value = $escore_sinais + $faixa.pontos }
                    conditional {
                      if ($faixa.pontos == 3) {
                        var.update $critico { value = true }
                      }
                    }
                  }
                }
              }
            }
          }
        }

        // Glicemia é opcional: só pontua quando medida.
        var $glicemia { value = $sinais|get:"glicemia":null }
        conditional {
          if ($glicemia != null) {
            var $gravidade { value = ($sinais|get:"glicemia_sinais_gravidade":false) == true }
            var $faixa_glicemia {
              value = $faixas|find:($$.parametro == "GLICEMIA" && ($$.minimo == null || $glicemia >= $$.minimo) && ($$.maximo == null || $glicemia <= $$.maximo) && ($$.condicao_gravidade == null || $$.condicao_gravidade == $gravidade))
            }
            conditional {
              if ($faixa_glicemia == null) {
                var.update $pendencias { value = $pendencias|push:"FAIXA_NAO_CONFIGURADA:GLICEMIA" }
              }
              else {
                var.update $pontos_sinais { value = $pontos_sinais|set:"GLICEMIA":$faixa_glicemia.pontos }
                var.update $escore_sinais { value = $escore_sinais + $faixa_glicemia.pontos }
                conditional {
                  if ($faixa_glicemia.pontos == 3) {
                    var.update $critico { value = true }
                  }
                }
              }
            }
          }
        }
      }
    }

    var $escore_total { value = null }
    var $prioridade { value = null }
    conditional {
      if (($pendencias|count) == 0) {
        var.update $escore_total { value = $escore_sintomas + $escore_sinais }
        conditional {
          if ($critico || $escore_total >= $limiar_vermelha) {
            var.update $prioridade { value = "VERMELHA" }
          }
          elseif ($escore_total >= $limiar_amarela) {
            var.update $prioridade { value = "AMARELA" }
          }
          else {
            var.update $prioridade { value = "AZUL" }
          }
        }
      }
    }
  }

  response = {
    pontos_sinais       : $pontos_sinais
    escore_sintomas     : $escore_sintomas
    escore_sinais       : $tabela_adulta ? $escore_sinais : null
    escore_total        : $escore_total
    item_critico        : $critico
    prioridade_calculada: $prioridade
    condicao_prioritaria: $condicao
    tabela_adulta       : $tabela_adulta
    pendencias          : $pendencias
  }

  test "bordas 1: PA 90, FC 90, FR 8, T 35.0, SpO2 91" {
    input = {sinais: {pa_sistolica: 90, fc: 90, fr: 8, temperatura: 35.0, spo2: 91}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.PA_SISTOLICA) {
      value = 3
    }
    expect.to_equal ($response.pontos_sinais.FC) {
      value = 0
    }
    expect.to_equal ($response.pontos_sinais.FR) {
      value = 3
    }
    expect.to_equal ($response.pontos_sinais.TEMPERATURA) {
      value = 3
    }
    expect.to_equal ($response.pontos_sinais.SPO2) {
      value = 3
    }
  }

  test "bordas 2: PA 91, FC 91, FR 9, T 35.1, SpO2 92" {
    input = {sinais: {pa_sistolica: 91, fc: 91, fr: 9, temperatura: 35.1, spo2: 92}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.PA_SISTOLICA) {
      value = 2
    }
    expect.to_equal ($response.pontos_sinais.FC) {
      value = 1
    }
    expect.to_equal ($response.pontos_sinais.FR) {
      value = 1
    }
    expect.to_equal ($response.pontos_sinais.TEMPERATURA) {
      value = 1
    }
    expect.to_equal ($response.pontos_sinais.SPO2) {
      value = 2
    }
  }

  test "bordas 3: PA 100, FC 110, FR 11, T 36.0, SpO2 93" {
    input = {sinais: {pa_sistolica: 100, fc: 110, fr: 11, temperatura: 36.0, spo2: 93}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.PA_SISTOLICA) {
      value = 2
    }
    expect.to_equal ($response.pontos_sinais.FC) {
      value = 1
    }
    expect.to_equal ($response.pontos_sinais.FR) {
      value = 1
    }
    expect.to_equal ($response.pontos_sinais.TEMPERATURA) {
      value = 1
    }
    expect.to_equal ($response.pontos_sinais.SPO2) {
      value = 2
    }
  }

  test "bordas 4: PA 101, FC 111, FR 12, T 36.1, SpO2 94" {
    input = {sinais: {pa_sistolica: 101, fc: 111, fr: 12, temperatura: 36.1, spo2: 94}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.PA_SISTOLICA) {
      value = 1
    }
    expect.to_equal ($response.pontos_sinais.FC) {
      value = 2
    }
    expect.to_equal ($response.pontos_sinais.FR) {
      value = 0
    }
    expect.to_equal ($response.pontos_sinais.TEMPERATURA) {
      value = 0
    }
    expect.to_equal ($response.pontos_sinais.SPO2) {
      value = 1
    }
  }

  test "bordas 5: PA 110, FC 130, FR 20, T 38.0, SpO2 95" {
    input = {sinais: {pa_sistolica: 110, fc: 130, fr: 20, temperatura: 38.0, spo2: 95}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.PA_SISTOLICA) {
      value = 1
    }
    expect.to_equal ($response.pontos_sinais.FC) {
      value = 2
    }
    expect.to_equal ($response.pontos_sinais.FR) {
      value = 0
    }
    expect.to_equal ($response.pontos_sinais.TEMPERATURA) {
      value = 0
    }
    expect.to_equal ($response.pontos_sinais.SPO2) {
      value = 1
    }
  }

  test "bordas 6: PA 111, FC 131, FR 21, T 38.1, SpO2 96" {
    input = {sinais: {pa_sistolica: 111, fc: 131, fr: 21, temperatura: 38.1, spo2: 96}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.PA_SISTOLICA) {
      value = 0
    }
    expect.to_equal ($response.pontos_sinais.FC) {
      value = 3
    }
    expect.to_equal ($response.pontos_sinais.FR) {
      value = 2
    }
    expect.to_equal ($response.pontos_sinais.TEMPERATURA) {
      value = 1
    }
    expect.to_equal ($response.pontos_sinais.SPO2) {
      value = 0
    }
  }

  test "bordas 7: PA 219, FC 51, FR 24, T 39.0" {
    input = {sinais: {pa_sistolica: 219, fc: 51, fr: 24, temperatura: 39.0, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.PA_SISTOLICA) {
      value = 0
    }
    expect.to_equal ($response.pontos_sinais.FC) {
      value = 0
    }
    expect.to_equal ($response.pontos_sinais.FR) {
      value = 2
    }
    expect.to_equal ($response.pontos_sinais.TEMPERATURA) {
      value = 1
    }
    expect.to_equal ($response.pontos_sinais.SPO2) {
      value = 0
    }
  }

  test "bordas 8: PA 220, FC 50, FR 25, T 39.1" {
    input = {sinais: {pa_sistolica: 220, fc: 50, fr: 25, temperatura: 39.1, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.PA_SISTOLICA) {
      value = 3
    }
    expect.to_equal ($response.pontos_sinais.FC) {
      value = 1
    }
    expect.to_equal ($response.pontos_sinais.FR) {
      value = 3
    }
    expect.to_equal ($response.pontos_sinais.TEMPERATURA) {
      value = 2
    }
    expect.to_equal ($response.pontos_sinais.SPO2) {
      value = 0
    }
  }

  test "bordas 9: FC 41" {
    input = {sinais: {pa_sistolica: 120, fc: 41, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.FC) {
      value = 1
    }
  }

  test "bordas 10: FC 40" {
    input = {sinais: {pa_sistolica: 120, fc: 40, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.FC) {
      value = 3
    }
  }

  test "glicemia 53 sem gravidade soma 2 e fica Azul" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98, glicemia: 53, glicemia_sinais_gravidade: false}, gestante: false, idade: 40, pontos_sintomas: [2], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.GLICEMIA) {
      value = 2
    }
    expect.to_equal ($response.escore_total) {
      value = 4
    }
    expect.to_equal ($response.item_critico) {
      value = false
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "AZUL"
    }
  }

  test "glicemia 53 com gravidade gera Vermelha" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98, glicemia: 53, glicemia_sinais_gravidade: true}, gestante: false, idade: 40, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.GLICEMIA) {
      value = 3
    }
    expect.to_equal ($response.item_critico) {
      value = true
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "VERMELHA"
    }
  }

  test "glicemia 54 com gravidade soma 2" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98, glicemia: 54, glicemia_sinais_gravidade: true}, gestante: false, idade: 40, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.GLICEMIA) {
      value = 2
    }
  }

  test "glicemia 59 sem gravidade soma 1" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98, glicemia: 59, glicemia_sinais_gravidade: false}, gestante: false, idade: 40, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.GLICEMIA) {
      value = 1
    }
  }

  test "glicemia 60 soma 0" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98, glicemia: 60, glicemia_sinais_gravidade: true}, gestante: false, idade: 40, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.pontos_sinais.GLICEMIA) {
      value = 0
    }
  }

  test "glicemia não medida não bloqueia" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_be_null ($response.pontos_sinais.GLICEMIA)
    expect.to_equal ($response.prioridade_calculada) {
      value = "AZUL"
    }
  }

  test "escore 4 sem item 3 é Azul" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [2, 2], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.escore_total) {
      value = 4
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "AZUL"
    }
  }

  test "escore 5 sem item 3 é Amarela" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [2, 2, 1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.escore_total) {
      value = 5
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "AMARELA"
    }
  }

  test "escore 9 sem item 3 é Amarela" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [2, 2, 2, 2, 1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.escore_total) {
      value = 9
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "AMARELA"
    }
  }

  test "escore 10 sem item 3 é Vermelha" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [2, 2, 2, 2, 2], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.escore_total) {
      value = 10
    }
    expect.to_equal ($response.item_critico) {
      value = false
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "VERMELHA"
    }
  }

  test "5.4 febre 1 + mal-estar 1 = 2 Azul" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [1, 1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.escore_total) {
      value = 2
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "AZUL"
    }
  }

  test "5.4 sintomas 2+2+2 e sinais 2 = 8 Amarela" {
    input = {sinais: {pa_sistolica: 120, fc: 111, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [2, 2, 2], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.escore_sintomas) {
      value = 6
    }
    expect.to_equal ($response.escore_sinais) {
      value = 2
    }
    expect.to_equal ($response.escore_total) {
      value = 8
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "AMARELA"
    }
  }

  test "5.4 sintomas 2+2+2+2 e sinais 2 = 10 Vermelha" {
    input = {sinais: {pa_sistolica: 120, fc: 111, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [2, 2, 2, 2], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.escore_total) {
      value = 10
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "VERMELHA"
    }
  }

  test "convulsão isolada de 3 pontos é Vermelha pela exceção" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [3], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.escore_total) {
      value = 3
    }
    expect.to_equal ($response.item_critico) {
      value = true
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "VERMELHA"
    }
  }

  test "sintoma digitado de 2 pontos soma ao escore" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [1, 2], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.escore_total) {
      value = 3
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "AZUL"
    }
  }

  test "sintoma digitado de 3 pontos é Vermelha" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [3], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.item_critico) {
      value = true
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "VERMELHA"
    }
  }

  test "SpO2 91 é Vermelha pela exceção" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 91}, gestante: false, idade: 40, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.item_critico) {
      value = true
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "VERMELHA"
    }
  }

  test "temperatura 39.1 não gera Vermelha sozinha" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 39.1, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.escore_total) {
      value = 3
    }
    expect.to_equal ($response.item_critico) {
      value = false
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "AZUL"
    }
  }

  test "SpO2 ausente bloqueia o cálculo" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: null}, gestante: false, idade: 40, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_be_null ($response.prioridade_calculada)
    expect.to_be_null ($response.escore_total)
    expect.to_contain ($response.pendencias) {
      value = "SPO2_NAO_INFORMADO"
    }
  }

  test "paciente de 10 anos exige classificação manual" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 10, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_be_null ($response.prioridade_calculada)
    expect.to_equal ($response.tabela_adulta) {
      value = false
    }
    expect.to_contain ($response.pendencias) {
      value = "TABELA_ADULTA_NAO_APLICAVEL"
    }
    expect.to_equal ($response.condicao_prioritaria) {
      value = "CRIANCA"
    }
  }

  test "paciente de 16 anos é calculado" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 16, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.tabela_adulta) {
      value = true
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "AZUL"
    }
    expect.to_equal ($response.condicao_prioritaria) {
      value = "NENHUMA"
    }
  }

  test "gestante exige classificação manual" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: true, idade: 30, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_be_null ($response.prioridade_calculada)
    expect.to_equal ($response.condicao_prioritaria) {
      value = "GESTANTE"
    }
    expect.to_contain ($response.pendencias) {
      value = "TABELA_ADULTA_NAO_APLICAVEL"
    }
  }

  test "gestante de 60 anos registra GESTANTE" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: true, idade: 60, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.condicao_prioritaria) {
      value = "GESTANTE"
    }
  }

  test "idoso de 68 anos mantém a cor do escore" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 68, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.condicao_prioritaria) {
      value = "IDOSO"
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "AZUL"
    }
  }

  test "12 anos não é criança" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 12, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.condicao_prioritaria) {
      value = "NENHUMA"
    }
    expect.to_equal ($response.tabela_adulta) {
      value = false
    }
  }

  test "11 anos é criança" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 11, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.condicao_prioritaria) {
      value = "CRIANCA"
    }
  }

  test "sem faixas configuradas bloqueia" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [1], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas: []}
    expect.to_be_null ($response.prioridade_calculada)
    expect.to_contain ($response.pendencias) {
      value = "FAIXA_NAO_CONFIGURADA:PA_SISTOLICA"
    }
  }

  test "sem sintoma nem observação bloqueia" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: false, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_be_null ($response.prioridade_calculada)
    expect.to_contain ($response.pendencias) {
      value = "SEM_SINTOMA_OU_OBSERVACAO"
    }
  }

  test "só observação é aceita" {
    input = {sinais: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98}, gestante: false, idade: 40, pontos_sintomas: [], tem_observacao: true, parametros: {LIMIAR_AMARELA: 5, LIMIAR_VERMELHA: 10, IDADE_MINIMA_TABELA_ADULTA: 16, IDADE_MINIMA_IDOSO: 60, IDADE_MAXIMA_CRIANCA: 11}, faixas_padrao: true}
    expect.to_equal ($response.escore_total) {
      value = 0
    }
    expect.to_equal ($response.prioridade_calculada) {
      value = "AZUL"
    }
  }
  guid = "L91G28UtiUcjP-YN5nC39Hr4F00"
}

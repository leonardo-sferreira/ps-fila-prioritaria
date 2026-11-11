// Sinais vitais lidos da ficha, com 0 tratado como "não medido".
// No servidor, as colunas de sinais vitais de ficha_atendimento são int/decimal sem null, então um campo deixado em
// branco é gravado como 0. Nenhum 0 é válido (o PATCH aceita PA ≥ 40, FC ≥ 20, FR ≥ 4, T ≥ 25, SpO2 ≥ 50,
// glicemia ≥ 10), então 0 volta a ser null antes da classificação e da tela. Sem isso, PA em branco viraria
// "PA 0" e geraria 3 pontos (Vermelha), e a pendência "Informe a PA" nunca apareceria.
function "classificacao/sinais_da_ficha" {
  description = "Extrai os sinais vitais da ficha convertendo 0 (campo vazio gravado pelo banco) em null."

  input {
    json ficha
  }

  stack {
    var $sinais {
      value = {glicemia_sinais_gravidade: ($input.ficha|get:"glicemia_sinais_gravidade":false) == true}
    }

    foreach (["pa_sistolica", "fc", "fr", "temperatura", "spo2", "glicemia"]) {
      each as $campo {
        var $bruto {
          value = $input.ficha|get:$campo:null
        }
        var $valor {
          value = ($bruto == null || $bruto == 0) ? null : $bruto
        }
        var.update $sinais {
          value = $sinais|set:$campo:$valor
        }
      }
    }
  }

  response = $sinais

  test "zeros gravados pelo banco viram não medido" {
    input = {ficha: {pa_sistolica: 0, fc: 0, fr: 0, temperatura: 0, spo2: 0, glicemia: 0, glicemia_sinais_gravidade: false}}
    expect.to_be_null ($response.pa_sistolica)
    expect.to_be_null ($response.fc)
    expect.to_be_null ($response.fr)
    expect.to_be_null ($response.temperatura)
    expect.to_be_null ($response.spo2)
    expect.to_be_null ($response.glicemia)
  }

  test "valores medidos passam sem mudança" {
    input = {ficha: {pa_sistolica: 120, fc: 80, fr: 16, temperatura: 36.5, spo2: 98, glicemia: 110, glicemia_sinais_gravidade: true}}
    expect.to_equal ($response.pa_sistolica) {
      value = 120
    }
    expect.to_equal ($response.temperatura) {
      value = 36.5
    }
    expect.to_equal ($response.glicemia) {
      value = 110
    }
    expect.to_be_true ($response.glicemia_sinais_gravidade)
  }

  test "mistura de medido, zero e ausente" {
    input = {ficha: {pa_sistolica: 150, fc: 0, spo2: 96}}
    expect.to_equal ($response.pa_sistolica) {
      value = 150
    }
    expect.to_be_null ($response.fc)
    expect.to_be_null ($response.fr)
    expect.to_equal ($response.spo2) {
      value = 96
    }
    expect.to_be_false ($response.glicemia_sinais_gravidade)
  }
}

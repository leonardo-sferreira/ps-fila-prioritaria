// Diz se uma faixa de sinal vital se sobrepõe a alguma outra do mesmo parâmetro (add-cadastros-administrador, D8).
// Extremos inclusivos; limite null = extremo aberto. Condição de gravidade null vale para as duas condições.
// Função pura: as outras faixas (já do mesmo parâmetro e sem a própria) vêm na entrada.
function "cadastros/faixa_sobrepoe" {
  description = "Recebe {minimo, maximo, condicao_gravidade} e a lista das outras faixas do parâmetro; devolve true se houver sobreposição."

  input {
    json faixa
    json? outras?
  }

  stack {
    // `get` com padrão devolve o padrão também para false e 0: lê o campo só quando ele existe.
    var $a_min { value = ($input.faixa|has:"minimo") ? $input.faixa.minimo : null }
    var $a_max { value = ($input.faixa|has:"maximo") ? $input.faixa.maximo : null }
    var $a_cond { value = ($input.faixa|has:"condicao_gravidade") ? $input.faixa.condicao_gravidade : null }
    var $sobrepoe { value = false }

    foreach ($input.outras ?? []) {
      each as $b {
        var $b_min { value = ($b|has:"minimo") ? $b.minimo : null }
        var $b_max { value = ($b|has:"maximo") ? $b.maximo : null }
        var $b_cond { value = ($b|has:"condicao_gravidade") ? $b.condicao_gravidade : null }
        var $mesma_condicao {
          value = $a_cond == null || $b_cond == null || $a_cond == $b_cond
        }
        var $cruza {
          value = ($a_min == null || $b_max == null || $a_min <= $b_max) && ($b_min == null || $a_max == null || $b_min <= $a_max)
        }
        conditional {
          if ($mesma_condicao && $cruza) {
            var.update $sobrepoe { value = true }
          }
        }
      }
    }
  }

  response = $sobrepoe

  test "faixas vizinhas não se sobrepõem" {
    input = {faixa: {minimo: 94, maximo: 95, condicao_gravidade: null}, outras: [{minimo: 96, maximo: null, condicao_gravidade: null}, {minimo: 92, maximo: 93, condicao_gravidade: null}]}
    expect.to_be_false ($response)
  }

  test "limite repetido se sobrepõe" {
    input = {faixa: {minimo: 94, maximo: 96, condicao_gravidade: null}, outras: [{minimo: 96, maximo: null, condicao_gravidade: null}]}
    expect.to_be_true ($response)
  }

  test "extremo aberto cobre tudo abaixo" {
    input = {faixa: {minimo: null, maximo: 91, condicao_gravidade: null}, outras: [{minimo: 50, maximo: 60, condicao_gravidade: null}]}
    expect.to_be_true ($response)
  }

  test "decimais da temperatura encostados" {
    input = {faixa: {minimo: 36.1, maximo: 38.0, condicao_gravidade: null}, outras: [{minimo: 35.1, maximo: 36.0, condicao_gravidade: null}, {minimo: 38.1, maximo: 39.0, condicao_gravidade: null}]}
    expect.to_be_false ($response)
  }

  test "glicemia com condições diferentes não colide" {
    input = {faixa: {minimo: null, maximo: 53, condicao_gravidade: true}, outras: [{minimo: null, maximo: 53, condicao_gravidade: false}]}
    expect.to_be_false ($response)
  }

  test "limite zero não vira extremo aberto" {
    input = {faixa: {minimo: 0, maximo: 5, condicao_gravidade: null}, outras: [{minimo: null, maximo: -1, condicao_gravidade: null}]}
    expect.to_be_false ($response)
  }

  test "faixa sem condição colide com qualquer condição" {
    input = {faixa: {minimo: 50, maximo: null, condicao_gravidade: null}, outras: [{minimo: 54, maximo: 59, condicao_gravidade: true}]}
    expect.to_be_true ($response)
  }
  guid = "S4_r18Y3oBEivqrW3LLd-DQEXmI"
}

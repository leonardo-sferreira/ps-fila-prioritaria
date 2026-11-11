// Limites dos parâmetros editáveis pelo Administrador (add-cadastros-administrador, D7). Função pura.
// Chave interna (POSICAO_CICLO_PRE_TRIAGEM) ou desconhecida: editavel = false.
// ESPECIALIDADE_PADRAO é do tipo ESPECIALIDADE: sem mínimo/máximo, validada contra as especialidades ativas.
function "cadastros/regra_parametro" {
  description = "Devolve {editavel, tipo, minimo, maximo, rotulo, unidade} de uma chave de parâmetro."

  input {
    text chave filters=trim
  }

  stack {
    var $regras {
      value = {
        LIMIAR_AMARELA                : {tipo: "INTEIRO", minimo: 1, maximo: 50, rotulo: "Escore a partir do qual a ficha é Amarela", unidade: "pontos"}
        LIMIAR_VERMELHA               : {tipo: "INTEIRO", minimo: 2, maximo: 60, rotulo: "Escore a partir do qual a ficha é Vermelha", unidade: "pontos"}
        IDADE_MAXIMA_CRIANCA          : {tipo: "INTEIRO", minimo: 5, maximo: 15, rotulo: "Idade máxima de criança (vai para Pediatria)", unidade: "anos"}
        IDADE_MINIMA_TABELA_ADULTA    : {tipo: "INTEIRO", minimo: 12, maximo: 21, rotulo: "Idade mínima para a tabela adulta de sinais vitais", unidade: "anos"}
        IDADE_MINIMA_IDOSO            : {tipo: "INTEIRO", minimo: 50, maximo: 80, rotulo: "Idade mínima de idoso", unidade: "anos"}
        INTERVALO_CHAMADA_SEGUNDOS    : {tipo: "INTEIRO", minimo: 10, maximo: 300, rotulo: "Intervalo após a 1ª chamada", unidade: "segundos"}
        INTERVALO_REPETICAO_SEGUNDOS  : {tipo: "INTEIRO", minimo: 5, maximo: 120, rotulo: "Intervalo após a 2ª e a 3ª chamada do ticket", unidade: "segundos"}
        TENTATIVAS_CHAMADA            : {tipo: "INTEIRO", minimo: 1, maximo: 10, rotulo: "Chamadas por oportunidade", unidade: "chamadas"}
        CICLO_PRE_TRIAGEM_PRIORITARIOS: {tipo: "INTEIRO", minimo: 1, maximo: 10, rotulo: "Pré-triagem: prioritários por ciclo", unidade: "tickets"}
        CICLO_PRE_TRIAGEM_NORMAIS     : {tipo: "INTEIRO", minimo: 1, maximo: 10, rotulo: "Pré-triagem: normais por ciclo", unidade: "tickets"}
        HORAS_EXPIRACAO               : {tipo: "INTEIRO", minimo: 6, maximo: 168, rotulo: "Prazo para dispensar fichas e tickets parados", unidade: "horas"}
        amarelas_por_ciclo            : {tipo: "INTEIRO", minimo: 1, maximo: 10, rotulo: "Fila médica: Amarelas por ciclo", unidade: "fichas"}
        azuis_por_ciclo               : {tipo: "INTEIRO", minimo: 1, maximo: 10, rotulo: "Fila médica: Azuis por ciclo", unidade: "fichas"}
        tamanho_previsao              : {tipo: "INTEIRO", minimo: 1, maximo: 20, rotulo: "Senhas na previsão do painel", unidade: "senhas"}
        ESPECIALIDADE_PADRAO          : {tipo: "ESPECIALIDADE", minimo: null, maximo: null, rotulo: "Especialidade padrão (ficha sem sintoma do catálogo)", unidade: ""}
      }
    }
    var $regra {
      value = $regras|get:$input.chave:null
    }
    var $resultado {
      value = {editavel: false, tipo: null, minimo: null, maximo: null, rotulo: $input.chave, unidade: ""}
    }
    conditional {
      if ($regra != null) {
        var.update $resultado {
          value = $regra|set:"editavel":true
        }
      }
    }
  }

  response = $resultado

  test "limiar com limites" {
    input = {chave: "LIMIAR_AMARELA"}
    expect.to_be_true ($response.editavel)
    expect.to_equal ($response.minimo) {
      value = 1
    }
    expect.to_equal ($response.maximo) {
      value = 50
    }
  }

  test "parâmetro da fila médica" {
    input = {chave: "tamanho_previsao"}
    expect.to_equal ($response.maximo) {
      value = 20
    }
  }

  test "posição do ciclo é interna" {
    input = {chave: "POSICAO_CICLO_PRE_TRIAGEM"}
    expect.to_be_false ($response.editavel)
  }

  test "chave desconhecida" {
    input = {chave: "FUSO_HORARIO"}
    expect.to_be_false ($response.editavel)
  }

  test "especialidade padrão sem limites numéricos" {
    input = {chave: "ESPECIALIDADE_PADRAO"}
    expect.to_be_true ($response.editavel)
    expect.to_equal ($response.tipo) {
      value = "ESPECIALIDADE"
    }
  }
}

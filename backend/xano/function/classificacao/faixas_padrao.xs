// Faixas iniciais de pontuação dos sinais vitais (Rev. 2.1, §21.2 e §21.3), fonte única usada pela carga
// (inicializar_classificacao) e pelos testes de pontuar. Extremos inclusivos; null = limite aberto.
// Pontuação acadêmica de simulação a partir da tabela adulta do NEWS2; não é NEWS2 nem protocolo clínico.
function "classificacao/faixas_padrao" {
  description = "Lista das faixas iniciais de pontuação dos sinais vitais (pessoas com 16 anos ou mais, não gestantes)."
  input {}
  stack {
    var $faixas {
      value = [
      {parametro: "PA_SISTOLICA", minimo: 111, maximo: 219, pontos: 0, condicao_gravidade: null}
      {parametro: "PA_SISTOLICA", minimo: 101, maximo: 110, pontos: 1, condicao_gravidade: null}
      {parametro: "PA_SISTOLICA", minimo: 91, maximo: 100, pontos: 2, condicao_gravidade: null}
      {parametro: "PA_SISTOLICA", minimo: null, maximo: 90, pontos: 3, condicao_gravidade: null}
      {parametro: "PA_SISTOLICA", minimo: 220, maximo: null, pontos: 3, condicao_gravidade: null}
      {parametro: "FC", minimo: 51, maximo: 90, pontos: 0, condicao_gravidade: null}
      {parametro: "FC", minimo: 41, maximo: 50, pontos: 1, condicao_gravidade: null}
      {parametro: "FC", minimo: 91, maximo: 110, pontos: 1, condicao_gravidade: null}
      {parametro: "FC", minimo: 111, maximo: 130, pontos: 2, condicao_gravidade: null}
      {parametro: "FC", minimo: null, maximo: 40, pontos: 3, condicao_gravidade: null}
      {parametro: "FC", minimo: 131, maximo: null, pontos: 3, condicao_gravidade: null}
      {parametro: "FR", minimo: 12, maximo: 20, pontos: 0, condicao_gravidade: null}
      {parametro: "FR", minimo: 9, maximo: 11, pontos: 1, condicao_gravidade: null}
      {parametro: "FR", minimo: 21, maximo: 24, pontos: 2, condicao_gravidade: null}
      {parametro: "FR", minimo: null, maximo: 8, pontos: 3, condicao_gravidade: null}
      {parametro: "FR", minimo: 25, maximo: null, pontos: 3, condicao_gravidade: null}
      {parametro: "TEMPERATURA", minimo: 36.1, maximo: 38.0, pontos: 0, condicao_gravidade: null}
      {parametro: "TEMPERATURA", minimo: 35.1, maximo: 36.0, pontos: 1, condicao_gravidade: null}
      {parametro: "TEMPERATURA", minimo: 38.1, maximo: 39.0, pontos: 1, condicao_gravidade: null}
      {parametro: "TEMPERATURA", minimo: 39.1, maximo: null, pontos: 2, condicao_gravidade: null}
      {parametro: "TEMPERATURA", minimo: null, maximo: 35.0, pontos: 3, condicao_gravidade: null}
      {parametro: "SPO2", minimo: 96, maximo: null, pontos: 0, condicao_gravidade: null}
      {parametro: "SPO2", minimo: 94, maximo: 95, pontos: 1, condicao_gravidade: null}
      {parametro: "SPO2", minimo: 92, maximo: 93, pontos: 2, condicao_gravidade: null}
      {parametro: "SPO2", minimo: null, maximo: 91, pontos: 3, condicao_gravidade: null}
      {parametro: "GLICEMIA", minimo: null, maximo: 53, pontos: 3, condicao_gravidade: true}
      {parametro: "GLICEMIA", minimo: null, maximo: 53, pontos: 2, condicao_gravidade: false}
      {parametro: "GLICEMIA", minimo: 54, maximo: 59, pontos: 2, condicao_gravidade: true}
      {parametro: "GLICEMIA", minimo: 54, maximo: 59, pontos: 1, condicao_gravidade: false}
      {parametro: "GLICEMIA", minimo: 60, maximo: null, pontos: 0, condicao_gravidade: null}
    ]
    }
  }
  response = {faixas: $faixas, total: $faixas|count}

  test "tem as 30 faixas" {
    input = {}
    expect.to_equal ($response.total) {
      value = 30
    }
  }
  guid = "DFxiBnSqXjobGgT--nQABJhvg4g"
}

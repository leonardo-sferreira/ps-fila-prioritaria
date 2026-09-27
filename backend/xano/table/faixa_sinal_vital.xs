// Faixas configuráveis de pontuação (0 a 3) de cada sinal vital.
table faixa_sinal_vital {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    enum parametro {
      values = ["PA_SISTOLICA", "FC", "FR", "TEMPERATURA", "SPO2", "GLICEMIA"]
    }
    decimal minimo
    decimal maximo
    int pontos
    bool? condicao_gravidade?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "parametro", op: "asc"}, {name: "minimo", op: "asc"}]}
  ]
  guid = "7sFCwwDTGHEuS9t5JF4hV1334WM"
}

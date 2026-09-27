// Parâmetros de regra configuráveis (chave-valor).
table parametro {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text chave filters=trim
    text valor
    enum tipo {
      values = ["INTEIRO", "ESPECIALIDADE"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "chave", op: "asc"}]}
  ]
  guid = "9JuRnfV2dPpuc-lR67X0yWRRXbo"
}

// Alternativas ordenadas (fallback) de uma especialidade.
table especialidade_alternativa {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int especialidade_id {
      table = "especialidade"
    }
    int alternativa_id {
      table = "especialidade"
    }
    int ordem
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "especialidade_id", op: "asc"}, {name: "alternativa_id", op: "asc"}]}
  ]
  guid = "xkq-SGlkvAckiGldSBRypk3duXw"
}

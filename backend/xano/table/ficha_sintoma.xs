// Sintomas registrados em uma ficha.
table ficha_sintoma {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int ficha_id {
      table = "ficha_atendimento"
    }
    int sintoma_id {
      table = "sintoma"
    }
    text? observacao?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "ficha_id", op: "asc"}, {name: "sintoma_id", op: "asc"}]}
  ]
  guid = "pdS71CLotmlEwb3i4ffIzt-RQd4"
}

// Último número de senha emitido por especialidade e dia.
table contador_senha {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    date data
    int especialidade_id {
      table = "especialidade"
    }
    int ultimo_numero?=0
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "data", op: "asc"}, {name: "especialidade_id", op: "asc"}]}
  ]
  guid = "eS93RkwypmH9-3KyrKLdTy6GiDQ"
}

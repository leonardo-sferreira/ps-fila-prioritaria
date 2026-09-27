// Área de atendimento; cada especialidade tem sua fila priorizada.
table especialidade {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text nome filters=trim
    text sigla filters=trim|upper
    text descricao?
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "sigla", op: "asc"}]}
    {type: "btree|unique", field: [{name: "nome", op: "asc"}]}
  ]
  guid = "t7LAZNY5bfuQWmio67kcYR6noxk"
}

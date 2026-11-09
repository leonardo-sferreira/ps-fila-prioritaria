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
    // Nome em minúsculas, sem espaços nas pontas, para a unicidade de nome nos cadastros do Administrador
    // (publicado na v1 pela migração de especialidade de add-cadastros-administrador).
    text nome_normalizado filters=trim|min:1|lower
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "sigla", op: "asc"}]}
    {type: "btree|unique", field: [{name: "nome", op: "asc"}]}
    {type: "btree|unique", field: [{name: "nome_normalizado", op: "asc"}]}
  ]
  guid = "t7LAZNY5bfuQWmio67kcYR6noxk"
}

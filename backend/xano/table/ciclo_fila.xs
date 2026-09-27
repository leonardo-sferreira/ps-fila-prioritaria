// Posição atual do ciclo amarelo/azul por especialidade.
table ciclo_fila {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int especialidade_id {
      table = "especialidade"
    }
    int posicao?=1
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "especialidade_id", op: "asc"}]}
  ]
  guid = "DWImWWHg6LVGLnkVtPogPG3yQ4A"
}

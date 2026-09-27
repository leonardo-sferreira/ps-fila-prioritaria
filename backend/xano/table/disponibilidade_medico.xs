// Período [inicio, fim) em que o médico atende, registrado pelo Administrador.
table disponibilidade_medico {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int medico_id {
      table = "medico"
    }
    timestamp inicio
    timestamp fim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "medico_id", op: "asc"}, {name: "inicio", op: "asc"}]}
  ]
  guid = "sCwZN3twGx0EydHilN19d9l7mwM"
}

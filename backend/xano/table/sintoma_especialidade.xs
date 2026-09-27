// Especialidades de um sintoma, em ordem de preferência.
table sintoma_especialidade {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int sintoma_id {
      table = "sintoma"
    }
    int especialidade_id {
      table = "especialidade"
    }
    int ordem
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "sintoma_id", op: "asc"}, {name: "especialidade_id", op: "asc"}]}
  ]
  guid = "eAsGCwD0lNPtGbEjWfEHxn02c94"
}

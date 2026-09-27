// Especialidades atendidas por um médico.
table medico_especialidade {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int medico_id {
      table = "medico"
    }
    int especialidade_id {
      table = "especialidade"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "medico_id", op: "asc"}, {name: "especialidade_id", op: "asc"}]}
  ]
  guid = "01tqR1aG80rEYUtDLV4tC9gDo8g"
}

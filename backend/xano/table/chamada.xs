// Tentativas de chamada, comparecimentos e desistências.
table chamada {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int ficha_id {
      table = "ficha_atendimento"
    }
    int medico_id {
      table = "medico"
    }
    int tentativa
    enum tipo {
      values = ["CHAMADA", "COMPARECIMENTO", "DESISTENCIA"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "ficha_id", op: "asc"}, {name: "tentativa", op: "asc"}, {name: "tipo", op: "asc"}]}
    {type: "btree", field: [{name: "created_at", op: "asc"}]}
  ]
  guid = "ntXxj8uyjUr8HtsV0khuM5vd8j4"
}

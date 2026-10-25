// Ticket emitido pelo Totem antes da triagem. Tipo autodeclarado (add-totem D5).
table ticket_pre_triagem {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    date data
    enum tipo?=NORMAL {
      values = ["PEDIATRICO", "PREFERENCIAL", "NORMAL"]
    }
  
    int numero
    timestamp emitido_em
    enum status {
      values = ["AGUARDANDO", "CHAMADO", "ATENDIDO", "NAO_COMPARECEU"]
    }
  
    int? chamado_por? {
      table = "usuario"
    }
  
    timestamp? chamado_em?
    int? paciente_id? {
      table = "paciente"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [
        {name: "data", op: "asc"}
        {name: "tipo", op: "asc"}
        {name: "numero", op: "asc"}
      ]
    }
    {type: "btree", field: [{name: "status", op: "asc"}]}
  ]

  guid = "s6COQFpyjrVme0bdKSkVFnioBio"
}
// Ticket emitido pelo totem (simulado) antes da triagem.
table ticket_pre_triagem {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    date data
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
    {type: "btree|unique", field: [{name: "data", op: "asc"}, {name: "numero", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
  ]
  guid = "s6COQFpyjrVme0bdKSkVFnioBio"
}

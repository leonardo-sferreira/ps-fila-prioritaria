// Trilha de auditoria imutável.
table historico_alteracao {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text tipo_evento
    text entidade
    int? registro_id?
    json? valor_anterior?
    json? valor_novo?
    text? justificativa?
    int? usuario_id? {
      table = "usuario"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "asc"}]}
    {type: "btree", field: [{name: "entidade", op: "asc"}, {name: "registro_id", op: "asc"}]}
    {type: "btree", field: [{name: "tipo_evento", op: "asc"}]}
  ]
  guid = "3BuEflEXk5itKwY99J_f8vjUum4"
}

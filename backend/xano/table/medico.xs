// Profissional que atende a fila priorizada (vinculado a um usuário MEDICO).
table medico {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int usuario_id {
      table = "usuario"
    }
    text registro_profissional filters=trim
    bool ativo?=true
    // Sala atual do médico (opcional, sem histórico); só sala ativa (add-cadastros-administrador, D4).
    int? sala_id? {
      table = "sala"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "usuario_id", op: "asc"}]}
  ]
  guid = "7yHfBgGfDw0NGf-FhvicsHA-7fo"
}

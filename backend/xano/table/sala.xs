// Local de atendimento; o médico pode ter uma sala atual (medico.sala_id). Desativada, nunca excluída
// (add-cadastros-administrador, D5).
table sala {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text nome filters=trim
    // lower(trim(nome)), para a unicidade sem diferenciar maiúsculas.
    text nome_normalizado filters=trim|lower
    text? descricao? filters=trim
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "nome_normalizado", op: "asc"}]}
  ]
  guid = "LDunBTTSzCuA36Bd0RkcLbedZ0U"
}

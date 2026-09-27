// Registro de login/logout da equipe e status operacional.
table sessao {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int usuario_id {
      table = "usuario"
    }
    timestamp login_em
    timestamp? logout_em?
    timestamp expira_em
    enum? status_operacional? {
      values = ["DISPONIVEL", "EM_ATENDIMENTO", "PAUSA", "AUSENTE"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "usuario_id", op: "asc"}]}
    {type: "btree", field: [{name: "login_em", op: "asc"}]}
  ]
  guid = "KzPDdME_vywm7-VbJ0n187oRvUE"
}

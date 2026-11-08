// Sintoma digitado pela Recepção/Triagem que não está no catálogo (add-classificacao-prioridade, D9).
// Vale só para a ficha: não entra no catálogo nem em GET /sintomas.
table ficha_sintoma_livre {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int ficha_id {
      table = "ficha_atendimento"
    }
    text descricao filters=trim
    // Gravidade escolhida pela Recepção/Triagem: 1 leve, 2 moderado, 3 grave.
    int pontuacao
    int? criado_por? {
      table = "usuario"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "ficha_id", op: "asc"}]}
  ]
  guid = "YazuQ9CF1ACkd1RZKUNezPsJTCM"
}

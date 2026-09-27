// Pessoa atendida no PS, identificada pelo CPF.
table paciente {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text cpf filters=trim
    text nome filters=trim
    date data_nascimento
    text? telefone?
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "cpf", op: "asc"}]}
  ]
  guid = "_STiW5zY86Lto5V4n8hb1vRyIgw"
}

// Queixa selecionável na triagem, com prioridade padrão.
table sintoma {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text nome filters=trim
    text descricao?
    enum grupo {
      values = ["CARDIOVASCULAR", "RESPIRATORIO", "NEUROLOGICO", "GASTROINTESTINAL", "TRAUMATICO_ORTOPEDICO", "GERAL"]
    }
    enum prioridade_padrao {
      values = ["VERMELHA", "AMARELA", "AZUL"]
    }
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "nome", op: "asc"}]}
  ]
  guid = "CRt2qRa0CUqbIMdWdVpNTRZW-0c"
}

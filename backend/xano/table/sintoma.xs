// Queixa selecionável na triagem, com pontuação acadêmica para composição futura do escore.
table sintoma {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text nome filters=trim
    text descricao?
    enum grupo {
      values = ["CARDIOVASCULAR", "RESPIRATORIO", "NEUROLOGICO", "GASTROINTESTINAL", "TRAUMATICO_ORTOPEDICO", "TRAUMATICO_NEUROLOGICO", "GERAL"]
    }
    int pontuacao filters=min:1|max:3
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "nome", op: "asc"}]}
  ]
  guid = "CRt2qRa0CUqbIMdWdVpNTRZW-0c"
}

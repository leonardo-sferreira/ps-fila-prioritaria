query "sintomas" verb=GET {
  api_group = "Triagem"
  description = "Lista o catálogo ativo de sintomas com a pontuação acadêmica da triagem."

  input {
  }

  stack {
    db.query "sintoma" {
      where = $db.sintoma.ativo == true
      sort = { nome: "asc" }
    } as $sintomas
  }

  response = $sintomas|map:{id: $$.id, nome: $$.nome, descricao: $$.descricao, grupo: $$.grupo, pontuacao: $$.pontuacao}
  guid = "L_FtBeusXNd0hegHQ00p7-_2Wf4"
}

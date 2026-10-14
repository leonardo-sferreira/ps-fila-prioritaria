query "fichas/{ficha_id}" verb=GET {
  api_group = "Triagem"
  description = "Retorna a ficha e os dados necessários para edição de sintomas e queixa geral."

  input { int ficha_id }

  stack {
    db.get ficha_atendimento {
      field_name = "id"
      field_value = $input.ficha_id
    } as $ficha

    precondition ($ficha != null) {
      error_type = "notfound"
      error = "FICHA_NAO_ENCONTRADA"
    }

    db.get paciente {
      field_name = "id"
      field_value = $ficha.paciente_id
    } as $paciente

    db.query sintoma {
      join = {
        ficha_sintoma: {
          table: "ficha_sintoma",
          where: $db.sintoma.id == $db.ficha_sintoma.sintoma_id
        }
      }
      where = $db.ficha_sintoma.ficha_id == $ficha.id
      return = {type: "list"}
    } as $sintomas
  }

  response = {
    ficha: { id: $ficha.id, paciente_id: $ficha.paciente_id, chegada_em: $ficha.chegada_em, status: $ficha.status, observacao: $ficha.observacao },
    paciente: { id: $paciente.id, cpf: $paciente.cpf, nome: $paciente.nome, data_nascimento: $paciente.data_nascimento },
    sintomas: $sintomas|map:{id: $$.id, nome: $$.nome, descricao: $$.descricao, grupo: $$.grupo, pontuacao: $$.pontuacao}
  }
  guid = "SVGFF-bcUFA-eaJt_rWal1sfpEY"
}

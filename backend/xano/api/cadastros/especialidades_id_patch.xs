// Edita nome e descrição da especialidade. A sigla não muda depois de criada: compõe as senhas já emitidas
// (add-cadastros-administrador).
query "especialidades/{especialidade_id}" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int especialidade_id
    text nome filters=trim
    text? descricao? filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    precondition (($input.nome|strlen) > 0) {
      error_type = "inputerror"
      error = "Informe o nome da especialidade."
    }

    db.get especialidade {
      field_name = "id"
      field_value = $input.especialidade_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Especialidade não encontrada."
    }

    var $nome_normalizado { value = $input.nome|to_lower }

    db.query especialidade {
      where = $db.especialidade.nome_normalizado == $nome_normalizado && $db.especialidade.id != $anterior.id
      return = {type: "exists"}
    } as $repetida

    precondition (!$repetida) {
      error_type = "inputerror"
      error = "Já existe especialidade com este nome."
    }

    db.transaction {
      stack {
        db.edit especialidade {
          field_name = "id"
          field_value = $anterior.id
          data = {nome: $input.nome, nome_normalizado: $nome_normalizado, descricao: $input.descricao}
        } as $especialidade

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "ESPECIALIDADE_EDITADA", entidade: "ESPECIALIDADE", registro_id: $anterior.id, valor_anterior: {nome: $anterior.nome, descricao: $anterior.descricao}, valor_novo: {nome: $especialidade.nome, descricao: $especialidade.descricao}}
        } as $auditoria
      }
    }
  }

  response = {id: $especialidade.id, nome: $especialidade.nome, sigla: $especialidade.sigla, descricao: $especialidade.descricao, ativo: $especialidade.ativo}
}

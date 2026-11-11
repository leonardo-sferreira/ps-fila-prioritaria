// Edita nome e descrição da sala (add-cadastros-administrador).
query "salas/{sala_id}" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int sala_id
    text nome filters=trim
    text? descricao? filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get sala {
      field_name = "id"
      field_value = $input.sala_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Sala não encontrada."
    }

    precondition (($input.nome|strlen) > 0) {
      error_type = "inputerror"
      error = "Informe o nome da sala."
    }

    var $nome_normalizado { value = $input.nome|to_lower }

    db.get sala {
      field_name = "nome_normalizado"
      field_value = $nome_normalizado
    } as $existente

    precondition ($existente == null || $existente.id == $anterior.id) {
      error_type = "inputerror"
      error = "Já existe sala com este nome."
    }

    db.transaction {
      stack {
        db.edit sala {
          field_name = "id"
          field_value = $anterior.id
          data = {nome: $input.nome, nome_normalizado: $nome_normalizado, descricao: $input.descricao}
        } as $sala

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "SALA_EDITADA", entidade: "SALA", registro_id: $anterior.id, valor_anterior: {nome: $anterior.nome, descricao: $anterior.descricao}, valor_novo: {nome: $sala.nome, descricao: $sala.descricao}}
        } as $auditoria
      }
    }
  }

  response = {id: $sala.id, nome: $sala.nome, descricao: $sala.descricao, ativo: $sala.ativo}
}

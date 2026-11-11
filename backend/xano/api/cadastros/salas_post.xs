// Cria sala com nome único (sem diferenciar maiúsculas) e descrição opcional (add-cadastros-administrador, D5).
query salas verb=POST {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    text nome filters=trim
    text? descricao? filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    precondition (($input.nome|strlen) > 0) {
      error_type = "inputerror"
      error = "Informe o nome da sala."
    }

    var $nome_normalizado { value = $input.nome|to_lower }

    db.get sala {
      field_name = "nome_normalizado"
      field_value = $nome_normalizado
    } as $existente

    precondition ($existente == null) {
      error_type = "inputerror"
      error = "Já existe sala com este nome."
    }

    db.transaction {
      stack {
        db.add sala {
          data = {nome: $input.nome, nome_normalizado: $nome_normalizado, descricao: $input.descricao, ativo: true}
        } as $sala

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "SALA_CRIADA", entidade: "SALA", registro_id: $sala.id, valor_anterior: null, valor_novo: {nome: $sala.nome, descricao: $sala.descricao}}
        } as $auditoria
      }
    }
  }

  response = {id: $sala.id, nome: $sala.nome, descricao: $sala.descricao, ativo: true, medicos: 0}
}

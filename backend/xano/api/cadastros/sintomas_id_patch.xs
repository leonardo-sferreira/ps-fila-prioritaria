// Edita sintoma e substitui os destinos (add-cadastros-administrador). Fichas antigas mantêm o sintoma.
query "sintomas/{sintoma_id}" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int sintoma_id
    text nome filters=trim
    text? descricao? filters=trim
    text grupo filters=trim|upper
    int pontuacao
    json especialidade_ids
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get sintoma {
      field_name = "id"
      field_value = $input.sintoma_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Sintoma não encontrado."
    }

    precondition (($input.nome|strlen) >= 3) {
      error_type = "inputerror"
      error = "Informe o nome do sintoma (3 ou mais caracteres)."
    }

    precondition ($input.pontuacao >= 1 && $input.pontuacao <= 3) {
      error_type = "inputerror"
      error = "A pontuação deve ser 1, 2 ou 3."
    }

    precondition (["CARDIOVASCULAR", "RESPIRATORIO", "NEUROLOGICO", "GASTROINTESTINAL", "TRAUMATICO_ORTOPEDICO", "TRAUMATICO_NEUROLOGICO", "GERAL"]|in:$input.grupo) {
      error_type = "inputerror"
      error = "Grupo de sintoma inválido."
    }

    db.query sintoma {
      where = $db.sintoma.id != $anterior.id
      return = {type: "list"}
    } as $outros

    var $nome_minusculo { value = $input.nome|to_lower }
    var $repetido { value = $outros|some:(($$.nome|to_lower) == $nome_minusculo) }

    precondition (!$repetido) {
      error_type = "inputerror"
      error = "Já existe sintoma com este nome."
    }

    function.run "cadastros/especialidades_validas" {
      input = {especialidade_ids: $input.especialidade_ids}
    } as $destinos

    db.query sintoma_especialidade {
      where = $db.sintoma_especialidade.sintoma_id == $anterior.id
      sort = {ordem: "asc"}
      return = {type: "list"}
    } as $destinos_anteriores

    var $ids_anteriores { value = $destinos_anteriores|map:$$.especialidade_id }

    db.transaction {
      stack {
        db.edit sintoma {
          field_name = "id"
          field_value = $anterior.id
          data = {nome: $input.nome, descricao: $input.descricao, grupo: $input.grupo, pontuacao: $input.pontuacao}
        } as $sintoma

        function.run "cadastros/gravar_vinculos" {
          input = {tipo: "SINTOMA", dono_id: $anterior.id, especialidade_ids: $destinos}
        } as $gravados

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "SINTOMA_EDITADO", entidade: "SINTOMA", registro_id: $anterior.id, valor_anterior: {nome: $anterior.nome, grupo: $anterior.grupo, pontuacao: $anterior.pontuacao, especialidade_ids: $ids_anteriores}, valor_novo: {nome: $sintoma.nome, grupo: $sintoma.grupo, pontuacao: $sintoma.pontuacao, especialidade_ids: $destinos}}
        } as $auditoria
      }
    }
  }

  response = {id: $sintoma.id, nome: $sintoma.nome, ativo: $sintoma.ativo, especialidade_ids: $destinos}
}

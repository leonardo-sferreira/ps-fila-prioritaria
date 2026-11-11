// Cria sintoma do catálogo com pontuação 1–3 e destinos em ordem de preferência (add-cadastros-administrador).
query sintomas verb=POST {
  api_group = "Cadastros"
  auth = "usuario"

  input {
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
      return = {type: "list"}
    } as $todos

    var $nome_minusculo { value = $input.nome|to_lower }
    var $repetido { value = $todos|some:(($$.nome|to_lower) == $nome_minusculo) }

    precondition (!$repetido) {
      error_type = "inputerror"
      error = "Já existe sintoma com este nome."
    }

    function.run "cadastros/especialidades_validas" {
      input = {especialidade_ids: $input.especialidade_ids}
    } as $destinos

    db.transaction {
      stack {
        db.add sintoma {
          data = {nome: $input.nome, descricao: $input.descricao, grupo: $input.grupo, pontuacao: $input.pontuacao, ativo: true}
        } as $sintoma

        function.run "cadastros/gravar_vinculos" {
          input = {tipo: "SINTOMA", dono_id: $sintoma.id, especialidade_ids: $destinos}
        } as $gravados

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "SINTOMA_CRIADO", entidade: "SINTOMA", registro_id: $sintoma.id, valor_anterior: null, valor_novo: {nome: $sintoma.nome, grupo: $sintoma.grupo, pontuacao: $sintoma.pontuacao, especialidade_ids: $destinos}}
        } as $auditoria
      }
    }
  }

  response = {id: $sintoma.id, nome: $sintoma.nome, ativo: true, especialidade_ids: $destinos}
  guid = "pN-i3r7R2ZJ_oiCqJIV5xhJU12Q"
}

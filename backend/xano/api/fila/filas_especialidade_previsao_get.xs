query "filas/{especialidade}/previsao" verb=GET {
  api_group = "Fila"
  auth = "usuario"

  input {
    int especialidade
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $auth.id
        perfis_permitidos: ["RECEPCAO_TRIAGEM", "MEDICO", "ADMINISTRADOR"]
      }
    } as $usuario

    db.get especialidade {
      field_name = "id"
      field_value = $input.especialidade
    } as $especialidade

    precondition ($especialidade != null) {
      error_type = "notfound"
      error = "ESPECIALIDADE_NAO_ENCONTRADA"
    }

    // Mesma montagem usada pelo painel público (add-painel-publico, D1).
    function.run "fila/previsao_especialidade" {
      input = {especialidade_id: $especialidade.id}
    } as $previsao
  }

  response = $previsao
  guid = "t-7XJLFYNQ_ve7OWc82CEULQAXk"
}
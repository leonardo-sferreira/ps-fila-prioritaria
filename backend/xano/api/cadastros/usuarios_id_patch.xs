// Edita nome e e-mail de um Administrador (add-autenticacao-perfis, D14). Médicos e Recepção/Triagem são editados
// pelos cadastros.
query "usuarios/{usuario_id}" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int usuario_id
    text nome filters=trim
    text email filters=trim|lower
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get usuario {
      field_name = "id"
      field_value = $input.usuario_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }

    precondition ($anterior.perfil == "ADMINISTRADOR") {
      error_type = "inputerror"
      error = "USUARIO_EDITADO_NOS_CADASTROS"
    }

    precondition (($input.nome|strlen) >= 3) {
      error_type = "inputerror"
      error = "Informe o nome."
    }

    function.run "cadastros/email_livre" {
      input = {email: $input.email, ignorar_usuario_id: $anterior.id}
    } as $email

    db.transaction {
      stack {
        db.edit usuario {
          field_name = "id"
          field_value = $anterior.id
          data = {nome: $input.nome, email: $email}
        } as $editado

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "ADMINISTRADOR_EDITADO", entidade: "USUARIO", registro_id: $anterior.id, valor_anterior: {nome: $anterior.nome, email: $anterior.email}, valor_novo: {nome: $editado.nome, email: $editado.email}}
        } as $auditoria
      }
    }
  }

  response = {id: $editado.id, nome: $editado.nome, email: $editado.email, perfil: $editado.perfil, ativo: $editado.ativo}
  guid = "OyeNbp_9SV_E5OtwAbIxhjbWAMo"
}

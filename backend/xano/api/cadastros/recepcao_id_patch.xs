// Edita nome e e-mail (no login), CPF e especialidade de referência da Recepção/Triagem (add-cadastros-administrador).
query "recepcao/{recepcao_id}" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int recepcao_id
    text nome filters=trim
    text email filters=trim|lower
    text cpf filters=trim
    int? especialidade_referencia_id?
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get recepcao_triagem {
      field_name = "id"
      field_value = $input.recepcao_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Cadastro não encontrado."
    }

    db.get usuario {
      field_name = "id"
      field_value = $anterior.usuario_id
    } as $login_anterior

    // Depois de uma troca de perfil o cadastro antigo fica só como histórico: não mexe mais no login (D14).
    precondition ($login_anterior.perfil == "RECEPCAO_TRIAGEM") {
      error_type = "inputerror"
      error = "CADASTRO_DE_OUTRO_PERFIL"
    }

    precondition (($input.nome|strlen) >= 3) {
      error_type = "inputerror"
      error = "Informe o nome."
    }

    function.run "pacientes/normalizar_cpf" {
      input = {cpf: $input.cpf}
    } as $cpf

    db.get recepcao_triagem {
      field_name = "cpf"
      field_value = $cpf
    } as $cpf_existente

    precondition ($cpf_existente == null || $cpf_existente.id == $anterior.id) {
      error_type = "inputerror"
      error = "CPF já cadastrado."
    }

    function.run "cadastros/email_livre" {
      input = {email: $input.email, ignorar_usuario_id: $anterior.usuario_id}
    } as $email

    var $referencia { value = ($input.especialidade_referencia_id == null || $input.especialidade_referencia_id == 0) ? null : $input.especialidade_referencia_id }
    conditional {
      if ($referencia != null) {
        function.run "cadastros/especialidades_validas" {
          input = {especialidade_ids: [$referencia]}
        } as $referencia_ok
      }
    }

    db.transaction {
      stack {
        db.edit usuario {
          field_name = "id"
          field_value = $anterior.usuario_id
          data = {nome: $input.nome, email: $email}
        } as $login

        db.edit recepcao_triagem {
          field_name = "id"
          field_value = $anterior.id
          data = {cpf: $cpf, especialidade_referencia_id: $referencia}
        } as $cadastro

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "RECEPCAO_EDITADA", entidade: "RECEPCAO_TRIAGEM", registro_id: $anterior.id, valor_anterior: {nome: $login_anterior.nome, email: $login_anterior.email, especialidade_referencia_id: $anterior.especialidade_referencia_id}, valor_novo: {nome: $login.nome, email: $login.email, especialidade_referencia_id: $referencia}}
        } as $auditoria
      }
    }
  }

  response = {id: $cadastro.id, nome: $login.nome, email: $login.email, cpf: $cpf, especialidade_referencia_id: $referencia, ativo: $cadastro.ativo}
  guid = "Zl8ULrWKdFG_1AlYG_CUMrvCMOk"
}

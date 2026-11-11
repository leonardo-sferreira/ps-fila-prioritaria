// Ativa ou desativa um Administrador (add-autenticacao-perfis, D9/D14). Não desativa a si mesmo nem o último
// administrador ativo. Médicos e Recepção/Triagem são ativados/desativados pelos cadastros, junto com o cadastro.
query "usuarios/{usuario_id}/ativo" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int usuario_id
    bool ativo
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

    conditional {
      if (!$input.ativo) {
        precondition ($anterior.id != $usuario.id) {
          error_type = "inputerror"
          error = "Não é possível desativar o próprio usuário"
        }

        db.query usuario {
          where = $db.usuario.perfil == "ADMINISTRADOR" && $db.usuario.ativo == true
          return = {type: "list"}
        } as $admins

        function.run "usuarios/deixa_sem_admin" {
          input = {admins_ativos: $admins|map:$$.id, usuario_id: $anterior.id}
        } as $sem_admin

        precondition (!$sem_admin) {
          error_type = "inputerror"
          error = "ULTIMO_ADMINISTRADOR"
        }
      }
    }

    db.transaction {
      stack {
        db.edit usuario {
          field_name = "id"
          field_value = $anterior.id
          data = {ativo: $input.ativo}
        } as $editado

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: ($input.ativo ? "ADMINISTRADOR_ATIVADO" : "ADMINISTRADOR_DESATIVADO"), entidade: "USUARIO", registro_id: $anterior.id, valor_anterior: {ativo: $anterior.ativo}, valor_novo: {ativo: $input.ativo}}
        } as $auditoria
      }
    }
  }

  response = {id: $editado.id, ativo: $editado.ativo}
}

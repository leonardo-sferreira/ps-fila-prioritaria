// Ativa ou desativa um usuário de qualquer perfil (add-autenticacao-perfis, D9/D14; revisão de 14/11/2026). Não
// desativa a si mesmo nem o último administrador ativo. O cadastro de Médico ou Recepção/Triagem, quando existe,
// acompanha o login na mesma transação.
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

    db.get medico {
      field_name = "usuario_id"
      field_value = $anterior.id
    } as $medico_existente

    db.get recepcao_triagem {
      field_name = "usuario_id"
      field_value = $anterior.id
    } as $recepcao_existente

    // Médico não é desativado com ficha chamada em andamento (mesma regra de medicos/{id}/ativo).
    conditional {
      if (!$input.ativo && $anterior.perfil == "MEDICO" && $medico_existente != null) {
        db.query ficha_atendimento {
          where = $db.ficha_atendimento.status == "CHAMADO" && $db.ficha_atendimento.medico_chamada_id == $medico_existente.id
          return = {type: "exists"}
        } as $com_chamada
        precondition (!$com_chamada) {
          error_type = "inputerror"
          error = "MEDICO_COM_FICHA_CHAMADA"
        }
      }
    }

    db.transaction {
      stack {
        conditional {
          if ($anterior.perfil == "MEDICO" && $medico_existente != null) {
            db.edit medico {
              field_name = "id"
              field_value = $medico_existente.id
              data = {ativo: $input.ativo}
            } as $medico_editado
          }
          elseif ($anterior.perfil == "RECEPCAO_TRIAGEM" && $recepcao_existente != null) {
            db.edit recepcao_triagem {
              field_name = "id"
              field_value = $recepcao_existente.id
              data = {ativo: $input.ativo}
            } as $recepcao_editada
          }
        }

        db.edit usuario {
          field_name = "id"
          field_value = $anterior.id
          data = {ativo: $input.ativo}
        } as $editado

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: ($input.ativo ? "USUARIO_ATIVADO" : "USUARIO_DESATIVADO"), entidade: "USUARIO", registro_id: $anterior.id, valor_anterior: {ativo: $anterior.ativo, perfil: $anterior.perfil}, valor_novo: {ativo: $input.ativo, perfil: $anterior.perfil}}
        } as $auditoria

        // Confere de novo, já com a gravação feita: duas desativações simultâneas não podem zerar os administradores.
        db.query usuario {
          where = $db.usuario.perfil == "ADMINISTRADOR" && $db.usuario.ativo == true
          return = {type: "count"}
        } as $admins_depois

        precondition ($admins_depois > 0) {
          error_type = "inputerror"
          error = "ULTIMO_ADMINISTRADOR"
        }
      }
    }
  }

  response = {id: $editado.id, ativo: $editado.ativo}
  guid = "efSAnMhfJgkzmkQ6OBHU63J7a9s"
}

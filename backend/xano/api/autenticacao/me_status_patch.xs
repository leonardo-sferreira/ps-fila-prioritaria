query "me/status" verb=PATCH {
  api_group = "Autenticacao"
  auth = "usuario"

  input {
    enum status {
      values = ["DISPONIVEL", "PAUSA", "AUSENTE"]
    }
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["MEDICO", "RECEPCAO_TRIAGEM"]}
    } as $usuario

    db.query sessao {
      where = $db.sessao.usuario_id == $usuario.id && $db.sessao.logout_em == null && $db.sessao.expira_em > now
      sort = {login_em: "desc"}
      return = {type: "single"}
    } as $sessao

    precondition ($sessao != null) {
      error_type = "unauthorized"
      error = "Sessão expirada. Faça login novamente."
    }

    conditional {
      if ($usuario.perfil == "MEDICO" && $input.status == "DISPONIVEL") {
        db.get medico {
          field_name = "usuario_id"
          field_value = $usuario.id
        } as $medico

        precondition ($medico != null && $medico.ativo) {
          error_type = "accessdenied"
          error = "Médico inativo."
        }

        db.query disponibilidade_medico {
          where = $db.disponibilidade_medico.medico_id == $medico.id && $db.disponibilidade_medico.inicio <= now && $db.disponibilidade_medico.fim > now && $db.disponibilidade_medico.encerrado_em == null
          return = {type: "exists"}
        } as $plantao

        precondition ($plantao) {
          error_type = "accessdenied"
          error = "Não há plantão vigente para ficar disponível."
        }
      }
    }

    db.edit sessao {
      field_name = "id"
      field_value = $sessao.id
      data = {status_operacional: $input.status}
    } as $atualizada
  }

  response = {status: $atualizada.status_operacional}
  guid = "mhjtw0_ikLClIWGkBNEgBBR4V94"
}

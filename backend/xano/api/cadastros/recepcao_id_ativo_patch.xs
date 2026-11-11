// Ativa ou desativa a pessoa da Recepção/Triagem e o login dela juntos (add-cadastros-administrador, D3).
query "recepcao/{recepcao_id}/ativo" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int recepcao_id
    bool ativo
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
    } as $login_atual

    // Depois de uma troca de perfil o cadastro antigo fica só como histórico: não mexe mais no login (D14).
    precondition ($login_atual.perfil == "RECEPCAO_TRIAGEM") {
      error_type = "inputerror"
      error = "CADASTRO_DE_OUTRO_PERFIL"
    }

    db.transaction {
      stack {
        db.edit recepcao_triagem {
          field_name = "id"
          field_value = $anterior.id
          data = {ativo: $input.ativo}
        } as $cadastro

        db.edit usuario {
          field_name = "id"
          field_value = $anterior.usuario_id
          data = {ativo: $input.ativo}
        } as $login

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: ($input.ativo ? "RECEPCAO_ATIVADA" : "RECEPCAO_DESATIVADA"), entidade: "RECEPCAO_TRIAGEM", registro_id: $anterior.id, valor_anterior: {ativo: $anterior.ativo}, valor_novo: {ativo: $input.ativo}}
        } as $auditoria
      }
    }
  }

  response = {id: $cadastro.id, ativo: $cadastro.ativo}
  guid = "wl7cEgoRkIL9CkhA1BzFoT3YY2I"
}

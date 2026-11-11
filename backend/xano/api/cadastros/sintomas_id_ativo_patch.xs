// Ativa ou desativa o sintoma. Inativo deixa de aparecer na triagem; fichas antigas continuam com ele
// (add-cadastros-administrador).
query "sintomas/{sintoma_id}/ativo" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int sintoma_id
    bool ativo
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

    db.transaction {
      stack {
        db.edit sintoma {
          field_name = "id"
          field_value = $anterior.id
          data = {ativo: $input.ativo}
        } as $sintoma

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: ($input.ativo ? "SINTOMA_ATIVADO" : "SINTOMA_DESATIVADO"), entidade: "SINTOMA", registro_id: $anterior.id, valor_anterior: {ativo: $anterior.ativo}, valor_novo: {ativo: $input.ativo}}
        } as $auditoria
      }
    }
  }

  response = {id: $sintoma.id, ativo: $sintoma.ativo}
}

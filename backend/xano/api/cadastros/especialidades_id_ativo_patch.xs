// Ativa ou desativa a especialidade. Não desativa a especialidade padrão nem a que tem fichas AGUARDANDO/CHAMADO
// (add-cadastros-administrador).
query "especialidades/{especialidade_id}/ativo" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int especialidade_id
    bool ativo
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get especialidade {
      field_name = "id"
      field_value = $input.especialidade_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Especialidade não encontrada."
    }

    conditional {
      if (!$input.ativo) {
        db.get parametro {
          field_name = "chave"
          field_value = "ESPECIALIDADE_PADRAO"
        } as $padrao

        var $id_padrao { value = ($padrao == null) ? 0 : ($padrao.valor|to_int) }

        precondition ($id_padrao != $anterior.id) {
          error_type = "inputerror"
          error = "Esta é a especialidade padrão: troque o parâmetro antes de desativá-la."
        }

        db.query ficha_atendimento {
          where = $db.ficha_atendimento.especialidade_atribuida_id == $anterior.id && $db.ficha_atendimento.status in ["AGUARDANDO", "CHAMADO"]
          return = {type: "exists"}
        } as $com_fichas

        precondition (!$com_fichas) {
          error_type = "inputerror"
          error = "ESPECIALIDADE_COM_FICHAS"
        }
      }
    }

    db.transaction {
      stack {
        db.edit especialidade {
          field_name = "id"
          field_value = $anterior.id
          data = {ativo: $input.ativo}
        } as $especialidade

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: ($input.ativo ? "ESPECIALIDADE_ATIVADA" : "ESPECIALIDADE_DESATIVADA"), entidade: "ESPECIALIDADE", registro_id: $anterior.id, valor_anterior: {ativo: $anterior.ativo}, valor_novo: {ativo: $input.ativo}}
        } as $auditoria
      }
    }
  }

  response = {id: $especialidade.id, ativo: $especialidade.ativo}
}

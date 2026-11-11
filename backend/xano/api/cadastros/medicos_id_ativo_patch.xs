// Ativa ou desativa o médico e o login dele juntos (add-cadastros-administrador, D3).
// Não desativa enquanto houver ficha CHAMADO pendente com o médico.
query "medicos/{medico_id}/ativo" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int medico_id
    bool ativo
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get medico {
      field_name = "id"
      field_value = $input.medico_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Médico não encontrado."
    }

    conditional {
      if (!$input.ativo) {
        db.query ficha_atendimento {
          where = $db.ficha_atendimento.status == "CHAMADO" && $db.ficha_atendimento.medico_chamada_id == $anterior.id
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
        db.edit medico {
          field_name = "id"
          field_value = $anterior.id
          data = {ativo: $input.ativo}
        } as $medico

        db.edit usuario {
          field_name = "id"
          field_value = $anterior.usuario_id
          data = {ativo: $input.ativo}
        } as $login

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: ($input.ativo ? "MEDICO_ATIVADO" : "MEDICO_DESATIVADO"), entidade: "MEDICO", registro_id: $anterior.id, valor_anterior: {ativo: $anterior.ativo}, valor_novo: {ativo: $input.ativo}}
        } as $auditoria
      }
    }
  }

  response = {id: $medico.id, ativo: $medico.ativo}
}

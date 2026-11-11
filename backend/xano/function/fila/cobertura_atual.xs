// Carrega médicos com plantão e sessão vigentes e calcula cobertura das especialidades próprias.
function "fila/cobertura_atual" {
  input {
  }

  stack {
    db.query medico {
      return = {type: "list"}
    } as $medicos

    var $instantaneo {
      value = []
    }

    foreach ($medicos) {
      each as $medico {
        db.get usuario {
          field_name = "id"
          field_value = $medico.usuario_id
        } as $usuario

        db.query disponibilidade_medico {
          where = $db.disponibilidade_medico.medico_id == $medico.id && $db.disponibilidade_medico.inicio <= now && $db.disponibilidade_medico.fim > now && $db.disponibilidade_medico.encerrado_em == null
          return = {type: "list"}
        } as $periodos

        db.query sessao {
          where = $db.sessao.usuario_id == $medico.usuario_id && $db.sessao.logout_em == null && $db.sessao.expira_em > now
          sort = {login_em: "desc"}
          return = {type: "list"}
        } as $sessoes

        var $sessao {
          value = $sessoes|first
        }

        db.query medico_especialidade {
          where = $db.medico_especialidade.medico_id == $medico.id
          return = {type: "list"}
        } as $vinculos

        var.update $instantaneo {
          value = $instantaneo
            |push:{id: $medico.id, usuario_id: $medico.usuario_id, medico_ativo: $medico.ativo, usuario_ativo: ($usuario != null && $usuario.ativo == true), plantao_vigente: (($periodos|count) > 0), sessao_ativa: ($sessao != null), sessao_id: ($sessao == null) ? null : $sessao.id, status: ($sessao == null) ? null : $sessao.status_operacional, especialidade_ids: $vinculos|map:$$.especialidade_id}
        }
      }
    }

    function.run "fila/avaliar_cobertura" {
      input = {medicos: $instantaneo}
    } as $resultado
  }

  response = $resultado
  guid = "4ffJLdazrQAIhrP7HUNL0XL2toI"
}

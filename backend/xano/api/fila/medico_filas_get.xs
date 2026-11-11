query "medico/filas" verb=GET {
  api_group = "Fila"
  auth = "usuario"

  input {
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["MEDICO"]}
    } as $usuario

    db.get medico {
      field_name = "usuario_id"
      field_value = $usuario.id
    } as $medico

    precondition ($medico != null && $medico.ativo) {
      error_type = "accessdenied"
      error = "MEDICO_INATIVO"
    }

    function.run "fila/cobertura_atual" as $cobertura
    var $apto {
      value = $cobertura.medicos|find:$$.id == $medico.id
    }

    db.query disponibilidade_medico {
      where = $db.disponibilidade_medico.medico_id == $medico.id && $db.disponibilidade_medico.inicio <= now && $db.disponibilidade_medico.fim > now && $db.disponibilidade_medico.encerrado_em == null
      return = {type: "exists"}
    } as $plantao

    db.query sessao {
      where = $db.sessao.usuario_id == $usuario.id && $db.sessao.logout_em == null && $db.sessao.expira_em > now
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

    var $proprias {
      value = $vinculos|map:$$.especialidade_id
    }

    db.query especialidade {
      return = {type: "list"}
    } as $especialidades

    var $filas {
      value = []
    }

    foreach ($especialidades) {
      each as $especialidade {
        db.query ficha_atendimento {
          where = $db.ficha_atendimento.status == "AGUARDANDO" && $db.ficha_atendimento.especialidade_atribuida_id == $especialidade.id
          return = {type: "count"}
        } as $quantidade

        var.update $filas {
          value = $filas
            |push:{especialidade_id: $especialidade.id, nome: $especialidade.nome, sigla: $especialidade.sigla, propria: ($proprias|contains:$especialidade.id), coberta: ($cobertura.especialidade_ids|contains:$especialidade.id), aguardando: $quantidade}
        }
      }
    }

    db.query ficha_atendimento {
      where = $db.ficha_atendimento.medico_chamada_id == $medico.id && $db.ficha_atendimento.status == "CHAMADO"
      return = {type: "single"}
    } as $ficha

    var $ficha_atual {
      value = null
    }

    var $historico {
      value = []
    }

    conditional {
      if ($ficha != null) {
        db.get paciente {
          field_name = "id"
          field_value = $ficha.paciente_id
        } as $paciente

        db.get especialidade {
          field_name = "id"
          field_value = $ficha.especialidade_atribuida_id
        } as $especialidade_atual

        db.query chamada {
          where = $db.chamada.ficha_id == $ficha.id
          sort = {created_at: "asc"}
          return = {type: "list"}
        } as $eventos

        var.update $historico {
          value = $eventos|map:{oportunidade: $$.oportunidade, tentativa: $$.tentativa, tipo: $$.tipo, medico_id: $$.medico_id, em: $$.created_at}
        }

        var.update $ficha_atual {
          value = {
            id              : $ficha.id
            senha           : $ficha.senha
            nome            : ($paciente == null) ? null : $paciente.nome
            especialidade_id: $ficha.especialidade_atribuida_id
            especialidade   : ($especialidade_atual == null) ? null : $especialidade_atual.nome
            prioridade      : $ficha.prioridade_atual
            oportunidade    : $ficha.oportunidade ?? 1
            tentativa       : $ficha.tentativas_chamada
            chamada_em      : $ficha.chamada_em
            status          : $ficha.status
          }
        }
      }
    }
  }

  response = {
    medico     : {id: $medico.id, apto: ($apto != null), status: ($sessao == null) ? "SEM_SESSAO" : $sessao.status_operacional, plantao_vigente: $plantao}
    filas      : $filas
    ficha_atual: $ficha_atual
    historico  : $historico
  }

  guid = "3lPl64a-2hX9CirWsH5E8waQApg"
}

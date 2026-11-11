// Fichas do dia da Recepção/Triagem (add-fichas-do-dia, D1): não finalizadas de qualquer data e finalizadas com
// chegada hoje (America/Sao_Paulo), da mais recente para a mais antiga. Sem CPF, sintomas ou sinais vitais.
query "fichas" verb=GET {
  api_group = "Triagem"
  description = "Lista as fichas não finalizadas e as finalizadas de hoje, com paciente (nome), senha, cor, especialidade e situação."

  auth = "usuario"

  input {}

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM"]}
    } as $usuario

    var $inicio_do_dia {
      value = "today"|to_timestamp:"America/Sao_Paulo"
    }

    db.query ficha_atendimento {
      where = $db.ficha_atendimento.status in ["EM_TRIAGEM", "AGUARDANDO", "CHAMADO"] || $db.ficha_atendimento.chegada_em >= $inicio_do_dia
      sort = {chegada_em: "desc", id: "desc"}
      return = {type: "list"}
    } as $fichas

    var $paciente_ids {
      value = $fichas|map:$$.paciente_id|unique
    }

    db.query paciente {
      where = $db.paciente.id in $paciente_ids
      return = {type: "list"}
    } as $pacientes

    db.query especialidade {
      return = {type: "list"}
    } as $especialidades

    var $lista { value = [] }

    foreach ($fichas) {
      each as $ficha {
        var $paciente {
          value = $pacientes|find:($$.id == $ficha.paciente_id)
        }
        var $especialidade {
          value = $especialidades|find:($$.id == $ficha.especialidade_atribuida_id)
        }
        var $nome_paciente {
          value = ($paciente == null) ? null : $paciente.nome
        }
        var $nome_especialidade {
          value = ($especialidade == null) ? null : $especialidade.nome
        }
        var.update $lista {
          value = $lista|push:{id: $ficha.id, status: $ficha.status, chegada_em: $ficha.chegada_em, senha: $ficha.senha, prioridade_atual: $ficha.prioridade_atual, especialidade: $nome_especialidade, paciente: {id: $ficha.paciente_id, nome: $nome_paciente}}
        }
      }
    }
  }

  response = {fichas: $lista, agora: now}
  guid = "r3ZFGG01ykvkFwO6-3DPV2iOgM4"
}

// Detalhe de uma ficha para o Administrador, só leitura (add-acompanhamento-administrador, tarefa 2.2).
// Triagem (sinais vitais, sintomas, escore e cor), especialidades sugerida e atribuída, senhas que a ficha teve,
// chamadas e histórico de alterações. Sem nome nem CPF do paciente.
query "admin/fichas/{ficha_id}" verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int ficha_id
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get ficha_atendimento {
      field_name = "id"
      field_value = $input.ficha_id
    } as $ficha

    precondition ($ficha != null) {
      error_type = "notfound"
      error = "Ficha não encontrada."
    }

    db.query especialidade {
      return = {type: "list"}
    } as $especialidades

    db.query usuario {
      return = {type: "list"}
    } as $usuarios

    db.query medico {
      return = {type: "list"}
    } as $medicos

    var $sugerida { value = ($ficha.especialidade_sugerida_id == null) ? null : ($especialidades|find:($$.id == $ficha.especialidade_sugerida_id)) }
    var $atribuida { value = ($ficha.especialidade_atribuida_id == null) ? null : ($especialidades|find:($$.id == $ficha.especialidade_atribuida_id)) }

    // Sintomas do catálogo e sintomas digitados.
    db.query ficha_sintoma {
      where = $db.ficha_sintoma.ficha_id == $ficha.id
      return = {type: "list"}
    } as $ligacoes

    db.query sintoma {
      return = {type: "list"}
    } as $catalogo

    var $sintomas { value = [] }
    foreach ($ligacoes) {
      each as $lig {
        var $s { value = $catalogo|find:($$.id == $lig.sintoma_id) }
        var.update $sintomas { value = $sintomas|push:{nome: (($s == null) ? "—" : $s.nome), pontuacao: (($s == null) ? null : $s.pontuacao), digitado: false} }
      }
    }

    db.query ficha_sintoma_livre {
      where = $db.ficha_sintoma_livre.ficha_id == $ficha.id
      return = {type: "list"}
    } as $livres

    foreach ($livres) {
      each as $livre {
        var.update $sintomas { value = $sintomas|push:{nome: $livre.descricao, pontuacao: $livre.pontuacao, digitado: true} }
      }
    }

    // Chamadas, da mais antiga para a mais recente.
    db.query chamada {
      where = $db.chamada.ficha_id == $ficha.id
      sort = {created_at: "asc"}
      return = {type: "list"}
    } as $registros_chamada

    var $chamadas { value = [] }
    foreach ($registros_chamada) {
      each as $ch {
        var $med { value = $medicos|find:($$.id == $ch.medico_id) }
        var $quem_ch { value = ($med == null) ? null : ($usuarios|find:($$.id == $med.usuario_id)) }
        var.update $chamadas { value = $chamadas|push:{em: $ch.created_at, tipo: $ch.tipo, tentativa: $ch.tentativa, oportunidade: $ch.oportunidade, medico: (($quem_ch == null) ? "—" : $quem_ch.nome)} }
      }
    }

    // Histórico de alterações da ficha (as duas grafias de entidade usadas pelas changes).
    db.query historico_alteracao {
      where = $db.historico_alteracao.registro_id == $ficha.id && ($db.historico_alteracao.entidade == "FICHA_ATENDIMENTO" || $db.historico_alteracao.entidade == "FICHA")
      sort = {created_at: "asc"}
      return = {type: "list"}
    } as $registros_historico

    var $historico { value = [] }
    var $senhas { value = [] }
    foreach ($registros_historico) {
      each as $h {
        var $quem_h { value = ($h.usuario_id == null) ? null : ($usuarios|find:($$.id == $h.usuario_id)) }
        var.update $historico { value = $historico|push:{em: $h.created_at, tipo_evento: $h.tipo_evento, usuario: (($h.usuario_id == null) ? "Sistema" : (($quem_h == null) ? "—" : $quem_h.nome)), valor_anterior: $h.valor_anterior, valor_novo: $h.valor_novo, justificativa: $h.justificativa} }
        var $senha_antes { value = ($h.valor_anterior == null) ? null : ($h.valor_anterior|get:"senha":null) }
        var $senha_depois { value = ($h.valor_novo == null) ? null : ($h.valor_novo|get:"senha":null) }
        conditional {
          if ($senha_antes != null && !($senhas|in:$senha_antes)) {
            var.update $senhas { value = $senhas|push:$senha_antes }
          }
        }
        conditional {
          if ($senha_depois != null && !($senhas|in:$senha_depois)) {
            var.update $senhas { value = $senhas|push:$senha_depois }
          }
        }
      }
    }

    conditional {
      if ($ficha.senha != null && !($senhas|in:$ficha.senha)) {
        var.update $senhas { value = $senhas|push:$ficha.senha }
      }
    }

    var $med_atual { value = ($ficha.medico_chamada_id == null) ? null : ($medicos|find:($$.id == $ficha.medico_chamada_id)) }
    var $quem_atual { value = ($med_atual == null) ? null : ($usuarios|find:($$.id == $med_atual.usuario_id)) }
  }

  response = {
    id                       : $ficha.id
    status                   : $ficha.status
    senha                    : $ficha.senha
    senhas                   : $senhas
    chegada_em               : $ficha.chegada_em
    fila_em                  : $ficha.fila_em
    finalizada_em            : $ficha.finalizada_em
    cor                      : $ficha.prioridade_atual
    cor_calculada            : $ficha.prioridade_calculada
    justificativa_ajuste     : $ficha.justificativa_ajuste
    condicao_prioritaria     : $ficha.condicao_prioritaria
    escore                   : $ficha.escore_risco
    gestante                 : $ficha.gestante
    sinais                   : {pa_sistolica: $ficha.pa_sistolica, fc: $ficha.fc, fr: $ficha.fr, temperatura: $ficha.temperatura, spo2: $ficha.spo2, glicemia: $ficha.glicemia}
    observacao               : $ficha.observacao
    sintomas                 : $sintomas
    especialidade_sugerida   : ($sugerida == null) ? null : $sugerida.nome
    especialidade_atribuida  : ($atribuida == null) ? null : $atribuida.nome
    medico                   : ($quem_atual == null) ? null : $quem_atual.nome
    tentativas_chamada       : $ficha.tentativas_chamada
    oportunidade             : $ficha.oportunidade
    chamadas                 : $chamadas
    historico                : $historico
  }
  guid = "V9Arx226kJyaNL062Os2GsKqDTM"
}

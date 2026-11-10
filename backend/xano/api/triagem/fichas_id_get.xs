query "fichas/{ficha_id}" verb=GET {
  api_group = "Triagem"
  description = "Retorna a ficha para edição, classificação e destino: paciente com idade, sintomas do catálogo e digitados, sinais vitais e resultado da classificação."

  auth = "usuario"

  input { int ficha_id }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM"]}
    } as $usuario

    // Só leitura: sem faixas ou parâmetros carregados, a classificação volta com pendências.
    // destino_da_ficha também calcula o destino previsto (add-direcionamento-senha, D7).
    function.run "direcionamento/destino_da_ficha" {
      input = {ficha_id: $input.ficha_id}
    } as $destino

    var $avaliacao { value = $destino.avaliacao }
    var $ficha { value = $avaliacao.ficha }

    db.get especialidade {
      field_name = "id"
      field_value = $ficha.especialidade_atribuida_id ?? 0
    } as $especialidade_atribuida
    var $paciente { value = $avaliacao.paciente }

    // Valores de referência mostrados ao lado dos sinais vitais: as faixas configuradas que valem 0 ponto.
    db.query faixa_sinal_vital {
      where = $db.faixa_sinal_vital.pontos == 0
      sort = {parametro: "asc", minimo: "asc"}
      return = {type: "list"}
    } as $faixas_referencia
  }

  response = {
    ficha: {
      id                       : $ficha.id
      paciente_id              : $ficha.paciente_id
      ticket_id                : $ficha.ticket_id
      chegada_em               : $ficha.chegada_em
      status                   : $ficha.status
      observacao               : $ficha.observacao
      gestante                 : $ficha.gestante == true
      pa_sistolica             : $ficha.pa_sistolica
      fc                       : $ficha.fc
      fr                       : $ficha.fr
      temperatura              : $ficha.temperatura
      spo2                     : $ficha.spo2
      glicemia                 : $ficha.glicemia
      glicemia_sinais_gravidade: $ficha.glicemia_sinais_gravidade == true
      senha                    : $ficha.senha
      especialidade            : ($especialidade_atribuida == null) ? null : {id: $especialidade_atribuida.id, nome: $especialidade_atribuida.nome, sigla: $especialidade_atribuida.sigla}
    }
    destino_previsto: ($ficha.status == "EM_TRIAGEM") ? {especialidade: $destino.especialidade, motivo: $destino.motivo} : null
    paciente: {id: $paciente.id, cpf: $paciente.cpf, nome: $paciente.nome, data_nascimento: $paciente.data_nascimento, idade: $avaliacao.idade}
    sintomas: $avaliacao.sintomas|map:{id: $$.id, nome: $$.nome, descricao: $$.descricao, grupo: $$.grupo, pontuacao: $$.pontuacao}
    sintomas_livres: $avaliacao.sintomas_livres|map:{id: $$.id, descricao: $$.descricao, pontuacao: $$.pontuacao}
    referencias_sinais: $faixas_referencia|map:{parametro: $$.parametro, minimo: $$.minimo, maximo: $$.maximo}
    classificacao: {
      pontos_sinais       : $avaliacao.classificacao.pontos_sinais
      escore_sintomas     : $avaliacao.classificacao.escore_sintomas
      escore_sinais       : $avaliacao.classificacao.escore_sinais
      escore_total        : $avaliacao.classificacao.escore_total
      item_critico        : $avaliacao.classificacao.item_critico
      tabela_adulta       : $avaliacao.classificacao.tabela_adulta
      pendencias          : $avaliacao.classificacao.pendencias
      condicao_prioritaria: $avaliacao.classificacao.condicao_prioritaria
      prioridade_calculada: $avaliacao.classificacao.prioridade_calculada
      prioridade_atual    : $ficha.prioridade_atual
      justificativa_ajuste: $ficha.justificativa_ajuste
    }
  }
  guid = "SVGFF-bcUFA-eaJt_rWal1sfpEY"
}

query "fichas/{ficha_id}" verb=GET {
  api_group = "Triagem"
  description = "Retorna a ficha para edição e classificação: paciente com idade, sintomas do catálogo e digitados, sinais vitais e resultado da classificação."

  auth = "usuario"

  input { int ficha_id }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM"]}
    } as $usuario

    // Só leitura: sem faixas ou parâmetros carregados, a classificação volta com pendências.
    function.run "classificacao/avaliar_ficha" {
      input = {ficha_id: $input.ficha_id}
    } as $avaliacao

    var $ficha { value = $avaliacao.ficha }
    var $paciente { value = $avaliacao.paciente }
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
    }
    paciente: {id: $paciente.id, cpf: $paciente.cpf, nome: $paciente.nome, data_nascimento: $paciente.data_nascimento, idade: $avaliacao.idade}
    sintomas: $avaliacao.sintomas|map:{id: $$.id, nome: $$.nome, descricao: $$.descricao, grupo: $$.grupo, pontuacao: $$.pontuacao}
    sintomas_livres: $avaliacao.sintomas_livres|map:{id: $$.id, descricao: $$.descricao, pontuacao: $$.pontuacao}
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

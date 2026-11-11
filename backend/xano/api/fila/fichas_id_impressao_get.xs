query "fichas/{ficha_id}/impressao" verb=GET {
  api_group = "Fila"
  auth = "usuario"

  input {
    int ficha_id
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["MEDICO"]}
    } as $usuario

    db.get medico {
      field_name = "usuario_id"
      field_value = $usuario.id
    } as $medico

    db.get ficha_atendimento {
      field_name = "id"
      field_value = $input.ficha_id
    } as $ficha

    precondition ($medico != null && $ficha != null && $ficha.medico_chamada_id == $medico.id && ($ficha.status == "CHAMADO" || $ficha.status == "ATENDIDO")) {
      error_type = "accessdenied"
      error = "FICHA_NAO_ATRIBUIDA"
    }

    function.run "classificacao/avaliar_ficha" {
      input = {ficha_id: $ficha.id}
    } as $avaliacao

    db.get especialidade {
      field_name = "id"
      field_value = $ficha.especialidade_atribuida_id
    } as $especialidade

    // 0 gravado pelo banco em campo vazio volta a ser "não medido" (classificacao/sinais_da_ficha).
    function.run "classificacao/sinais_da_ficha" {
      input = {ficha: $ficha}
    } as $sinais_ficha

    db.query chamada {
      where = $db.chamada.ficha_id == $ficha.id
      sort = {created_at: "asc"}
      return = {type: "list"}
    } as $eventos
  }

  response = {
    ficha          : {id: $ficha.id, senha: $ficha.senha, chegada_em: $ficha.chegada_em, status: $ficha.status, observacao: $ficha.observacao, pa_sistolica: $sinais_ficha.pa_sistolica, fc: $sinais_ficha.fc, fr: $sinais_ficha.fr, temperatura: $sinais_ficha.temperatura, spo2: $sinais_ficha.spo2, glicemia: $sinais_ficha.glicemia, glicemia_sinais_gravidade: $ficha.glicemia_sinais_gravidade, escore_risco: $ficha.escore_risco, classificacao_risco: $ficha.classificacao_risco, prioridade_atual: $ficha.prioridade_atual, condicao_prioritaria: $ficha.condicao_prioritaria, especialidade: ($especialidade == null) ? null : {id: $especialidade.id, nome: $especialidade.nome, sigla: $especialidade.sigla}}
    paciente       : {nome: $avaliacao.paciente.nome, idade: $avaliacao.idade}
    sintomas       : $avaliacao.sintomas|map:{nome: $$.nome, descricao: $$.descricao}
    sintomas_livres: $avaliacao.sintomas_livres|map:$$.descricao
    historico      : $eventos|map:{tipo: $$.tipo, oportunidade: $$.oportunidade, tentativa: $$.tentativa, medico_id: $$.medico_id, em: $$.created_at}
  }

  guid = "nZy3DmgelB8_8NOksLy1pETzrHM"
}

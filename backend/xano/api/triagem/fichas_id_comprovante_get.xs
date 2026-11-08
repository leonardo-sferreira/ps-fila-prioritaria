// Comprovante da senha (add-direcionamento-senha, D6; RF21/RF48, Rev. 2.1 §9): só senha, prioridade,
// especialidade e horário de entrada. Nada de nome, CPF, data de nascimento, sintomas ou sinais vitais.
query "fichas/{ficha_id}/comprovante" verb=GET {
  api_group = "Triagem"
  description = "Dados do comprovante de 80 mm de uma ficha com senha ativa, sem dados pessoais nem clínicos."

  auth = "usuario"

  input {
    int ficha_id
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM"]}
    } as $usuario

    db.get ficha_atendimento {
      field_name = "id"
      field_value = $input.ficha_id
    } as $ficha

    precondition ($ficha != null) {
      error_type = "notfound"
      error = "FICHA_NAO_ENCONTRADA"
    }

    precondition (($ficha.status == "AGUARDANDO" || $ficha.status == "CHAMADO") && $ficha.senha != null) {
      error_type = "inputerror"
      error = "SENHA_NAO_ATIVA"
    }

    db.get especialidade {
      field_name = "id"
      field_value = $ficha.especialidade_atribuida_id
    } as $especialidade
  }

  response = {
    senha        : $ficha.senha
    prioridade   : $ficha.prioridade_atual
    especialidade: ($especialidade == null) ? null : {nome: $especialidade.nome, sigla: $especialidade.sigla}
    chegada_em   : $ficha.chegada_em
  }
  guid = "FjyozPNxP3648tKhIYYdnfONX8U"
}

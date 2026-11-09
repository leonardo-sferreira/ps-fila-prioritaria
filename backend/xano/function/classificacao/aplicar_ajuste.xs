// Ajuste manual da prioridade (add-classificacao-prioridade, D6), extraído do endpoint de prioridade para ser usado
// também pelo PATCH da ficha na mesma operação da alteração clínica (add-reavaliacao-ficha-aguardando, D2).
// Deve ser chamada dentro da transação do chamador, depois da validação de estado e do recálculo.
// Com reavaliar_senha (ajuste isolado em AGUARDANDO), troca a letra da senha antes de auditar, para a auditoria
// registrar a senha anterior e a nova. O PATCH passa falso: ele refaz destino e senha e audita depois.
function "classificacao/aplicar_ajuste" {
  description = "Valida e grava a prioridade atual escolhida com justificativa, auditando PRIORIDADE_ALTERADA."

  input {
    int ficha_id
    int usuario_id
    text prioridade? filters=trim|upper
    text justificativa? filters=trim
    bool reavaliar_senha?
  }

  stack {
    precondition (["VERMELHA", "AMARELA", "AZUL"]|in:$input.prioridade) {
      error_type = "inputerror"
      error = "PRIORIDADE_INVALIDA"
    }

    precondition ($input.justificativa != null && ($input.justificativa|strlen) > 0) {
      error_type = "inputerror"
      error = "JUSTIFICATIVA_OBRIGATORIA"
    }

    // Compara com a classificação vigente, não com um valor gravado antigo.
    function.run "classificacao/avaliar_ficha" {
      input = {ficha_id: $input.ficha_id}
    } as $avaliacao

    var $ficha { value = $avaliacao.ficha }

    var $prioridade_calculada {
      value = $avaliacao.classificacao.prioridade_calculada
    }

    precondition ($prioridade_calculada == null || $prioridade_calculada != $input.prioridade) {
      error_type = "inputerror"
      error = "PRIORIDADE_IGUAL_A_CALCULADA"
    }

    db.patch ficha_atendimento {
      field_name = "id"
      field_value = $input.ficha_id
      data = {prioridade_calculada: $prioridade_calculada, prioridade_atual: $input.prioridade, justificativa_ajuste: $input.justificativa}
    } as $ficha_ajustada

    var $reavaliacao { value = null }

    conditional {
      if ($input.reavaliar_senha) {
        function.run "direcionamento/reavaliar_senha" {
          input = {ficha_id: $input.ficha_id, prioridade_anterior: $ficha.prioridade_atual, refazer_destino: false}
        } as $reavaliacao_feita
        var.update $reavaliacao { value = $reavaliacao_feita }
      }
    }

    function.run "registrar_alteracao" {
      input = {
        usuario_id    : $input.usuario_id
        tipo_evento   : "PRIORIDADE_ALTERADA"
        entidade      : "FICHA_ATENDIMENTO"
        registro_id   : $input.ficha_id
        valor_anterior: {prioridade_calculada: $ficha.prioridade_calculada, prioridade_atual: $ficha.prioridade_atual, justificativa_ajuste: $ficha.justificativa_ajuste, senha: $ficha.senha}
        valor_novo    : {prioridade_calculada: $prioridade_calculada, prioridade_atual: $input.prioridade, senha: ($reavaliacao == null) ? $ficha.senha : $reavaliacao.senha}
        justificativa : $input.justificativa
      }
    } as $auditoria
  }

  response = {prioridade_calculada: $prioridade_calculada, prioridade_atual: $input.prioridade, justificativa_ajuste: $input.justificativa, reavaliacao: $reavaliacao}
  guid = "Aril-UAJ_SWk0PkBkhZIl1hVMqU"
}

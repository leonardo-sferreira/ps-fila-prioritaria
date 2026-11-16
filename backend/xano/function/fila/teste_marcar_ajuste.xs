// Apoio ao teste do detalhe da ficha (add-acompanhamento-administrador, tarefa 2.4): grava na ficha Amarela do
// cenário sintético um ajuste de cor com justificativa (calculada AZUL, atual AMARELA) e a auditoria
// PRIORIDADE_ALTERADA em nome da Recepção do cenário. Não troca a senha, para teste_encerrar_cenario continuar
// achando a ficha. Altera apenas fichas criadas por teste_criar_cenario.
function "fila/teste_marcar_ajuste" {
  input {
    int ficha_id
    int usuario_id
    text marcador filters=trim
  }

  stack {
    db.get ficha_atendimento {
      field_name = "id"
      field_value = $input.ficha_id
    } as $ficha

    precondition ($ficha != null && $ficha.status == "AGUARDANDO" && $ficha.senha == ("A-CAR-"|concat:$input.marcador)) {
      error_type = "accessdenied"
      error = "FICHA_DE_TESTE_INVALIDA"
    }

    db.get paciente {
      field_name = "id"
      field_value = $ficha.paciente_id
    } as $paciente

    db.get usuario {
      field_name = "id"
      field_value = $input.usuario_id
    } as $recepcao

    precondition ($paciente != null && $paciente.nome == "Paciente Fictício Fila Dois" && $recepcao != null && $recepcao.email == ("fila-recepcao-"|concat:$input.marcador|concat:"@example.invalid")) {
      error_type = "accessdenied"
      error = "FICHA_DE_TESTE_INVALIDA"
    }

    db.transaction {
      stack {
        db.edit ficha_atendimento {
          field_name = "id"
          field_value = $ficha.id
          data = {prioridade_calculada: "AZUL", justificativa_ajuste: "Teste: ajuste sintético"}
        } as $ajustada

        function.run "registrar_alteracao" {
          input = {
            usuario_id    : $recepcao.id
            tipo_evento   : "PRIORIDADE_ALTERADA"
            entidade      : "FICHA_ATENDIMENTO"
            registro_id   : $ficha.id
            valor_anterior: {prioridade: "AZUL", senha: $ficha.senha}
            valor_novo    : {prioridade: "AMARELA", senha: $ficha.senha}
            justificativa : "Teste: ajuste sintético"
          }
        } as $auditoria
      }
    }
  }

  response = {ficha_id: $ajustada.id, cor_calculada: $ajustada.prioridade_calculada, cor: $ajustada.prioridade_atual}
  guid = "0x0mMcY_9OYBnzBZbBbHeDFmqCw"
}

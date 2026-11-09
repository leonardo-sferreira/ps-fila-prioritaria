// Reavaliação da ficha AGUARDANDO (add-reavaliacao-ficha-aguardando, D3 e D4), usada pelo PATCH da ficha e pelo
// ajuste de prioridade. Deve ser chamada dentro da transação do chamador, depois do recálculo e do ajuste, com a
// prioridade e a especialidade que a ficha tinha antes da operação. Refaz o destino quando pedido, decide a senha
// por senha_reavaliada e grava especialidade, senha e número. Não muda status nem chegada_em.
function "direcionamento/reavaliar_senha" {
  description = "Refaz destino e senha da ficha AGUARDANDO depois de uma alteração e grava o resultado."

  input {
    int ficha_id
    text prioridade_anterior
    // Falso no ajuste de prioridade: só a cor muda e a especialidade continua a mesma.
    bool refazer_destino
  }

  stack {
    db.get ficha_atendimento {
      field_name = "id"
      field_value = $input.ficha_id
    } as $ficha

    // A ficha nunca fica na fila sem cor (decisão do usuário, 09/11/2026); o chamador desfaz a operação.
    precondition ($ficha.prioridade_atual != null) {
      error_type = "inputerror"
      error = "FICHA_SEM_PRIORIDADE"
    }

    db.get especialidade {
      field_name = "id"
      field_value = $ficha.especialidade_atribuida_id
    } as $especialidade_anterior

    var $especialidade { value = $especialidade_anterior }
    var $motivo { value = null }

    conditional {
      if ($input.refazer_destino) {
        function.run "direcionamento/destino_da_ficha" {
          input = {ficha_id: $ficha.id}
        } as $destino

        precondition ($destino.especialidade != null) {
          error_type = "inputerror"
          error = "DESTINO_NAO_CONFIGURADO"
        }

        var.update $especialidade { value = $destino.especialidade }
        var.update $motivo { value = $destino.motivo }
      }
    }

    function.run "direcionamento/senha_reavaliada" {
      input = {
        senha_atual              : $ficha.senha
        senha_numero             : $ficha.senha_numero
        especialidade_anterior_id: $ficha.especialidade_atribuida_id
        prioridade_anterior      : $input.prioridade_anterior
        especialidade_nova_id    : $especialidade.id
        prioridade_nova          : $ficha.prioridade_atual
        sigla_nova               : $especialidade.sigla
      }
    } as $decisao

    var $senha { value = $decisao.senha }
    var $numero { value = $ficha.senha_numero }

    conditional {
      if ($decisao.acao == "NOVO_NUMERO") {
        function.run "direcionamento/gerar_senha" {
          input = {especialidade_id: $especialidade.id, sigla: $especialidade.sigla, prioridade: $ficha.prioridade_atual}
        } as $senha_gerada
        var.update $senha { value = $senha_gerada.senha }
        var.update $numero { value = $senha_gerada.numero }
      }
    }

    conditional {
      if ($decisao.acao != "MANTER") {
        db.patch ficha_atendimento {
          field_name = "id"
          field_value = $ficha.id
          data = {
            especialidade_sugerida_id : $especialidade.id
            especialidade_atribuida_id: $especialidade.id
            senha                     : $senha
            senha_numero              : $numero
          }
        } as $ficha_reavaliada
      }
    }
  }

  response = {
    especialidade_anterior: {id: $especialidade_anterior.id, nome: $especialidade_anterior.nome, sigla: $especialidade_anterior.sigla}
    especialidade         : {id: $especialidade.id, nome: $especialidade.nome, sigla: $especialidade.sigla}
    motivo                : $motivo
    senha_anterior        : $ficha.senha
    senha                 : $senha
    senha_alterada        : $decisao.acao != "MANTER"
  }
  guid = "BA4F_It6gU7i0bsKfpX-qn6WMu8"
}

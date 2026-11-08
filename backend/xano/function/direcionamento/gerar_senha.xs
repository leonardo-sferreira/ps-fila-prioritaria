// Senha COR-ESP-NNN (add-direcionamento-senha, D4). Número diário por especialidade em America/Sao_Paulo,
// compartilhado entre cores, guardado em contador_senha (índice único data + especialidade).
// Deve ser chamada dentro da transação da confirmação. O contador é sempre gravado com valor explícito, porque no
// servidor `ultimo_numero` não tem default (tabela divergente, não republicada). Exclusividade sob confirmações
// simultâneas não comprovada (limitação registrada no proposal).
function "direcionamento/gerar_senha" {
  description = "Reserva o próximo número do dia da especialidade e devolve a senha formatada."

  input {
    int especialidade_id
    text sigla
    // VERMELHA, AMARELA ou AZUL.
    text prioridade
  }

  stack {
    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $numero { value = null }
    var $tentativa { value = 0 }

    // Duas primeiras senhas do dia ao mesmo tempo colidem no índice único; tenta de novo lendo o valor gravado.
    while ($numero == null && $tentativa < 5) {
      each {
        var.update $tentativa { value = $tentativa + 1 }
        try_catch {
          try {
            db.query contador_senha {
              where = $db.contador_senha.data == $hoje && $db.contador_senha.especialidade_id == $input.especialidade_id
              return = {type: "single"}
            } as $contador

            conditional {
              if ($contador == null) {
                db.add contador_senha {
                  data = {data: $hoje, especialidade_id: $input.especialidade_id, ultimo_numero: 1}
                } as $contador_criado
                var.update $numero { value = 1 }
              }
              else {
                var $proximo { value = ($contador.ultimo_numero ?? 0) + 1 }
                db.edit contador_senha {
                  field_name = "id"
                  field_value = $contador.id
                  data = {ultimo_numero: $proximo}
                } as $contador_atualizado
                var.update $numero { value = $proximo }
              }
            }
          }
          catch {
            var.update $numero { value = null }
          }
        }
      }
    }

    precondition ($numero != null) {
      error_type = "standard"
      error = "SENHA_NAO_GERADA"
    }

    function.run "direcionamento/formatar_senha" {
      input = {prioridade: $input.prioridade, sigla: $input.sigla, numero: $numero}
    } as $senha
  }

  response = {senha: $senha, numero: $numero}
  guid = "A6eMEYZqCrJ3-ZOpQElXdU4DYBs"
}

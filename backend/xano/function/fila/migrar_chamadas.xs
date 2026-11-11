// Migração idempotente após adicionar os campos da oportunidade e da ordem efetiva.
// Preenche oportunidade 1 e ordem inicial sem alterar chegada nem senha.
function "fila/migrar_chamadas" {
  input {
  }

  stack {
    var $fichas_atualizadas {
      value = 0
    }

    var $eventos_atualizados {
      value = 0
    }

    db.transaction {
      stack {
        db.query ficha_atendimento {
          where = $db.ficha_atendimento.oportunidade == null || $db.ficha_atendimento.fila_em == null
          return = {type: "list"}
        } as $fichas

        foreach ($fichas) {
          each as $ficha {
            db.edit ficha_atendimento {
              field_name = "id"
              field_value = $ficha.id
              data = {
                oportunidade: $ficha.oportunidade ?? 1
                fila_em     : $ficha.fila_em ?? $ficha.chegada_em
              }
            } as $migrada

            var.update $fichas_atualizadas {
              value = $fichas_atualizadas + 1
            }
          }
        }

        db.query chamada {
          where = $db.chamada.oportunidade == null
          return = {type: "list"}
        } as $eventos

        foreach ($eventos) {
          each as $evento {
            db.edit chamada {
              field_name = "id"
              field_value = $evento.id
              data = {oportunidade: 1}
            } as $migrado

            var.update $eventos_atualizados {
              value = $eventos_atualizados + 1
            }
          }
        }
      }
    }
  }

  response = {
    fichas : $fichas_atualizadas
    eventos: $eventos_atualizados
  }

  guid = "tHcwdjSLOsSHJW6PD9mAF04HEoQ"
}

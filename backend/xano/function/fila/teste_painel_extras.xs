// Apoio a tests/api/test_painel.py (add-painel-publico, tarefa 1.2). Uso restrito ao CLI; não há endpoint público.
// FICHAS: cria `quantidade` fichas AGUARDANDO fictícias na especialidade da sigla, marcadas em observacao com
//         "teste-painel-<marcador>", para medir o tamanho da previsão (8 e 3 elegíveis).
// TICKET: cria um ticket de pré-triagem fictício já CHAMADO (número a partir de 900, para reconhecer na tela da Recepção).
// RECHAMAR: rechama o ticket fictício (tentativas + 1 e chamado_em = agora).
// LIMPAR: cancela as fichas fictícias do marcador, inativa os pacientes e encerra o ticket como DESISTENCIA, sem horário de chamada,
//          para ele não continuar no painel real dentro da janela HORAS_PAINEL.
function "fila/teste_painel_extras" {
  input {
    enum acao {
      values = ["FICHAS", "TICKET", "RECHAMAR", "LIMPAR"]
    }
    text marcador filters=trim
    text? sigla? filters=trim|upper
    int? quantidade?
    int? ticket_id?
  }

  stack {
    precondition (($input.marcador|strlen) >= 10) {
      error_type = "inputerror"
      error = "MARCADOR_INVALIDO"
    }

    var $marca {
      value = "teste-painel-" ~ $input.marcador
    }

    var $saida {
      value = {}
    }

    conditional {
      if ($input.acao == "FICHAS") {
        db.get especialidade {
          field_name = "sigla"
          field_value = $input.sigla
        } as $esp

        precondition ($esp != null && ($input.quantidade ?? 0) >= 1 && ($input.quantidade ?? 0) <= 10) {
          error_type = "inputerror"
          error = "PARAMETROS_INVALIDOS"
        }

        // Numeração continua entre chamadas FICHAS do mesmo marcador: a senha e o CPF são únicos no Xano.
        db.query ficha_atendimento {
          where = $db.ficha_atendimento.observacao == $marca
          return = {type: "count"}
        } as $existentes

        db.add paciente {
          data = {cpf: "TESTE-PAINEL-" ~ $input.marcador ~ "-" ~ ($existentes|to_text), nome: "Paciente Fictício Painel", data_nascimento: "1990-01-01", ativo: true}
        } as $paciente

        var $ids {
          value = []
        }

        foreach ((1..$input.quantidade)) {
          each as $n {
            db.add ficha_atendimento {
              data = {
                paciente_id               : $paciente.id
                chegada_em                : now
                fila_em                   : now
                status                    : "AGUARDANDO"
                prioridade_atual          : "AZUL"
                condicao_prioritaria      : "NENHUMA"
                especialidade_atribuida_id: $esp.id
                senha                     : "B-" ~ $esp.sigla ~ "-T" ~ (($n + $existentes)|to_text) ~ "-" ~ $input.marcador
                oportunidade              : 1
                tentativas_chamada        : 0
                observacao                : $marca
              }
            } as $ficha

            var.update $ids {
              value = $ids|push:$ficha.id
            }
          }
        }

        var.update $saida {
          value = {fichas: $ids}
        }
      }

      elseif ($input.acao == "TICKET") {
        // Data fixa no passado: o ticket fictício não entra na numeração diária real do Totem (que continua a partir
        // do maior número do dia). O painel acha o ticket pelo chamado_em, não pela data.
        var $hoje {
          value = "2000-01-01"
        }

        // Número único nessa data: o próximo livre a partir de 900.
        db.query ticket_pre_triagem {
          where = $db.ticket_pre_triagem.data == $hoje && $db.ticket_pre_triagem.numero >= 900
          return = {type: "count"}
        } as $ja_usados

        db.add ticket_pre_triagem {
          data = {
            data       : $hoje
            tipo       : "NORMAL"
            numero     : 900 + $ja_usados
            emitido_em : now
            status     : "CHAMADO"
            oportunidade: 1
            tentativas : 1
            presente   : false
            fila_em    : now
            chamado_em : now
          }
        } as $ticket

        var.update $saida {
          value = {ticket_id: $ticket.id, numero: $ticket.numero}
        }
      }

      elseif ($input.acao == "RECHAMAR") {
        db.get ticket_pre_triagem {
          field_name = "id"
          field_value = $input.ticket_id
        } as $ticket

        precondition ($ticket != null && $ticket.numero >= 900 && $ticket.chamado_por == null && $ticket.status == "CHAMADO") {
          error_type = "accessdenied"
          error = "TICKET_DE_TESTE_INVALIDO"
        }

        db.edit ticket_pre_triagem {
          field_name = "id"
          field_value = $ticket.id
          data = {tentativas: $ticket.tentativas + 1, chamado_em: now}
        } as $rechamado

        var.update $saida {
          value = {ticket_id: $rechamado.id, tentativas: $rechamado.tentativas}
        }
      }

      else {
        db.query ficha_atendimento {
          where = $db.ficha_atendimento.observacao == $marca
          return = {type: "list"}
        } as $fichas

        foreach ($fichas) {
          each as $f {
            db.edit ficha_atendimento {
              field_name = "id"
              field_value = $f.id
              data = {status: "CANCELADO", finalizada_em: now}
            } as $cancelada

            db.edit paciente {
              field_name = "id"
              field_value = $f.paciente_id
              data = {ativo: false}
            } as $paciente_inativo
          }
        }

        conditional {
          if ($input.ticket_id != null) {
            db.get ticket_pre_triagem {
              field_name = "id"
              field_value = $input.ticket_id
            } as $ticket_fim

            conditional {
              if ($ticket_fim != null && $ticket_fim.numero >= 900 && $ticket_fim.chamado_por == null) {
                db.edit ticket_pre_triagem {
                  field_name = "id"
                  field_value = $ticket_fim.id
                  data = {status: "DESISTENCIA", chamado_em: null}
                } as $ticket_encerrado
              }
            }
          }
        }

        var.update $saida {
          value = {fichas_canceladas: $fichas|count}
        }
      }
    }
  }

  response = $saida
  guid = "5mpwycSlbStSuewEbgfG6otzwb4"
}

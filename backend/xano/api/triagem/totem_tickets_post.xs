// Emissão pública de ticket pelo Totem (add-totem D1, D2, D5). Sem sessão de equipe e sem dados pessoais;
// a chave do dispositivo vem do servidor Reflex e é comparada com a variável de ambiente TOTEM_CHAVE.
query "totem/tickets" verb=POST {
  api_group = "Triagem"
  description = "Emite o próximo ticket do dia (C/P/N) no fuso America/Sao_Paulo e o deixa AGUARDANDO na fila de pré-triagem."

  input {
    text chave_dispositivo? {
      sensitive = true
    }
    text tipo? filters=trim|upper
  }

  stack {
    precondition ($env.TOTEM_CHAVE != null && $env.TOTEM_CHAVE != "" && $input.chave_dispositivo == $env.TOTEM_CHAVE) {
      error_type = "unauthorized"
      error = "Dispositivo não autorizado."
    }

    precondition (["PEDIATRICO", "PREFERENCIAL", "NORMAL"]|in:$input.tipo) {
      error_type = "inputerror"
      error = "Tipo de ticket inválido."
    }

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    // O índice único (data, tipo, numero) impede número repetido; se duas emissões colidirem, tenta de novo.
    var $ticket {
      value = null
    }

    var $tentativa {
      value = 0
    }

    while ($ticket == null && $tentativa < 5) {
      each {
        var.update $tentativa {
          value = $tentativa + 1
        }

        try_catch {
          try {
            db.query ticket_pre_triagem {
              where = $db.ticket_pre_triagem.data == $hoje && $db.ticket_pre_triagem.tipo == $input.tipo
              sort = {numero: "desc"}
              return = {type: "single"}
            } as $ultimo

            db.add ticket_pre_triagem {
              data = {
                data       : $hoje
                tipo       : $input.tipo
                numero     : ($ultimo == null ? 1 : $ultimo.numero + 1)
                emitido_em : now
                status     : "AGUARDANDO"
                oportunidade: 1
                tentativas : 0
                presente   : false
              }
            } as $criado

            var.update $ticket {
              value = $criado
            }
          }

          catch {
            var.update $ticket {
              value = null
            }
          }
        }
      }
    }

    precondition ($ticket != null) {
      error_type = "standard"
      error = "Não foi possível emitir o ticket. Tente novamente."
    }

    var $prefixo {
      value = ($ticket.tipo == "PEDIATRICO" ? "C" : ($ticket.tipo == "PREFERENCIAL" ? "P" : "N"))
    }

    var $numero_texto {
      value = $ticket.numero|to_text
    }

    conditional {
      if ($ticket.numero < 10) {
        var.update $numero_texto {
          value = "00" ~ $numero_texto
        }
      }
      elseif ($ticket.numero < 100) {
        var.update $numero_texto {
          value = "0" ~ $numero_texto
        }
      }
    }
  }

  // Só dados operacionais: nada de paciente, nome ou CPF.
  response = {
    tipo  : $ticket.tipo
    numero: $ticket.numero
    codigo: $prefixo ~ "-" ~ $numero_texto
  }
  guid = "KjTA83cjLme80UN_FTuGs92vQHE"
}

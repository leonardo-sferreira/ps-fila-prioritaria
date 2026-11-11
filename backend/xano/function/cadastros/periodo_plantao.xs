// Converte data + horas de um plantão em início e fim (epoch ms) no fuso America/Sao_Paulo
// (add-cadastros-administrador, D6). Fim menor ou igual ao início cai no dia seguinte (plantão noturno),
// então o período tem no máximo 24 h. Função pura: não acessa o banco.
function "cadastros/periodo_plantao" {
  description = "Valida data (AAAA-MM-DD) e horas (HH:MM) do plantão e devolve início e fim em epoch ms, ou o erro."

  input {
    text data filters=trim
    text hora_inicio filters=trim
    text hora_fim filters=trim
  }

  stack {
    var $data_ok {
      value = "/^\\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01])$/"|regex_matches:$input.data
    }
    var $inicio_ok {
      value = "/^([01]\\d|2[0-3]):[0-5]\\d$/"|regex_matches:$input.hora_inicio
    }
    var $fim_ok {
      value = "/^([01]\\d|2[0-3]):[0-5]\\d$/"|regex_matches:$input.hora_fim
    }

    var $resultado { value = {valido: false, erro: "PERIODO_INVALIDO", inicio: null, fim: null} }

    conditional {
      if ($data_ok && $inicio_ok && $fim_ok) {
        var $inicio {
          value = ($input.data ~ " " ~ $input.hora_inicio)|to_timestamp:"America/Sao_Paulo"
        }
        var $fim {
          value = ($input.data ~ " " ~ $input.hora_fim)|to_timestamp:"America/Sao_Paulo"
        }
        conditional {
          if ($fim <= $inicio) {
            var.update $fim { value = $fim + 86400000 }
          }
        }
        var.update $resultado { value = {valido: true, erro: null, inicio: $inicio, fim: $fim} }
      }
    }
  }

  response = $resultado

  test "plantão diurno 07:00–19:00" {
    input = {data: "2026-11-11", hora_inicio: "07:00", hora_fim: "19:00"}
    expect.to_be_true ($response.valido)
    expect.to_equal ($response.inicio) {
      value = 1794391200000
    }
    expect.to_equal ($response.fim) {
      value = 1794434400000
    }
  }

  test "plantão noturno 19:00–07:00 termina no dia seguinte" {
    input = {data: "2026-11-11", hora_inicio: "19:00", hora_fim: "07:00"}
    expect.to_equal ($response.inicio) {
      value = 1794434400000
    }
    expect.to_equal ($response.fim) {
      value = 1794477600000
    }
  }

  test "fim igual ao início vira plantão de 24 h" {
    input = {data: "2026-11-11", hora_inicio: "23:30", hora_fim: "23:30"}
    expect.to_equal ($response.fim) {
      value = 1794537000000
    }
  }

  test "hora inválida" {
    input = {data: "2026-11-11", hora_inicio: "24:00", hora_fim: "07:00"}
    expect.to_be_false ($response.valido)
  }

  test "data em formato errado" {
    input = {data: "11/11/2026", hora_inicio: "07:00", hora_fim: "19:00"}
    expect.to_be_false ($response.valido)
  }
  guid = "VdWkQKY9YTDlMsfnPfXl-X1MZPE"
}

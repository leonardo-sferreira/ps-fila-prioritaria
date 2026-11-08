// Formata a senha COR-ESP-NNN (add-direcionamento-senha, D4): V/A/B pela cor, sigla da especialidade e número com
// no mínimo 3 dígitos. Função pura, separada de gerar_senha para ser testada sem banco.
function "direcionamento/formatar_senha" {
  description = "Monta a senha COR-ESP-NNN a partir da prioridade, da sigla e do número."

  input {
    text prioridade
    text sigla
    int numero
  }

  stack {
    var $cor { value = "B" }
    conditional {
      if ($input.prioridade == "VERMELHA") {
        var.update $cor { value = "V" }
      }
      elseif ($input.prioridade == "AMARELA") {
        var.update $cor { value = "A" }
      }
    }

    var $numero_texto { value = $input.numero|to_text }
    conditional {
      if ($input.numero < 10) {
        var.update $numero_texto { value = "00" ~ $numero_texto }
      }
      elseif ($input.numero < 100) {
        var.update $numero_texto { value = "0" ~ $numero_texto }
      }
    }
  }

  response = $cor ~ "-" ~ ($input.sigla|to_upper) ~ "-" ~ $numero_texto

  test "primeira Vermelha de Clínica Geral" {
    input = {prioridade: "VERMELHA", sigla: "CLI", numero: 1}
    expect.to_equal ($response) {
      value = "V-CLI-001"
    }
  }

  test "Amarela de Cardiologia número 42" {
    input = {prioridade: "AMARELA", sigla: "CAR", numero: 42}
    expect.to_equal ($response) {
      value = "A-CAR-042"
    }
  }

  test "Azul acima de 999" {
    input = {prioridade: "AZUL", sigla: "CLI", numero: 1000}
    expect.to_equal ($response) {
      value = "B-CLI-1000"
    }
  }
  guid = "d46AU16_PXe9FpAq7MGZPhzxLk8"
}

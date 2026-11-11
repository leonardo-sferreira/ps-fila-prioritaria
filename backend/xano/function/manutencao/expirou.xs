// Regra pura da expiração (add-expiracao-24h, D2): um registro ativo expira quando o seu horário (chegada da ficha
// ou emissão do ticket) ficou mais de `horas` horas antes de `agora`. Exatamente no prazo ainda não expira.
// Horário vazio ou prazo que não seja positivo nunca expira. Não acessa o banco.
function "manutencao/expirou" {
  description = "Diz se um horário (epoch ms) passou do prazo de expiração em horas, em relação a agora (epoch ms)."

  input {
    int? horario?
    int agora
    int? horas?
  }

  stack {
    var $expirou { value = false }
    conditional {
      if ($input.horario != null && $input.horas != null && $input.horas > 0) {
        var $limite {
          value = $input.agora - ($input.horas * 3600000)
        }
        var.update $expirou {
          value = $input.horario < $limite
        }
      }
    }
  }

  response = $expirou

  test "24 horas exatas ainda não expiram" {
    input = {horario: 1794070800000, agora: 1794157200000, horas: 24}
    expect.to_be_false ($response)
  }

  test "24 horas e 1 ms expiram" {
    input = {horario: 1794070799999, agora: 1794157200000, horas: 24}
    expect.to_be_true ($response)
  }

  test "dentro do prazo não expira" {
    input = {horario: 1794150000000, agora: 1794157200000, horas: 24}
    expect.to_be_false ($response)
  }

  test "horário vazio não expira" {
    input = {horario: null, agora: 1794157200000, horas: 24}
    expect.to_be_false ($response)
  }

  test "prazo zero ou ausente não expira" {
    input = {horario: 1700000000000, agora: 1794157200000, horas: 0}
    expect.to_be_false ($response)
  }

  test "prazo configurado diferente de 24" {
    input = {horario: 1794150000000, agora: 1794157200000, horas: 1}
    expect.to_be_true ($response)
  }
  guid = "rdR0VZ-g78pGGphfb4Czn5Ixdt0"
}

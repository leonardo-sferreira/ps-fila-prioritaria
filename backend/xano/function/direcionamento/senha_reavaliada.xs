// Regra da senha na reavaliação da ficha AGUARDANDO (add-reavaliacao-ficha-aguardando, D4). Função pura:
// nada mudou → MANTER; só a cor → TROCAR_COR (mesma sigla e número, sem tocar no contador);
// especialidade mudou → NOVO_NUMERO (o chamador reserva o número com gerar_senha).
function "direcionamento/senha_reavaliada" {
  description = "Decide se a senha da ficha reavaliada é mantida, troca só a cor ou precisa de número novo."

  input {
    text senha_atual
    int senha_numero
    int especialidade_anterior_id
    text prioridade_anterior
    int especialidade_nova_id
    text prioridade_nova
    text sigla_nova
  }

  stack {
    var $acao { value = "MANTER" }
    var $senha { value = $input.senha_atual }

    conditional {
      if ($input.especialidade_nova_id != $input.especialidade_anterior_id) {
        var.update $acao { value = "NOVO_NUMERO" }
        var.update $senha { value = null }
      }
      elseif ($input.prioridade_nova != $input.prioridade_anterior) {
        var.update $acao { value = "TROCAR_COR" }
        function.run "direcionamento/formatar_senha" {
          input = {prioridade: $input.prioridade_nova, sigla: $input.sigla_nova, numero: $input.senha_numero}
        } as $senha_nova
        var.update $senha { value = $senha_nova }
      }
    }
  }

  response = {acao: $acao, senha: $senha}

  test "nada muda mantém a senha" {
    input = {senha_atual: "A-CAR-001", senha_numero: 1, especialidade_anterior_id: 1, prioridade_anterior: "AMARELA", especialidade_nova_id: 1, prioridade_nova: "AMARELA", sigla_nova: "CAR"}
    expect.to_equal ($response.acao) {
      value = "MANTER"
    }
    expect.to_equal ($response.senha) {
      value = "A-CAR-001"
    }
  }

  test "só a cor muda troca a letra e mantém o número" {
    input = {senha_atual: "A-CAR-001", senha_numero: 1, especialidade_anterior_id: 1, prioridade_anterior: "AMARELA", especialidade_nova_id: 1, prioridade_nova: "VERMELHA", sigla_nova: "CAR"}
    expect.to_equal ($response.acao) {
      value = "TROCAR_COR"
    }
    expect.to_equal ($response.senha) {
      value = "V-CAR-001"
    }
  }

  test "especialidade muda pede número novo" {
    input = {senha_atual: "A-CAR-001", senha_numero: 1, especialidade_anterior_id: 1, prioridade_anterior: "AMARELA", especialidade_nova_id: 3, prioridade_nova: "AMARELA", sigla_nova: "NEU"}
    expect.to_equal ($response.acao) {
      value = "NOVO_NUMERO"
    }
    expect.to_be_null ($response.senha)
  }

  test "especialidade e cor mudam pede número novo" {
    input = {senha_atual: "B-CLI-012", senha_numero: 12, especialidade_anterior_id: 2, prioridade_anterior: "AZUL", especialidade_nova_id: 4, prioridade_nova: "VERMELHA", sigla_nova: "ORT"}
    expect.to_equal ($response.acao) {
      value = "NOVO_NUMERO"
    }
  }
  guid = "wRyMuzT5uSWBiwJK4ddbskHjDpc"
}

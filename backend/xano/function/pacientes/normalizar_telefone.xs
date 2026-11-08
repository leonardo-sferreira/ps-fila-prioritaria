// Regra do telefone na edição de Paciente, extraída de PATCH pacientes/{paciente_id} para ser testável sem sessão:
// o endpoint exige login e o teste unitário do Xano não simula usuário autenticado.
// Texto vazio ou null limpam o telefone (no banco, telefone ausente é null); `alterado` compara com o valor atual.
function "pacientes/normalizar_telefone" {
  description = "Normaliza o telefone enviado (vazio vira null) e informa se difere do telefone atual."

  input {
    text? telefone?
    text? atual?
  }

  stack {
    var $valor { value = $input.telefone }
    conditional {
      if ($valor == "") {
        var.update $valor { value = null }
      }
    }

    var $atual { value = $input.atual }
    conditional {
      if ($atual == "") {
        var.update $atual { value = null }
      }
    }
  }

  response = {valor: $valor, alterado: $valor != $atual}

  test "limpa telefone com null" {
    input = {telefone: null, atual: "11999999999"}
    expect.to_be_null ($response.valor)
    expect.to_be_true ($response.alterado)
  }

  test "limpa telefone com texto vazio" {
    input = {telefone: "", atual: "11999999999"}
    expect.to_be_null ($response.valor)
    expect.to_be_true ($response.alterado)
  }

  test "telefone vazio já está ausente" {
    input = {telefone: "", atual: null}
    expect.to_be_null ($response.valor)
    expect.to_be_false ($response.alterado)
  }

  test "mesmo telefone não é alteração" {
    input = {telefone: "11999999999", atual: "11999999999"}
    expect.to_be_false ($response.alterado)
  }

  test "telefone novo é alteração" {
    input = {telefone: "11888888888", atual: "11999999999"}
    expect.to_equal ($response.valor) {
      value = "11888888888"
    }
    expect.to_be_true ($response.alterado)
  }
  guid = "5hWvP66AjIwciwUJd8BLWgCr9q0"
}

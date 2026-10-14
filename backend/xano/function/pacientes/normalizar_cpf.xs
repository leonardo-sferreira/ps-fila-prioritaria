// Normaliza e valida CPF para todas as operações de Paciente.
function "pacientes/normalizar_cpf" {
  description = "Remove a pontuação aceita e valida os dígitos verificadores do CPF."

  input {
    text cpf filters=trim
  }

  stack {
    var $cpf {
      value = $input.cpf|replace:".":""|replace:"-":""
    }

    precondition ("/^[0-9]{11}$/"|regex_matches:$cpf) {
      error_type = "inputerror"
      error = "CPF inválido"
    }

    precondition (
      $cpf != "00000000000" && $cpf != "11111111111" &&
      $cpf != "22222222222" && $cpf != "33333333333" &&
      $cpf != "44444444444" && $cpf != "55555555555" &&
      $cpf != "66666666666" && $cpf != "77777777777" &&
      $cpf != "88888888888" && $cpf != "99999999999"
    ) {
      error_type = "inputerror"
      error = "CPF inválido"
    }

    var $soma_primeiro_digito { value = (($cpf|substr:0:1|to_int) * 10) + (($cpf|substr:1:1|to_int) * 9) + (($cpf|substr:2:1|to_int) * 8) + (($cpf|substr:3:1|to_int) * 7) + (($cpf|substr:4:1|to_int) * 6) + (($cpf|substr:5:1|to_int) * 5) + (($cpf|substr:6:1|to_int) * 4) + (($cpf|substr:7:1|to_int) * 3) + (($cpf|substr:8:1|to_int) * 2) }
    var $resto_primeiro_digito { value = $soma_primeiro_digito % 11 }
    var $primeiro_digito { value = 0 }
    conditional {
      if ($resto_primeiro_digito >= 2) {
        var.update $primeiro_digito { value = 11 - $resto_primeiro_digito }
      }
    }

    precondition ($primeiro_digito == ($cpf|substr:9:1|to_int)) {
      error_type = "inputerror"
      error = "CPF inválido"
    }

    var $soma_segundo_digito { value = (($cpf|substr:0:1|to_int) * 11) + (($cpf|substr:1:1|to_int) * 10) + (($cpf|substr:2:1|to_int) * 9) + (($cpf|substr:3:1|to_int) * 8) + (($cpf|substr:4:1|to_int) * 7) + (($cpf|substr:5:1|to_int) * 6) + (($cpf|substr:6:1|to_int) * 5) + (($cpf|substr:7:1|to_int) * 4) + (($cpf|substr:8:1|to_int) * 3) + (($cpf|substr:9:1|to_int) * 2) }
    var $resto_segundo_digito { value = $soma_segundo_digito % 11 }
    var $segundo_digito { value = 0 }
    conditional {
      if ($resto_segundo_digito >= 2) {
        var.update $segundo_digito { value = 11 - $resto_segundo_digito }
      }
    }

    precondition ($segundo_digito == ($cpf|substr:10:1|to_int)) {
      error_type = "inputerror"
      error = "CPF inválido"
    }
  }

  response = $cpf

  test "normaliza CPF válido com pontuação" {
    input = { cpf: "529.982.247-25" }
    expect.to_equal ($response) { value = "52998224725" }
  }

  test "aceita CPF válido sem pontuação" {
    input = { cpf: "52998224725" }
    expect.to_equal ($response) { value = "52998224725" }
  }

  test "recusa sequência repetida" {
    input = { cpf: "111.111.111-11" }
    expect.to_throw
  }

  test "recusa tamanho inválido" {
    input = { cpf: "1234567890" }
    expect.to_throw
  }

  test "recusa dígitos verificadores inválidos" {
    input = { cpf: "52998224724" }
    expect.to_throw
  }
  guid = "TXzK002eVr_ymyHw79kiAI-I8_U"
}

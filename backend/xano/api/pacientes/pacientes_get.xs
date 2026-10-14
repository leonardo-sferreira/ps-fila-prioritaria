query "pacientes" verb=GET {
  api_group = "Pacientes"
  description = "Pesquisa um Paciente pelo CPF normalizado. Autorização será integrada pela change de autenticação."

  input {
    text cpf filters=trim
  }

  stack {
    function.run "pacientes/normalizar_cpf" {
      input = { cpf: $input.cpf }
    } as $cpf_normalizado

    db.get "paciente" {
      field_name = "cpf"
      field_value = $cpf_normalizado
    } as $paciente
  }

  response = $paciente
  guid = "AUJsfs61oj5aXv8AtcZc6D4RuDc"
}

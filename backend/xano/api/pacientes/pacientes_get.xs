query "pacientes" verb=GET {
  api_group = "Pacientes"
  description = "Pesquisa um Paciente pelo CPF normalizado para Recepção/Triagem ou Administrador."
  auth = "usuario"

  input {
    text cpf filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $auth.id,
        perfis_permitidos: ["RECEPCAO_TRIAGEM", "ADMINISTRADOR"]
      }
    } as $usuario

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

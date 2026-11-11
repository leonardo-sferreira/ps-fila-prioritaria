query "medico/chamar-proximo" verb=POST {
  api_group = "Fila"
  auth = "usuario"

  input {
    json? ficha_id?
    json? id?
  }

  stack {
    precondition ($input.ficha_id == null && $input.id == null) {
      error_type = "inputerror"
      error = "ESCOLHA_MANUAL_PROIBIDA"
    }

    function.run "fila/chamar_proximo" {
      input = {usuario_id: $auth.id}
    } as $resultado
  }

  response = $resultado
  guid = "i5Texx67TeGa_aF3YEYCBEykZVo"
}

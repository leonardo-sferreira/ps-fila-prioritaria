query "medico/fichas/{ficha_id}/acao" verb=POST {
  api_group = "Fila"
  auth = "usuario"

  input {
    int ficha_id
    text acao filters=trim
  }

  stack {
    function.run "fila/agir_chamada" {
      input = {
        usuario_id: $auth.id
        ficha_id  : $input.ficha_id
        acao      : $input.acao
      }
    } as $resultado
  }

  response = $resultado
  guid = "HoZwLlBwx91-eftC7CVg_5KEQ3o"
}

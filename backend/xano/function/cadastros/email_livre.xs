// Recusa e-mail já usado por outro usuário, sem diferenciar maiúsculas (add-cadastros-administrador, D3).
// Na edição, `ignorar_usuario_id` é o próprio usuário. Devolve o e-mail normalizado.
function "cadastros/email_livre" {
  description = "Valida o formato e a unicidade do e-mail de login; devolve o e-mail em minúsculas."

  input {
    text email filters=trim|lower
    int? ignorar_usuario_id?
  }

  stack {
    precondition ("/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/"|regex_matches:$input.email) {
      error_type = "inputerror"
      error = "E-mail inválido."
    }

    db.get usuario {
      field_name = "email"
      field_value = $input.email
    } as $existente

    precondition ($existente == null || $existente.id == $input.ignorar_usuario_id) {
      error_type = "inputerror"
      error = "Este e-mail já é usado por outro usuário."
    }
  }

  response = $input.email
  guid = "zRKdLk_-9SipUZpvFE3kE5IpkdQ"
}

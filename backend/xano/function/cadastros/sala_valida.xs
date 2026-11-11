// Sala opcional do médico: vazia é aceita; informada, precisa existir e estar ativa (add-cadastros-administrador, D4).
function "cadastros/sala_valida" {
  description = "Devolve o sala_id (ou null) depois de conferir que a sala existe e está ativa."

  input {
    int? sala_id?
  }

  stack {
    var $sala_id { value = ($input.sala_id == null || $input.sala_id == 0) ? null : $input.sala_id }
    conditional {
      if ($sala_id != null) {
        db.get sala {
          field_name = "id"
          field_value = $sala_id
        } as $sala
        precondition ($sala != null && $sala.ativo == true) {
          error_type = "inputerror"
          error = "Sala inexistente ou inativa."
        }
      }
    }
  }

  response = $sala_id
  guid = "b3ckdXjLRe8AJtInb_KOjqycEr4"
}

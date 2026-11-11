// Confere uma lista ordenada de IDs de especialidade: ao menos uma, todas existentes e ativas
// (add-cadastros-administrador, D4). Remove repetições mantendo a ordem. Usada por sintomas e médicos.
function "cadastros/especialidades_validas" {
  description = "Recusa lista vazia ou com especialidade inexistente/inativa; devolve os IDs sem repetição, na ordem recebida."

  input {
    json? especialidade_ids?
  }

  stack {
    var $ids { value = [] }
    foreach ($input.especialidade_ids ?? []) {
      each as $bruto {
        var $id { value = $bruto|to_int }
        conditional {
          if (!($ids|in:$id)) {
            var.update $ids { value = $ids|push:$id }
          }
        }
      }
    }

    precondition (($ids|count) > 0) {
      error_type = "inputerror"
      error = "Informe ao menos uma especialidade."
    }

    db.query especialidade {
      where = $db.especialidade.id in $ids && $db.especialidade.ativo == true
      return = {type: "count"}
    } as $ativas

    precondition ($ativas == ($ids|count)) {
      error_type = "inputerror"
      error = "Especialidade inexistente ou inativa."
    }
  }

  response = $ids
  guid = "ldpH3RpN_ouBz--JbNajf4ElB6c"
}

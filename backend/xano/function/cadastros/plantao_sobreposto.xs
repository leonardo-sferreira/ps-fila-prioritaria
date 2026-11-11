// Diz se [inicio, fim) se sobrepõe a outro plantão não encerrado do mesmo médico (add-cadastros-administrador, D6).
// Intervalos semiabertos: um plantão pode começar exatamente quando o outro termina.
function "cadastros/plantao_sobreposto" {
  description = "true quando existe outro período do médico com inicio < fim e fim > inicio (ignorando o próprio, na edição)."

  input {
    int medico_id
    int inicio
    int fim
    int? ignorar_id?
  }

  stack {
    db.query disponibilidade_medico {
      where = $db.disponibilidade_medico.medico_id == $input.medico_id && $db.disponibilidade_medico.encerrado_em == null && $db.disponibilidade_medico.inicio < $input.fim && $db.disponibilidade_medico.fim > $input.inicio && $db.disponibilidade_medico.id != ($input.ignorar_id ?? 0)
      return = {type: "exists"}
    } as $existe
  }

  response = $existe
}

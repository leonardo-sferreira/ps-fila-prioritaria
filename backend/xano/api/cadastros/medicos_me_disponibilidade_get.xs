// "Meus plantões": o Médico vê os próprios períodos em andamento e futuros, sem alterar (add-cadastros-administrador, D1).
query "medicos/me/disponibilidade" verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {}

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["MEDICO"]}
    } as $usuario

    db.get medico {
      field_name = "usuario_id"
      field_value = $usuario.id
    } as $medico

    precondition ($medico != null) {
      error_type = "accessdenied"
      error = "Cadastro de médico não encontrado."
    }

    var $agora { value = now }

    db.query disponibilidade_medico {
      where = $db.disponibilidade_medico.medico_id == $medico.id && $db.disponibilidade_medico.fim > $agora && $db.disponibilidade_medico.encerrado_em == null
      sort = {inicio: "asc"}
      return = {type: "list"}
    } as $periodos
  }

  response = {agora: $agora, plantoes: $periodos|map:{id: $$.id, inicio: $$.inicio, fim: $$.fim}}
}

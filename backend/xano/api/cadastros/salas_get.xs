// Salas com os médicos que as têm como sala atual (add-cadastros-administrador).
query salas verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {}

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.query sala {
      sort = {nome: "asc"}
      return = {type: "list"}
    } as $salas

    db.query medico {
      where = $db.medico.sala_id != null
      return = {type: "list"}
    } as $medicos

    var $lista { value = [] }
    foreach ($salas) {
      each as $sala {
        var $quantos { value = ($medicos|filter:($$.sala_id == $sala.id))|count }
        var.update $lista {
          value = $lista|push:{id: $sala.id, nome: $sala.nome, descricao: $sala.descricao, ativo: $sala.ativo, medicos: $quantos}
        }
      }
    }
  }

  response = $lista
}

// Catálogo completo para o Administrador: ativos e inativos, com os destinos em ordem (add-cadastros-administrador).
// A triagem continua usando GET sintomas do grupo Triagem (só ativos).
query sintomas verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {}

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.query sintoma {
      sort = {nome: "asc"}
      return = {type: "list"}
    } as $sintomas

    db.query sintoma_especialidade {
      sort = {ordem: "asc"}
      return = {type: "list"}
    } as $destinos

    db.query especialidade {
      return = {type: "list"}
    } as $especialidades

    var $lista { value = [] }
    foreach ($sintomas) {
      each as $sintoma {
        var $meus { value = $destinos|filter:($$.sintoma_id == $sintoma.id) }
        var $nomes { value = [] }
        foreach ($meus) {
          each as $destino {
            var $esp { value = $especialidades|find:($$.id == $destino.especialidade_id) }
            var.update $nomes { value = $nomes|push:(($esp == null) ? "?" : $esp.nome) }
          }
        }
        var $ids_destino { value = $meus|map:$$.especialidade_id }
        var.update $lista {
          value = $lista|push:{id: $sintoma.id, nome: $sintoma.nome, descricao: $sintoma.descricao, grupo: $sintoma.grupo, pontuacao: $sintoma.pontuacao, ativo: $sintoma.ativo, especialidade_ids: $ids_destino, especialidades: $nomes}
        }
      }
    }
  }

  response = $lista
}

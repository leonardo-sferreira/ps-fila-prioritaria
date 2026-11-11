// Médicos com login, CRM, especialidades próprias e sala atual (add-cadastros-administrador).
query medicos verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {}

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.query medico {
      return = {type: "list"}
    } as $medicos

    var $usuario_ids { value = $medicos|map:$$.usuario_id }

    db.query usuario {
      where = $db.usuario.id in $usuario_ids
      return = {type: "list"}
    } as $usuarios

    db.query medico_especialidade {
      return = {type: "list"}
    } as $vinculos

    db.query especialidade {
      return = {type: "list"}
    } as $especialidades

    db.query sala {
      return = {type: "list"}
    } as $salas

    var $lista { value = [] }
    foreach ($medicos) {
      each as $medico {
        var $login { value = $usuarios|find:($$.id == $medico.usuario_id) }
        var $meus { value = $vinculos|filter:($$.medico_id == $medico.id) }
        var $ids_esp { value = $meus|map:$$.especialidade_id }
        var $nomes_esp { value = [] }
        foreach ($ids_esp) {
          each as $id_esp {
            var $esp { value = $especialidades|find:($$.id == $id_esp) }
            var.update $nomes_esp { value = $nomes_esp|push:(($esp == null) ? "?" : $esp.nome) }
          }
        }
        var $sala { value = ($medico.sala_id == null) ? null : ($salas|find:($$.id == $medico.sala_id)) }
        var $nome { value = ($login == null) ? "" : $login.nome }
        var $email { value = ($login == null) ? "" : $login.email }
        var $nome_sala { value = ($sala == null) ? null : $sala.nome }
        var.update $lista {
          value = $lista|push:{id: $medico.id, usuario_id: $medico.usuario_id, nome: $nome, email: $email, crm: $medico.registro_profissional, ativo: $medico.ativo, especialidade_ids: $ids_esp, especialidades: $nomes_esp, sala_id: $medico.sala_id, sala: $nome_sala}
        }
      }
    }
  }

  response = $lista|sort:"nome":"itext":true
}

// Todos os usuários com nome, e-mail, perfil e situação, sem senha (add-autenticacao-perfis, gestao-usuarios).
// Para médico e Recepção/Triagem traz também o ID do cadastro, para a tela levar ao cadastro certo.
query usuarios verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {}

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.query usuario {
      sort = {nome: "asc"}
      return = {type: "list"}
    } as $usuarios

    db.query medico {
      return = {type: "list"}
    } as $medicos

    db.query recepcao_triagem {
      return = {type: "list"}
    } as $recepcao

    var $lista { value = [] }
    foreach ($usuarios) {
      each as $item {
        var $medico { value = $medicos|find:($$.usuario_id == $item.id) }
        var $cadastro_recepcao { value = $recepcao|find:($$.usuario_id == $item.id) }
        var $proprio { value = $item.id == $usuario.id }
        var.update $lista {
          value = $lista|push:{id: $item.id, nome: $item.nome, email: $item.email, perfil: $item.perfil, ativo: $item.ativo, proprio: $proprio, medico_id: (($medico == null) ? null : $medico.id), recepcao_id: (($cadastro_recepcao == null) ? null : $cadastro_recepcao.id)}
        }
      }
    }
  }

  response = $lista
  guid = "Rx5xq6D72yrttfhm8bQGxPqvCuE"
}

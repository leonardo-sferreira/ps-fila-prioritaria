// Pessoas da Recepção/Triagem com login, CPF e especialidade de referência (add-cadastros-administrador).
query recepcao verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {}

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.query recepcao_triagem {
      return = {type: "list"}
    } as $cadastros

    var $usuario_ids { value = $cadastros|map:$$.usuario_id }

    db.query usuario {
      where = $db.usuario.id in $usuario_ids
      return = {type: "list"}
    } as $usuarios

    db.query especialidade {
      return = {type: "list"}
    } as $especialidades

    var $lista { value = [] }
    foreach ($cadastros) {
      each as $cadastro {
        var $login { value = $usuarios|find:($$.id == $cadastro.usuario_id) }
        var $esp { value = ($cadastro.especialidade_referencia_id == null) ? null : ($especialidades|find:($$.id == $cadastro.especialidade_referencia_id)) }
        var $nome { value = ($login == null) ? "" : $login.nome }
        var $email { value = ($login == null) ? "" : $login.email }
        var $nome_esp { value = ($esp == null) ? null : $esp.nome }
        var.update $lista {
          value = $lista|push:{id: $cadastro.id, usuario_id: $cadastro.usuario_id, nome: $nome, email: $email, cpf: $cadastro.cpf, especialidade_referencia_id: $cadastro.especialidade_referencia_id, especialidade_referencia: $nome_esp, ativo: $cadastro.ativo, pendente: false}
        }
      }
    }

    // Logins de Recepção/Triagem sem cadastro (criados fora das telas): aparecem com id 0 e pendente = true,
    // para o Administrador completar o CPF em Usuários (usuarios/{id} cria o cadastro).
    db.query usuario {
      where = $db.usuario.perfil == "RECEPCAO_TRIAGEM"
      return = {type: "list"}
    } as $logins_recepcao

    foreach ($logins_recepcao) {
      each as $login_sem {
        conditional {
          if (!($usuario_ids|in:$login_sem.id)) {
            var.update $lista {
              value = $lista|push:{id: 0, usuario_id: $login_sem.id, nome: $login_sem.nome, email: $login_sem.email, cpf: null, especialidade_referencia_id: null, especialidade_referencia: null, ativo: $login_sem.ativo, pendente: true}
            }
          }
        }
      }
    }
  }

  response = $lista|sort:"nome":"itext":true
  guid = "-t0t219caQPmy3blwheHnBp6KHU"
}

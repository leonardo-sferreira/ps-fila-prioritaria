// Equipe com sessão ativa, para o dashboard do Administrador (add-acompanhamento-administrador, D6, tarefa 2.2).
// Sessão ativa: sem logout e ainda não expirada; vale a mais recente de cada usuário. Sem e-mail nem CPF.
query "admin/equipe" verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {}

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.query sessao {
      where = $db.sessao.logout_em == null && $db.sessao.expira_em > now
      sort = {login_em: "desc"}
      return = {type: "list"}
    } as $sessoes

    var $usuario_ids {
      value = $sessoes|map:$$.usuario_id|unique
    }

    db.query usuario {
      where = $db.usuario.id in $usuario_ids
      return = {type: "list"}
    } as $usuarios

    var $equipe { value = [] }
    foreach ($usuario_ids) {
      each as $id {
        var $sessao { value = $sessoes|find:($$.usuario_id == $id) }
        var $pessoa { value = $usuarios|find:($$.id == $id) }
        conditional {
          if ($pessoa != null && $pessoa.ativo) {
            var.update $equipe {
              value = $equipe|push:{usuario_id: $id, nome: $pessoa.nome, perfil: $pessoa.perfil, status: $sessao.status_operacional, login_em: $sessao.login_em}
            }
          }
        }
      }
    }
  }

  response = {equipe: $equipe, agora: now}
}

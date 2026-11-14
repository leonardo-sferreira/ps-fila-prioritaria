// Todos os usuários com nome, e-mail, perfil e situação, sem senha (add-autenticacao-perfis, gestao-usuarios).
// Para médico e Recepção/Triagem traz também o cadastro (CRM, especialidades e sala; CPF e especialidade de
// referência), para a edição na própria tela de Usuários (revisão de 14/11/2026).
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

    db.query medico_especialidade {
      return = {type: "list"}
    } as $vinculos

    var $lista { value = [] }
    foreach ($usuarios) {
      each as $item {
        var $medico { value = $medicos|find:($$.usuario_id == $item.id) }
        var $cadastro_recepcao { value = $recepcao|find:($$.usuario_id == $item.id) }
        var $proprio { value = $item.id == $usuario.id }
        var $esp_medico { value = ($medico == null) ? [] : (($vinculos|filter:($$.medico_id == $medico.id))|map:$$.especialidade_id) }
        var.update $lista {
          value = $lista|push:{id: $item.id, nome: $item.nome, email: $item.email, perfil: $item.perfil, ativo: $item.ativo, proprio: $proprio, medico_id: (($medico == null) ? null : $medico.id), recepcao_id: (($cadastro_recepcao == null) ? null : $cadastro_recepcao.id), crm: (($medico == null) ? null : $medico.registro_profissional), sala_id: (($medico == null) ? null : $medico.sala_id), especialidade_ids: $esp_medico, cpf: (($cadastro_recepcao == null) ? null : $cadastro_recepcao.cpf), especialidade_referencia_id: (($cadastro_recepcao == null) ? null : $cadastro_recepcao.especialidade_referencia_id)}
        }
      }
    }
  }

  response = $lista
  guid = "Rx5xq6D72yrttfhm8bQGxPqvCuE"
}

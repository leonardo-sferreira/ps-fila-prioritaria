// Cria outro Administrador (add-autenticacao-perfis, D14). Médicos e Recepção/Triagem são criados pelos cadastros.
// A senha nunca vai para a auditoria nem para a resposta.
query usuarios verb=POST {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    text nome filters=trim
    text email filters=trim|lower
    text senha {
      sensitive = true
    }
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    precondition (($input.nome|strlen) >= 3) {
      error_type = "inputerror"
      error = "Informe o nome."
    }

    precondition (($input.senha|strlen) >= 8) {
      error_type = "inputerror"
      error = "A senha inicial deve ter 8 ou mais caracteres."
    }

    function.run "cadastros/email_livre" {
      input = {email: $input.email}
    } as $email

    db.transaction {
      stack {
        db.add usuario {
          data = {nome: $input.nome, email: $email, password: $input.senha, perfil: "ADMINISTRADOR", ativo: true}
        } as $novo

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "ADMINISTRADOR_CRIADO", entidade: "USUARIO", registro_id: $novo.id, valor_anterior: null, valor_novo: {nome: $novo.nome, email: $novo.email, perfil: "ADMINISTRADOR"}}
        } as $auditoria
      }
    }
  }

  response = {id: $novo.id, nome: $novo.nome, email: $novo.email, perfil: "ADMINISTRADOR", ativo: true}
  guid = "B83ut4b2TJqj5XyRdrx8_Dour5Y"
}

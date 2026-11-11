// Cria o login (perfil MEDICO) e o médico juntos, com especialidades próprias e sala opcional
// (add-cadastros-administrador, D3 e D4). A senha nunca vai para a auditoria nem para a resposta.
query medicos verb=POST {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    text nome filters=trim
    text email filters=trim|lower
    text senha {
      sensitive = true
    }
    text crm filters=trim
    json especialidade_ids
    int? sala_id?
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    precondition (($input.nome|strlen) >= 3) {
      error_type = "inputerror"
      error = "Informe o nome do médico."
    }

    precondition (($input.senha|strlen) >= 8) {
      error_type = "inputerror"
      error = "A senha inicial deve ter 8 ou mais caracteres."
    }

    precondition (($input.crm|strlen) >= 4) {
      error_type = "inputerror"
      error = "Informe o CRM."
    }

    function.run "cadastros/email_livre" {
      input = {email: $input.email}
    } as $email

    function.run "cadastros/especialidades_validas" {
      input = {especialidade_ids: $input.especialidade_ids}
    } as $proprias

    function.run "cadastros/sala_valida" {
      input = {sala_id: $input.sala_id}
    } as $sala_id

    db.transaction {
      stack {
        db.add usuario {
          data = {nome: $input.nome, email: $email, password: $input.senha, perfil: "MEDICO", ativo: true}
        } as $login

        db.add medico {
          data = {usuario_id: $login.id, registro_profissional: $input.crm, ativo: true, sala_id: $sala_id}
        } as $medico

        function.run "cadastros/gravar_vinculos" {
          input = {tipo: "MEDICO", dono_id: $medico.id, especialidade_ids: $proprias}
        } as $gravados

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "MEDICO_CRIADO", entidade: "MEDICO", registro_id: $medico.id, valor_anterior: null, valor_novo: {nome: $login.nome, email: $login.email, crm: $medico.registro_profissional, especialidade_ids: $proprias, sala_id: $sala_id}}
        } as $auditoria
      }
    }
  }

  response = {id: $medico.id, usuario_id: $login.id, nome: $login.nome, email: $login.email, crm: $medico.registro_profissional, ativo: true, especialidade_ids: $proprias, sala_id: $sala_id}
}

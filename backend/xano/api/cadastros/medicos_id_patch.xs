// Edita nome e e-mail (no login), CRM, especialidades próprias e sala do médico (add-cadastros-administrador).
// A senha não muda aqui: o médico usa "Esqueci minha senha".
query "medicos/{medico_id}" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int medico_id
    text nome filters=trim
    text email filters=trim|lower
    text crm filters=trim
    json especialidade_ids
    int? sala_id?
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.get medico {
      field_name = "id"
      field_value = $input.medico_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Médico não encontrado."
    }

    db.get usuario {
      field_name = "id"
      field_value = $anterior.usuario_id
    } as $login_anterior

    // Depois de uma troca de perfil o cadastro antigo fica só como histórico: não mexe mais no login (D14).
    precondition ($login_anterior.perfil == "MEDICO") {
      error_type = "inputerror"
      error = "CADASTRO_DE_OUTRO_PERFIL"
    }

    precondition (($input.nome|strlen) >= 3) {
      error_type = "inputerror"
      error = "Informe o nome do médico."
    }

    precondition (($input.crm|strlen) >= 4) {
      error_type = "inputerror"
      error = "Informe o CRM."
    }

    function.run "cadastros/email_livre" {
      input = {email: $input.email, ignorar_usuario_id: $anterior.usuario_id}
    } as $email

    function.run "cadastros/especialidades_validas" {
      input = {especialidade_ids: $input.especialidade_ids}
    } as $proprias

    function.run "cadastros/sala_valida" {
      input = {sala_id: $input.sala_id}
    } as $sala_id

    db.query medico_especialidade {
      where = $db.medico_especialidade.medico_id == $anterior.id
      return = {type: "list"}
    } as $vinculos_anteriores

    var $ids_anteriores { value = $vinculos_anteriores|map:$$.especialidade_id }

    db.transaction {
      stack {
        db.edit usuario {
          field_name = "id"
          field_value = $anterior.usuario_id
          data = {nome: $input.nome, email: $email}
        } as $login

        db.edit medico {
          field_name = "id"
          field_value = $anterior.id
          data = {registro_profissional: $input.crm, sala_id: $sala_id}
        } as $medico

        function.run "cadastros/gravar_vinculos" {
          input = {tipo: "MEDICO", dono_id: $anterior.id, especialidade_ids: $proprias}
        } as $gravados

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "MEDICO_EDITADO", entidade: "MEDICO", registro_id: $anterior.id, valor_anterior: {nome: $login_anterior.nome, email: $login_anterior.email, crm: $anterior.registro_profissional, especialidade_ids: $ids_anteriores, sala_id: $anterior.sala_id}, valor_novo: {nome: $login.nome, email: $login.email, crm: $medico.registro_profissional, especialidade_ids: $proprias, sala_id: $sala_id}}
        } as $auditoria
      }
    }
  }

  response = {id: $medico.id, nome: $login.nome, email: $login.email, crm: $medico.registro_profissional, ativo: $medico.ativo, especialidade_ids: $proprias, sala_id: $sala_id}
  guid = "gwf2FljM9stV28H3IvfYp2whSy0"
}

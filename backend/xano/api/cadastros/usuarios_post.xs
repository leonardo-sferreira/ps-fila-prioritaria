// Cria um usuário de qualquer perfil (add-autenticacao-perfis, D14; revisão de 14/11/2026): o Administrador cadastra
// Administradores, Médicos e Recepção/Triagem. Para Médico e Recepção/Triagem cria também o cadastro do perfil, na
// mesma transação, com os dados exigidos. A senha nunca vai para a auditoria nem para a resposta.
query usuarios verb=POST {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    text nome filters=trim
    text email filters=trim|lower
    text senha {
      sensitive = true
    }
    // Sem perfil, cria Administrador (compatível com a tela antiga).
    text? perfil? filters=trim|upper
    // Médico:
    text? crm? filters=trim
    json? especialidade_ids?
    int? sala_id?
    // Recepção/Triagem:
    text? cpf? filters=trim
    int? especialidade_referencia_id?
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    var $perfil { value = (($input.perfil ?? "") == "") ? "ADMINISTRADOR" : $input.perfil }

    precondition (["RECEPCAO_TRIAGEM", "MEDICO", "ADMINISTRADOR"]|in:$perfil) {
      error_type = "inputerror"
      error = "Perfil inválido."
    }

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

    // Dados exigidos pelo perfil, validados antes de qualquer gravação.
    var $proprias { value = [] }
    var $sala_id { value = null }
    var $cpf { value = null }
    var $referencia { value = null }
    conditional {
      if ($perfil == "MEDICO") {
        precondition ((($input.crm ?? "")|strlen) >= 4) {
          error_type = "inputerror"
          error = "Informe o CRM."
        }
        function.run "cadastros/especialidades_validas" {
          input = {especialidade_ids: $input.especialidade_ids}
        } as $especialidades_ok
        var.update $proprias { value = $especialidades_ok }
        function.run "cadastros/sala_valida" {
          input = {sala_id: $input.sala_id}
        } as $sala_ok
        var.update $sala_id { value = $sala_ok }
      }
      elseif ($perfil == "RECEPCAO_TRIAGEM") {
        function.run "pacientes/normalizar_cpf" {
          input = {cpf: $input.cpf ?? ""}
        } as $cpf_ok
        db.get recepcao_triagem {
          field_name = "cpf"
          field_value = $cpf_ok
        } as $dono_cpf
        precondition ($dono_cpf == null) {
          error_type = "inputerror"
          error = "CPF já cadastrado."
        }
        var.update $cpf { value = $cpf_ok }
        conditional {
          if ($input.especialidade_referencia_id != null && $input.especialidade_referencia_id != 0) {
            function.run "cadastros/especialidades_validas" {
              input = {especialidade_ids: [$input.especialidade_referencia_id]}
            } as $referencia_ok
            var.update $referencia { value = $input.especialidade_referencia_id }
          }
        }
      }
    }

    db.transaction {
      stack {
        db.add usuario {
          data = {nome: $input.nome, email: $email, password: $input.senha, perfil: $perfil, ativo: true}
        } as $novo

        conditional {
          if ($perfil == "MEDICO") {
            db.add medico {
              data = {usuario_id: $novo.id, registro_profissional: $input.crm, sala_id: $sala_id, ativo: true}
            } as $medico_novo
            function.run "cadastros/gravar_vinculos" {
              input = {tipo: "MEDICO", dono_id: $medico_novo.id, especialidade_ids: $proprias}
            } as $gravados
          }
          elseif ($perfil == "RECEPCAO_TRIAGEM") {
            db.add recepcao_triagem {
              data = {usuario_id: $novo.id, cpf: $cpf, especialidade_referencia_id: $referencia, ativo: true}
            } as $recepcao_nova
          }
        }

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "USUARIO_CRIADO", entidade: "USUARIO", registro_id: $novo.id, valor_anterior: null, valor_novo: {nome: $novo.nome, email: $novo.email, perfil: $perfil, crm: (($perfil == "MEDICO") ? $input.crm : null), especialidade_ids: $proprias, sala_id: $sala_id, especialidade_referencia_id: $referencia}}
        } as $auditoria
      }
    }
  }

  response = {id: $novo.id, nome: $novo.nome, email: $novo.email, perfil: $perfil, ativo: true}
  guid = "B83ut4b2TJqj5XyRdrx8_Dour5Y"
}

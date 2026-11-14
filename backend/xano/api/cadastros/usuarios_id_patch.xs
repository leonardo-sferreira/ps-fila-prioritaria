// Edita um usuário de qualquer perfil (add-autenticacao-perfis, D14; revisão de 14/11/2026): nome e e-mail no login e,
// conforme o perfil atual, CRM/especialidades/sala do Médico ou CPF/especialidade de referência da Recepção/Triagem.
// Se o login não tiver o cadastro do perfil (usuário criado fora das telas), o cadastro é criado aqui, na mesma
// transação. O perfil não muda aqui: a troca é feita em usuarios/{id}/perfil.
query "usuarios/{usuario_id}" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int usuario_id
    text nome filters=trim
    text email filters=trim|lower
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

    db.get usuario {
      field_name = "id"
      field_value = $input.usuario_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }

    precondition (($input.nome|strlen) >= 3) {
      error_type = "inputerror"
      error = "Informe o nome."
    }

    function.run "cadastros/email_livre" {
      input = {email: $input.email, ignorar_usuario_id: $anterior.id}
    } as $email

    db.get medico {
      field_name = "usuario_id"
      field_value = $anterior.id
    } as $medico_existente

    db.get recepcao_triagem {
      field_name = "usuario_id"
      field_value = $anterior.id
    } as $recepcao_existente

    // Dados do perfil atual, validados antes de qualquer gravação.
    var $proprias { value = [] }
    var $sala_id { value = null }
    var $cpf { value = null }
    var $referencia { value = null }
    conditional {
      if ($anterior.perfil == "MEDICO") {
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
      elseif ($anterior.perfil == "RECEPCAO_TRIAGEM") {
        function.run "pacientes/normalizar_cpf" {
          input = {cpf: $input.cpf ?? ""}
        } as $cpf_ok
        db.get recepcao_triagem {
          field_name = "cpf"
          field_value = $cpf_ok
        } as $dono_cpf
        precondition ($dono_cpf == null || $dono_cpf.usuario_id == $anterior.id) {
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
        db.edit usuario {
          field_name = "id"
          field_value = $anterior.id
          data = {nome: $input.nome, email: $email}
        } as $editado

        conditional {
          if ($anterior.perfil == "MEDICO") {
            conditional {
              if ($medico_existente != null) {
                db.edit medico {
                  field_name = "id"
                  field_value = $medico_existente.id
                  data = {registro_profissional: $input.crm, sala_id: $sala_id}
                } as $medico_gravado
              }
              else {
                db.add medico {
                  data = {usuario_id: $anterior.id, registro_profissional: $input.crm, sala_id: $sala_id, ativo: $anterior.ativo}
                } as $medico_gravado
              }
            }
            function.run "cadastros/gravar_vinculos" {
              input = {tipo: "MEDICO", dono_id: $medico_gravado.id, especialidade_ids: $proprias}
            } as $gravados
          }
          elseif ($anterior.perfil == "RECEPCAO_TRIAGEM") {
            conditional {
              if ($recepcao_existente != null) {
                db.edit recepcao_triagem {
                  field_name = "id"
                  field_value = $recepcao_existente.id
                  data = {cpf: $cpf, especialidade_referencia_id: $referencia}
                } as $recepcao_gravada
              }
              else {
                db.add recepcao_triagem {
                  data = {usuario_id: $anterior.id, cpf: $cpf, especialidade_referencia_id: $referencia, ativo: $anterior.ativo}
                } as $recepcao_gravada
              }
            }
          }
        }

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "USUARIO_EDITADO", entidade: "USUARIO", registro_id: $anterior.id, valor_anterior: {nome: $anterior.nome, email: $anterior.email, crm: (($medico_existente == null) ? null : $medico_existente.registro_profissional), sala_id: (($medico_existente == null) ? null : $medico_existente.sala_id), especialidade_referencia_id: (($recepcao_existente == null) ? null : $recepcao_existente.especialidade_referencia_id)}, valor_novo: {nome: $editado.nome, email: $editado.email, crm: (($anterior.perfil == "MEDICO") ? $input.crm : null), especialidade_ids: $proprias, sala_id: $sala_id, especialidade_referencia_id: $referencia}}
        } as $auditoria
      }
    }
  }

  response = {id: $editado.id, nome: $editado.nome, email: $editado.email, perfil: $editado.perfil, ativo: $editado.ativo}
  guid = "OyeNbp_9SV_E5OtwAbIxhjbWAMo"
}

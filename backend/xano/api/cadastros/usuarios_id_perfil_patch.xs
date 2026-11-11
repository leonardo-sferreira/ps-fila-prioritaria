// Troca o perfil de um usuário (add-autenticacao-perfis, D14). Não troca o próprio perfil, não deixa o sistema sem
// administrador ativo e não troca médico com ficha CHAMADO. Na mesma transação: desativa o cadastro do perfil antigo,
// reativa (ou cria) o do perfil novo com os dados exigidos e grava o perfil. Vale na próxima requisição do usuário.
query "usuarios/{usuario_id}/perfil" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int usuario_id
    text perfil filters=trim|upper
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

    precondition (["RECEPCAO_TRIAGEM", "MEDICO", "ADMINISTRADOR"]|in:$input.perfil) {
      error_type = "inputerror"
      error = "Perfil inválido."
    }

    db.get usuario {
      field_name = "id"
      field_value = $input.usuario_id
    } as $anterior

    precondition ($anterior != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }

    precondition ($anterior.id != $usuario.id) {
      error_type = "inputerror"
      error = "PROPRIO_PERFIL"
    }

    precondition ($anterior.perfil != $input.perfil) {
      error_type = "inputerror"
      error = "O usuário já tem este perfil."
    }

    // Sai de Administrador: não pode deixar o sistema sem administrador ativo.
    conditional {
      if ($anterior.perfil == "ADMINISTRADOR" && $anterior.ativo) {
        db.query usuario {
          where = $db.usuario.perfil == "ADMINISTRADOR" && $db.usuario.ativo == true
          return = {type: "list"}
        } as $admins
        function.run "usuarios/deixa_sem_admin" {
          input = {admins_ativos: $admins|map:$$.id, usuario_id: $anterior.id}
        } as $sem_admin
        precondition (!$sem_admin) {
          error_type = "inputerror"
          error = "ULTIMO_ADMINISTRADOR"
        }
      }
    }

    db.get medico {
      field_name = "usuario_id"
      field_value = $anterior.id
    } as $medico_existente

    db.get recepcao_triagem {
      field_name = "usuario_id"
      field_value = $anterior.id
    } as $recepcao_existente

    // Sai de Médico: não pode ter ficha chamada em andamento.
    conditional {
      if ($anterior.perfil == "MEDICO" && $medico_existente != null) {
        db.query ficha_atendimento {
          where = $db.ficha_atendimento.status == "CHAMADO" && $db.ficha_atendimento.medico_chamada_id == $medico_existente.id
          return = {type: "exists"}
        } as $com_chamada
        precondition (!$com_chamada) {
          error_type = "inputerror"
          error = "MEDICO_COM_FICHA_CHAMADA"
        }
      }
    }

    // Dados exigidos pelo perfil novo, validados antes de qualquer gravação.
    var $proprias { value = [] }
    var $sala_id { value = null }
    var $cpf { value = null }
    var $referencia { value = null }
    conditional {
      if ($input.perfil == "MEDICO") {
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
      elseif ($input.perfil == "RECEPCAO_TRIAGEM") {
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
        // 1. Desativa o cadastro do perfil antigo (histórico preservado).
        conditional {
          if ($anterior.perfil == "MEDICO" && $medico_existente != null) {
            db.edit medico {
              field_name = "id"
              field_value = $medico_existente.id
              data = {ativo: false}
            } as $medico_desativado
          }
          elseif ($anterior.perfil == "RECEPCAO_TRIAGEM" && $recepcao_existente != null) {
            db.edit recepcao_triagem {
              field_name = "id"
              field_value = $recepcao_existente.id
              data = {ativo: false}
            } as $recepcao_desativada
          }
        }

        // 2. Reativa ou cria o cadastro do perfil novo, com a mesma situação do login.
        conditional {
          if ($input.perfil == "MEDICO") {
            conditional {
              if ($medico_existente != null) {
                db.edit medico {
                  field_name = "id"
                  field_value = $medico_existente.id
                  data = {registro_profissional: $input.crm, sala_id: $sala_id, ativo: $anterior.ativo}
                } as $medico_novo
              }
              else {
                db.add medico {
                  data = {usuario_id: $anterior.id, registro_profissional: $input.crm, sala_id: $sala_id, ativo: $anterior.ativo}
                } as $medico_novo
              }
            }
            function.run "cadastros/gravar_vinculos" {
              input = {tipo: "MEDICO", dono_id: $medico_novo.id, especialidade_ids: $proprias}
            } as $gravados
          }
          elseif ($input.perfil == "RECEPCAO_TRIAGEM") {
            conditional {
              if ($recepcao_existente != null) {
                db.edit recepcao_triagem {
                  field_name = "id"
                  field_value = $recepcao_existente.id
                  data = {cpf: $cpf, especialidade_referencia_id: $referencia, ativo: $anterior.ativo}
                } as $recepcao_nova
              }
              else {
                db.add recepcao_triagem {
                  data = {usuario_id: $anterior.id, cpf: $cpf, especialidade_referencia_id: $referencia, ativo: $anterior.ativo}
                } as $recepcao_nova
              }
            }
          }
        }

        // 3. Grava o perfil; vale na próxima requisição (verificar_acesso lê o perfil a cada chamada).
        db.edit usuario {
          field_name = "id"
          field_value = $anterior.id
          data = {perfil: $input.perfil}
        } as $editado

        function.run "registrar_alteracao" {
          input = {usuario_id: $usuario.id, tipo_evento: "PERFIL_ALTERADO", entidade: "USUARIO", registro_id: $anterior.id, valor_anterior: {perfil: $anterior.perfil}, valor_novo: {perfil: $input.perfil, crm: (($input.perfil == "MEDICO") ? $input.crm : null), especialidade_ids: $proprias, sala_id: $sala_id, especialidade_referencia_id: $referencia}}
        } as $auditoria

        // 4. Confere de novo, já com a gravação feita: duas trocas simultâneas não podem zerar os administradores.
        db.query usuario {
          where = $db.usuario.perfil == "ADMINISTRADOR" && $db.usuario.ativo == true
          return = {type: "count"}
        } as $admins_depois

        precondition ($admins_depois > 0) {
          error_type = "inputerror"
          error = "ULTIMO_ADMINISTRADOR"
        }
      }
    }
  }

  response = {id: $editado.id, perfil: $editado.perfil, ativo: $editado.ativo}
}

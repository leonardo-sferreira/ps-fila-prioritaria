// Encerra o acesso de um cenário sintético, preservando fichas e auditoria históricas.
function "fila/teste_encerrar_cenario" {
  input {
    text marcador filters=trim
  }

  stack {
    db.get usuario {
      field_name = "email"
      field_value = "fila-um-" ~ $input.marcador ~ "@example.invalid"
    } as $usuario_um

    db.get usuario {
      field_name = "email"
      field_value = "fila-dois-" ~ $input.marcador ~ "@example.invalid"
    } as $usuario_dois

    db.get usuario {
      field_name = "email"
      field_value = "fila-recepcao-" ~ $input.marcador ~ "@example.invalid"
    } as $usuario_recepcao

    db.get usuario {
      field_name = "email"
      field_value = "fila-admin-" ~ $input.marcador ~ "@example.invalid"
    } as $usuario_admin

    precondition ($usuario_um != null && $usuario_dois != null && $usuario_um.nome == "Teste Fila Médico Um" && $usuario_dois.nome == "Teste Fila Médico Dois") {
      error_type = "accessdenied"
      error = "CENARIO_TESTE_INVALIDO"
    }

    precondition (($usuario_recepcao == null || $usuario_recepcao.nome == "Teste Fila Recepção") && ($usuario_admin == null || $usuario_admin.nome == "Teste Fila Administrador")) {
      error_type = "accessdenied"
      error = "CENARIO_TESTE_INVALIDO"
    }

    db.get medico {
      field_name = "usuario_id"
      field_value = $usuario_um.id
    } as $medico_um

    db.get medico {
      field_name = "usuario_id"
      field_value = $usuario_dois.id
    } as $medico_dois

    precondition ($medico_um != null && $medico_dois != null && $medico_um.registro_profissional == ("TESTE-UM-" ~ $input.marcador) && $medico_dois.registro_profissional == ("TESTE-DOIS-" ~ $input.marcador)) {
      error_type = "accessdenied"
      error = "CENARIO_TESTE_INVALIDO"
    }

    db.query ficha_atendimento {
      where = $db.ficha_atendimento.senha == ("V-CAR-" ~ $input.marcador)
      return = {type: "list"}
    } as $fichas

    precondition (($fichas|count) == 2 && ($fichas|filter:$$.status == "AGUARDANDO" || $$.status == "CHAMADO"|count) == 0) {
      error_type = "inputerror"
      error = "FICHAS_DE_TESTE_PENDENTES"
    }

    db.transaction {
      stack {
        foreach ($fichas) {
          each as $ficha {
            db.get paciente {
              field_name = "id"
              field_value = $ficha.paciente_id
            } as $paciente

            precondition ($paciente != null && ($paciente.nome == "Paciente Fictício Fila Um" || $paciente.nome == "Paciente Fictício Fila Dois")) {
              error_type = "accessdenied"
              error = "CENARIO_TESTE_INVALIDO"
            }

            db.edit paciente {
              field_name = "id"
              field_value = $paciente.id
              data = {ativo: false}
            } as $paciente_encerrado
          }
        }

        db.query sessao {
          where = $db.sessao.usuario_id == $usuario_um.id || $db.sessao.usuario_id == $usuario_dois.id
          return = {type: "list"}
        } as $sessoes

        foreach ($sessoes) {
          each as $sessao {
            db.edit sessao {
              field_name = "id"
              field_value = $sessao.id
              data = {logout_em: $sessao.logout_em ?? now}
            } as $sessao_encerrada
          }
        }

        db.query disponibilidade_medico {
          where = $db.disponibilidade_medico.medico_id == $medico_um.id || $db.disponibilidade_medico.medico_id == $medico_dois.id
          return = {type: "list"}
        } as $periodos

        foreach ($periodos) {
          each as $periodo {
            db.edit disponibilidade_medico {
              field_name = "id"
              field_value = $periodo.id
              data = {encerrado_em: $periodo.encerrado_em ?? now}
            } as $periodo_encerrado
          }
        }

        db.edit medico {
          field_name = "id"
          field_value = $medico_um.id
          data = {ativo: false}
        } as $medico_um_encerrado

        db.edit medico {
          field_name = "id"
          field_value = $medico_dois.id
          data = {ativo: false}
        } as $medico_dois_encerrado

        db.edit usuario {
          field_name = "id"
          field_value = $usuario_um.id
          data = {ativo: false}
        } as $usuario_um_encerrado

        db.edit usuario {
          field_name = "id"
          field_value = $usuario_dois.id
          data = {ativo: false}
        } as $usuario_dois_encerrado

        conditional {
          if ($usuario_recepcao != null) {
            db.edit usuario {
              field_name = "id"
              field_value = $usuario_recepcao.id
              data = {ativo: false}
            } as $usuario_recepcao_encerrado
          }
        }

        conditional {
          if ($usuario_admin != null) {
            db.edit usuario {
              field_name = "id"
              field_value = $usuario_admin.id
              data = {ativo: false}
            } as $usuario_admin_encerrado
          }
        }
      }
    }
  }

  response = {
    usuarios          : [$usuario_um.id, $usuario_dois.id]
    fichas_preservadas: $fichas|count
  }

  guid = "aVUyPLOfrr_LqDW_gOLTxAt0XhI"
}

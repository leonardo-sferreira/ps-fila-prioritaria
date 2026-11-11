// Uso restrito ao CLI do workspace para testes de integração. Não há endpoint público.
// Cria dois médicos e duas fichas inteiramente fictícios para testar a chamada.
function "fila/teste_criar_cenario" {
  input {
    text marcador filters=trim
    password senha
    text cpf_um
    text cpf_dois
  }

  stack {
    db.get especialidade {
      field_name = "sigla"
      field_value = "CAR"
    } as $cardiologia

    db.get especialidade {
      field_name = "sigla"
      field_value = "CLI"
    } as $clinica

    db.get especialidade {
      field_name = "sigla"
      field_value = "NEU"
    } as $neurologia

    precondition ($cardiologia != null && $clinica != null && $neurologia != null) {
      error_type = "inputerror"
      error = "ESPECIALIDADES_NAO_CONFIGURADAS"
    }

    var $saida {
      value = null
    }

    db.transaction {
      stack {
        db.add usuario {
          data = {
            nome    : "Teste Fila Médico Um"
            email   : "fila-um-" ~ $input.marcador ~ "@example.invalid"
            password: $input.senha
            perfil  : "MEDICO"
            ativo   : true
          }
        } as $usuario_um

        db.add usuario {
          data = {
            nome    : "Teste Fila Médico Dois"
            email   : "fila-dois-" ~ $input.marcador ~ "@example.invalid"
            password: $input.senha
            perfil  : "MEDICO"
            ativo   : true
          }
        } as $usuario_dois

        db.add usuario {
          data = {
            nome    : "Teste Fila Recepção"
            email   : "fila-recepcao-" ~ $input.marcador ~ "@example.invalid"
            password: $input.senha
            perfil  : "RECEPCAO_TRIAGEM"
            ativo   : true
          }
        } as $usuario_recepcao

        db.add usuario {
          data = {
            nome    : "Teste Fila Administrador"
            email   : "fila-admin-" ~ $input.marcador ~ "@example.invalid"
            password: $input.senha
            perfil  : "ADMINISTRADOR"
            ativo   : true
          }
        } as $usuario_admin

        db.add medico {
          data = {
            usuario_id           : $usuario_um.id
            registro_profissional: "TESTE-UM-" ~ $input.marcador
            ativo                : true
          }
        } as $medico_um

        db.add medico {
          data = {
            usuario_id           : $usuario_dois.id
            registro_profissional: "TESTE-DOIS-" ~ $input.marcador
            ativo                : true
          }
        } as $medico_dois

        db.add medico_especialidade {
          data = {
            medico_id       : $medico_um.id
            especialidade_id: $cardiologia.id
          }
        } as $vinculo_um

        db.add medico_especialidade {
          data = {
            medico_id       : $medico_um.id
            especialidade_id: $neurologia.id
          }
        } as $vinculo_dois

        db.add medico_especialidade {
          data = {
            medico_id       : $medico_dois.id
            especialidade_id: $clinica.id
          }
        } as $vinculo_tres

        db.add disponibilidade_medico {
          data = {
            medico_id: $medico_um.id
            inicio   : now|add_secs_to_timestamp:-3600
            fim      : now|add_secs_to_timestamp:3600
          }
        } as $periodo_um

        db.add disponibilidade_medico {
          data = {
            medico_id: $medico_dois.id
            inicio   : now|add_secs_to_timestamp:-3600
            fim      : now|add_secs_to_timestamp:3600
          }
        } as $periodo_dois

        db.add sessao {
          data = {
            usuario_id        : $usuario_um.id
            login_em          : now
            expira_em         : now|add_secs_to_timestamp:3600
            status_operacional: "DISPONIVEL"
          }
        } as $sessao_um

        db.add sessao {
          data = {
            usuario_id        : $usuario_dois.id
            login_em          : now
            expira_em         : now|add_secs_to_timestamp:3600
            status_operacional: "DISPONIVEL"
          }
        } as $sessao_dois

        db.add paciente {
          data = {
            cpf            : $input.cpf_um
            nome           : "Paciente Fictício Fila Um"
            data_nascimento: "1990-01-01"
            ativo          : true
          }
        } as $paciente_um

        db.add paciente {
          data = {
            cpf            : $input.cpf_dois
            nome           : "Paciente Fictício Fila Dois"
            data_nascimento: "1990-01-01"
            ativo          : true
          }
        } as $paciente_dois

        db.add ficha_atendimento {
          data = {
            paciente_id               : $paciente_um.id
            chegada_em                : now
            fila_em                   : now
            status                    : "AGUARDANDO"
            prioridade_atual          : "VERMELHA"
            condicao_prioritaria      : "NENHUMA"
            especialidade_atribuida_id: $cardiologia.id
            senha                     : "V-CAR-" ~ $input.marcador
            oportunidade              : 1
            tentativas_chamada        : 0
          }
        } as $ficha_um

        db.add ficha_atendimento {
          data = {
            paciente_id               : $paciente_dois.id
            chegada_em                : now
            fila_em                   : now
            status                    : "AGUARDANDO"
            prioridade_atual          : "AMARELA"
            condicao_prioritaria      : "NENHUMA"
            especialidade_atribuida_id: $cardiologia.id
            senha                     : "A-CAR-" ~ $input.marcador
            oportunidade              : 1
            tentativas_chamada        : 0
          }
        } as $ficha_dois

        security.create_auth_token {
          table = "usuario"
          extras = {}
          expiration = 3600
          id = $usuario_um.id
        } as $token_um

        security.create_auth_token {
          table = "usuario"
          extras = {}
          expiration = 3600
          id = $usuario_dois.id
        } as $token_dois

        security.create_auth_token {
          table = "usuario"
          extras = {}
          expiration = 3600
          id = $usuario_recepcao.id
        } as $token_recepcao

        security.create_auth_token {
          table = "usuario"
          extras = {}
          expiration = 3600
          id = $usuario_admin.id
        } as $token_admin

        var.update $saida {
          value = {
            marcador        : $input.marcador
            usuario_um      : $usuario_um.id
            usuario_dois    : $usuario_dois.id
            usuario_recepcao: $usuario_recepcao.id
            usuario_admin   : $usuario_admin.id
            medico_um       : $medico_um.id
            medico_dois     : $medico_dois.id
            ficha_um        : $ficha_um.id
            ficha_dois      : $ficha_dois.id
            paciente_um     : $paciente_um.id
            paciente_dois   : $paciente_dois.id
            sessao_um       : $sessao_um.id
            sessao_dois     : $sessao_dois.id
            periodo_um      : $periodo_um.id
            periodo_dois    : $periodo_dois.id
            vinculos        : [$vinculo_um.id, $vinculo_dois.id, $vinculo_tres.id]
            token_um        : $token_um
            token_dois      : $token_dois
            token_recepcao  : $token_recepcao
            token_admin     : $token_admin
          }
        }
      }
    }
  }

  response = $saida
  guid = "RjG7nR6odthPJeDXIpvJu8Aud7Q"
}

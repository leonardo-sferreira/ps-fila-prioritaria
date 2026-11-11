// Seleciona e reserva uma ficha para o médico em transação com bloqueio de registro.
function "fila/chamar_proximo" {
  input {
    int usuario_id
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $input.usuario_id
        perfis_permitidos: ["MEDICO"]
      }
    } as $usuario

    db.get medico {
      field_name = "usuario_id"
      field_value = $usuario.id
    } as $medico

    precondition ($medico != null && $medico.ativo) {
      error_type = "accessdenied"
      error = "MEDICO_INATIVO"
    }

    var $saida {
      value = null
    }

    for (3) {
      each as $tentativa_reserva {
        conditional {
          if ($saida == null) {
            try_catch {
              try {
                db.transaction {
                  stack {
                    // O UPDATE sem mudança material trava a linha do médico até o fim da transação.
                    db.edit medico {
                      field_name = "id"
                      field_value = $medico.id
                      data = {ativo: $medico.ativo}
                    } as $medico_travado

                    function.run "fila/cobertura_atual" as $cobertura
                    var $apto {
                      value = $cobertura.medicos|find:$$.id == $medico.id
                    }

                    precondition ($apto != null && $apto.usuario_id == $usuario.id) {
                      error_type = "inputerror"
                      error = "MEDICO_INDISPONIVEL"
                    }

                    db.query ficha_atendimento {
                      where = $db.ficha_atendimento.medico_chamada_id == $medico.id && $db.ficha_atendimento.status == "CHAMADO"
                      return = {type: "exists"}
                    } as $pendente

                    precondition (!$pendente) {
                      error_type = "inputerror"
                      error = "FICHA_PENDENTE"
                    }

                    function.run "fila/selecionar_atual" {
                      input = {medico_id: $medico.id}
                    } as $selecao

                    var $candidata {
                      value = $selecao.selecao.candidata
                    }

                    conditional {
                      if ($candidata == null) {
                        var.update $saida {
                          value = {fila_vazia: true, mensagem: "FILA_VAZIA"}
                        }
                      }

                      else {
                        // A atualização mantém a oportunidade e bloqueia a ficha até o commit.
                        db.edit ficha_atendimento {
                          field_name = "id"
                          field_value = $candidata.ficha.id
                          data = {oportunidade: $candidata.ficha.oportunidade ?? 1}
                        } as $ficha_travada

                        db.get ficha_atendimento {
                          field_name = "id"
                          field_value = $candidata.ficha.id
                        } as $ficha_confirmada

                        precondition ($ficha_confirmada.status == "AGUARDANDO") {
                          error_type = "inputerror"
                          error = "CONFLITO_FILA"
                        }

                        db.edit ficha_atendimento {
                          field_name = "id"
                          field_value = $candidata.ficha.id
                          data = {
                            status            : "CHAMADO"
                            medico_chamada_id : $medico.id
                            tentativas_chamada: 1
                            chamada_em        : now
                          }
                        } as $ficha_reservada

                        db.add chamada {
                          data = {
                            ficha_id    : $candidata.ficha.id
                            medico_id   : $medico.id
                            oportunidade: $candidata.ficha.oportunidade ?? 1
                            tentativa   : 1
                            tipo        : "CHAMADA"
                            created_at  : now
                          }
                        } as $evento

                        conditional {
                          if ($candidata.avanca_ciclo) {
                            conditional {
                              if ($candidata.ciclo_id == null) {
                                db.add ciclo_fila {
                                  data = {
                                    especialidade_id: $candidata.especialidade_id
                                    posicao         : $candidata.proxima_posicao
                                  }
                                } as $ciclo_novo
                              }

                              else {
                                db.edit ciclo_fila {
                                  field_name = "id"
                                  field_value = $candidata.ciclo_id
                                  data = {posicao: $candidata.proxima_posicao}
                                } as $ciclo_atualizado
                              }
                            }
                          }
                        }

                        db.edit sessao {
                          field_name = "id"
                          field_value = $apto.sessao_id
                          data = {status_operacional: "DISPONIVEL"}
                        } as $sessao_atualizada

                        function.run registrar_alteracao {
                          input = {
                            usuario_id    : $usuario.id
                            tipo_evento   : "CHAMADA"
                            entidade      : "FICHA_ATENDIMENTO"
                            registro_id   : $candidata.ficha.id
                            valor_anterior: {
                            status      : "AGUARDANDO"
                            oportunidade: $candidata.ficha.oportunidade ?? 1
                          }
                            valor_novo    : {
                            status   : "CHAMADO"
                            medico_id: $medico.id
                            tentativa: 1
                          }
                          }
                        } as $auditoria

                        db.get paciente {
                          field_name = "id"
                          field_value = $candidata.ficha.paciente_id
                        } as $paciente

                        var.update $saida {
                          value = {
                            fila_vazia: false
                            ficha     : {id: $candidata.ficha.id, senha: $candidata.ficha.senha, status: "CHAMADO", nome: ($paciente == null) ? null : $paciente.nome, especialidade_id: $candidata.especialidade_id, especialidade: $candidata.especialidade_nome, oportunidade: $candidata.ficha.oportunidade ?? 1, tentativa: 1}
                            origem    : $selecao.selecao.origem
                          }
                        }
                      }
                    }
                  }
                }
              }

              catch {
                db.query ficha_atendimento {
                  where = $db.ficha_atendimento.medico_chamada_id == $medico.id && $db.ficha_atendimento.status == "CHAMADO"
                  return = {type: "exists"}
                } as $ficou_pendente

                // Uma ação simultânea pode ter criado a ficha pendente depois da seleção.
                conditional {
                  if ($ficou_pendente) {
                    precondition (false) {
                      error_type = "inputerror"
                      error = "FICHA_PENDENTE"
                    }
                  }

                  else {
                    function.run "fila/cobertura_atual" as $cobertura_apos_erro
                    var $apto_apos_erro {
                      value = $cobertura_apos_erro.medicos|find:$$.id == $medico.id
                    }

                    precondition ($apto_apos_erro != null) {
                      error_type = "inputerror"
                      error = "MEDICO_INDISPONIVEL"
                    }

                    // Uma ficha disputada pode ter sido reservada por outro médico.
                    // A próxima iteração refaz a seleção com os dados atuais.
                  }
                }
              }
            }
          }
        }
      }
    }

    precondition ($saida != null) {
      error_type = "inputerror"
      error = "CONFLITO_FILA"
    }
  }

  response = $saida
  guid = "bbWrHJOvg5OPWCzylg_w_1f9b7s"
}

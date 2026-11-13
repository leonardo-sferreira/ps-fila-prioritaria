// Regras puras de elegibilidade e cobertura; a leitura dos registros fica em cobertura_atual.
// Calcula médicos aptos e especialidades cobertas pelos próprios médicos.
function "fila/avaliar_cobertura" {
  input {
    json medicos
  }

  stack {
    var $aptos {
      value = []
    }

    var $cobertas {
      value = []
    }

    foreach ($input.medicos) {
      each as $medico {
        var $apto {
          value = $medico.medico_ativo == true && $medico.usuario_ativo == true && $medico.plantao_vigente == true && $medico.sessao_ativa == true && ($medico.status == "DISPONIVEL" || $medico.status == "EM_ATENDIMENTO")
        }

        conditional {
          if ($apto) {
            var.update $aptos {
              value = $aptos|push:$medico
            }

            foreach ($medico.especialidade_ids ?? []) {
              each as $especialidade_id {
                var.update $cobertas {
                  value = $cobertas|push:$especialidade_id
                }
              }
            }
          }
        }
      }
    }
  }

  response = {medicos: $aptos, especialidade_ids: $cobertas|unique}

  test "pausa e ausência não cobrem; atendimento cobre" {
    input = {
      medicos: [{id: 1, medico_ativo: true, usuario_ativo: true, plantao_vigente: true, sessao_ativa: true, status: "PAUSA", especialidade_ids: [1]}, {id: 2, medico_ativo: true, usuario_ativo: true, plantao_vigente: true, sessao_ativa: true, status: "AUSENTE", especialidade_ids: [2]}, {id: 3, medico_ativo: true, usuario_ativo: true, plantao_vigente: true, sessao_ativa: true, status: "EM_ATENDIMENTO", especialidade_ids: [3]}]
    }

    expect.to_equal ($response.especialidade_ids) {
      value = [3]
    }
  }

  guid = "ena6Xv7Lc-kFmtNJFBACr3RlQEY"
}

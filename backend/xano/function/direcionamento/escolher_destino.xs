// Regra pura do destino da ficha (add-direcionamento-senha, D2; Rev. 2.1 §6, §14.2 e D09). Não acessa o banco.
// Até a idade máxima de criança → Pediatria. Sem sintoma do catálogo ligado a especialidade → especialidade padrão.
// Senão, entre as especialidades ligadas aos sintomas: 1º maior pontuação individual, 2º maior soma,
// 3º menos fichas AGUARDANDO, 4º menor ID. Cor e disponibilidade de Médico não entram.
function "direcionamento/escolher_destino" {
  description = "Escolhe a especialidade de destino pela idade, pelos sintomas do catálogo e pelo desempate da Rev. 2.1."

  input {
    int? idade?
    int? idade_maxima_crianca?
    int? pediatria_id?
    int? padrao_id?
    // [{pontuacao, especialidade_ids: [..]}] dos sintomas do catálogo da ficha (digitados não entram).
    json? sintomas?
    // [{especialidade_id, aguardando}] com a quantidade de fichas AGUARDANDO por especialidade.
    json? filas?
  }

  stack {
    var $destino { value = null }
    var $motivo { value = null }
    var $sintomas { value = $input.sintomas ?? [] }
    var $filas { value = $input.filas ?? [] }

    var $crianca {
      value = $input.idade != null && $input.idade_maxima_crianca != null && $input.idade <= $input.idade_maxima_crianca
    }

    conditional {
      if ($crianca) {
        var.update $destino { value = $input.pediatria_id }
        var.update $motivo { value = ($input.pediatria_id == null) ? "PEDIATRIA_NAO_CONFIGURADA" : "PEDIATRIA" }
      }
      else {
        // Especialidades candidatas: as ligadas a algum sintoma do catálogo (um sintoma conta para todas as suas).
        var $maior_por { value = {} }

        foreach ($sintomas) {
          each as $sintoma {
            foreach ($sintoma.especialidade_ids ?? []) {
              each as $especialidade_id {
                var $chave { value = $especialidade_id|to_text }
                var.update $maior_por {
                  value = $maior_por|set:$chave:(($maior_por|get:$chave:0)|max:$sintoma.pontuacao)
                }
              }
            }
          }
        }

        var $candidatas { value = $maior_por|keys }

        conditional {
          if (($candidatas|count) == 0) {
            var.update $destino { value = $input.padrao_id }
            var.update $motivo { value = ($input.padrao_id == null) ? "PADRAO_NAO_CONFIGURADO" : "PADRAO" }
          }
          else {
            // Critérios em variáveis simples, sem objeto na comparação: com {maior, soma, ...} o Xano perdia a soma e o
            // desempate caía direto na fila (defeito encontrado no roteiro do card 103 em 20/11/2026). A maior
            // pontuação e a soma de cada candidata são recalculadas aqui direto da lista de sintomas.
            var $melhor_id { value = null }
            var $melhor_maior { value = 0 }
            var $melhor_soma { value = 0 }
            var $melhor_aguardando { value = 0 }

            foreach ($candidatas) {
              each as $chave {
                var $id_atual { value = $chave|to_int }
                var $maior_atual { value = 0 }
                var $soma_atual { value = 0 }

                foreach ($sintomas) {
                  each as $sintoma_candidato {
                    conditional {
                      if (($sintoma_candidato.especialidade_ids ?? [])|in:$id_atual) {
                        var.update $soma_atual { value = $soma_atual + $sintoma_candidato.pontuacao }
                        conditional {
                          if ($sintoma_candidato.pontuacao > $maior_atual) {
                            var.update $maior_atual { value = $sintoma_candidato.pontuacao }
                          }
                        }
                      }
                    }
                  }
                }

                var $fila {
                  value = $filas|find:($$.especialidade_id == $id_atual)
                }
                var $aguardando_atual { value = ($fila == null) ? 0 : ($fila.aguardando ?? 0) }
                var $vence { value = false }

                conditional {
                  if ($melhor_id == null) {
                    var.update $vence { value = true }
                  }
                  elseif ($maior_atual > $melhor_maior) {
                    var.update $vence { value = true }
                  }
                  elseif ($maior_atual == $melhor_maior && $soma_atual > $melhor_soma) {
                    var.update $vence { value = true }
                  }
                  elseif ($maior_atual == $melhor_maior && $soma_atual == $melhor_soma && $aguardando_atual < $melhor_aguardando) {
                    var.update $vence { value = true }
                  }
                  elseif ($maior_atual == $melhor_maior && $soma_atual == $melhor_soma && $aguardando_atual == $melhor_aguardando && $id_atual < $melhor_id) {
                    var.update $vence { value = true }
                  }
                }

                conditional {
                  if ($vence) {
                    var.update $melhor_id { value = $id_atual }
                    var.update $melhor_maior { value = $maior_atual }
                    var.update $melhor_soma { value = $soma_atual }
                    var.update $melhor_aguardando { value = $aguardando_atual }
                  }
                }
              }
            }

            var.update $destino { value = $melhor_id }
            var.update $motivo { value = "SINTOMAS" }
          }
        }
      }
    }
  }

  response = {especialidade_id: $destino, motivo: $motivo}

  test "um sintoma de Cardiologia" {
    input = {idade: 40, idade_maxima_crianca: 11, pediatria_id: 5, padrao_id: 2, sintomas: [{pontuacao: 2, especialidade_ids: [1]}], filas: []}
    expect.to_equal ($response.especialidade_id) {
      value = 1
    }
    expect.to_equal ($response.motivo) {
      value = "SINTOMAS"
    }
  }

  test "maior pontuação individual vence (Neurologia 3 contra Cardiologia 2)" {
    input = {idade: 40, idade_maxima_crianca: 11, pediatria_id: 5, padrao_id: 2, sintomas: [{pontuacao: 2, especialidade_ids: [1]}, {pontuacao: 3, especialidade_ids: [3]}], filas: []}
    expect.to_equal ($response.especialidade_id) {
      value = 3
    }
  }

  test "empate na maior decidido pela soma (Cardiologia 2+2 contra Clínica 2)" {
    input = {idade: 40, idade_maxima_crianca: 11, pediatria_id: 5, padrao_id: 2, sintomas: [{pontuacao: 2, especialidade_ids: [1]}, {pontuacao: 2, especialidade_ids: [1]}, {pontuacao: 2, especialidade_ids: [2]}], filas: []}
    expect.to_equal ($response.especialidade_id) {
      value = 1
    }
  }

  test "soma vence mesmo com fila maior (Cardiologia 2+2 com 3 na fila contra Clínica 2)" {
    input = {idade: 40, idade_maxima_crianca: 11, pediatria_id: 5, padrao_id: 2, sintomas: [{pontuacao: 2, especialidade_ids: [1]}, {pontuacao: 2, especialidade_ids: [1]}, {pontuacao: 2, especialidade_ids: [2]}], filas: [{especialidade_id: 1, aguardando: 3}, {especialidade_id: 2, aguardando: 0}]}
    expect.to_equal ($response.especialidade_id) {
      value = 1
    }
  }

  test "soma vence o menor ID (Clínica 2+2 contra Cardiologia 2)" {
    input = {idade: 40, idade_maxima_crianca: 11, pediatria_id: 5, padrao_id: 2, sintomas: [{pontuacao: 2, especialidade_ids: [2]}, {pontuacao: 2, especialidade_ids: [2]}, {pontuacao: 2, especialidade_ids: [1]}], filas: []}
    expect.to_equal ($response.especialidade_id) {
      value = 2
    }
  }

  test "empate decidido pela fila menor" {
    input = {idade: 40, idade_maxima_crianca: 11, pediatria_id: 5, padrao_id: 2, sintomas: [{pontuacao: 2, especialidade_ids: [1]}, {pontuacao: 2, especialidade_ids: [3]}], filas: [{especialidade_id: 1, aguardando: 4}, {especialidade_id: 3, aguardando: 1}]}
    expect.to_equal ($response.especialidade_id) {
      value = 3
    }
  }

  test "empate total decidido pelo menor ID" {
    input = {idade: 40, idade_maxima_crianca: 11, pediatria_id: 5, padrao_id: 2, sintomas: [{pontuacao: 2, especialidade_ids: [4]}, {pontuacao: 2, especialidade_ids: [3]}], filas: [{especialidade_id: 3, aguardando: 2}, {especialidade_id: 4, aguardando: 2}]}
    expect.to_equal ($response.especialidade_id) {
      value = 3
    }
  }

  test "11 anos vai para Pediatria" {
    input = {idade: 11, idade_maxima_crianca: 11, pediatria_id: 5, padrao_id: 2, sintomas: [{pontuacao: 3, especialidade_ids: [3]}], filas: []}
    expect.to_equal ($response.especialidade_id) {
      value = 5
    }
    expect.to_equal ($response.motivo) {
      value = "PEDIATRIA"
    }
  }

  test "12 anos segue os sintomas" {
    input = {idade: 12, idade_maxima_crianca: 11, pediatria_id: 5, padrao_id: 2, sintomas: [{pontuacao: 3, especialidade_ids: [3]}], filas: []}
    expect.to_equal ($response.especialidade_id) {
      value = 3
    }
  }

  test "sem sintoma do catálogo vai para a especialidade padrão" {
    input = {idade: 40, idade_maxima_crianca: 11, pediatria_id: 5, padrao_id: 2, sintomas: [], filas: []}
    expect.to_equal ($response.especialidade_id) {
      value = 2
    }
    expect.to_equal ($response.motivo) {
      value = "PADRAO"
    }
  }

  test "sem especialidade padrão configurada" {
    input = {idade: 40, idade_maxima_crianca: 11, pediatria_id: 5, padrao_id: null, sintomas: [], filas: []}
    expect.to_be_null ($response.especialidade_id)
    expect.to_equal ($response.motivo) {
      value = "PADRAO_NAO_CONFIGURADO"
    }
  }
  guid = "6zsW5To7DFBi-S4AuDfVcTEUInc"
}

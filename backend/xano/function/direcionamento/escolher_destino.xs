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
        // Maior pontuação individual e soma por especialidade candidata (um sintoma conta para todas as suas).
        var $maior_por { value = {} }
        var $soma_por { value = {} }

        foreach ($sintomas) {
          each as $sintoma {
            foreach ($sintoma.especialidade_ids ?? []) {
              each as $especialidade_id {
                var $chave { value = $especialidade_id|to_text }
                var.update $maior_por {
                  value = $maior_por|set:$chave:(($maior_por|get:$chave:0)|max:$sintoma.pontuacao)
                }
                var.update $soma_por {
                  value = $soma_por|set:$chave:(($soma_por|get:$chave:0) + $sintoma.pontuacao)
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
            var $melhor { value = null }

            foreach ($candidatas) {
              each as $chave {
                var $fila {
                  value = $filas|find:($$.especialidade_id == ($chave|to_int))
                }
                // Valores em variáveis próprias: dentro do objeto, `get:$chave:0, soma:` fazia o Xano engolir a chave seguinte.
                var $maior_atual { value = $maior_por|get:$chave:0 }
                var $soma_atual { value = $soma_por|get:$chave:0 }
                var $aguardando_atual { value = ($fila == null) ? 0 : ($fila.aguardando ?? 0) }
                var $atual {
                  value = {id: ($chave|to_int), maior: $maior_atual, soma: $soma_atual, aguardando: $aguardando_atual}
                }
                conditional {
                  if ($melhor == null) {
                    var.update $melhor { value = $atual }
                  }
                  elseif ($atual.maior > $melhor.maior || ($atual.maior == $melhor.maior && $atual.soma > $melhor.soma) || ($atual.maior == $melhor.maior && $atual.soma == $melhor.soma && $atual.aguardando < $melhor.aguardando) || ($atual.maior == $melhor.maior && $atual.soma == $melhor.soma && $atual.aguardando == $melhor.aguardando && $atual.id < $melhor.id)) {
                    var.update $melhor { value = $atual }
                  }
                }
              }
            }

            var.update $destino { value = $melhor.id }
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

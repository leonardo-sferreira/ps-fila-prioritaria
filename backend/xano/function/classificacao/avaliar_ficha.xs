// Lê a ficha e tudo o que a classificação usa e chama a regra pura `pontuar` (add-classificacao-prioridade, D4).
// Só leitura: o PATCH grava o resultado; o GET apenas devolve. Faixa ou parâmetro ausente vira pendência.
function "classificacao/avaliar_ficha" {
  description = "Calcula a classificação atual da ficha e devolve ficha, paciente, idade, sintomas e resultado."

  input {
    int ficha_id
  }

  stack {
    db.get ficha_atendimento {
      field_name = "id"
      field_value = $input.ficha_id
    } as $ficha

    precondition ($ficha != null) {
      error_type = "notfound"
      error = "FICHA_NAO_ENCONTRADA"
    }

    db.get paciente {
      field_name = "id"
      field_value = $ficha.paciente_id
    } as $paciente

    // Idade completa na data de chegada, no fuso oficial do PS.
    var $idade { value = null }
    conditional {
      if ($paciente != null && $paciente.data_nascimento != null && $ficha.chegada_em != null) {
        var $chegada { value = $ficha.chegada_em|format_timestamp:"Y-m-d":"America/Sao_Paulo" }
        var $nascimento { value = $paciente.data_nascimento|to_text }
        var $anos { value = ($chegada|substr:0:4|to_int) - ($nascimento|substr:0:4|to_int) }
        var $dia_chegada { value = (($chegada|substr:5:2|to_int) * 100) + ($chegada|substr:8:2|to_int) }
        var $dia_nascimento { value = (($nascimento|substr:5:2|to_int) * 100) + ($nascimento|substr:8:2|to_int) }
        conditional {
          if ($dia_chegada < $dia_nascimento) {
            var.update $anos { value = $anos - 1 }
          }
        }
        var.update $idade { value = $anos }
      }
    }

    db.query ficha_sintoma {
      where = $db.ficha_sintoma.ficha_id == $ficha.id
      return = {type: "list"}
    } as $vinculos

    var $sintoma_ids { value = ($vinculos|map:$$.sintoma_id)|unique }

    db.query sintoma {
      where = $db.sintoma.id in $sintoma_ids
      return = {type: "list"}
    } as $sintomas

    db.query ficha_sintoma_livre {
      where = $db.ficha_sintoma_livre.ficha_id == $ficha.id
      sort = {id: "asc"}
      return = {type: "list"}
    } as $sintomas_livres

    db.query faixa_sinal_vital {
      return = {type: "list"}
    } as $faixas

    var $parametros { value = {} }
    foreach (["LIMIAR_AMARELA", "LIMIAR_VERMELHA", "IDADE_MINIMA_TABELA_ADULTA", "IDADE_MINIMA_IDOSO", "IDADE_MAXIMA_CRIANCA"]) {
      each as $chave {
        db.get parametro {
          field_name = "chave"
          field_value = $chave
        } as $parametro
        conditional {
          if ($parametro != null) {
            var.update $parametros { value = $parametros|set:$chave:($parametro.valor|to_int) }
          }
        }
      }
    }

    var $pontos_sintomas { value = ($sintomas|map:$$.pontuacao)|merge:($sintomas_livres|map:$$.pontuacao) }

    function.run "classificacao/pontuar" {
      input = {
        sinais         : {pa_sistolica: $ficha.pa_sistolica, fc: $ficha.fc, fr: $ficha.fr, temperatura: $ficha.temperatura, spo2: $ficha.spo2, glicemia: $ficha.glicemia, glicemia_sinais_gravidade: $ficha.glicemia_sinais_gravidade}
        gestante       : $ficha.gestante == true
        idade          : $idade
        pontos_sintomas: $pontos_sintomas
        tem_observacao : (($ficha.observacao ?? "")|trim|strlen) > 0
        parametros     : $parametros
        faixas         : $faixas
      }
    } as $classificacao
  }

  response = {
    ficha          : $ficha
    paciente       : $paciente
    idade          : $idade
    sintomas       : $sintomas
    sintomas_livres: $sintomas_livres
    classificacao  : $classificacao
  }
  guid = "HJDvtd_TtnrvsSA27iaT8-vwXxg"
}

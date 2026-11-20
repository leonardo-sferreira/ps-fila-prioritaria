// Previsão das próximas senhas de uma especialidade (add-painel-publico, D1): monta parâmetros do ciclo, posição
// atual e fichas AGUARDANDO e chama a regra pura prever_fila. Compartilhada pelo endpoint autenticado de previsão
// e pelo painel público, para os dois mostrarem a mesma ordem da chamada real (RN25, CA11). Só leitura.
// Devolve [{senha, cor}] das próximas senhas da especialidade pela mesma regra da chamada.
function "fila/previsao_especialidade" {
  input {
    int especialidade_id
  }

  stack {
    db.get parametro {
      field_name = "chave"
      field_value = "amarelas_por_ciclo"
    } as $param_amarelas

    db.get parametro {
      field_name = "chave"
      field_value = "azuis_por_ciclo"
    } as $param_azuis

    db.get parametro {
      field_name = "chave"
      field_value = "tamanho_previsao"
    } as $param_tamanho

    precondition ($param_amarelas != null && $param_azuis != null && $param_tamanho != null) {
      error_type = "inputerror"
      error = "PARAMETROS_NAO_CONFIGURADOS"
    }

    db.get ciclo_fila {
      field_name = "especialidade_id"
      field_value = $input.especialidade_id
    } as $ciclo

    var $posicao {
      value = ($ciclo == null) ? 1 : $ciclo.posicao
    }

    db.query ficha_atendimento {
      where = $db.ficha_atendimento.status == "AGUARDANDO" && $db.ficha_atendimento.especialidade_atribuida_id == $input.especialidade_id
      return = {type: "list"}
    } as $fichas

    function.run "fila/prever_fila" {
      input = {
        fichas  : $fichas
        posicao : $posicao
        amarelas: $param_amarelas.valor|to_int
        azuis   : $param_azuis.valor|to_int
        limite  : $param_tamanho.valor|to_int
      }
    } as $previsao
  }

  response = $previsao
  guid = "gSh1nZUso8FNPiACYB6uTZJFBT4"
}
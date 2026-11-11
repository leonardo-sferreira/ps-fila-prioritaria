query "filas/{especialidade}/previsao" verb=GET {
  api_group = "Fila"
  auth = "usuario"

  input {
    int especialidade
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $auth.id
        perfis_permitidos: ["RECEPCAO_TRIAGEM", "MEDICO", "ADMINISTRADOR"]
      }
    } as $usuario

    db.get especialidade {
      field_name = "id"
      field_value = $input.especialidade
    } as $especialidade

    precondition ($especialidade != null) {
      error_type = "notfound"
      error = "ESPECIALIDADE_NAO_ENCONTRADA"
    }

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
      field_value = $especialidade.id
    } as $ciclo

    var $posicao {
      value = ($ciclo == null) ? 1 : $ciclo.posicao
    }

    db.query ficha_atendimento {
      where = $db.ficha_atendimento.status == "AGUARDANDO" && $db.ficha_atendimento.especialidade_atribuida_id == $especialidade.id
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
  guid = "t-7XJLFYNQ_ve7OWc82CEULQAXk"
}

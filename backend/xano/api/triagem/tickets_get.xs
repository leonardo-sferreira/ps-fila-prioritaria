query "tickets" verb=GET {
  api_group = "Triagem"
  auth = "usuario"
  input {}
  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM", "ADMINISTRADOR"]}
    } as $usuario
    db.get parametro {
      field_name = "chave"
      field_value = "INTERVALO_CHAMADA_SEGUNDOS"
    } as $intervalo
    db.get parametro {
      field_name = "chave"
      field_value = "INTERVALO_REPETICAO_SEGUNDOS"
    } as $intervalo_repeticao
    db.get parametro {
      field_name = "chave"
      field_value = "TENTATIVAS_CHAMADA"
    } as $limite
    // Parâmetro ausente vira 0 em vez de quebrar a consulta: INTERVALO_REPETICAO_SEGUNDOS só é criado por
    // inicializar_parametros_fila no primeiro "Chamar próximo" (chamada-manual-pre-triagem, D3). A tela trata 0 como
    // "sem contagem" e o Xano valida o prazo nas ações.
    var $segundos_intervalo { value = 0 }
    var $segundos_repeticao { value = 0 }
    var $chamadas_maximas { value = 0 }
    conditional {
      if ($intervalo != null) {
        var.update $segundos_intervalo { value = $intervalo.valor|to_int }
      }
    }
    conditional {
      if ($intervalo_repeticao != null) {
        var.update $segundos_repeticao { value = $intervalo_repeticao.valor|to_int }
      }
    }
    conditional {
      if ($limite != null) {
        var.update $chamadas_maximas { value = $limite.valor|to_int }
      }
    }
    db.query ticket_pre_triagem {
      where = $db.ticket_pre_triagem.status in ["AGUARDANDO", "CHAMADO"]
      sort = {emitido_em: "asc", id: "asc"}
      return = {type: "list"}
    } as $tickets
  }
  response = {tickets: $tickets, agora: now, intervalo_segundos: $segundos_intervalo, intervalo_repeticao_segundos: $segundos_repeticao, tentativas_maximas: $chamadas_maximas}
  guid = "9v_043dHDFrRkGee1sMi9cqba9c"
}

query "tickets" verb=GET {
  api_group = "Triagem"
  auth = "usuario"
  input {}
  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM"]}
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
    db.query ticket_pre_triagem {
      where = $db.ticket_pre_triagem.status in ["AGUARDANDO", "CHAMADO"]
      sort = {emitido_em: "asc", id: "asc"}
      return = {type: "list"}
    } as $tickets
  }
  response = {tickets: $tickets, agora: now, intervalo_segundos: ($intervalo.valor|to_int), intervalo_repeticao_segundos: ($intervalo_repeticao.valor|to_int), tentativas_maximas: ($limite.valor|to_int)}
  guid = "9v_043dHDFrRkGee1sMi9cqba9c"
}

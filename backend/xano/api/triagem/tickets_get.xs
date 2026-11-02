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
    db.query ticket_pre_triagem {
      where = $db.ticket_pre_triagem.status in ["AGUARDANDO", "CHAMADO"]
      sort = {emitido_em: "asc", id: "asc"}
      return = {type: "list"}
    } as $tickets
  }
  response = {tickets: $tickets, agora: now, intervalo_segundos: ($intervalo.valor|to_int)}
  guid = "9v_043dHDFrRkGee1sMi9cqba9c"
}

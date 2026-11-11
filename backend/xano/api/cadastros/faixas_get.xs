// Faixas de pontuação dos sinais vitais, por parâmetro e limite inferior (add-cadastros-administrador, D8).
query faixas verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {}

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.query faixa_sinal_vital {
      sort = {parametro: "asc", pontos: "asc"}
      return = {type: "list"}
    } as $faixas
  }

  response = $faixas|map:{id: $$.id, parametro: $$.parametro, minimo: $$.minimo, maximo: $$.maximo, pontos: $$.pontos, condicao_gravidade: $$.condicao_gravidade}
}

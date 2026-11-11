// Parâmetros com valor atual, rótulo, unidade e limites; só os editáveis vêm marcados (add-cadastros-administrador, D7).
query parametros verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {}

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.query parametro {
      sort = {chave: "asc"}
      return = {type: "list"}
    } as $parametros

    var $lista { value = [] }
    foreach ($parametros) {
      each as $parametro {
        function.run "cadastros/regra_parametro" {
          input = {chave: $parametro.chave}
        } as $regra
        var.update $lista {
          value = $lista|push:{chave: $parametro.chave, valor: $parametro.valor, tipo: $regra.tipo, editavel: $regra.editavel, minimo: $regra.minimo, maximo: $regra.maximo, rotulo: $regra.rotulo, unidade: $regra.unidade}
        }
      }
    }
  }

  response = $lista
}

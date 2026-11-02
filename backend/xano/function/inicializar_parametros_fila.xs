function "inicializar_parametros_fila" {
  input {}
  stack {
    foreach ([{chave: "CICLO_PRE_TRIAGEM_PRIORITARIOS", valor: "2"}, {chave: "CICLO_PRE_TRIAGEM_NORMAIS", valor: "1"}, {chave: "POSICAO_CICLO_PRE_TRIAGEM", valor: "0"}, {chave: "INTERVALO_CHAMADA_SEGUNDOS", valor: "30"}, {chave: "TENTATIVAS_CHAMADA", valor: "3"}]) {
      each as $padrao {
        db.get parametro {
          field_name = "chave"
          field_value = $padrao.chave
        } as $existente
        conditional {
          if ($existente == null) {
            db.add parametro {
              data = {chave: $padrao.chave, valor: $padrao.valor, tipo: "INTEIRO"}
            } as $criado
          }
        }
      }
    }
  }
  response = true
  guid = "pelvKEuyNRsiNBJ-KOpVaF3XENo"
}

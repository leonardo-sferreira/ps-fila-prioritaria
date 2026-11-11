// Altera um parâmetro editável dentro dos limites de cadastros/regra_parametro (add-cadastros-administrador, D7).
// Coerência: criança < tabela adulta <= idoso; limiar Amarela < Vermelha; especialidade padrão ativa.
// A alteração das quantidades do ciclo da fila médica reinicia a posição de todas as especialidades (PR #39).
query "parametros/{chave}" verb=PATCH {
  api_group = "Cadastros"
  auth = "usuario"
  input {
    text chave filters=trim
    int valor
  }
  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $auth.id
        perfis_permitidos: ["ADMINISTRADOR"]
      }
    } as $usuario
    function.run "cadastros/regra_parametro" {
      input = {chave: $input.chave}
    } as $regra
    precondition ($regra.editavel) {
      error_type = "inputerror"
      error = "PARAMETRO_NAO_EDITAVEL_AQUI"
    }
    conditional {
      if ($regra.tipo == "ESPECIALIDADE") {
        function.run "cadastros/especialidades_validas" {
          input = {especialidade_ids: [$input.valor]}
        } as $especialidade_ok
      }
      else {
        precondition ($input.valor >= $regra.minimo && $input.valor <= $regra.maximo) {
          error_type = "inputerror"
          error = "PARAMETRO_FORA_DOS_LIMITES"
        }
      }
    }

    // Coerência entre parâmetros relacionados, com o valor novo no lugar do atual.
    db.query parametro {
      where = $db.parametro.chave in ["IDADE_MAXIMA_CRIANCA", "IDADE_MINIMA_TABELA_ADULTA", "IDADE_MINIMA_IDOSO", "LIMIAR_AMARELA", "LIMIAR_VERMELHA"]
      return = {type: "list"}
    } as $relacionados
    var $valores { value = {} }
    foreach ($relacionados) {
      each as $relacionado {
        var.update $valores { value = $valores|set:$relacionado.chave:($relacionado.valor|to_int) }
      }
    }
    var.update $valores { value = $valores|set:$input.chave:$input.valor }
    var $crianca { value = $valores|get:"IDADE_MAXIMA_CRIANCA":null }
    var $adulta { value = $valores|get:"IDADE_MINIMA_TABELA_ADULTA":null }
    var $idoso { value = $valores|get:"IDADE_MINIMA_IDOSO":null }
    var $amarela { value = $valores|get:"LIMIAR_AMARELA":null }
    var $vermelha { value = $valores|get:"LIMIAR_VERMELHA":null }
    precondition (($crianca == null || $adulta == null || $crianca < $adulta) && ($adulta == null || $idoso == null || $adulta <= $idoso)) {
      error_type = "inputerror"
      error = "IDADES_INCOERENTES"
    }
    precondition ($amarela == null || $vermelha == null || $amarela < $vermelha) {
      error_type = "inputerror"
      error = "LIMIARES_INCOERENTES"
    }

    var $resultado {
      value = null
    }
    db.transaction {
      stack {
        db.get parametro {
          field_name = "chave"
          field_value = $input.chave
        } as $anterior
        precondition ($anterior != null) {
          error_type = "notfound"
          error = "PARAMETRO_NAO_CONFIGURADO"
        }
        conditional {
          if ($anterior.valor != ($input.valor|to_text)) {
            db.edit parametro {
              field_name = "id"
              field_value = $anterior.id
              data = {valor: $input.valor|to_text}
            } as $atualizado
            conditional {
              if ($input.chave == "amarelas_por_ciclo" || $input.chave == "azuis_por_ciclo") {
                db.query ciclo_fila {
                  return = {type: "list"}
                } as $ciclos
                foreach ($ciclos) {
                  each as $ciclo {
                    db.edit ciclo_fila {
                      field_name = "id"
                      field_value = $ciclo.id
                      data = {posicao: 1}
                    } as $reiniciado
                  }
                }
              }
            }

            function.run registrar_alteracao {
              input = {
                usuario_id    : $usuario.id
                tipo_evento   : "PARAMETRO_ALTERADO"
                entidade      : "PARAMETRO"
                registro_id   : $anterior.id
                valor_anterior: {chave: $anterior.chave, valor: $anterior.valor}
                valor_novo    : {chave: $anterior.chave, valor: $atualizado.valor}
              }
            } as $auditoria

            var.update $resultado {
              value = {chave: $atualizado.chave, valor: $atualizado.valor}
            }
          }

          else {
            var.update $resultado {
              value = {chave: $anterior.chave, valor: $anterior.valor}
            }
          }
        }
      }
    }
  }

  response = $resultado
  guid = "WpCoQrBr6eU_Bo10xcsyVpKmP-c"
}

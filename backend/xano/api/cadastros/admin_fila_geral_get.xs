// Fila geral do plantão para o Administrador, só leitura (add-acompanhamento-administrador, D3, tarefa 2.1).
// Fichas EM_TRIAGEM, AGUARDANDO e CHAMADO de todas as especialidades. As AGUARDANDO recebem a posição prevista
// pela mesma regra da chamada (fila/prever_fila, até a 20ª de cada especialidade; depois disso, posicao = null).
// Sem nome nem CPF do paciente. A ordenação da tela fica no Reflex (chamadas, depois aguardando por posição).
query "admin/fila-geral" verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    int? especialidade_id?
    // VERMELHA, AMARELA, AZUL ou vazio.
    text? cor? filters=trim|upper
    // EM_TRIAGEM, AGUARDANDO, CHAMADO ou vazio.
    text? status? filters=trim|upper
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    db.query ficha_atendimento {
      where = $db.ficha_atendimento.status == "EM_TRIAGEM" || $db.ficha_atendimento.status == "AGUARDANDO" || $db.ficha_atendimento.status == "CHAMADO"
      return = {type: "list"}
    } as $abertas

    db.query especialidade {
      return = {type: "list"}
    } as $especialidades

    db.query medico {
      return = {type: "list"}
    } as $medicos

    db.query usuario {
      where = $db.usuario.perfil == "MEDICO"
      return = {type: "list"}
    } as $usuarios_medicos

    db.get parametro {
      field_name = "chave"
      field_value = "amarelas_por_ciclo"
    } as $param_amarelas

    db.get parametro {
      field_name = "chave"
      field_value = "azuis_por_ciclo"
    } as $param_azuis

    // Posição prevista das AGUARDANDO, por especialidade, com a regra da chamada.
    var $posicoes { value = [] }
    foreach ($especialidades) {
      each as $esp {
        var $aguardando_esp { value = $abertas|filter:($$.status == "AGUARDANDO" && $$.especialidade_atribuida_id == $esp.id) }
        conditional {
          if (($aguardando_esp|count) > 0) {
            db.get ciclo_fila {
              field_name = "especialidade_id"
              field_value = $esp.id
            } as $ciclo

            function.run "fila/prever_fila" {
              input = {
                fichas  : $aguardando_esp
                posicao : ($ciclo == null) ? 1 : $ciclo.posicao
                amarelas: ($param_amarelas == null) ? 2 : ($param_amarelas.valor|to_int)
                azuis   : ($param_azuis == null) ? 1 : ($param_azuis.valor|to_int)
                limite  : 20
              }
            } as $previsao

            var $ordem { value = 0 }
            foreach ($previsao) {
              each as $prevista {
                var.update $ordem { value = $ordem + 1 }
                var.update $posicoes { value = $posicoes|push:{senha: $prevista.senha, posicao: $ordem} }
              }
            }
          }
        }
      }
    }

    var $itens { value = [] }
    foreach ($abertas) {
      each as $f {
        var $esp_f { value = ($f.especialidade_atribuida_id == null) ? null : ($especialidades|find:($$.id == $f.especialidade_atribuida_id)) }
        var $med_f { value = ($f.medico_chamada_id == null) ? null : ($medicos|find:($$.id == $f.medico_chamada_id)) }
        var $usu_f { value = ($med_f == null) ? null : ($usuarios_medicos|find:($$.id == $med_f.usuario_id)) }
        var $pos_f { value = ($f.status == "AGUARDANDO" && $f.senha != null) ? ($posicoes|find:($$.senha == $f.senha)) : null }
        var.update $itens {
          value = $itens|push:{id: $f.id, senha: $f.senha, status: $f.status, cor: $f.prioridade_atual, condicao_prioritaria: $f.condicao_prioritaria, especialidade_id: $f.especialidade_atribuida_id, especialidade: (($esp_f == null) ? null : $esp_f.nome), chegada_em: $f.chegada_em, posicao: (($pos_f == null) ? null : $pos_f.posicao), medico: (($usu_f == null) ? null : $usu_f.nome), tentativa: (($f.status == "CHAMADO") ? $f.tentativas_chamada : null), oportunidade: (($f.status == "CHAMADO") ? $f.oportunidade : null)}
        }
      }
    }

    var $filtro_esp { value = ($input.especialidade_id == null || $input.especialidade_id == 0) ? $itens : ($itens|filter:($$.especialidade_id == $input.especialidade_id)) }
    var $filtro_cor { value = (($input.cor ?? "") == "") ? $filtro_esp : ($filtro_esp|filter:($$.cor == $input.cor)) }
    var $filtro_status { value = (($input.status ?? "") == "") ? $filtro_cor : ($filtro_cor|filter:($$.status == $input.status)) }
  }

  response = $filtro_status
  guid = "mxQOi4MvudBI6SZLlsUEPkbqdjU"
}

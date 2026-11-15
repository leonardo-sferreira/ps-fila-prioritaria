// Auditoria consolidada para o Administrador, só leitura (add-acompanhamento-administrador, D2, tarefa 2.3).
// Junta historico_alteracao (alterações), chamada (CHAMADA/COMPARECIMENTO/DESISTENCIA) e sessao (LOGIN/LOGOUT) num
// formato único, ordenado do mais recente para o mais antigo e paginado em 50. Período obrigatório no backend: sem
// datas, vale o dia de hoje (America/Sao_Paulo); no máximo 31 dias. Registro sem usuário é da carga automática ("Sistema").
query "admin/auditoria" verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    // Datas AAAA-MM-DD no fuso de Brasília.
    text? data_inicio? filters=trim
    text? data_fim? filters=trim
    // ALTERACAO, CHAMADA, SESSAO ou vazio (todas).
    text? origem? filters=trim|upper
    int? usuario_id?
    int? pagina?
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    var $hoje { value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo" }
    var $dia_inicio { value = (($input.data_inicio ?? "") == "") ? $hoje : $input.data_inicio }
    var $dia_fim { value = (($input.data_fim ?? "") == "") ? $dia_inicio : $input.data_fim }

    function.run "cadastros/periodo_plantao" {
      input = {data: $dia_inicio, hora_inicio: "00:00", hora_fim: "00:00"}
    } as $janela_inicio

    function.run "cadastros/periodo_plantao" {
      input = {data: $dia_fim, hora_inicio: "00:00", hora_fim: "00:00"}
    } as $janela_fim

    precondition ($janela_inicio.valido && $janela_fim.valido) {
      error_type = "inputerror"
      error = "Data inválida."
    }

    var $de { value = $janela_inicio.inicio }
    var $ate { value = $janela_fim.fim }

    precondition ($ate > $de) {
      error_type = "inputerror"
      error = "A data final deve ser igual ou posterior à inicial."
    }

    // 31 dias em milissegundos.
    precondition (($ate - $de) <= 2678400000) {
      error_type = "inputerror"
      error = "Consulte no máximo 31 dias por vez."
    }

    var $origem { value = $input.origem ?? "" }
    var $pagina { value = (($input.pagina ?? 1) < 1) ? 1 : ($input.pagina ?? 1) }

    db.query usuario {
      return = {type: "list"}
    } as $usuarios

    var $eventos { value = [] }

    // 1. Alterações.
    conditional {
      if ($origem == "" || $origem == "ALTERACAO") {
        db.query historico_alteracao {
          where = $db.historico_alteracao.created_at >= $de && $db.historico_alteracao.created_at < $ate
          return = {type: "list"}
        } as $alteracoes
        foreach ($alteracoes) {
          each as $alt {
            var $quem { value = ($alt.usuario_id == null) ? null : ($usuarios|find:($$.id == $alt.usuario_id)) }
            var.update $eventos {
              value = $eventos|push:{em: $alt.created_at, origem: "ALTERACAO", tipo_evento: $alt.tipo_evento, entidade: $alt.entidade, registro_id: $alt.registro_id, usuario_id: $alt.usuario_id, usuario: (($alt.usuario_id == null) ? "Sistema" : (($quem == null) ? "—" : $quem.nome)), valor_anterior: $alt.valor_anterior, valor_novo: $alt.valor_novo, justificativa: $alt.justificativa}
            }
          }
        }
      }
    }

    // 2. Chamadas da fila médica.
    conditional {
      if ($origem == "" || $origem == "CHAMADA") {
        db.query chamada {
          where = $db.chamada.created_at >= $de && $db.chamada.created_at < $ate
          return = {type: "list"}
        } as $chamadas
        db.query medico {
          return = {type: "list"}
        } as $medicos
        foreach ($chamadas) {
          each as $ch {
            var $med { value = $medicos|find:($$.id == $ch.medico_id) }
            var $quem_ch { value = ($med == null) ? null : ($usuarios|find:($$.id == $med.usuario_id)) }
            var.update $eventos {
              value = $eventos|push:{em: $ch.created_at, origem: "CHAMADA", tipo_evento: $ch.tipo, entidade: "FICHA", registro_id: $ch.ficha_id, usuario_id: (($quem_ch == null) ? null : $quem_ch.id), usuario: (($quem_ch == null) ? "—" : $quem_ch.nome), valor_anterior: null, valor_novo: {tentativa: $ch.tentativa, oportunidade: $ch.oportunidade}, justificativa: null}
            }
          }
        }
      }
    }

    // 3. Entradas e saídas do sistema.
    conditional {
      if ($origem == "" || $origem == "SESSAO") {
        db.query sessao {
          where = $db.sessao.login_em >= $de && $db.sessao.login_em < $ate
          return = {type: "list"}
        } as $logins
        foreach ($logins) {
          each as $s {
            var $quem_s { value = $usuarios|find:($$.id == $s.usuario_id) }
            var.update $eventos {
              value = $eventos|push:{em: $s.login_em, origem: "SESSAO", tipo_evento: "LOGIN", entidade: "SESSAO", registro_id: $s.id, usuario_id: $s.usuario_id, usuario: (($quem_s == null) ? "—" : $quem_s.nome), valor_anterior: null, valor_novo: null, justificativa: null}
            }
          }
        }
        db.query sessao {
          where = $db.sessao.logout_em != null && $db.sessao.logout_em >= $de && $db.sessao.logout_em < $ate
          return = {type: "list"}
        } as $logouts
        foreach ($logouts) {
          each as $so {
            var $quem_so { value = $usuarios|find:($$.id == $so.usuario_id) }
            var.update $eventos {
              value = $eventos|push:{em: $so.logout_em, origem: "SESSAO", tipo_evento: "LOGOUT", entidade: "SESSAO", registro_id: $so.id, usuario_id: $so.usuario_id, usuario: (($quem_so == null) ? "—" : $quem_so.nome), valor_anterior: null, valor_novo: null, justificativa: null}
            }
          }
        }
      }
    }

    var $filtrados { value = ($input.usuario_id == null || $input.usuario_id == 0) ? $eventos : ($eventos|filter:($$.usuario_id == $input.usuario_id)) }
    var $ordenados { value = $filtrados|sort:"em":"number":false }
    var $total { value = $ordenados|count }
    var $pagina_itens { value = $ordenados|slice:(($pagina - 1) * 50):50 }
  }

  response = {itens: $pagina_itens, total: $total, pagina: $pagina, por_pagina: 50, de: $dia_inicio, ate: $dia_fim}
}

// Plantões que tocam um dia (America/Sao_Paulo), com médico, sala e especialidades (add-cadastros-administrador, D6).
query disponibilidade verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    // AAAA-MM-DD; vazio = hoje.
    text? data? filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    var $dia { value = (($input.data ?? "") == "") ? (now|format_timestamp:"Y-m-d":"America/Sao_Paulo") : $input.data }

    function.run "cadastros/periodo_plantao" {
      input = {data: $dia, hora_inicio: "00:00", hora_fim: "00:00"}
    } as $janela

    precondition ($janela.valido) {
      error_type = "inputerror"
      error = "Data inválida."
    }

    db.query disponibilidade_medico {
      where = $db.disponibilidade_medico.inicio < $janela.fim && $db.disponibilidade_medico.fim > $janela.inicio
      sort = {inicio: "asc"}
      return = {type: "list"}
    } as $periodos

    db.query medico {
      return = {type: "list"}
    } as $medicos

    var $usuario_ids { value = $medicos|map:$$.usuario_id }

    db.query usuario {
      where = $db.usuario.id in $usuario_ids
      return = {type: "list"}
    } as $usuarios

    db.query sala {
      return = {type: "list"}
    } as $salas

    db.query medico_especialidade {
      return = {type: "list"}
    } as $vinculos

    db.query especialidade {
      return = {type: "list"}
    } as $especialidades

    var $agora { value = now }
    var $lista { value = [] }
    foreach ($periodos) {
      each as $periodo {
        var $medico { value = $medicos|find:($$.id == $periodo.medico_id) }
        var $login { value = ($medico == null) ? null : ($usuarios|find:($$.id == $medico.usuario_id)) }
        var $sala { value = ($medico == null || $medico.sala_id == null) ? null : ($salas|find:($$.id == $medico.sala_id)) }
        var $ids_esp { value = ($vinculos|filter:($$.medico_id == $periodo.medico_id))|map:$$.especialidade_id }
        var $siglas { value = [] }
        foreach ($ids_esp) {
          each as $id_esp {
            var $esp { value = $especialidades|find:($$.id == $id_esp) }
            var.update $siglas { value = $siglas|push:(($esp == null) ? "?" : $esp.sigla) }
          }
        }
        var $nome { value = ($login == null) ? "" : $login.nome }
        var $nome_sala { value = ($sala == null) ? null : $sala.nome }
        var $iniciado { value = $periodo.inicio <= $agora }
        var $em_andamento { value = $periodo.inicio <= $agora && $periodo.fim > $agora && $periodo.encerrado_em == null }
        var.update $lista {
          value = $lista|push:{id: $periodo.id, medico_id: $periodo.medico_id, medico: $nome, sala: $nome_sala, especialidades: $siglas, inicio: $periodo.inicio, fim: $periodo.fim, encerrado_em: $periodo.encerrado_em, iniciado: $iniciado, em_andamento: $em_andamento}
        }
      }
    }
  }

  response = {data: $dia, agora: $agora, plantoes: $lista}
  guid = "KaAGy7uzUynjZsgtCb__4VM9kf0"
}

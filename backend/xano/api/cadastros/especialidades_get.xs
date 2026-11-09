// Lista especialidades; somente o Administrador consulta inativas e os dados de manutenção.
query especialidades verb=GET {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    // Ausente: todas para o Administrador; somente ativas para os demais perfis.
    bool? ativo?
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $auth.id
        perfis_permitidos: ["RECEPCAO_TRIAGEM", "MEDICO", "ADMINISTRADOR"]
      }
    } as $usuario
  
    precondition ($usuario.perfil == "ADMINISTRADOR" || $input.ativo != false) {
      error_type = "accessdenied"
      error = "Acesso negado para consultar especialidades inativas."
    }
  
    db.query especialidade {
      where = ($usuario.perfil == "ADMINISTRADOR" || $db.especialidade.ativo) && ($input.ativo == null || $db.especialidade.ativo == $input.ativo)
      sort = {nome: "asc"}
      return = {type: "list"}
    } as $especialidades
  
    var $resultado {
      value = $especialidades|map:{id: $$.id, nome: $$.nome, sigla: $$.sigla}
    }
  
    conditional {
      if ($usuario.perfil == "ADMINISTRADOR") {
        var.update $resultado {
          value = $especialidades|map:{id: $$.id, nome: $$.nome, sigla: $$.sigla, descricao: $$.descricao, ativo: $$.ativo}
        }
      }
    }
  }

  response = $resultado
  guid = "kJ3qOOeV9KaDfyN82md7at0wOec"
}
// PREPARAÇÃO LOCAL — NÃO PUBLICAR antes da migração aprovada de especialidade.
// Dependência obrigatória: nome_normalizado textual, obrigatório/não nulo,
// calculado pelo servidor com lower(trim(nome)), com índice único não diferido.
// Preservar também o índice único de sigla. Ver design.md, Fatia 1B.
query especialidades verb=POST {
  api_group = "Cadastros"
  auth = "usuario"

  input {
    text nome filters=trim
    text sigla filters=trim
    text descricao? filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $auth.id
        perfis_permitidos: ["ADMINISTRADOR"]
      }
    } as $usuario
  
    precondition (($input.nome|strlen) > 0) {
      error_type = "inputerror"
      error = "Informe o nome da especialidade."
    }
  
    var $sigla {
      value = $input.sigla|to_upper
    }
  
    precondition (("/^\\p{L}{3}$/u"|regex_matches:$input.sigla) && ("/^\\p{L}{3}$/u"|regex_matches:$sigla)) {
      error_type = "inputerror"
      error = "A sigla deve ter exatamente 3 letras."
    }
  
    var $nome_normalizado {
      value = $input.nome|to_lower
    }
  
    var $nome_duplicado {
      value = false
    }
  
    var $sigla_duplicada {
      value = false
    }
  
    var $consulta_ok {
      value = false
    }
  
    try_catch {
      try {
        db.query especialidade {
          where = $db.especialidade.nome_normalizado == $nome_normalizado
          return = {type: "exists"}
        } as $nome_duplicado
      
        db.query especialidade {
          where = $db.especialidade.sigla == $sigla
          return = {type: "exists"}
        } as $sigla_duplicada
      
        var.update $consulta_ok {
          value = true
        }
      }
    
      catch {
        // Nunca devolver SQL, exceção interna ou valores privados.
      }
    }
  
    precondition ($consulta_ok) {
      error = "Não foi possível cadastrar a especialidade."
    }
  
    precondition ($nome_duplicado == false) {
      error_type = "inputerror"
      error = "Já existe especialidade com este nome."
    }
  
    precondition ($sigla_duplicada == false) {
      error_type = "inputerror"
      error = "Já existe especialidade com esta sigla."
    }
  
    var $resultado {
      value = null
    }
  
    var $concluiu {
      value = false
    }
  
    var $inseriu {
      value = false
    }
  
    try_catch {
      try {
        db.transaction {
          stack {
            db.add especialidade {
              data = {
                nome            : $input.nome
                nome_normalizado: $nome_normalizado
                sigla           : $sigla
                descricao       : $input.descricao
                ativo           : true
              }
            } as $especialidade
          
            var.update $inseriu {
              value = true
            }
          
            function.run registrar_alteracao {
              input = {
                usuario_id    : $auth.id
                tipo_evento   : "CADASTRO"
                entidade      : "especialidade"
                registro_id   : $especialidade.id
                valor_anterior: null
                valor_novo    : {
                id              : $especialidade.id
                nome            : $especialidade.nome
                nome_normalizado: $especialidade.nome_normalizado
                sigla           : $especialidade.sigla
                descricao       : $especialidade.descricao
                ativo           : $especialidade.ativo
              }
                justificativa : null
              }
            } as $auditoria
          
            var.update $resultado {
              value = {
                id       : $especialidade.id
                nome     : $especialidade.nome
                sigla    : $especialidade.sigla
                descricao: $especialidade.descricao
                ativo    : $especialidade.ativo
              }
            }
          }
        }
      
        var.update $concluiu {
          value = true
        }
      }
    
      catch {
        // Se o INSERT falhou, procurar conflito confirmado após rollback.
        // A consulta não é a proteção concorrente; os índices são obrigatórios.
        conditional {
          if ($inseriu == false) {
            try_catch {
              try {
                db.query especialidade {
                  where = $db.especialidade.nome_normalizado == $nome_normalizado
                  return = {type: "exists"}
                } as $nome_duplicado
              
                db.query especialidade {
                  where = $db.especialidade.sigla == $sigla
                  return = {type: "exists"}
                } as $sigla_duplicada
              }
            
              catch {
                var.update $nome_duplicado {
                  value = false
                }
              
                var.update $sigla_duplicada {
                  value = false
                }
              }
            }
          }
        }
      }
    }
  
    precondition ($nome_duplicado == false) {
      error_type = "inputerror"
      error = "Já existe especialidade com este nome."
    }
  
    precondition ($sigla_duplicada == false) {
      error_type = "inputerror"
      error = "Já existe especialidade com esta sigla."
    }
  
    precondition ($concluiu) {
      error = "Não foi possível cadastrar a especialidade."
    }
  }

  response = $resultado
  guid = "y485oGMtHUqa14tX3CP59DncrQs"
}
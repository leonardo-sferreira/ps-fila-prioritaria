// Carga idempotente do direcionamento (add-direcionamento-senha, D1): especialidades com sigla de senha,
// ligação de cada sintoma do catálogo de docs/domain-model.md à sua especialidade e ESPECIALIDADE_PADRAO.
// Ligações só são inseridas com a tabela vazia, para não sobrescrever ajustes futuros do Administrador.
function "direcionamento/inicializar_direcionamento" {
  description = "Cria especialidades (CAR, CLI, NEU, ORT, PED), ligações sintoma → especialidade e o parâmetro ESPECIALIDADE_PADRAO, se ainda não existirem."
  input {}
  stack {
    foreach ([{sigla: "CAR", nome: "Cardiologia"}, {sigla: "CLI", nome: "Clínica Geral"}, {sigla: "NEU", nome: "Neurologia"}, {sigla: "ORT", nome: "Ortopedia"}, {sigla: "PED", nome: "Pediatria"}]) {
      each as $padrao {
        db.get especialidade {
          field_name = "sigla"
          field_value = $padrao.sigla
        } as $existente
        conditional {
          if ($existente == null) {
            db.add especialidade {
              // nome_normalizado é obrigatório desde a migração de especialidade dos cadastros: lower(trim(nome)).
              data = {nome: $padrao.nome, nome_normalizado: $padrao.nome|to_lower, sigla: $padrao.sigla, ativo: true}
            } as $criada
          }
        }
      }
    }

    db.query especialidade {
      return = {type: "list"}
    } as $especialidades

    db.query sintoma_especialidade {
      return = {type: "count"}
    } as $ligacoes_existentes

    conditional {
      if ($ligacoes_existentes == 0) {
        var $ligacoes {
          value = [
            {sintoma: "Dor ou pressão no peito", sigla: "CAR"}
            {sintoma: "Palpitações", sigla: "CAR"}
            {sintoma: "Desmaio / síncope", sigla: "CAR"}
            {sintoma: "Inchaço nas pernas associado a falta de ar", sigla: "CAR"}
            {sintoma: "Falta de ar", sigla: "CLI"}
            {sintoma: "Falta de ar intensa / dificuldade grave para respirar", sigla: "CLI"}
            {sintoma: "Chiado no peito", sigla: "CLI"}
            {sintoma: "Dor ao respirar", sigla: "CLI"}
            {sintoma: "Tosse com sangue", sigla: "CLI"}
            {sintoma: "Tosse sem falta de ar", sigla: "CLI"}
            {sintoma: "Convulsão em atividade", sigla: "NEU"}
            {sintoma: "Convulsão já cessada / período pós-crise", sigla: "NEU"}
            {sintoma: "Alteração súbita da fala", sigla: "NEU"}
            {sintoma: "Fraqueza ou paralisia de um lado do corpo", sigla: "NEU"}
            {sintoma: "Perda súbita de visão", sigla: "NEU"}
            {sintoma: "Perda súbita de equilíbrio ou coordenação", sigla: "NEU"}
            {sintoma: "Confusão mental aguda", sigla: "NEU"}
            {sintoma: "Dor de cabeça súbita e muito intensa", sigla: "NEU"}
            {sintoma: "Tontura / vertigem", sigla: "NEU"}
            {sintoma: "Dor de cabeça leve ou habitual", sigla: "NEU"}
            {sintoma: "Vômito com sangue", sigla: "CLI"}
            {sintoma: "Sangue nas fezes / fezes muito escuras", sigla: "CLI"}
            {sintoma: "Dor abdominal intensa", sigla: "CLI"}
            {sintoma: "Vômitos persistentes", sigla: "CLI"}
            {sintoma: "Dor abdominal leve", sigla: "CLI"}
            {sintoma: "Náusea", sigla: "CLI"}
            {sintoma: "Diarreia sem sinais de desidratação", sigla: "CLI"}
            {sintoma: "Constipação / cólica leve", sigla: "CLI"}
            {sintoma: "Politrauma / trauma de grande impacto", sigla: "ORT"}
            {sintoma: "Fratura exposta", sigla: "ORT"}
            {sintoma: "Suspeita de fratura fechada", sigla: "ORT"}
            {sintoma: "Trauma na cabeça com alteração neurológica", sigla: "NEU"}
            {sintoma: "Trauma na cabeça sem alteração neurológica", sigla: "NEU"}
            {sintoma: "Corte profundo / sangramento importante", sigla: "ORT"}
            {sintoma: "Corte superficial", sigla: "ORT"}
            {sintoma: "Torção / entorse", sigla: "ORT"}
            {sintoma: "Dor em membro após trauma", sigla: "ORT"}
            {sintoma: "Dor em membro sem trauma importante", sigla: "ORT"}
            {sintoma: "Queda sem sinais de gravidade", sigla: "ORT"}
            {sintoma: "Reação alérgica com dificuldade respiratória", sigla: "CLI"}
            {sintoma: "Reação alérgica sem dificuldade respiratória", sigla: "CLI"}
            {sintoma: "Febre", sigla: "CLI"}
            {sintoma: "Dor intensa sem localização específica", sigla: "CLI"}
            {sintoma: "Dor leve sem localização específica", sigla: "CLI"}
            {sintoma: "Mal-estar", sigla: "CLI"}
            {sintoma: "Fraqueza generalizada", sigla: "CLI"}
          ]
        }
        foreach ($ligacoes) {
          each as $ligacao {
            db.get sintoma {
              field_name = "nome"
              field_value = $ligacao.sintoma
            } as $sintoma
            var $especialidade {
              value = $especialidades|find:($$.sigla == $ligacao.sigla)
            }
            conditional {
              if ($sintoma != null && $especialidade != null) {
                db.add sintoma_especialidade {
                  data = {sintoma_id: $sintoma.id, especialidade_id: $especialidade.id, ordem: 1}
                } as $ligacao_criada
              }
            }
          }
        }
      }
    }

    db.get parametro {
      field_name = "chave"
      field_value = "ESPECIALIDADE_PADRAO"
    } as $padrao_existente

    conditional {
      if ($padrao_existente == null) {
        var $clinica_geral {
          value = $especialidades|find:($$.sigla == "CLI")
        }
        conditional {
          if ($clinica_geral != null) {
            db.add parametro {
              data = {chave: "ESPECIALIDADE_PADRAO", valor: $clinica_geral.id|to_text, tipo: "ESPECIALIDADE"}
            } as $padrao_criado
          }
        }
      }
    }

    db.query sintoma_especialidade {
      return = {type: "count"}
    } as $total_ligacoes
  }
  response = {especialidades: $especialidades|count, ligacoes: $total_ligacoes}
  guid = "FWlfq8bCA1OFdNh2WBL4cwg-z9Q"
}

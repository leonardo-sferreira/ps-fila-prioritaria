// Carga idempotente do catálogo acadêmico existente em docs/domain-model.md.
function "sintomas/carregar_catalogo_inicial" {
  description = "Insere ou atualiza o catálogo oficial de sintomas sem duplicar registros. Não calcula classificação."

  input {
  }

  stack {
    var $catalogo {
      value = [
        {nome: "Dor ou pressão no peito", grupo: "CARDIOVASCULAR", pontuacao: 2},
        {nome: "Palpitações", grupo: "CARDIOVASCULAR", pontuacao: 2},
        {nome: "Desmaio / síncope", grupo: "CARDIOVASCULAR", pontuacao: 2},
        {nome: "Inchaço nas pernas associado a falta de ar", grupo: "CARDIOVASCULAR", pontuacao: 2},
        {nome: "Falta de ar", grupo: "RESPIRATORIO", pontuacao: 2},
        {nome: "Falta de ar intensa / dificuldade grave para respirar", grupo: "RESPIRATORIO", pontuacao: 3},
        {nome: "Chiado no peito", grupo: "RESPIRATORIO", pontuacao: 2},
        {nome: "Dor ao respirar", grupo: "RESPIRATORIO", pontuacao: 2},
        {nome: "Tosse com sangue", grupo: "RESPIRATORIO", pontuacao: 2},
        {nome: "Tosse sem falta de ar", grupo: "RESPIRATORIO", pontuacao: 1},
        {nome: "Convulsão em atividade", grupo: "NEUROLOGICO", pontuacao: 3},
        {nome: "Convulsão já cessada / período pós-crise", grupo: "NEUROLOGICO", pontuacao: 2},
        {nome: "Alteração súbita da fala", grupo: "NEUROLOGICO", pontuacao: 3},
        {nome: "Fraqueza ou paralisia de um lado do corpo", grupo: "NEUROLOGICO", pontuacao: 3},
        {nome: "Perda súbita de visão", grupo: "NEUROLOGICO", pontuacao: 3},
        {nome: "Perda súbita de equilíbrio ou coordenação", grupo: "NEUROLOGICO", pontuacao: 3},
        {nome: "Confusão mental aguda", grupo: "NEUROLOGICO", pontuacao: 2},
        {nome: "Dor de cabeça súbita e muito intensa", grupo: "NEUROLOGICO", pontuacao: 2},
        {nome: "Tontura / vertigem", grupo: "NEUROLOGICO", pontuacao: 2},
        {nome: "Dor de cabeça leve ou habitual", grupo: "NEUROLOGICO", pontuacao: 1},
        {nome: "Vômito com sangue", grupo: "GASTROINTESTINAL", pontuacao: 3},
        {nome: "Sangue nas fezes / fezes muito escuras", grupo: "GASTROINTESTINAL", pontuacao: 2},
        {nome: "Dor abdominal intensa", grupo: "GASTROINTESTINAL", pontuacao: 2},
        {nome: "Vômitos persistentes", grupo: "GASTROINTESTINAL", pontuacao: 2},
        {nome: "Dor abdominal leve", grupo: "GASTROINTESTINAL", pontuacao: 1},
        {nome: "Náusea", grupo: "GASTROINTESTINAL", pontuacao: 1},
        {nome: "Diarreia sem sinais de desidratação", grupo: "GASTROINTESTINAL", pontuacao: 1},
        {nome: "Constipação / cólica leve", grupo: "GASTROINTESTINAL", pontuacao: 1},
        {nome: "Politrauma / trauma de grande impacto", grupo: "TRAUMATICO_ORTOPEDICO", pontuacao: 3},
        {nome: "Fratura exposta", grupo: "TRAUMATICO_ORTOPEDICO", pontuacao: 3},
        {nome: "Suspeita de fratura fechada", grupo: "TRAUMATICO_ORTOPEDICO", pontuacao: 2},
        {nome: "Trauma na cabeça com alteração neurológica", grupo: "TRAUMATICO_NEUROLOGICO", pontuacao: 3},
        {nome: "Trauma na cabeça sem alteração neurológica", grupo: "TRAUMATICO_NEUROLOGICO", pontuacao: 2},
        {nome: "Corte profundo / sangramento importante", grupo: "TRAUMATICO_ORTOPEDICO", pontuacao: 2},
        {nome: "Corte superficial", grupo: "TRAUMATICO_ORTOPEDICO", pontuacao: 1},
        {nome: "Torção / entorse", grupo: "TRAUMATICO_ORTOPEDICO", pontuacao: 1},
        {nome: "Dor em membro após trauma", grupo: "TRAUMATICO_ORTOPEDICO", pontuacao: 2},
        {nome: "Dor em membro sem trauma importante", grupo: "TRAUMATICO_ORTOPEDICO", pontuacao: 1},
        {nome: "Queda sem sinais de gravidade", grupo: "TRAUMATICO_ORTOPEDICO", pontuacao: 1},
        {nome: "Reação alérgica com dificuldade respiratória", grupo: "GERAL", pontuacao: 3},
        {nome: "Reação alérgica sem dificuldade respiratória", grupo: "GERAL", pontuacao: 2},
        {nome: "Febre", grupo: "GERAL", pontuacao: 1},
        {nome: "Dor intensa sem localização específica", grupo: "GERAL", pontuacao: 2},
        {nome: "Dor leve sem localização específica", grupo: "GERAL", pontuacao: 1},
        {nome: "Mal-estar", grupo: "GERAL", pontuacao: 1},
        {nome: "Fraqueza generalizada", grupo: "GERAL", pontuacao: 1}
      ]
    }

    db.transaction {
      stack {
        foreach ($catalogo) {
          each as $item {
            db.get "sintoma" {
              field_name = "nome"
              field_value = $item.nome
            } as $sintoma_existente

            conditional {
              if ($sintoma_existente == null) {
                db.add "sintoma" {
                  data = {
                    nome: $item.nome,
                    grupo: $item.grupo,
                    pontuacao: $item.pontuacao,
                    ativo: true
                  }
                } as $sintoma_criado
              }
              else {
                db.patch "sintoma" {
                  field_name = "id"
                  field_value = $sintoma_existente.id
                  data = {
                    grupo: $item.grupo,
                    pontuacao: $item.pontuacao,
                    ativo: true
                  }
                } as $sintoma_atualizado
              }
            }
          }
        }
      }
    }
  }

  response = { carregados: ($catalogo|count) }

  test "catalogo oficial contém 46 sintomas" {
    input = {}
    expect.to_equal ($response.carregados) { value = 46 }
  }
  guid = "GDW7MKLUF2zaAohf0KlkBDhKMq4"
}

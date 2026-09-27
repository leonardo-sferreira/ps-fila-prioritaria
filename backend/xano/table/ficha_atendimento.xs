// Passagem do paciente pelo PS, da triagem até o comparecimento, a desistência ou o cancelamento.
table ficha_atendimento {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int paciente_id {
      table = "paciente"
    }
    int? ticket_id? {
      table = "ticket_pre_triagem"
    }
    int aberta_por {
      table = "usuario"
    }
    timestamp chegada_em
    enum status {
      values = ["EM_TRIAGEM", "AGUARDANDO", "CHAMADO", "ATENDIDO", "DESISTENCIA", "CANCELADO"]
    }
    text? observacao?
    bool gestante?=false
    int? pa_sistolica?
    int? fc?
    int? fr?
    decimal? temperatura?
    int? spo2?
    int? glicemia?
    bool glicemia_sinais_gravidade?=false
    int? escore_risco?
    bool parametro_critico?=false
    enum? classificacao_risco? {
      values = ["BAIXO", "MODERADO", "ALTO"]
    }
    enum? prioridade_calculada? {
      values = ["VERMELHA", "AMARELA", "AZUL"]
    }
    enum? prioridade_atual? {
      values = ["VERMELHA", "AMARELA", "AZUL"]
    }
    text? justificativa_ajuste?
    enum condicao_prioritaria?=NENHUMA {
      values = ["NENHUMA", "IDOSO", "CRIANCA", "GESTANTE"]
    }
    int? especialidade_sugerida_id? {
      table = "especialidade"
    }
    int? especialidade_atribuida_id? {
      table = "especialidade"
    }
    text? senha?
    int? senha_numero?
    bool sem_medico_no_direcionamento?=false
    int? medico_chamada_id? {
      table = "medico"
    }
    int tentativas_chamada?=0
    timestamp? chamada_em?
    timestamp? finalizada_em?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "paciente_id", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}, {name: "especialidade_atribuida_id", op: "asc"}, {name: "chegada_em", op: "asc"}]}
    {type: "btree", field: [{name: "medico_chamada_id", op: "asc"}, {name: "status", op: "asc"}]}
  ]
  guid = "F1t2vdYqDe0nBfmsSHzHL_gCSwY"
}

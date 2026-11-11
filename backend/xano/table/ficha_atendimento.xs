table ficha_atendimento {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    // ID do paciente associado à ficha de atendimento.
    int paciente_id? {
      table = "paciente"
    }

    // ID do ticket de pré-triagem associado.
    int ticket_id? {
      table = "ticket_pre_triagem"
    }

    // ID do usuário que abriu a ficha.
    int aberta_por? {
      table = "usuario"
    }

    // Data e hora da chegada.
    timestamp chegada_em?

    // Status atual da ficha de atendimento.
    enum status? {
      values = [
        "EM_TRIAGEM"
        "AGUARDANDO"
        "CHAMADO"
        "ATENDIDO"
        "DESISTENCIA"
        "CANCELADO"
      ]

    }

    // Observações adicionais para a ficha.
    text observacao? filters=trim

    // Indica se a paciente é gestante.
    bool gestante?

    // Pressão arterial sistólica.
    int pa_sistolica?

    // Frequência cardíaca.
    int fc?

    // Frequência respiratória.
    int fr?

    // Temperatura corporal.
    decimal temperatura?

    // Saturação de oxigênio.
    int spo2?

    // Nível de glicemia.
    int glicemia?

    // Indica sinais de gravidade relacionados à glicemia.
    bool glicemia_sinais_gravidade?

    // Escore de risco calculado.
    int escore_risco?

    // Indica se há algum parâmetro crítico.
    bool parametro_critico?

    // Classificação de risco da ficha.
    enum classificacao_risco? {
      values = ["BAIXO", "MODERADO", "ALTO"]
    }

    // Prioridade calculada automaticamente.
    enum prioridade_calculada? {
      values = ["VERMELHA", "AMARELA", "AZUL"]
    }

    // Prioridade atual atribuída.
    enum prioridade_atual? {
      values = ["VERMELHA", "AMARELA", "AZUL"]
    }

    // Justificativa para ajuste de prioridade.
    text justificativa_ajuste? filters=trim

    // Condição prioritária do paciente.
    enum condicao_prioritaria?=NENHUMA {
      values = ["NENHUMA", "IDOSO", "CRIANCA", "GESTANTE"]
    }

    // ID da especialidade sugerida para atendimento.
    int especialidade_sugerida_id? {
      table = "especialidade"
    }

    // ID da especialidade atribuída para atendimento.
    int especialidade_atribuida_id? {
      table = "especialidade"
    }

    // Senha de atendimento.
    text senha? filters=trim

    // Número da senha de atendimento.
    int senha_numero?

    // Indica se não há médico disponível para direcionamento.
    bool sem_medico_no_direcionamento?

    // ID do médico responsável pela chamada.
    int medico_chamada_id? {
      table = "medico"
    }

    // Número de tentativas de chamada.
    int tentativas_chamada?

    int oportunidade?=1
    timestamp? fila_em?

    // Data e hora da chamada.
    timestamp chamada_em?

    // Data e hora de finalização da ficha.
    timestamp finalizada_em?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "paciente_id", op: "asc"}]}
    {
      type : "btree"
      field: [
        {name: "status", op: "asc"}
        {name: "especialidade_atribuida_id", op: "asc"}
        {name: "chegada_em", op: "asc"}
      ]
    }
    {
      type : "btree"
      field: [
        {name: "medico_chamada_id", op: "asc"}
        {name: "status", op: "asc"}
      ]
    }
  ]

  guid = "F1t2vdYqDe0nBfmsSHzHL_gCSwY"
}

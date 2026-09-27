# Delta de especificação

## Purpose

Registra cada passagem do paciente pelo PS, com a queixa, os sintomas e os sinais vitais coletados na triagem, que servem de base para a classificação de prioridade.

## ADDED Requirements

### Requirement: Acesso à ficha por perfil
A Recepção/Triagem DEVE poder abrir, editar e cancelar fichas. O Administrador DEVE poder apenas consultá-las. O Médico NÃO DEVE acessar as operações de triagem.

#### Scenario: Médico tenta abrir ficha
- **QUANDO** um usuário Médico tenta abrir ou alterar uma ficha
- **ENTÃO** o backend responde como acesso negado e nada é alterado

#### Scenario: Administrador consulta ficha
- **QUANDO** um usuário Administrador consulta uma ficha
- **ENTÃO** o sistema retorna os dados sem permitir alteração

### Requirement: Abertura de ficha
O sistema DEVE abrir uma nova ficha para um paciente ativo, registrando o usuário que abriu, o ticket de origem (quando houver) e o horário de chegada, com status EM_TRIAGEM. Cada chegada gera uma nova ficha (RN03). Um paciente NÃO DEVE ter mais de uma ficha não finalizada (EM_TRIAGEM, AGUARDANDO ou CHAMADO).

#### Scenario: Abertura a partir do ticket
- **QUANDO** a Recepção/Triagem identifica o paciente do ticket chamado e aciona "Abrir ficha"
- **ENTÃO** a ficha é criada em EM_TRIAGEM, com horário de chegada igual ao horário de emissão do ticket

#### Scenario: Abertura sem ticket
- **QUANDO** a Recepção/Triagem abre uma ficha sem ticket de origem
- **ENTÃO** o horário de chegada é o horário da abertura

#### Scenario: Paciente com ficha em andamento
- **QUANDO** a Recepção/Triagem tenta abrir uma ficha para um paciente que já tem ficha AGUARDANDO
- **ENTÃO** o sistema recusa, informa a senha ou a ficha existente e não cria outra

#### Scenario: Retorno após desistência
- **QUANDO** um paciente cuja última ficha está em DESISTÊNCIA volta ao PS
- **ENTÃO** uma nova ficha é aberta com novo horário de chegada, sem recuperar a posição anterior (RN30)

### Requirement: Sintomas e observações da queixa
A ficha DEVE aceitar um ou mais sintomas ativos, sem repetição, e uma observação de texto livre de até 500 caracteres. Para concluir a triagem, a ficha DEVE ter ao menos um sintoma ou uma observação não vazia (RN04). Sintomas e observação DEVEM poder ser alterados enquanto a ficha estiver em EM_TRIAGEM ou AGUARDANDO (RF11), e a alteração DEVE ser auditada.

#### Scenario: Sintomas registrados
- **QUANDO** a Recepção/Triagem seleciona "Febre" e "Tosse"
- **ENTÃO** a ficha passa a ter os dois sintomas

#### Scenario: Sintoma inativo
- **QUANDO** a Recepção/Triagem tenta incluir um sintoma inativo
- **ENTÃO** o sistema recusa a inclusão

#### Scenario: Ficha sem queixa
- **QUANDO** a Recepção/Triagem tenta concluir a triagem sem sintomas e sem observação
- **ENTÃO** o sistema recusa com a mensagem "Informe ao menos um sintoma ou a queixa"

#### Scenario: Alteração auditada
- **QUANDO** a Recepção/Triagem troca os sintomas de uma ficha AGUARDANDO
- **ENTÃO** a auditoria registra a lista anterior, a nova lista, o usuário e a data/hora

#### Scenario: Ficha finalizada não é alterada
- **QUANDO** alguém tenta alterar os sintomas de uma ficha ATENDIDO, DESISTÊNCIA ou CANCELADO
- **ENTÃO** o sistema recusa a alteração

### Requirement: Sinais vitais
A ficha DEVE registrar PA sistólica (mmHg), FC (bpm), FR (irpm), temperatura (°C, uma casa decimal) e SpO2 (%), obrigatórios para concluir a triagem, e glicemia capilar (mg/dL) opcional, com o indicador "sinais de gravidade" (alteração de consciência, sinais de cetoacidose ou sintomas de hipoglicemia). Valores fora das faixas plausíveis DEVEM ser recusados: PA sistólica 40–300, FC 20–250, FR 4–80, temperatura 30,0–45,0, SpO2 50–100, glicemia 10–1000. A alteração de sinais vitais DEVE ser auditada.

#### Scenario: Sinais vitais válidos
- **QUANDO** a Recepção/Triagem informa PA 120, FC 80, FR 16, temperatura 36,8 e SpO2 98
- **ENTÃO** os valores são gravados na ficha

#### Scenario: Valor implausível
- **QUANDO** a Recepção/Triagem informa SpO2 101 ou FC 19
- **ENTÃO** o sistema recusa e indica o campo e a faixa aceita

#### Scenario: Sinal obrigatório ausente
- **QUANDO** a Recepção/Triagem tenta concluir a triagem sem a FR
- **ENTÃO** o sistema recusa e indica o campo faltante

#### Scenario: Glicemia não medida
- **QUANDO** a triagem é concluída sem glicemia
- **ENTÃO** a ficha é aceita e a glicemia não pontua no escore

### Requirement: Gestação
A Recepção/Triagem DEVE poder marcar a ficha como gestante (RF09). A marcação e a desmarcação DEVEM ser auditadas.

#### Scenario: Marcar gestante
- **QUANDO** a Recepção/Triagem marca a ficha como gestante
- **ENTÃO** a ficha passa a ter condição prioritária

### Requirement: Cancelamento de ficha
A Recepção/Triagem DEVE poder cancelar uma ficha em EM_TRIAGEM ou AGUARDANDO, informando justificativa de ao menos 10 caracteres. A ficha passa a CANCELADO, sai da fila ativa e o cancelamento é auditado.

#### Scenario: Cancelamento com justificativa
- **QUANDO** a Recepção/Triagem cancela uma ficha AGUARDANDO com a justificativa "Paciente foi embora antes da chamada"
- **ENTÃO** a ficha passa a CANCELADO e a auditoria registra a justificativa

#### Scenario: Cancelamento sem justificativa
- **QUANDO** a justificativa está vazia ou tem menos de 10 caracteres
- **ENTÃO** o sistema recusa o cancelamento

#### Scenario: Ficha já chamada
- **QUANDO** a Recepção/Triagem tenta cancelar uma ficha CHAMADO
- **ENTÃO** o sistema recusa e informa que a ficha está com o médico

# Delta de especificação

## Purpose

Organiza a fila de tickets impessoais emitidos pelo Totem, permitindo à Recepção/Triagem chamá-los antes da triagem clínica, sem prioridade clínica.

## ADDED Requirements

### Requirement: Consumir tickets emitidos pelo Totem
A fila DEVE receber os tickets impessoais criados pela change `add-totem`, mantendo número, horário e identidade únicos no dia operacional em `America/Sao_Paulo`.

#### Scenario: Ticket emitido entra na fila
- **QUANDO** o Totem registra um novo ticket
- **ENTÃO** o mesmo ticket aparece como AGUARDANDO, sem novo número gerado pela fila

### Requirement: Fila pré-triagem visível à Recepção/Triagem
O sistema DEVE mostrar à Recepção/Triagem os tickets do dia com status AGUARDANDO, em ordem de emissão, e os tickets CHAMADO, com o horário de emissão. Somente os perfis Recepção/Triagem e Administrador DEVEM ter acesso a essa lista.

#### Scenario: Lista da fila
- **QUANDO** a Recepção/Triagem abre a fila pré-triagem
- **ENTÃO** vê os tickets aguardando do mais antigo para o mais recente

#### Scenario: Médico tenta ver a fila pré-triagem
- **QUANDO** um usuário Médico consulta a fila pré-triagem
- **ENTÃO** o backend responde como acesso negado

### Requirement: Chamar o próximo ticket
A Recepção/Triagem DEVE poder chamar o próximo ticket, que é sempre o AGUARDANDO mais antigo do dia. O ticket passa a CHAMADO, vinculado ao usuário que chamou. Cada usuário DEVE ter no máximo um ticket CHAMADO por vez, e dois usuários NÃO DEVEM receber o mesmo ticket.

#### Scenario: Chamada em ordem de emissão
- **QUANDO** os tickets 5, 6 e 7 estão aguardando e a Recepção/Triagem aciona "Chamar próximo"
- **ENTÃO** o ticket 5 passa a CHAMADO

#### Scenario: Duas estações ao mesmo tempo
- **QUANDO** dois usuários Recepção/Triagem acionam "Chamar próximo" ao mesmo tempo, com os tickets 5 e 6 aguardando
- **ENTÃO** um recebe o ticket 5 e o outro o ticket 6

#### Scenario: Fila vazia
- **QUANDO** não há tickets aguardando e a Recepção/Triagem aciona "Chamar próximo"
- **ENTÃO** o sistema informa "Não há pacientes aguardando a triagem"

#### Scenario: Usuário já tem ticket chamado
- **QUANDO** o usuário já tem um ticket CHAMADO e aciona "Chamar próximo"
- **ENTÃO** o sistema recusa e pede que ele conclua o ticket atual

### Requirement: Repetir chamada dentro de uma oportunidade
Para o ticket CHAMADO, a Recepção/Triagem DEVE poder repetir a chamada até 3 vezes na oportunidade atual, respeitando intervalo mínimo de 30 segundos entre chamadas da mesma senha. Repetir NÃO DEVE criar novo ticket. Somente quem chamou o ticket pode operá-lo.

#### Scenario: Intervalo mínimo
- **QUANDO** a Recepção/Triagem tenta rechamar antes de completar 30 segundos desde a chamada anterior
- **ENTÃO** o backend recusa e informa quando poderá chamar novamente, sem registrar chamada

#### Scenario: Três chamadas na primeira oportunidade
- **QUANDO** o paciente não responde após a terceira chamada da primeira oportunidade
- **ENTÃO** o mesmo ticket volta ao fim da fila com a mesma identidade e número, para uma única nova oportunidade

#### Scenario: Segunda oportunidade esgotada
- **QUANDO** o paciente não responde após até 3 chamadas da segunda oportunidade
- **ENTÃO** o ticket passa a NAO_COMPARECEU e sai definitivamente da fila ativa

#### Scenario: Rechamada não gera ticket
- **QUANDO** a Recepção/Triagem rechama um ticket já chamado
- **ENTÃO** registra outra chamada no ticket existente, sem alterar seu número ou identidade

### Requirement: Ciclo de estados do Ticket Pré-Triagem
O ciclo de estados DEVE ser `AGUARDANDO → CHAMADO`; após até 3 chamadas sem resposta na primeira oportunidade, `CHAMADO → AGUARDANDO` com oportunidade incrementada e posição no fim da fila; após até 3 chamadas sem resposta na segunda oportunidade, `CHAMADO → NAO_COMPARECEU`. Identificação faz `CHAMADO → ATENDIDO`; desistência explicitamente registrada faz `CHAMADO → DESISTENCIA`. Rechamada mantém o mesmo ticket em `CHAMADO` e não cria nova identidade. `ATENDIDO`, `NAO_COMPARECEU` e `DESISTENCIA` são estados finais.

#### Scenario: Ciclo de retorno preserva o ticket
- **QUANDO** um ticket completa três chamadas sem resposta na primeira oportunidade e é selecionado novamente
- **ENTÃO** permanece o mesmo ticket e número, a oportunidade aumenta e sua posição segue os tickets já aguardando

### Requirement: Concluir ou desistir do ticket chamado
A Recepção/Triagem DEVE poder marcar "Paciente identificado" (status ATENDIDO) ou registrar desistência explícita (status DESISTENCIA). Esses estados são finais e saem da fila ativa.

#### Scenario: Paciente identificado
- **QUANDO** a Recepção/Triagem pesquisa o CPF do paciente do ticket 5 e aciona "Paciente identificado"
- **ENTÃO** o ticket 5 passa a ATENDIDO, vinculado ao paciente, e sai da fila

#### Scenario: Desistência explícita
- **QUANDO** a Recepção/Triagem registra desistência explícita para o ticket chamado
- **ENTÃO** o ticket passa a DESISTENCIA e sai definitivamente da fila ativa

#### Scenario: Outro usuário tenta concluir
- **QUANDO** um usuário tenta concluir um ticket chamado por outro usuário
- **ENTÃO** o sistema recusa a operação

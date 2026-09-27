# Delta de especificação

## Purpose

Permite que a equipe de Recepção/Triagem e os Médicos informem seu status operacional durante o plantão, para que o Administrador saiba quem está atendendo.

## ADDED Requirements

### Requirement: Status operacional por sessão
Toda sessão de Recepção/Triagem e de Médico DEVE ter um status operacional: DISPONIVEL, EM_ATENDIMENTO, PAUSA ou AUSENTE. Ao fazer login, o status inicial DEVE ser DISPONIVEL. Sessões de Administrador NÃO DEVEM ter status operacional.

#### Scenario: Status inicial
- **QUANDO** um usuário Médico faz login
- **ENTÃO** sua sessão começa com status DISPONIVEL

### Requirement: Alteração do próprio status
O usuário Recepção/Triagem ou Médico DEVE poder mudar o próprio status para DISPONIVEL, PAUSA ou AUSENTE. O status EM_ATENDIMENTO NÃO DEVE ser escolhido manualmente. Um usuário NÃO DEVE alterar o status de outro.

#### Scenario: Pausa para almoço
- **QUANDO** um usuário Recepção/Triagem muda o status para PAUSA
- **ENTÃO** o status da sessão passa a PAUSA

#### Scenario: Tentativa de marcar Em atendimento
- **QUANDO** um usuário tenta mudar o próprio status para EM_ATENDIMENTO
- **ENTÃO** o sistema recusa a alteração

#### Scenario: Administrador sem status
- **QUANDO** um usuário Administrador tenta alterar status operacional
- **ENTÃO** o sistema recusa, porque o perfil não tem status operacional

### Requirement: Status automático do médico
O status do médico DEVE passar a EM_ATENDIMENTO quando ele confirmar o comparecimento de um paciente, e voltar a DISPONIVEL quando ele acionar "Chamar próximo" com sucesso ou escolher DISPONIVEL manualmente.

#### Scenario: Comparecimento confirmado
- **QUANDO** o médico confirma o comparecimento de uma ficha
- **ENTÃO** seu status passa a EM_ATENDIMENTO

#### Scenario: Próxima chamada
- **QUANDO** o médico em EM_ATENDIMENTO aciona "Chamar próximo" com sucesso
- **ENTÃO** seu status volta a DISPONIVEL

### Requirement: Médico em pausa ou ausente não chama pacientes
O médico com status PAUSA ou AUSENTE NÃO DEVE conseguir acionar "Chamar próximo". Repetir chamada, confirmar comparecimento e registrar desistência da ficha que ele já está chamando continuam permitidos.

#### Scenario: Chamada durante a pausa
- **QUANDO** um médico com status PAUSA aciona "Chamar próximo"
- **ENTÃO** o sistema recusa com a mensagem "Altere seu status para Disponível para chamar pacientes"

#### Scenario: Resolver a ficha pendente durante a pausa
- **QUANDO** um médico entra em PAUSA com uma ficha CHAMADO e depois confirma o comparecimento dela
- **ENTÃO** a confirmação é aceita

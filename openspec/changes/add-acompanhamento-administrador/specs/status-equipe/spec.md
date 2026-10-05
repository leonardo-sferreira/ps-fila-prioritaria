# Delta de especificação

## Purpose

Permite que a equipe de Recepção/Triagem e os Médicos informem seu status operacional durante o plantão, para que o Administrador saiba quem está atendendo.

## ADDED Requirements

### Requirement: Status operacional por sessão
Toda sessão autenticada de Recepção/Triagem e de Médico DEVE ter um status operacional: DISPONIVEL, EM_ATENDIMENTO, PAUSA ou AUSENTE. Ao fazer login, o status inicial DEVE ser DISPONIVEL. Sessões de Administrador NÃO DEVEM ter status operacional. Status operacional não determina se a sessão está autenticada: sessão ativa continua definida por `logout_em` nulo e `expira_em` futuro; PAUSA e AUSENTE não fazem logout.

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
O Médico com status PAUSA ou AUSENTE NÃO DEVE receber novas atribuições nem conseguir acionar "Chamar próximo". Fichas já sob sua responsabilidade permanecem atribuídas e podem ser resolvidas; repetir chamada, confirmar comparecimento e registrar desistência continuam permitidos.

#### Scenario: Chamada durante a pausa
- **QUANDO** um médico com status PAUSA aciona "Chamar próximo"
- **ENTÃO** o sistema recusa com a mensagem "Altere seu status para Disponível para chamar pacientes"

#### Scenario: Resolver a ficha pendente durante a pausa
- **QUANDO** um médico entra em PAUSA com uma ficha CHAMADO e depois confirma o comparecimento dela
- **ENTÃO** a confirmação é aceita

### Requirement: Encerramento do plantão condicionado à fila atribuída
O Médico DEVE poder solicitar o encerramento do plantão, mas o sistema SÓ DEVE concluir esse encerramento quando não houver nenhuma ficha ativa sob sua responsabilidade. Enquanto houver ficha atribuída não finalizada, a ação de encerramento DEVE permanecer indisponível; PAUSA não encerra o plantão.

#### Scenario: Encerramento indisponível com ficha atribuída
- **QUANDO** um Médico solicita encerrar o plantão enquanto ainda há ficha atribuída não finalizada
- **ENTÃO** o sistema mantém o plantão aberto, mantém a ficha sob sua responsabilidade e não conclui o encerramento

#### Scenario: Encerramento após zerar a fila atribuída
- **QUANDO** todas as fichas atribuídas ao Médico foram finalizadas e ele solicita encerrar o plantão
- **ENTÃO** o sistema encerra o plantão e o Médico deixa de receber novas atribuições

### Requirement: Sessão e estado operacional independentes
PAUSA, AUSENTE e plantão encerrado NÃO DEVEM encerrar ou invalidar por si sós a sessão autenticada. O usuário continua autenticado até logout explícito ou expiração conforme `add-autenticacao-perfis`.

#### Scenario: Pausa mantém sessão ativa
- **QUANDO** Médico ou Recepção/Triagem muda para PAUSA sem fazer logout
- **ENTÃO** continua na lista de sessões ativas enquanto `logout_em` for nulo e `expira_em` estiver no futuro, com status PAUSA

# status-equipe Specification

## Purpose
Permite que a equipe de Recepção/Triagem e os Médicos informem seu status operacional durante o plantão, para que o Administrador saiba quem está atendendo.

## Requirements

### Requirement: Status operacional por sessão
Toda sessão autenticada de Médico DEVE começar sem disponibilidade operacional; ele DEVE escolher DISPONIVEL explicitamente para iniciar o recebimento de atribuições. A sessão de Recepção/Triagem começa DISPONIVEL. Depois a equipe pode ter status DISPONIVEL, EM_ATENDIMENTO, PAUSA ou AUSENTE. Sessões de Administrador NÃO DEVEM ter status operacional. Status operacional não determina se a sessão está autenticada: sessão ativa continua definida por `logout_em` nulo e `expira_em` futuro; PAUSA e AUSENTE não fazem logout.

#### Scenario: Status inicial
- **QUANDO** um usuário Médico faz login ou entra novamente após perder acesso à sessão anterior
- **ENTÃO** sua nova sessão começa indisponível e não recebe novas atribuições até ele escolher DISPONIVEL

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

### Requirement: Consulta do próprio status sem efeitos colaterais
O GET me/status DEVE permitir somente a Médico ou Recepção/Triagem ativos consultar o status da própria sessão ativa mais recente, sem alterar dados ou aceitar identidade de outro usuário. Sessão ausente, encerrada ou expirada DEVE ser recusada. A interface da Recepção DEVE consultar antes de apresentar um status como confirmado e NÃO DEVE inventar um valor quando a integração estiver indisponível.

#### Scenario: Recepção abre o seletor
- **QUANDO** a Recepção/Triagem autenticada abre sua área inicial
- **ENTÃO** consulta o próprio status, sem enviar alteração, e pode escolher Disponível, Pausa ou Ausente após uma consulta válida

#### Scenario: Consulta ainda não publicada
- **QUANDO** o GET me/status não está disponível ou retorna resposta inválida
- **ENTÃO** o seletor informa indisponibilidade, não apresenta status fictício e permite tentar atualizar sem executar PATCH

#### Scenario: Alteração com resultado incerto
- **QUANDO** ocorre timeout ou a resposta não confirma o status solicitado
- **ENTÃO** a interface não anuncia sucesso nem repete a operação, orienta atualização e mantém o estado como não confirmado

#### Scenario: Envio em andamento
- **QUANDO** uma consulta ou alteração de status está em andamento
- **ENTÃO** o seletor bloqueia interações concorrentes e não emite uma segunda requisição

#### Scenario: Administrador tenta consultar o próprio status operacional
- **QUANDO** um Administrador chama GET me/status
- **ENTÃO** a autorização recusa o acesso, pois o perfil não possui status operacional

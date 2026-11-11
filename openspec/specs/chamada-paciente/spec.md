# Chamada de paciente — Especificação

## Purpose

Permite ao médico chamar o próximo paciente escolhido pelo sistema, repetir a chamada, confirmar o comparecimento ou registrar a desistência, sem nunca escolher o paciente nem registrar dados clínicos.

## Requirements

### Requirement: Acesso às ações de chamada
Somente o perfil Médico DEVE poder chamar, repetir, confirmar comparecimento, registrar desistência e imprimir a ficha. O médico NÃO DEVE poder escolher manualmente a ficha a ser chamada (RN24).

#### Scenario: Recepção tenta chamar
- **QUANDO** um usuário Recepção/Triagem aciona "Chamar próximo"
- **ENTÃO** o backend responde como acesso negado

#### Scenario: Tentativa de escolher a ficha
- **QUANDO** uma requisição de "Chamar próximo" envia o identificador de uma ficha específica
- **ENTÃO** o backend rejeita a requisição sem reservar ficha nem registrar chamada

### Requirement: Visão das filas pelo médico
O Médico DEVE ver as filas de especialidade e a ficha sob sua responsabilidade, que pode vir de uma especialidade própria, descoberta ou coberta em apoio. Antes da atribuição, dados pessoais NÃO DEVEM ser exibidos. A escolha da ficha DEVE seguir `fila-priorizada`.

#### Scenario: Médico de uma especialidade
- **QUANDO** um médico de Cardiologia abre sua tela
- **ENTÃO** vê as filas e sua ficha atribuída, sem nome/CPF de fichas ainda não atribuídas

### Requirement: Chamar próximo
Um Médico elegível (cadastro e usuário ativos, disponibilidade e plantão vigentes, sessão operacional apta e nenhuma ficha CHAMADO pendente) DEVE poder solicitar "Chamar próximo". O backend DEVE selecionar a ficha pela regra de `fila-priorizada`, reservá-la e registrar a tentativa 1 na mesma operação. A especialidade e a senha da ficha NÃO DEVEM mudar. Nome só é exibido após atribuição autorizada (RF23, RF28, §7.2, D02).

#### Scenario: Chamada bem-sucedida
- **QUANDO** um médico disponível de Clínica Geral aciona "Chamar próximo" e a fila tem fichas
- **ENTÃO** a primeira ficha pela regra passa a CHAMADO, com tentativa 1 registrada com médico e data/hora

#### Scenario: Apoio a outra especialidade
- **QUANDO** um Médico de Cardiologia chama uma Vermelha de Clínica Geral descoberta porque sua próxima própria é Azul
- **ENTÃO** a ficha permanece em Clínica Geral, mantém sua senha e é atribuída ao Médico de Cardiologia

#### Scenario: Fila vazia
- **QUANDO** não há ficha AGUARDANDO em nenhuma fila própria, descoberta ou outra coberta
- **ENTÃO** o sistema informa que não há pacientes aguardando, sem registrar chamada nem avançar ciclo (RF36, CA15)

#### Scenario: Médico indisponível
- **QUANDO** um médico sem disponibilidade vigente aciona "Chamar próximo"
- **ENTÃO** o sistema recusa e informa que ele não está disponível no momento

#### Scenario: Pausa, ausência ou plantão encerrado
- **QUANDO** um médico em PAUSA ou AUSENTE, ou com plantão encerrado, aciona "Chamar próximo"
- **ENTÃO** o backend recusa sem reservar ficha nem registrar chamada

#### Scenario: Novo login do mesmo médico
- **QUANDO** um Médico entra novamente enquanto outra sessão ainda está ativa
- **ENTÃO** a nova sessão fica indisponível e a chamada só é liberada após escolha explícita de DISPONIVEL

#### Scenario: Ficha pendente
- **QUANDO** o médico já tem uma ficha CHAMADO e aciona "Chamar próximo"
- **ENTÃO** o sistema recusa e pede que ele confirme o comparecimento ou registre a desistência da ficha atual

### Requirement: Chamada sem duplicidade
Duas chamadas simultâneas NÃO DEVEM receber a mesma ficha. Reserva, registro da tentativa e avanço do ciclo DEVEM ser atômicos; cliques repetidos NÃO DEVEM gerar ficha ou tentativa duplicada (RF38, RN34, RNF04, Rev. 2.1, §14.3 item 6).

#### Scenario: Dois médicos ao mesmo tempo
- **QUANDO** dois médicos da mesma especialidade acionam "Chamar próximo" ao mesmo tempo, com duas fichas na fila
- **ENTÃO** cada um recebe uma ficha diferente (CA14)

#### Scenario: Uma ficha para dois médicos
- **QUANDO** dois médicos acionam "Chamar próximo" ao mesmo tempo com uma única ficha na fila
- **ENTÃO** um recebe a ficha e o outro recebe a mensagem de fila vazia

#### Scenario: Duplo clique
- **QUANDO** o médico aciona "Chamar próximo" duas vezes seguidas muito rápido
- **ENTÃO** só uma ficha é chamada e só uma tentativa é registrada

#### Scenario: Disputa pela candidata entre especialidades
- **QUANDO** dois médicos selecionam simultaneamente a mesma candidata de uma fila descoberta
- **ENTÃO** somente um a reserva; o outro refaz a seleção, sem duplicar evento ou avanço do ciclo

### Requirement: Repetir chamada
O sistema DEVE permitir até 3 chamadas por oportunidade e exigir ao menos 30 segundos entre chamadas da mesma senha. Após a terceira chamada da primeira oportunidade sem comparecimento, a ficha DEVE retornar uma vez ao fim da mesma fila, mantendo senha/identidade. Sem resposta após a segunda oportunidade, encerra como DESISTÊNCIA conforme o estado final definido para a ficha. Desistência explicitamente registrada remove a ficha imediatamente.

#### Scenario: Segunda e terceira tentativas
- **QUANDO** o médico repete a chamada de uma ficha na tentativa 1 e depois na tentativa 2
- **ENTÃO** ficam registradas as tentativas 2 e 3

#### Scenario: Primeira oportunidade esgotada
- **QUANDO** a ficha completa 3 chamadas na primeira oportunidade sem comparecimento
- **ENTÃO** retorna ao fim da mesma fila com a mesma senha e recebe sua única nova oportunidade

#### Scenario: Segunda oportunidade sem resposta
- **QUANDO** a ficha esgota até 3 chamadas na segunda oportunidade sem comparecimento
- **ENTÃO** fica em DESISTÊNCIA e sai definitivamente da fila ativa

### Requirement: Ciclo de estados da Ficha em chamada
Para fins de chamada, a ficha percorre `AGUARDANDO → CHAMADO`; chamada repetida mantém `CHAMADO` e incrementa a tentativa da oportunidade atual; três chamadas sem resposta fazem `CHAMADO → AGUARDANDO`, incrementam a oportunidade e reposicionam a ficha ao fim da mesma fila. Comparecimento explícito faz `CHAMADO → ATENDIDO`; desistência explicitamente registrada faz `CHAMADO → DESISTÊNCIA`. `ATENDIDO` e `DESISTÊNCIA` são finais; não comparecimento isolado não é estado final.

#### Scenario: Rechamada preserva estado e identidade
- **QUANDO** o Médico rechama uma ficha em estado CHAMADO
- **ENTÃO** a ficha continua CHAMADO, a tentativa atual é incrementada e não é criada nova ficha nem senha

#### Scenario: Repetição antes do intervalo mínimo
- **QUANDO** o Médico tenta repetir a chamada 29 segundos depois da tentativa anterior
- **ENTÃO** o sistema recusa e informa quantos segundos faltam, sem registrar nova tentativa

#### Scenario: Repetição depois do intervalo mínimo
- **QUANDO** o Médico repete a chamada 30 segundos ou mais depois da tentativa anterior
- **ENTÃO** a nova tentativa é registrada

#### Scenario: Ficha de outro médico
- **QUANDO** um médico tenta repetir, confirmar ou registrar desistência de uma ficha chamada por outro médico
- **ENTÃO** o sistema recusa a operação

### Requirement: Confirmar comparecimento
O médico DEVE poder confirmar o comparecimento da ficha que está chamando, em qualquer tentativa. A ficha passa a ATENDIDO, sai da fila ativa e registra o horário de finalização (RF30, RN28). ATENDIDO não significa conclusão clínica (RN31).

#### Scenario: Comparecimento na segunda tentativa
- **QUANDO** o paciente comparece após a tentativa 2 e o médico confirma
- **ENTÃO** a ficha passa a ATENDIDO e deixa de aparecer em filas e previsões

### Requirement: Registrar desistência
O Médico DEVE poder registrar desistência explicitamente para a ficha sob sua responsabilidade a qualquer momento. A ficha passa a DESISTÊNCIA, sai definitivamente da fila ativa e registra horário e responsável. Esgotar a segunda oportunidade sem comparecimento também encerra a ficha como DESISTÊNCIA.

#### Scenario: Desistência explícita
- **QUANDO** o Médico registra desistência para a ficha chamada antes de esgotar as oportunidades
- **ENTÃO** a ficha passa a DESISTÊNCIA e deixa de aparecer entre as próximas chamadas

#### Scenario: Segunda oportunidade sem resposta
- **QUANDO** a ficha esgota até 3 chamadas na segunda oportunidade sem comparecimento
- **ENTÃO** fica em DESISTÊNCIA e sai definitivamente da fila ativa

### Requirement: Histórico de chamadas
Toda tentativa de chamada, confirmação de comparecimento e desistência DEVE ser registrada com ficha, médico, número da oportunidade, número da tentativa e data/hora, sem duplicidade (RF37, RNF03). A mesma tentativa numérica pode ocorrer em oportunidades diferentes.

#### Scenario: Consulta do histórico da ficha
- **QUANDO** uma ficha teve 3 tentativas e desistência
- **ENTÃO** o histórico mostra as 3 tentativas e o registro da desistência, com médico e horários

#### Scenario: Tentativa 1 na segunda oportunidade
- **QUANDO** a ficha retornou ao fim da fila depois da primeira oportunidade e é chamada novamente
- **ENTÃO** o histórico registra tentativa 1 da oportunidade 2 sem conflitar com a tentativa 1 da oportunidade 1

### Requirement: Impressão da ficha de atendimento
O médico DEVE poder imprimir a ficha de atendimento de uma ficha que ele chamou (CHAMADO ou ATENDIDO), com paciente (nome e idade), sintomas, observação, sinais vitais, escore e classificação de risco, prioridade atual, condição prioritária, especialidade e senha.

#### Scenario: Impressão após comparecimento
- **QUANDO** o médico confirma o comparecimento e aciona "Imprimir ficha"
- **ENTÃO** é gerada a página de impressão com os dados da triagem

#### Scenario: Ficha de outro médico
- **QUANDO** um médico tenta imprimir uma ficha que não chamou
- **ENTÃO** o sistema recusa a operação

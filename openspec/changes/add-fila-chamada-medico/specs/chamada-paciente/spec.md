# Delta de especificação

## Purpose

Permite ao médico chamar o próximo paciente escolhido pelo sistema, repetir a chamada, confirmar o comparecimento ou registrar a desistência, sem nunca escolher o paciente nem registrar dados clínicos.

## ADDED Requirements

### Requirement: Acesso às ações de chamada
Somente o perfil Médico DEVE poder chamar, repetir, confirmar comparecimento, registrar desistência e imprimir a ficha. O médico NÃO DEVE poder escolher manualmente a ficha a ser chamada (RN24).

#### Scenario: Recepção tenta chamar
- **QUANDO** um usuário Recepção/Triagem aciona "Chamar próximo"
- **ENTÃO** o backend responde como acesso negado

#### Scenario: Tentativa de escolher a ficha
- **QUANDO** uma requisição de "Chamar próximo" envia o identificador de uma ficha específica
- **ENTÃO** o identificador é ignorado e a ficha é escolhida pela regra da fila

### Requirement: Visão das filas pelo médico
O médico DEVE ver, para cada especialidade sua, as fichas AGUARDANDO na ordem prevista, com senha, cor, condição prioritária e tempo de espera, sem nome nem CPF, e a ficha que ele está chamando no momento.

#### Scenario: Médico com duas especialidades
- **QUANDO** um médico de Cardiologia e Clínica Geral abre sua tela
- **ENTÃO** vê as duas filas na ordem prevista, sem dados pessoais

### Requirement: Chamar próximo
Um médico disponível no momento e sem ficha CHAMADO pendente DEVE poder acionar "Chamar próximo". O sistema DEVE escolher a próxima ficha de cada especialidade do médico pela regra da fila e, entre essas candidatas, a de cor mais grave; em empate, a com condição prioritária; depois, a de chegada mais antiga. A ficha escolhida passa a CHAMADO, vinculada ao médico, com a tentativa 1 registrada, e o ciclo da especialidade dela é atualizado. Somente nesse momento o médico vê o nome do paciente, para conferência.

#### Scenario: Chamada bem-sucedida
- **QUANDO** um médico disponível de Clínica Geral aciona "Chamar próximo" e a fila tem fichas
- **ENTÃO** a primeira ficha pela regra passa a CHAMADO, com tentativa 1 registrada com médico e data/hora

#### Scenario: Escolha entre especialidades
- **QUANDO** o médico atende Cardiologia (próxima: Amarela) e Clínica Geral (próxima: Vermelha)
- **ENTÃO** é chamada a Vermelha de Clínica Geral

#### Scenario: Fila vazia
- **QUANDO** não há fichas AGUARDANDO em nenhuma especialidade do médico
- **ENTÃO** o sistema informa "Não há pacientes aguardando nesta fila" e nada é registrado (CA15)

#### Scenario: Médico indisponível
- **QUANDO** um médico sem disponibilidade vigente aciona "Chamar próximo"
- **ENTÃO** o sistema recusa e informa que ele não está disponível no momento

#### Scenario: Ficha pendente
- **QUANDO** o médico já tem uma ficha CHAMADO e aciona "Chamar próximo"
- **ENTÃO** o sistema recusa e pede que ele confirme o comparecimento ou registre a desistência da ficha atual

### Requirement: Chamada sem duplicidade
Duas chamadas simultâneas NÃO DEVEM receber a mesma ficha, e cliques repetidos NÃO DEVEM gerar tentativas duplicadas (RF38, RN34, RNF04, seção 20).

#### Scenario: Dois médicos ao mesmo tempo
- **QUANDO** dois médicos da mesma especialidade acionam "Chamar próximo" ao mesmo tempo, com duas fichas na fila
- **ENTÃO** cada um recebe uma ficha diferente (CA14)

#### Scenario: Uma ficha para dois médicos
- **QUANDO** dois médicos acionam "Chamar próximo" ao mesmo tempo com uma única ficha na fila
- **ENTÃO** um recebe a ficha e o outro recebe a mensagem de fila vazia

#### Scenario: Duplo clique
- **QUANDO** o médico aciona "Chamar próximo" duas vezes seguidas muito rápido
- **ENTÃO** só uma ficha é chamada e só uma tentativa é registrada

### Requirement: Repetir chamada
O médico DEVE poder repetir a chamada da ficha que ele está chamando enquanto o número de tentativas for menor que o máximo configurado (inicial 3). Cada repetição registra uma nova tentativa com data/hora (RF29, RN27).

#### Scenario: Segunda e terceira tentativas
- **QUANDO** o médico repete a chamada de uma ficha na tentativa 1 e depois na tentativa 2
- **ENTÃO** ficam registradas as tentativas 2 e 3

#### Scenario: Limite de tentativas
- **QUANDO** o médico tenta repetir a chamada de uma ficha que já está na tentativa 3
- **ENTÃO** o sistema recusa e oferece "Registrar desistência"

#### Scenario: Ficha de outro médico
- **QUANDO** um médico tenta repetir, confirmar ou registrar desistência de uma ficha chamada por outro médico
- **ENTÃO** o sistema recusa a operação

### Requirement: Confirmar comparecimento
O médico DEVE poder confirmar o comparecimento da ficha que está chamando, em qualquer tentativa. A ficha passa a ATENDIDO, sai da fila ativa e registra o horário de finalização (RF30, RN28). ATENDIDO não significa conclusão clínica (RN31).

#### Scenario: Comparecimento na segunda tentativa
- **QUANDO** o paciente comparece após a tentativa 2 e o médico confirma
- **ENTÃO** a ficha passa a ATENDIDO e deixa de aparecer em filas e previsões

### Requirement: Registrar desistência
O médico DEVE poder registrar desistência somente quando a ficha que está chamando tiver atingido o máximo de tentativas. A ficha passa a DESISTÊNCIA, sai da fila ativa e registra o horário de finalização (RF31, RN29, CA13).

#### Scenario: Desistência após a terceira tentativa
- **QUANDO** a ficha está na tentativa 3 sem comparecimento e o médico registra desistência
- **ENTÃO** a ficha passa a DESISTÊNCIA e deixa de aparecer entre as próximas chamadas

#### Scenario: Desistência antecipada
- **QUANDO** o médico tenta registrar desistência na tentativa 2
- **ENTÃO** o sistema recusa e informa quantas tentativas faltam

### Requirement: Histórico de chamadas
Toda tentativa de chamada, confirmação de comparecimento e desistência DEVE ser registrada com ficha, médico, número da tentativa e data/hora, sem duplicidade (RF37, RNF03).

#### Scenario: Consulta do histórico da ficha
- **QUANDO** uma ficha teve 3 tentativas e desistência
- **ENTÃO** o histórico mostra as 3 tentativas e o registro da desistência, com médico e horários

### Requirement: Impressão da ficha de atendimento
O médico DEVE poder imprimir a ficha de atendimento de uma ficha que ele chamou (CHAMADO ou ATENDIDO), com paciente (nome e idade), sintomas, observação, sinais vitais, escore e classificação de risco, prioridade atual, condição prioritária, especialidade e senha.

#### Scenario: Impressão após comparecimento
- **QUANDO** o médico confirma o comparecimento e aciona "Imprimir ficha"
- **ENTÃO** é gerada a página de impressão com os dados da triagem

#### Scenario: Ficha de outro médico
- **QUANDO** um médico tenta imprimir uma ficha que não chamou
- **ENTÃO** o sistema recusa a operação

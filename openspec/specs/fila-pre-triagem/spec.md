# Fila de pré-triagem

## Purpose

Ordenar e operar os tickets impessoais do Totem na Recepção/Triagem com chamada segura e reentrada controlada.

## Requirements

### Requirement: Seleção por prioridade e antiguidade
O sistema DEVE selecionar automaticamente tickets AGUARDANDO pelo ciclo configurável inicial de dois prioritários para um Normal. Pediátrico DEVE preceder Preferencial nas vagas prioritárias; dentro do mesmo tipo DEVE prevalecer a ordem de fila.

#### Scenario: Ciclo com todos os tipos
- **QUANDO** há tickets suficientes dos três tipos e o ciclo começa na primeira posição
- **ENTÃO** seleciona dois prioritários, preferindo Pediátrico enquanto houver, e depois um Normal

#### Scenario: Grupo vazio
- **QUANDO** a classe prevista está vazia e a outra tem tickets
- **ENTÃO** seleciona um ticket disponível sem avançar a posição do ciclo

#### Scenario: Fila vazia
- **QUANDO** não há ticket aguardando
- **ENTÃO** informa fila vazia sem modificar o ciclo

### Requirement: Oportunidades de chamada
Após iniciar a primeira chamada, o sistema DEVE realizar automaticamente até três chamadas por oportunidade, com intervalo mínimo inicial configurável de 30 segundos entre chamadas da mesma senha, e uma única reentrada ao fim da fila do próprio tipo após a primeira oportunidade sem comparecimento.

#### Scenario: Avanço automático
- **QUANDO** decorre o intervalo configurado sem confirmação de presença
- **ENTÃO** o sistema solicita nova chamada ou encerra a oportunidade após a última tentativa, validando o prazo e o estado no Xano

#### Scenario: Presença confirmada
- **QUANDO** a Recepção confirma presença durante a chamada
- **ENTÃO** o backend persiste a confirmação, impede novos avanços e permite a identificação e abertura da ficha

#### Scenario: Tela fechada
- **QUANDO** nenhuma tela autorizada da fila está aberta e conectada
- **ENTÃO** os avanços são retomados quando uma tela autorizada voltar a consultar a fila

#### Scenario: Repetição prematura
- **QUANDO** se tenta repetir antes de 30 segundos
- **ENTÃO** a operação é recusada sem incrementar tentativas

#### Scenario: Primeira ausência
- **QUANDO** a primeira oportunidade é encerrada sem comparecimento após as três chamadas e transcorrido o intervalo configurado desde a terceira
- **ENTÃO** o mesmo ticket retorna a AGUARDANDO ao fim da fila e recebe uma única nova oportunidade

#### Scenario: Segunda ausência
- **QUANDO** a segunda oportunidade é encerrada sem comparecimento após as três chamadas e transcorrido o intervalo configurado desde a terceira
- **ENTÃO** o ticket passa a NAO_COMPARECEU e sai da fila ativa

#### Scenario: Limite de tentativas
- **QUANDO** se solicita uma quarta chamada na mesma oportunidade
- **ENTÃO** a operação é recusada sem alterar a contagem

### Requirement: Validação transacional da chamada
O backend DEVE validar o estado do ticket antes de alterá-lo e DEVE agrupar reserva, ciclo e auditoria em `db.transaction`. O sistema NÃO DEVE afirmar exclusividade para operações simultâneas, pois ela não foi comprovada; a operação sequencial é uma limitação aceita nesta sprint.

#### Scenario: Ticket já chamado
- **QUANDO** uma operação sequencial tenta reservar um ticket que já não está AGUARDANDO
- **ENTÃO** a operação é recusada sem alterar o ticket ou o ciclo

### Requirement: Operação autorizada e acompanhamento
A Recepção/Triagem DEVE poder consultar a fila, visualizar senha, tentativa e contagem regressiva, chamar próximo, confirmar presença, registrar desistência e iniciar identificação após presença. A tela DEVE atualizar automaticamente a partir do Xano; os avanços dependem de uma tela autorizada aberta e conectada. O backend DEVE validar autenticação e perfil em cada operação e registrar alterações relevantes em auditoria. Qualquer operador autorizado DEVE poder retomar chamada ativa.

#### Scenario: Perfil sem permissão
- **QUANDO** Médico tenta chamar ticket
- **ENTÃO** o backend recusa a operação sem alterar a fila

#### Scenario: Sessão inválida
- **QUANDO** uma operação é solicitada sem sessão válida
- **ENTÃO** o backend recusa o acesso sem retornar dados protegidos ou alterar a fila

#### Scenario: Espera após terceira chamada
- **QUANDO** a ausência é solicitada antes de transcorrer o intervalo configurado desde a terceira chamada
- **ENTÃO** o backend recusa sem alterar o ticket

#### Scenario: Retomada por outro operador
- **QUANDO** outro operador autorizado da Recepção/Triagem acessa um ticket CHAMADO
- **ENTÃO** DEVE poder retomar suas ações sem transferência e os eventos DEVEM identificar o autor de cada operação

#### Scenario: Retorno da classe prevista
- **QUANDO** a classe prevista volta a ter ticket após chamada alternativa
- **ENTÃO** a próxima seleção usa a posição preservada do ciclo

### Requirement: Desistência explícita de ticket
O backend DEVE permitir exclusivamente à Recepção/Triagem registrar desistência explícita de ticket em AGUARDANDO ou CHAMADO, alterando-o para o estado final DESISTENCIA e removendo-o imediatamente da fila ativa. O ticket em DESISTENCIA NÃO DEVE ser chamado novamente nem reentrar na fila. A operação NÃO DEVE alterar automaticamente o estado de Fichas. A alteração e sua auditoria DEVEM ser atômicas, na operação.

#### Scenario: Desistência de ticket aguardando
- **QUANDO** a Recepção/Triagem registra desistência de ticket AGUARDANDO
- **ENTÃO** o ticket passa a DESISTENCIA e sai imediatamente da fila ativa

#### Scenario: Desistência de ticket chamado
- **QUANDO** a Recepção/Triagem registra desistência de ticket CHAMADO
- **ENTÃO** o ticket passa a DESISTENCIA e sai imediatamente da fila ativa sem alterar o estado de qualquer Ficha

#### Scenario: Tentativa após desistência
- **QUANDO** se tenta chamar novamente ou reintroduzir ticket em DESISTENCIA
- **ENTÃO** o backend recusa e mantém o estado final

#### Scenario: Ticket já finalizado
- **QUANDO** se solicita desistência de ticket ATENDIDO, NAO_COMPARECEU ou DESISTENCIA
- **ENTÃO** o backend recusa sem alterar o ticket ou Fichas

#### Scenario: Perfil não autorizado
- **QUANDO** Médico, Administrador ou pessoa sem sessão válida solicita desistência
- **ENTÃO** o backend recusa sem alterar o ticket ou Fichas

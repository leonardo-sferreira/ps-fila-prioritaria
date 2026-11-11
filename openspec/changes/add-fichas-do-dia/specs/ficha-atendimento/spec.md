# Delta de especificação

## MODIFIED Requirements

### Requirement: Nova chegada e ficha não finalizada
Cada nova chegada DEVE gerar nova ficha e preservar o histórico. Uma segunda ficha NÃO DEVE ser criada se o paciente já tiver ficha em `EM_TRIAGEM`, `AGUARDANDO` ou `CHAMADO`. Quando a abertura não informa ticket e o paciente já tem ficha nessas situações, o sistema DEVE devolver essa mesma ficha com a indicação de que já existia e a sua situação, sem criar ficha, sem alterá-la e sem registrar novo cadastro. A ficha `EM_TRIAGEM` continua sendo reaberta para a triagem (decisão do PO, 08/11/2026). Para a ficha `AGUARDANDO` ou `CHAMADO`, a Recepção/Triagem DEVE ver que o paciente já está na fila, com a senha, e PODE abrir a ficha atual (decisão do PO, 10/11/2026). Quando a abertura informa ticket e o paciente já tem ficha não finalizada, a operação DEVE ser recusada com mensagem clara. Fichas em `ATENDIDO`, `DESISTENCIA` ou `CANCELADO` são finais e NÃO DEVEM impedir nova chegada. O sistema NÃO DEVE criar estados adicionais para essa regra.

#### Scenario: Ficha não finalizada bloqueia nova abertura
- **QUANDO** o paciente possui ficha em `AGUARDANDO` ou `CHAMADO` e uma nova ficha é solicitada sem ticket
- **ENTÃO** nenhuma segunda ficha é criada, a resposta traz a ficha atual com a situação, e a Recepção/Triagem vê que o paciente já está na fila, com o botão "Abrir ficha atual"

#### Scenario: Ficha em triagem é reaberta
- **QUANDO** o paciente possui ficha em `EM_TRIAGEM` e a Recepção/Triagem clica em "Continuar" sem ticket
- **ENTÃO** a mesma ficha é aberta para edição, sem criar outra nem registrar novo cadastro na auditoria

#### Scenario: Chegada após estado final
- **QUANDO** a última ficha do paciente está em `ATENDIDO`, `DESISTENCIA` ou `CANCELADO` e ocorre nova chegada
- **ENTÃO** uma nova ficha é criada e a ficha finalizada permanece no histórico

#### Scenario: Abrir a ficha atual a partir da identificação
- **QUANDO** a Recepção/Triagem clica em "Abrir ficha atual" para um paciente com ficha `AGUARDANDO`
- **ENTÃO** a ficha abre editável para a reavaliação, com a mesma senha e sem mudar de situação

#### Scenario: Nova chegada com ticket e ficha na fila
- **QUANDO** a abertura informa ticket e o paciente já tem ficha em `EM_TRIAGEM`, `AGUARDANDO` ou `CHAMADO`
- **ENTÃO** a operação é recusada, nenhuma ficha é criada e o ticket não muda de estado

## ADDED Requirements

### Requirement: Fichas do dia
A Recepção/Triagem DEVE ter uma tela com as fichas não finalizadas, de qualquer data, e as finalizadas com chegada no dia atual (fuso America/Sao_Paulo), da chegada mais recente para a mais antiga. Cada linha DEVE mostrar hora de chegada, nome do paciente, senha, cor, especialidade e situação, e DEVE ter a ação de abrir a ficha. A tela DEVE permitir filtrar por situação (em triagem, aguardando, chamadas, finalizadas) e buscar por nome ou senha, sem diferenciar acentos nem maiúsculas. O endpoint DEVE validar o perfil Recepção/Triagem e NÃO DEVE devolver CPF, sintomas ou sinais vitais. A tela NÃO DEVE alterar fichas.

#### Scenario: Ficha aguardando aparece e abre para reavaliação
- **QUANDO** existe uma ficha `AGUARDANDO` com senha `A-NEU-002` e a Recepção/Triagem abre "Fichas do dia"
- **ENTÃO** a ficha aparece com a senha, a cor Amarela e a especialidade, e "Abrir" leva à ficha editável

#### Scenario: Finalizadas só de hoje
- **QUANDO** há uma ficha `ATENDIDO` com chegada ontem e outra com chegada hoje
- **ENTÃO** só a de hoje aparece na lista

#### Scenario: Não finalizada de ontem continua na lista
- **QUANDO** uma ficha `AGUARDANDO` teve chegada às 23:50 de ontem
- **ENTÃO** ela aparece na lista de hoje

#### Scenario: Filtro e busca
- **QUANDO** a Recepção/Triagem filtra por "Aguardando" e busca "jose"
- **ENTÃO** a lista mostra só as fichas aguardando de pacientes cujo nome contém "José", e a busca pela senha `A-NEU-002` encontra a ficha correspondente

#### Scenario: Nenhuma ficha
- **QUANDO** não há fichas que atendam ao filtro
- **ENTÃO** a tela mostra uma mensagem de lista vazia, sem erro

#### Scenario: Perfil sem permissão
- **QUANDO** um Médico ou Administrador consulta o endpoint das fichas do dia
- **ENTÃO** o backend recusa e nenhuma ficha é devolvida

#### Scenario: Resposta sem dados sensíveis
- **QUANDO** o endpoint das fichas do dia é consultado
- **ENTÃO** a resposta não contém CPF, sintomas nem sinais vitais

# Delta de especificação

## Purpose

Dá ao Administrador uma visão consolidada do plantão (fila geral, equipe logada com seus status e trilha de auditoria), apenas para acompanhamento.

## ADDED Requirements

### Requirement: Acesso exclusivo do Administrador
A fila geral, a lista de pessoas logadas e a consulta da auditoria DEVEM estar disponíveis somente para o Administrador.

#### Scenario: Médico tenta acessar o acompanhamento
- **QUANDO** um usuário Médico ou Recepção/Triagem consulta a fila geral, a equipe ou a auditoria
- **ENTÃO** o backend responde como acesso negado

### Requirement: Fila geral
O sistema DEVE listar todas as fichas EM_TRIAGEM, AGUARDANDO e CHAMADO de todas as especialidades, com senha (quando houver), cor atual, condição prioritária, especialidade atribuída, tempo de espera desde a chegada, status e, para fichas CHAMADO, médico e número da tentativa. A lista DEVE permitir filtro por especialidade, cor e status, e as fichas AGUARDANDO de cada especialidade DEVEM aparecer na mesma ordem da regra da fila.

#### Scenario: Visão do plantão
- **QUANDO** o Administrador abre a fila geral com fichas em triagem, aguardando e chamadas
- **ENTÃO** vê todas elas com as informações acima e as AGUARDANDO na ordem prevista de chamada

#### Scenario: Filtro por cor
- **QUANDO** o Administrador filtra por cor Vermelha
- **ENTÃO** a lista mostra apenas as fichas Vermelhas não finalizadas

#### Scenario: Fichas finalizadas não aparecem
- **QUANDO** uma ficha passa a ATENDIDO, DESISTÊNCIA ou CANCELADO
- **ENTÃO** ela deixa de aparecer na fila geral

### Requirement: Detalhe da ficha para o Administrador
O Administrador DEVE poder abrir o detalhe de uma ficha, somente leitura, com os dados da triagem, as especialidades sugerida e atribuída, as senhas que ela teve, as chamadas e o histórico de alterações.

#### Scenario: Detalhe com histórico
- **QUANDO** o Administrador abre uma ficha que teve a prioridade ajustada e foi chamada duas vezes
- **ENTÃO** vê o ajuste com justificativa e as duas tentativas, sem nenhuma ação de edição

### Requirement: Pessoas logadas e status
O sistema DEVE listar os usuários com sessão ativa (sem logout e não expirada), com nome, perfil, status operacional (quando aplicável) e horário de login, com filtro por perfil.

#### Scenario: Equipe logada
- **QUANDO** dois médicos (um DISPONIVEL e um PAUSA) e um usuário Recepção/Triagem estão logados
- **ENTÃO** a lista mostra os três com seus perfis, status e horários de login

#### Scenario: Sessão expirada ou encerrada
- **QUANDO** um usuário faz logout ou sua sessão expira
- **ENTÃO** ele deixa de aparecer na lista de pessoas logadas

### Requirement: Consulta da auditoria
O sistema DEVE mostrar os eventos de auditoria mais recentes primeiro, incluindo alterações de prioridade, sintomas, sinais vitais, disponibilidade, cadastros e parâmetros, chamadas (tentativas, comparecimentos e desistências), logins e logouts, cada um com tipo, registro afetado, valor anterior, valor novo, justificativa, responsável e data/hora. A consulta DEVE ser paginada (50 por página) e permitir filtro por tipo de evento, usuário responsável e período.

#### Scenario: Últimas alterações
- **QUANDO** o Administrador abre a auditoria
- **ENTÃO** vê os 50 eventos mais recentes, do mais novo para o mais antigo

#### Scenario: Filtro por tipo e período
- **QUANDO** o Administrador filtra "Prioridade alterada" entre 30/09/2026 08:00 e 12:00
- **ENTÃO** vê apenas os ajustes de prioridade desse intervalo, com responsável e justificativa

#### Scenario: Login registrado
- **QUANDO** um usuário faz login
- **ENTÃO** a auditoria passa a ter um evento de login com o usuário e a data/hora

### Requirement: Atualização da tela de acompanhamento
A tela de acompanhamento DEVE se atualizar automaticamente em até 10 segundos, sem ação do Administrador.

#### Scenario: Nova ficha aparece sozinha
- **QUANDO** uma ficha nova é aberta enquanto o Administrador está com a fila geral aberta
- **ENTÃO** ela aparece na lista em até 10 segundos

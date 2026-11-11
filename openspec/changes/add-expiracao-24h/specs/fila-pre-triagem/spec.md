# Delta de especificação

## ADDED Requirements

### Requirement: Expiração do ticket após o prazo
O sistema DEVE encerrar como `DESISTENCIA` todo ticket da pré-triagem em `AGUARDANDO` ou `CHAMADO` emitido há mais do que o prazo configurável `HORAS_EXPIRACAO` (inicialmente 24 horas), pela mesma rotina agendada das fichas, sem ação de usuário. Cada encerramento DEVE ficar no histórico como evento `EXPIRACAO`, sem usuário. A expiração é limpeza de registro abandonado, NÃO DEVE contar como chamada nem como "não compareceu" e NÃO DEVE alterar tickets finais.

#### Scenario: Ticket esquecido na fila
- **QUANDO** o ticket `N-031` está `AGUARDANDO` com emissão há 25 horas
- **ENTÃO** a rotina o encerra como `DESISTENCIA`, ele sai da fila de pré-triagem e o histórico registra `EXPIRACAO`

#### Scenario: Ticket chamado e abandonado
- **QUANDO** um ticket está `CHAMADO`, sem ação da Recepção, com emissão há 25 horas
- **ENTÃO** a rotina o encerra como `DESISTENCIA`, sem alterar a contagem de chamadas

#### Scenario: Ticket dentro do prazo
- **QUANDO** um ticket está `AGUARDANDO` com emissão há 2 horas
- **ENTÃO** a rotina não o altera

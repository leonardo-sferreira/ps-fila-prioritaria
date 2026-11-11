# Delta de especificação

## ADDED Requirements

### Requirement: Dispensa de ticket parado além do prazo
Na mesma ação de dispensa das fichas, o Administrador DEVE poder encerrar como `DESISTENCIA` todo ticket da pré-triagem em `AGUARDANDO` ou `CHAMADO` emitido há mais do que o prazo configurável `HORAS_EXPIRACAO` (inicialmente 24 horas). Cada encerramento DEVE ficar no histórico como evento `EXPIRACAO`, em nome do Administrador. A dispensa é limpeza de registro abandonado: NÃO DEVE contar como chamada nem como "não compareceu", NÃO DEVE alterar a contagem de chamadas e NÃO DEVE alterar tickets finais.

#### Scenario: Ticket esquecido na fila
- **QUANDO** o ticket `N-031` está `AGUARDANDO` com emissão há 25 horas e o Administrador dispensa os parados
- **ENTÃO** o ticket passa a `DESISTENCIA`, sai da fila de pré-triagem, e o histórico registra `EXPIRACAO`

#### Scenario: Ticket chamado e abandonado
- **QUANDO** um ticket está `CHAMADO`, sem ação da Recepção, com emissão há 25 horas
- **ENTÃO** a dispensa o encerra como `DESISTENCIA` sem alterar a contagem de chamadas

#### Scenario: Ticket dentro do prazo
- **QUANDO** um ticket está `AGUARDANDO` com emissão há 2 horas
- **ENTÃO** ele não aparece na prévia nem é alterado

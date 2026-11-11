# Delta de especificação

## ADDED Requirements

### Requirement: Dispensa de ficha parada além do prazo
O Administrador DEVE poder ver as fichas em `EM_TRIAGEM`, `AGUARDANDO` ou `CHAMADO` cuja chegada ocorreu há mais do que o prazo configurável `HORAS_EXPIRACAO` (inicialmente 24 horas) e dispensá-las de uma vez como `DESISTENCIA`. A prévia NÃO DEVE alterar dados. A dispensa DEVE recalcular no servidor o que está parado no momento da ação e DEVE registrar cada encerramento no histórico como evento `EXPIRACAO`, em nome do Administrador, com o estado anterior e a justificativa. A ficha dispensada DEVE sair da fila ativa e NÃO DEVE impedir uma nova chegada do paciente. A dispensa NÃO DEVE alterar fichas finais nem o ticket ligado à ficha. Somente o perfil Administrador DEVE ter acesso. Sem o parâmetro configurado como inteiro positivo, nada DEVE ser alterado.

#### Scenario: Ficha em triagem abandonada
- **QUANDO** uma ficha está `EM_TRIAGEM` com chegada há 25 horas e o Administrador clica em "Dispensar todos" e confirma
- **ENTÃO** a ficha passa a `DESISTENCIA`, o histórico registra `EXPIRACAO` com o Administrador, e o paciente pode abrir uma nova ficha

#### Scenario: Senha esquecida na fila
- **QUANDO** uma ficha está `AGUARDANDO` com a senha `A-NEU-002` e chegada há 25 horas
- **ENTÃO** ela aparece na prévia e, após a dispensa, sai da fila da especialidade

#### Scenario: Ainda dentro do prazo
- **QUANDO** uma ficha está `AGUARDANDO` com chegada há exatamente 24 horas
- **ENTÃO** ela não aparece na prévia nem é dispensada

#### Scenario: Ficha final não muda
- **QUANDO** uma ficha está `ATENDIDO` com chegada há 30 horas
- **ENTÃO** ela não aparece na prévia nem é alterada

#### Scenario: Ficha atendida entre a prévia e a dispensa
- **QUANDO** uma ficha aparecia na prévia, mas foi atendida antes da confirmação
- **ENTÃO** a dispensa não a altera

#### Scenario: Perfil sem permissão
- **QUANDO** a Recepção/Triagem ou o Médico chamam a prévia ou a dispensa
- **ENTÃO** o backend recusa e nada é alterado

#### Scenario: Parâmetro inválido
- **QUANDO** `HORAS_EXPIRACAO` não é um inteiro positivo
- **ENTÃO** a dispensa não altera nenhuma ficha e informa o motivo

# Delta de especificação

## ADDED Requirements

### Requirement: Expiração da ficha após o prazo
O sistema DEVE encerrar como `DESISTENCIA` toda ficha em `EM_TRIAGEM`, `AGUARDANDO` ou `CHAMADO` cuja chegada tenha ocorrido há mais do que o prazo configurável `HORAS_EXPIRACAO` (inicialmente 24 horas), por uma rotina agendada, sem ação de usuário. Cada encerramento DEVE ficar no histórico como evento `EXPIRACAO`, sem usuário, com o estado anterior e a justificativa. A ficha encerrada DEVE sair da fila ativa e NÃO DEVE impedir uma nova chegada do paciente. A rotina NÃO DEVE alterar fichas finais nem o ticket ligado à ficha. Sem o parâmetro configurado como inteiro positivo, a rotina NÃO DEVE alterar nenhuma ficha.

#### Scenario: Ficha em triagem abandonada
- **QUANDO** uma ficha está `EM_TRIAGEM` com chegada há 25 horas
- **ENTÃO** a rotina a encerra como `DESISTENCIA` e registra `EXPIRACAO` no histórico, e o paciente pode abrir uma nova ficha

#### Scenario: Senha esquecida na fila
- **QUANDO** uma ficha está `AGUARDANDO` com a senha `A-NEU-002` e chegada há 25 horas
- **ENTÃO** a rotina a encerra como `DESISTENCIA` e a senha sai da fila da especialidade

#### Scenario: Ainda dentro do prazo
- **QUANDO** uma ficha está `AGUARDANDO` com chegada há exatamente 24 horas
- **ENTÃO** a rotina não a altera

#### Scenario: Ficha final não muda
- **QUANDO** uma ficha está `ATENDIDO` com chegada há 30 horas
- **ENTÃO** a rotina não a altera nem registra histórico

#### Scenario: Parâmetro ausente
- **QUANDO** `HORAS_EXPIRACAO` não está configurado ou não é um inteiro positivo
- **ENTÃO** a rotina não altera nenhuma ficha e informa o motivo

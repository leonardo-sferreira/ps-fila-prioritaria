# auditoria Specification

## Purpose
Garante que toda alteração administrativa fique registrada de forma imutável.

## Requirements

### Requirement: Auditoria dos cadastros
Toda criação, edição, ativação, desativação e remoção feita nos cadastros do Administrador DEVE gravar um evento em `historico_alteracao` com o tipo do evento, a entidade, o registro, o valor anterior, o valor novo e o Administrador, na mesma transação da alteração. Operação recusada NÃO DEVE gravar evento. NÃO DEVE existir endpoint que altere ou apague eventos de auditoria.

#### Scenario: Alteração auditada
- **QUANDO** o Administrador desativa a sala "Consultório 3"
- **ENTÃO** o histórico registra `SALA_DESATIVADA` com o estado anterior, o novo e o usuário

#### Scenario: Operação recusada
- **QUANDO** uma criação de médico é recusada por e-mail repetido
- **ENTÃO** nenhum evento de auditoria é gravado

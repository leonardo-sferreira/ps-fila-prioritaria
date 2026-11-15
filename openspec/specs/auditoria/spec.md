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

### Requirement: Auditoria atômica e imutável
Toda operação relevante feita por usuário autenticado DEVE gravar um evento em `historico_alteracao` com tipo do evento, entidade, registro, valor anterior, valor novo, usuário da sessão, data/hora e, quando exigida, justificativa. O evento DEVE ser gravado na mesma transação da alteração: se a alteração falhar, o evento NÃO DEVE permanecer. O responsável DEVE ser o usuário da sessão, nunca um valor enviado na requisição. NÃO DEVE existir endpoint que crie, edite ou exclua eventos diretamente.

#### Scenario: Operação recusada
- **QUANDO** uma alteração é recusada por validação
- **ENTÃO** nenhum evento de auditoria é gravado

#### Scenario: Falha depois do registro desfaz tudo
- **QUANDO** uma operação grava a auditoria e falha antes de terminar
- **ENTÃO** nem a alteração nem o evento permanecem gravados

#### Scenario: Tentativa de gravar ou alterar auditoria pela API
- **QUANDO** qualquer usuário, inclusive o Administrador, procura criar, editar ou excluir um evento de auditoria pela API
- **ENTÃO** não existe operação que permita isso

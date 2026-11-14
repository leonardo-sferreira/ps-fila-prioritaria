## ADDED Requirements

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

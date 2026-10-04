# Delta de especificação

## Purpose

Registra de forma imutável quem alterou o quê e quando nas informações relevantes do sistema, atendendo RF37 e RNF07. É a base de auditoria que todas as changes usam.

## ADDED Requirements

### Requirement: Conteúdo do registro de auditoria
Todo registro de auditoria DEVE conter tipo do evento, entidade e identificador do registro afetado, valor anterior, valor novo, usuário responsável, data/hora e, quando a operação exigir, justificativa.

#### Scenario: Registro completo
- **QUANDO** uma operação auditada é concluída
- **ENTÃO** existe um registro com todos os campos acima preenchidos; o valor anterior fica vazio apenas em criações e o valor novo fica vazio apenas em remoções

#### Scenario: Operação executada pela carga inicial
- **QUANDO** o Administrador executa a carga inicial e ela cria registros
- **ENTÃO** cada criação é auditada com o Administrador que executou a carga como usuário responsável

### Requirement: Auditoria atômica com a operação
O registro de auditoria DEVE ser gravado junto com a alteração. Se a alteração falhar, NÃO DEVE existir registro de auditoria dela; se a gravação da auditoria falhar, a alteração NÃO DEVE ser confirmada.

#### Scenario: Operação recusada não gera auditoria
- **QUANDO** uma alteração é recusada por validação
- **ENTÃO** nenhum registro de auditoria é criado para ela

#### Scenario: Falha depois do registro desfaz tudo
- **QUANDO** uma operação grava a auditoria e falha antes de terminar
- **ENTÃO** nem a alteração nem o registro de auditoria permanecem gravados

### Requirement: Imutabilidade
Registros de auditoria NÃO DEVEM poder ser criados diretamente, editados nem excluídos pela API, por nenhum perfil. Eles só são criados como efeito de uma operação auditada.

#### Scenario: Tentativa de alterar auditoria
- **QUANDO** qualquer usuário, inclusive o Administrador, tenta editar ou excluir um registro de auditoria pela API
- **ENTÃO** não existe operação que permita isso e o registro permanece inalterado

#### Scenario: Tentativa de criar auditoria avulsa
- **QUANDO** qualquer usuário tenta gravar um registro de auditoria diretamente pela API
- **ENTÃO** não existe operação que permita isso

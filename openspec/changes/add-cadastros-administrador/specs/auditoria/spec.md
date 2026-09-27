# Delta de especificação

## Purpose

Registra de forma imutável quem alterou o quê e quando nas informações relevantes do sistema, atendendo RF37 e RNF07.

## ADDED Requirements

### Requirement: Conteúdo do registro de auditoria
Todo registro de auditoria DEVE conter tipo do evento, entidade e identificador do registro afetado, valor anterior, valor novo, usuário responsável, data/hora e, quando a operação exigir, justificativa.

#### Scenario: Registro completo
- **QUANDO** uma operação auditada é concluída
- **ENTÃO** existe um registro com todos os campos acima preenchidos; o valor anterior fica vazio apenas em criações e o valor novo fica vazio apenas em remoções

### Requirement: Auditoria atômica com a operação
O registro de auditoria DEVE ser gravado junto com a alteração. Se a alteração falhar, NÃO DEVE existir registro de auditoria dela; se a gravação da auditoria falhar, a alteração NÃO DEVE ser confirmada.

#### Scenario: Operação recusada não gera auditoria
- **QUANDO** uma alteração é recusada por validação
- **ENTÃO** nenhum registro de auditoria é criado para ela

### Requirement: Imutabilidade
Registros de auditoria NÃO DEVEM poder ser editados nem excluídos pela API, por nenhum perfil.

#### Scenario: Tentativa de alterar auditoria
- **QUANDO** qualquer usuário, inclusive o Administrador, tenta editar ou excluir um registro de auditoria pela API
- **ENTÃO** não existe operação que permita isso e o registro permanece inalterado

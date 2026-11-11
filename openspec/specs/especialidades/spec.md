# especialidades Specification

## Purpose
Permite ao Administrador manter as especialidades que organizam as filas e compõem as senhas.

## Requirements

### Requirement: Cadastro de especialidades
O Administrador DEVE poder listar todas as especialidades (ativas e inativas), criar uma especialidade com nome, sigla de exatamente 3 letras (gravada em maiúsculas) e descrição opcional, editar nome e descrição e ativar ou desativar. Nome e sigla DEVEM ser únicos, sem diferenciar maiúsculas. A sigla NÃO DEVE ser alterada depois de criada, porque compõe as senhas já emitidas. Especialidade NÃO DEVE ser excluída.

#### Scenario: Criar especialidade
- **QUANDO** o Administrador cria "Dermatologia" com a sigla "der"
- **ENTÃO** a especialidade é criada ativa com a sigla "DER" e a operação é auditada

#### Scenario: Sigla inválida ou repetida
- **QUANDO** a sigla tem 2 ou 4 letras, contém número ou já existe em outra especialidade
- **ENTÃO** a criação é recusada com mensagem clara e nada é gravado

#### Scenario: Desativar especialidade com fichas na fila
- **QUANDO** o Administrador tenta desativar uma especialidade com fichas AGUARDANDO ou CHAMADO
- **ENTÃO** a operação é recusada e a especialidade continua ativa

#### Scenario: Desativar a especialidade padrão
- **QUANDO** o Administrador tenta desativar a especialidade configurada em `ESPECIALIDADE_PADRAO`
- **ENTÃO** a operação é recusada

#### Scenario: Perfil sem permissão
- **QUANDO** a Recepção/Triagem ou o Médico tentam criar, editar ou desativar especialidade
- **ENTÃO** o backend recusa e nada é alterado

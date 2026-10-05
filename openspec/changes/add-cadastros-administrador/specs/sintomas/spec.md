# Delta de especificação

## Purpose

Permite ao Administrador manter o catálogo de sintomas e seus destinos clínicos, usando pontuação numérica e o catálogo oficial de `docs/domain-model.md`.

## ADDED Requirements

### Requirement: Cadastro de sintomas exclusivo do Administrador
O sistema DEVE permitir somente ao Administrador criar, editar, ativar e desativar sintomas e suas relações com especialidades. Os demais perfis autenticados DEVEM poder apenas consultar os sintomas ativos.

#### Scenario: Não administrador tenta alterar sintoma
- **QUANDO** um usuário Médico ou Recepção/Triagem tenta criar ou editar um sintoma
- **ENTÃO** o backend responde como acesso negado e nada é alterado

#### Scenario: Consulta pela Recepção/Triagem
- **QUANDO** um usuário Recepção/Triagem consulta os sintomas
- **ENTÃO** o sistema retorna apenas os sintomas ativos, agrupados por grupo, com nome, pontuação e destinos de especialidade

### Requirement: Dados do sintoma
Cada sintoma DEVE ter nome único (sem diferenciar maiúsculas e minúsculas), grupo, pontuação inteira de 1 a 3, situação e destino(s) conforme a relação definida pelo domínio, e pode ter descrição. A pontuação não representa cor e NÃO DEVE ser convertida em cor fixa. Os grupos e sintomas iniciais DEVEM seguir o catálogo integral de `docs/domain-model.md`.

#### Scenario: Criação bem-sucedida
- **QUANDO** o Administrador cria o sintoma "Dor ou pressão no peito", grupo Cardiovascular, pontuação 2 e destino Cardiologia
- **ENTÃO** o sintoma é criado ativo com os dados numéricos e a relação de direcionamento informados

#### Scenario: Pontuação fora da escala
- **QUANDO** o Administrador informa pontuação 0 ou 4
- **ENTÃO** o sistema recusa e informa que a pontuação deve ser um inteiro de 1 a 3

#### Scenario: Nome duplicado
- **QUANDO** o Administrador cria um sintoma com nome igual ao de outro existente, com outra caixa
- **ENTÃO** o sistema recusa com a mensagem "Sintoma já cadastrado"

### Requirement: Relação de direcionamento entre sintoma e especialidade
O Administrador DEVE poder manter a relação entre cada sintoma e a(s) especialidade(s) de destino indicadas pelo catálogo oficial, incluindo sua ordem quando houver mais de um destino. A relação NÃO DEVE conter duplicatas nem especialidades inativas. A regra de combinação quando a ficha contém sintomas de destinos diferentes pertence à change `add-direcionamento-senha`.

#### Scenario: Definir especialidades do sintoma
- **QUANDO** o Administrador associa "Dor ou pressão no peito" ao destino Cardiologia conforme o catálogo
- **ENTÃO** a relação aponta para Cardiologia e preserva a ordem definida no catálogo

#### Scenario: Especialidade inativa na relação
- **QUANDO** o Administrador tenta associar um sintoma a uma especialidade inativa
- **ENTÃO** o sistema recusa a associação e informa que a especialidade está inativa

### Requirement: Desativação sem exclusão
Sintomas NÃO DEVEM ser excluídos. Um sintoma inativo NÃO DEVE aparecer para seleção em novas fichas, mas continua nas fichas já registradas.

#### Scenario: Desativar sintoma
- **QUANDO** o Administrador desativa um sintoma
- **ENTÃO** ele deixa de ser retornado na consulta de sintomas ativos

### Requirement: Alterações de sintomas são auditadas
Toda alteração de sintoma, de sua pontuação ou de seus destinos DEVE gerar registro de auditoria.

#### Scenario: Mudança de pontuação auditada
- **QUANDO** o Administrador muda a pontuação de "Febre" de 1 para 2
- **ENTÃO** a auditoria registra 1 como valor anterior, 2 como valor novo, o usuário e a data/hora

### Requirement: Carga inicial de sintomas e especialidades
O catálogo inicial de sintomas é carregado por `add-base-compartilhada` e DEVE seguir integralmente `docs/domain-model.md`, com nome, grupo, pontuação de 1 a 3 e destino(s). A regra pediátrica de destino também deve seguir essa baseline. Esta change especifica a gestão administrativa, não uma segunda carga inicial.

#### Scenario: Ambiente recém-preparado
- **QUANDO** a carga inicial é executada em um ambiente vazio
- **ENTÃO** a tela permite consultar e manter os sintomas do catálogo oficial sem representar pontuação como cor

#### Scenario: Carga executada de novo
- **QUANDO** a carga inicial é executada em um ambiente que já tem esses registros
- **ENTÃO** nenhum registro é duplicado

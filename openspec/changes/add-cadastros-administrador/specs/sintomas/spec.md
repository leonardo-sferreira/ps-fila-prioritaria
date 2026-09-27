# Delta de especificação

## Purpose

Permite ao Administrador manter os sintomas selecionáveis na triagem, com a prioridade padrão de cada um e a relação ordenada com as especialidades que devem atendê-los.

## ADDED Requirements

### Requirement: Cadastro de sintomas exclusivo do Administrador
O sistema DEVE permitir somente ao Administrador criar, editar, ativar e desativar sintomas e suas relações com especialidades. Os demais perfis autenticados DEVEM poder apenas consultar os sintomas ativos.

#### Scenario: Não administrador tenta alterar sintoma
- **QUANDO** um usuário Médico ou Recepção/Triagem tenta criar ou editar um sintoma
- **ENTÃO** o backend responde como acesso negado e nada é alterado

#### Scenario: Consulta pela Recepção/Triagem
- **QUANDO** um usuário Recepção/Triagem consulta os sintomas
- **ENTÃO** o sistema retorna apenas os sintomas ativos, agrupados por grupo, com nome e prioridade padrão

### Requirement: Dados do sintoma
Cada sintoma DEVE ter nome único (sem diferenciar maiúsculas e minúsculas), grupo, prioridade padrão e situação, e pode ter descrição. A prioridade padrão DEVE ser uma das cores Vermelha, Amarela ou Azul (RN06). O grupo DEVE ser um de: Cardiovascular, Respiratório, Neurológico, Gastrointestinal, Traumático/Ortopédico, Geral.

#### Scenario: Criação bem-sucedida
- **QUANDO** o Administrador cria o sintoma "Dor no peito", grupo Cardiovascular, prioridade Vermelha
- **ENTÃO** o sintoma é criado ativo

#### Scenario: Prioridade inválida
- **QUANDO** o Administrador informa uma prioridade diferente de Vermelha, Amarela ou Azul (por exemplo, "Verde")
- **ENTÃO** o sistema recusa com a mensagem "Prioridade inválida" e não cria o sintoma

#### Scenario: Nome duplicado
- **QUANDO** o Administrador cria um sintoma com nome igual ao de outro existente, com outra caixa
- **ENTÃO** o sistema recusa com a mensagem "Sintoma já cadastrado"

### Requirement: Relação ordenada entre sintoma e especialidades
O Administrador DEVE poder associar a cada sintoma uma ou mais especialidades ativas em ordem de preferência. A primeira da lista é a especialidade preferencial do sintoma. A lista NÃO DEVE conter repetições.

#### Scenario: Definir especialidades do sintoma
- **QUANDO** o Administrador associa "Dor no peito" a [Cardiologia, Clínica Geral]
- **ENTÃO** Cardiologia fica com ordem 1 (preferencial) e Clínica Geral com ordem 2

#### Scenario: Especialidade inativa na relação
- **QUANDO** o Administrador tenta associar um sintoma a uma especialidade inativa
- **ENTÃO** o sistema recusa a associação e informa que a especialidade está inativa

### Requirement: Desativação sem exclusão
Sintomas NÃO DEVEM ser excluídos. Um sintoma inativo NÃO DEVE aparecer para seleção em novas fichas, mas continua nas fichas já registradas.

#### Scenario: Desativar sintoma
- **QUANDO** o Administrador desativa um sintoma
- **ENTÃO** ele deixa de ser retornado na consulta de sintomas ativos

### Requirement: Alterações de sintomas são auditadas
Toda alteração de sintoma, de sua prioridade padrão ou de suas especialidades DEVE gerar registro de auditoria.

#### Scenario: Mudança de prioridade padrão auditada
- **QUANDO** o Administrador muda a prioridade padrão de "Febre" de Azul para Amarela
- **ENTÃO** a auditoria registra "Azul" como valor anterior, "Amarela" como valor novo, o usuário e a data/hora

### Requirement: Carga inicial de sintomas e especialidades
O sistema DEVE disponibilizar uma carga inicial de exemplo com as especialidades Clínica Geral (CLI), Cardiologia (CAR), Ortopedia (ORT), Neurologia (NEU) e Pediatria (PED) e com os sintomas da seção 6 do documento formal, cada um com prioridade padrão e especialidade preferencial.

#### Scenario: Ambiente recém-preparado
- **QUANDO** a carga inicial é executada em um ambiente vazio
- **ENTÃO** as especialidades e os sintomas de exemplo ficam disponíveis e ativos

#### Scenario: Carga executada de novo
- **QUANDO** a carga inicial é executada em um ambiente que já tem esses registros
- **ENTÃO** nenhum registro é duplicado

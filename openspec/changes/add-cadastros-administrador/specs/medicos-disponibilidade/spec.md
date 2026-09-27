# Delta de especificação

## Purpose

Permite ao Administrador cadastrar médicos com suas especialidades e registrar os períodos em que cada médico atende, base para decidir quais filas podem receber pacientes.

## ADDED Requirements

### Requirement: Gestão de médicos e disponibilidade exclusiva do Administrador
O sistema DEVE permitir somente ao Administrador cadastrar médicos, alterar suas especialidades e registrar, alterar ou remover disponibilidade. O Médico NÃO DEVE conseguir alterar a própria disponibilidade (RN16).

#### Scenario: Médico tenta alterar a própria disponibilidade
- **QUANDO** um usuário Médico chama a operação de criar ou alterar disponibilidade, inclusive para si mesmo
- **ENTÃO** o backend responde como acesso negado e nada é alterado

#### Scenario: Médico consulta a própria agenda
- **QUANDO** um usuário Médico consulta sua disponibilidade
- **ENTÃO** o sistema retorna apenas os períodos do próprio médico, somente para leitura

### Requirement: Cadastro de médico
Todo médico DEVE estar vinculado a exatamente um usuário com perfil Médico, ter registro profissional e ter ao menos uma especialidade ativa. Um usuário NÃO DEVE estar vinculado a mais de um médico.

#### Scenario: Cadastro bem-sucedido
- **QUANDO** o Administrador vincula o usuário Médico "Ana" ao registro "CRM-ACAD-001" com as especialidades Cardiologia e Clínica Geral
- **ENTÃO** o médico é criado ativo com as duas especialidades

#### Scenario: Usuário sem perfil Médico
- **QUANDO** o Administrador tenta vincular um usuário com perfil Recepção/Triagem como médico
- **ENTÃO** o sistema recusa com a mensagem "O usuário precisa ter perfil Médico"

#### Scenario: Médico sem especialidade
- **QUANDO** o Administrador tenta salvar um médico sem nenhuma especialidade
- **ENTÃO** o sistema recusa e informa que ao menos uma especialidade é obrigatória

#### Scenario: Usuário já vinculado
- **QUANDO** o Administrador tenta vincular a um novo médico um usuário que já tem médico
- **ENTÃO** o sistema recusa e informa que o usuário já está vinculado

### Requirement: Registro de disponibilidade por período
O Administrador DEVE registrar a disponibilidade informando médico, data, hora inicial e hora final. A hora final DEVE ser posterior à inicial, e os períodos de um mesmo médico NÃO DEVEM se sobrepor na mesma data.

#### Scenario: Disponibilidade registrada
- **QUANDO** o Administrador registra o médico "Ana" em 30/09/2026, das 07:00 às 19:00
- **ENTÃO** o período é gravado e aparece na agenda do dia

#### Scenario: Período inválido
- **QUANDO** a hora final é igual ou anterior à hora inicial
- **ENTÃO** o sistema recusa com a mensagem "A hora final deve ser posterior à inicial"

#### Scenario: Sobreposição
- **QUANDO** o Administrador registra para "Ana" 13:00–20:00 na mesma data em que já existe 07:00–19:00
- **ENTÃO** o sistema recusa e informa o período conflitante

#### Scenario: Médico inativo
- **QUANDO** o Administrador registra disponibilidade para um médico inativo ou cujo usuário está inativo
- **ENTÃO** o sistema recusa o registro

### Requirement: Médico disponível agora
O sistema DEVE considerar um médico disponível em um instante somente se ele e seu usuário estiverem ativos e existir um período de disponibilidade que contenha esse instante. O intervalo inclui a hora inicial e exclui a hora final. O sistema DEVE oferecer uma consulta das especialidades ativas que têm ao menos um médico disponível no momento.

#### Scenario: Dentro do período
- **QUANDO** são 10:00 de 30/09/2026 e "Ana" (Cardiologia) tem disponibilidade das 07:00 às 19:00 nesse dia
- **ENTÃO** a consulta indica Cardiologia com médico disponível

#### Scenario: Valores-limite do período
- **QUANDO** o único período de "Ana" é 07:00–19:00 e a consulta é feita às 06:59, às 07:00, às 18:59 e às 19:00
- **ENTÃO** "Ana" está indisponível às 06:59, disponível às 07:00 e às 18:59, e indisponível às 19:00

#### Scenario: Usuário do médico desativado
- **QUANDO** o usuário de "Ana" é desativado durante um período de disponibilidade
- **ENTÃO** "Ana" deixa de ser considerada disponível imediatamente

### Requirement: Alteração e remoção de disponibilidade auditadas
O Administrador DEVE poder alterar e remover períodos de disponibilidade. Toda criação, alteração ou remoção DEVE gerar registro de auditoria com valor anterior e novo (RNF07).

#### Scenario: Remoção auditada
- **QUANDO** o Administrador remove o período de "Ana" em 30/09/2026
- **ENTÃO** o período deixa de valer e a auditoria registra o período removido, o usuário e a data/hora

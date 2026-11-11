# Delta de especificação

## Purpose

Permite ao Administrador manter os cadastros de Médico, Recepção/Triagem e Sala, as especialidades próprias N:N e a disponibilidade do Médico. Os vínculos próprios orientam a preferência de chamada, sem impedir apoio a outras filas.

## ADDED Requirements

### Requirement: Gestão de médicos e disponibilidade exclusiva do Administrador
O sistema DEVE permitir somente ao Administrador cadastrar/editar Médico e Recepção/Triagem juntamente com seus usuários correspondentes, manter salas e registrar, alterar ou remover disponibilidade. O Médico NÃO DEVE conseguir alterar a própria disponibilidade (RN16). A autorização DEVE ser verificada no backend.

#### Scenario: Médico tenta alterar a própria disponibilidade
- **QUANDO** um usuário Médico chama a operação de criar ou alterar disponibilidade, inclusive para si mesmo
- **ENTÃO** o backend responde como acesso negado e nada é alterado

#### Scenario: Médico consulta a própria agenda
- **QUANDO** um usuário Médico consulta sua disponibilidade
- **ENTÃO** o sistema retorna apenas os períodos do próprio médico, somente para leitura

### Requirement: Cadastro de médico
Todo Médico DEVE estar vinculado 1:1 a um usuário de perfil MEDICO e possuir nome profissional/de exibição, CRM, uma ou mais especialidades próprias vinculadas por `medico_especialidade` e situação ativo/inativo. Um usuário NÃO DEVE estar vinculado a mais de um Médico. O Administrador DEVE poder editar os vínculos próprios, sem duplicá-los. Eles orientam preferência, não proíbem apoio a outras filas.

#### Scenario: Cadastro bem-sucedido
- **QUANDO** o Administrador vincula o usuário Médico "Ana" ao registro "CRM-ACAD-001" com Cardiologia e Clínica Geral
- **ENTÃO** o médico é criado ativo com os dois vínculos próprios, sem duplicidade

#### Scenario: Usuário sem perfil Médico
- **QUANDO** o Administrador tenta vincular um usuário com perfil Recepção/Triagem como médico
- **ENTÃO** o sistema recusa com a mensagem "O usuário precisa ter perfil Médico"

#### Scenario: Edição das especialidades próprias
- **QUANDO** o Administrador troca Clínica Geral por Pediatria nas especialidades próprias de Ana
- **ENTÃO** os vínculos passam a representar Cardiologia e Pediatria e a auditoria registra a alteração

#### Scenario: Apoio a fila diferente das próprias
- **QUANDO** um Médico cadastrado com Cardiologia estiver elegível para apoiar uma fila descoberta de Clínica Geral
- **ENTÃO** o vínculo próprio não impede o apoio nem altera a especialidade da ficha

#### Scenario: Usuário já vinculado
- **QUANDO** o Administrador tenta vincular a um novo médico um usuário que já tem médico
- **ENTÃO** o sistema recusa e informa que o usuário já está vinculado

### Requirement: Registro de disponibilidade por período
O Administrador DEVE registrar a disponibilidade (RF15) informando médico, data, hora inicial e hora final. A hora final DEVE ser posterior à inicial, e os períodos de um mesmo médico NÃO DEVEM se sobrepor na mesma data.

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
O sistema DEVE considerar um Médico elegível em um instante somente se ele e seu usuário estiverem ativos, houver período de disponibilidade vigente, plantão não encerrado e sessão operacional apta. A consulta DEVE fornecer as especialidades próprias sem usá-las como filtro absoluto. PAUSA/AUSENTE impedem novas atribuições; EM_ATENDIMENTO não torna descoberta a especialidade própria. O intervalo inclui a hora inicial e exclui a hora final; horários usam `America/Sao_Paulo`.

#### Scenario: Dentro do período
- **QUANDO** são 10:00 de 30/09/2026 e "Ana" (Cardiologia) tem disponibilidade das 07:00 às 19:00 nesse dia
- **ENTÃO** a consulta indica Cardiologia com médico disponível

#### Scenario: Valores-limite do período
- **QUANDO** o único período de "Ana" é 07:00–19:00 e a consulta é feita às 06:59, às 07:00, às 18:59 e às 19:00
- **ENTÃO** "Ana" está indisponível às 06:59, disponível às 07:00 e às 18:59, e indisponível às 19:00

#### Scenario: Usuário do médico desativado
- **QUANDO** o usuário de "Ana" é desativado durante um período de disponibilidade
- **ENTÃO** "Ana" deixa de ser considerada disponível imediatamente

#### Scenario: Pausa deixa de cobrir especialidade
- **QUANDO** Ana é a única médica própria de Cardiologia e sua sessão passa a PAUSA ou AUSENTE
- **ENTÃO** Cardiologia fica descoberta para a seleção de apoio

#### Scenario: Atendimento mantém cobertura
- **QUANDO** Ana é a única médica própria de Cardiologia, está em EM_ATENDIMENTO e tem plantão e sessão vigentes
- **ENTÃO** Cardiologia não é considerada descoberta

### Requirement: Cadastro de Recepção/Triagem
Cada pessoa de perfil RECEPCAO_TRIAGEM DEVE possuir um registro próprio vinculado 1:1 ao Usuário correspondente, com nome, CPF, especialidade de referência quando aplicável e situação. O Administrador DEVE criar e editar o usuário e o registro de domínio na mesma operação administrativa; permissões de triagem continuam sendo verificadas no backend conforme a matriz global.

#### Scenario: Criar cadastro vinculado
- **QUANDO** o Administrador cadastra uma pessoa de Recepção/Triagem com usuário válido
- **ENTÃO** o sistema mantém o vínculo 1:1 e os dados de nome e CPF no registro próprio

### Requirement: Cadastro e vínculo operacional de Sala
Sala DEVE ser uma entidade própria com identificador, nome/número, descrição opcional e situação. O Administrador DEVE manter o cadastro, e o sistema DEVE relacionar operacionalmente o Médico à sala atual quando aplicável. Especialidade NÃO DEVE ser usada como sinônimo de Sala.

#### Scenario: Médico atende em sala
- **QUANDO** uma chamada é feita por um Médico associado a uma Sala ativa
- **ENTÃO** o sistema consegue fornecer a Sala associada à chamada sem alterar a especialidade da ficha

#### Scenario: Especialidade não é sala
- **QUANDO** uma ficha está na fila de Cardiologia e o médico atende na Sala 2
- **ENTÃO** o destino clínico continua Cardiologia e o local é Sala 2

### Requirement: Alteração e remoção de disponibilidade auditadas
O Administrador DEVE poder alterar e remover períodos de disponibilidade. Remover ou encerrar o período significa que o médico passa a ficar indisponível (RF15). Toda criação, alteração ou remoção DEVE gerar registro de auditoria com valor anterior e novo (RNF07).

#### Scenario: Remoção auditada
- **QUANDO** o Administrador remove o período de "Ana" em 30/09/2026
- **ENTÃO** o período deixa de valer e a auditoria registra o período removido, o usuário e a data/hora

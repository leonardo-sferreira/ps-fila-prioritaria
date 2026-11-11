# Delta de especificação

## Purpose

Permite ao Administrador manter médicos, Recepção/Triagem, salas e plantões, que a fila médica usa para saber quem pode chamar e de quais especialidades.

## ADDED Requirements

### Requirement: Cadastro de médico com login
O Administrador DEVE poder cadastrar um médico informando nome, e-mail, senha inicial (8 ou mais caracteres), CRM, uma ou mais especialidades próprias ativas e, opcionalmente, uma sala ativa. O sistema DEVE criar o usuário com perfil Médico e o cadastro do médico na mesma operação. O e-mail DEVE ser único, sem diferenciar maiúsculas. A edição DEVE permitir alterar nome, e-mail, CRM, especialidades próprias e sala. Desativar o médico DEVE desativar também o login; um médico com ficha CHAMADO pendente NÃO DEVE ser desativado.

#### Scenario: Novo médico com duas especialidades
- **QUANDO** o Administrador cadastra a médica Ana, CRM 12345-SP, com Cardiologia e Clínica Geral
- **ENTÃO** são criados o usuário (perfil Médico) e o médico com as duas especialidades próprias, e a operação é auditada

#### Scenario: E-mail já usado
- **QUANDO** o e-mail informado já pertence a outro usuário, com ou sem diferença de maiúsculas
- **ENTÃO** o cadastro é recusado e nada é criado

#### Scenario: Sem especialidade própria
- **QUANDO** nenhuma especialidade ativa é informada
- **ENTÃO** o cadastro é recusado

#### Scenario: Desativar médico com ficha chamada
- **QUANDO** o Administrador tenta desativar um médico que tem ficha CHAMADO pendente
- **ENTÃO** a operação é recusada

#### Scenario: Médico desativado perde o acesso
- **QUANDO** o Administrador desativa um médico sem ficha pendente
- **ENTÃO** o médico e o login ficam inativos, e a próxima requisição do médico é recusada

### Requirement: Cadastro da Recepção/Triagem com login
O Administrador DEVE poder cadastrar uma pessoa da Recepção/Triagem com nome, e-mail, senha inicial, CPF válido e especialidade de referência opcional, criando o usuário com perfil Recepção/Triagem na mesma operação; editar e ativar ou desativar (o login acompanha). O CPF DEVE ser único. A especialidade de referência é cadastral e NÃO DEVE limitar a triagem.

#### Scenario: CPF inválido ou repetido
- **QUANDO** o CPF tem dígitos verificadores inválidos ou já está cadastrado
- **ENTÃO** o cadastro é recusado

### Requirement: Cadastro de salas
O Administrador DEVE poder listar, criar, editar e ativar ou desativar salas com nome único e descrição opcional. O médico PODE ter uma sala atual ativa. Desativar uma sala DEVE desfazer o vínculo dos médicos que a tinham como sala atual. Sala NÃO DEVE ser confundida com especialidade.

#### Scenario: Sala inativa no médico
- **QUANDO** o Administrador tenta definir uma sala inativa como sala atual de um médico
- **ENTÃO** a operação é recusada

### Requirement: Plantões dos médicos
O Administrador DEVE poder registrar, alterar e remover períodos de plantão de um médico ativo, informando data, hora de início e hora de fim no fuso America/Sao_Paulo. Quando a hora de fim é menor ou igual à de início, o fim DEVE cair no dia seguinte. O período NÃO DEVE passar de 24 horas nem se sobrepor a outro período do mesmo médico. Período já iniciado NÃO DEVE ser removido nem ter o início alterado; só o fim pode ser ajustado. O Médico DEVE ver os próprios plantões, sem poder alterá-los.

#### Scenario: Plantão diurno
- **QUANDO** o Administrador registra 11/11/2026 das 07:00 às 19:00 para a médica Ana
- **ENTÃO** o período vai de 07:00 a 19:00 em Brasília e a operação é auditada

#### Scenario: Plantão noturno
- **QUANDO** o Administrador registra 11/11/2026 das 19:00 às 07:00
- **ENTÃO** o período vai de 11/11 19:00 a 12/11 07:00

#### Scenario: Sobreposição
- **QUANDO** já existe 07:00–19:00 e o Administrador registra 18:00–23:00 no mesmo dia para o mesmo médico
- **ENTÃO** o registro é recusado

#### Scenario: Plantões encostados
- **QUANDO** já existe 07:00–19:00 e o Administrador registra 19:00–23:00
- **ENTÃO** o registro é aceito, porque os períodos são semiabertos

#### Scenario: Remover plantão iniciado
- **QUANDO** o Administrador tenta remover um período que já começou
- **ENTÃO** a remoção é recusada e o período continua

#### Scenario: Médico tenta alterar plantão
- **QUANDO** um Médico tenta criar, alterar ou remover um período
- **ENTÃO** o backend recusa

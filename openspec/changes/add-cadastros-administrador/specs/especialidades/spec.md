# Delta de especificação

## Purpose

Permite ao Administrador manter as especialidades de atendimento, suas siglas usadas na senha e a lista ordenada de especialidades alternativas usada como fallback no direcionamento.

## ADDED Requirements

### Requirement: Cadastro de especialidades exclusivo do Administrador
O sistema DEVE permitir somente ao Administrador criar, editar, ativar e desativar especialidades. Os demais perfis autenticados DEVEM poder apenas consultar as especialidades ativas.

#### Scenario: Não administrador tenta alterar especialidade
- **QUANDO** um usuário Recepção/Triagem ou Médico tenta criar, editar ou desativar uma especialidade
- **ENTÃO** o backend responde como acesso negado e nada é alterado

#### Scenario: Consulta por outro perfil
- **QUANDO** um usuário Recepção/Triagem consulta as especialidades
- **ENTÃO** o sistema retorna somente as especialidades ativas, com nome e sigla

### Requirement: Dados da especialidade
Cada especialidade DEVE ter nome, sigla e situação (ativa/inativa), e pode ter descrição. A sigla DEVE ter exatamente 3 letras, ser gravada em maiúsculas e ser única entre todas as especialidades. O nome DEVE ser único, sem diferenciar maiúsculas e minúsculas.

#### Scenario: Criação bem-sucedida
- **QUANDO** o Administrador informa nome "Clínica Geral" e sigla "cli"
- **ENTÃO** a especialidade é criada ativa com a sigla "CLI"

#### Scenario: Sigla inválida
- **QUANDO** o Administrador informa uma sigla com 2 ou 4 caracteres, ou com números
- **ENTÃO** o sistema recusa com a mensagem "A sigla deve ter exatamente 3 letras" e não cria a especialidade

#### Scenario: Sigla ou nome duplicado
- **QUANDO** o Administrador informa uma sigla ou um nome já usados por outra especialidade
- **ENTÃO** o sistema recusa, indica o campo duplicado e não cria a especialidade

### Requirement: Desativação sem exclusão
Especialidades NÃO DEVEM ser excluídas. Uma especialidade inativa NÃO DEVE receber novos pacientes nem aparecer como opção de direcionamento, mas continua visível no histórico.

#### Scenario: Desativar especialidade
- **QUANDO** o Administrador desativa uma especialidade
- **ENTÃO** ela deixa de aparecer na consulta de especialidades ativas e o registro continua existindo

### Requirement: Especialidades alternativas ordenadas
O Administrador DEVE poder definir, para cada especialidade, uma lista ordenada de especialidades alternativas. A lista NÃO DEVE conter a própria especialidade nem repetições.

#### Scenario: Definir alternativas
- **QUANDO** o Administrador define para Cardiologia as alternativas [Clínica Geral, Neurologia], nessa ordem
- **ENTÃO** o sistema grava as duas alternativas com ordens 1 e 2

#### Scenario: Alternativa inválida
- **QUANDO** o Administrador inclui a própria especialidade ou repete uma especialidade na lista de alternativas
- **ENTÃO** o sistema recusa a lista inteira e informa o motivo

### Requirement: Alterações de especialidades são auditadas
Toda criação, edição, ativação, desativação ou alteração de alternativas de uma especialidade DEVE gerar registro de auditoria.

#### Scenario: Edição auditada
- **QUANDO** o Administrador altera o nome de uma especialidade
- **ENTÃO** a auditoria registra o valor anterior, o valor novo, o usuário e a data/hora

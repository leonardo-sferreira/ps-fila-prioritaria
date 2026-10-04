# Delta de especificação

## Purpose

Disponibiliza, desde a primeira sprint, as especialidades e os sintomas de exemplo que a triagem e o direcionamento usam, por meio de uma carga inicial repetível e de consultas somente leitura.

## ADDED Requirements

### Requirement: Carga inicial de especialidades e sintomas
O sistema DEVE oferecer ao Administrador uma carga inicial com as especialidades Clínica Geral (CLI), Cardiologia (CAR), Ortopedia (ORT), Neurologia (NEU) e Pediatria (PED), com Clínica Geral como alternativa de cada uma das outras, e com os sintomas da seção 6 do documento formal, cada um com grupo, prioridade padrão e especialidade preferencial. A carga DEVE ser idempotente: executada de novo, NÃO DEVE duplicar registros nem sobrescrever dados alterados depois.

#### Scenario: Ambiente recém-preparado
- **QUANDO** o Administrador executa a carga inicial em um ambiente vazio
- **ENTÃO** as especialidades e os sintomas de exemplo ficam disponíveis e ativos, e "Dor no peito" aparece com prioridade Vermelha e especialidade preferencial Cardiologia

#### Scenario: Carga executada de novo
- **QUANDO** a carga inicial é executada em um ambiente que já tem esses registros
- **ENTÃO** nenhum registro é duplicado

#### Scenario: Dado alterado depois da carga
- **QUANDO** a prioridade padrão de um sintoma foi alterada depois da primeira carga e a carga é executada de novo
- **ENTÃO** a prioridade alterada é mantida

#### Scenario: Não administrador tenta executar a carga
- **QUANDO** um usuário Recepção/Triagem ou Médico tenta executar a carga inicial
- **ENTÃO** o backend responde como acesso negado e nada é gravado

### Requirement: Consulta de especialidades ativas
Qualquer usuário autenticado e ativo DEVE poder consultar as especialidades ativas, com nome e sigla. Especialidades inativas NÃO DEVEM ser retornadas.

#### Scenario: Consulta pela Recepção/Triagem
- **QUANDO** um usuário Recepção/Triagem consulta as especialidades
- **ENTÃO** o sistema retorna apenas as especialidades ativas, com nome e sigla

#### Scenario: Consulta sem autenticação
- **QUANDO** a consulta de especialidades é chamada sem token
- **ENTÃO** o backend responde como não autenticado

### Requirement: Consulta de sintomas ativos
Qualquer usuário autenticado e ativo DEVE poder consultar os sintomas ativos, agrupados por grupo, com nome e prioridade padrão. Sintomas inativos NÃO DEVEM ser retornados.

#### Scenario: Consulta pela Recepção/Triagem
- **QUANDO** um usuário Recepção/Triagem consulta os sintomas
- **ENTÃO** o sistema retorna apenas os sintomas ativos, agrupados por grupo, com nome e prioridade padrão

#### Scenario: Sintoma inativo
- **QUANDO** um sintoma está inativo
- **ENTÃO** ele não aparece na consulta de sintomas

#### Scenario: Consulta sem autenticação
- **QUANDO** a consulta de sintomas é chamada sem token
- **ENTÃO** o backend responde como não autenticado

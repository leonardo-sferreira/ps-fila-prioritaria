# Delta de especificação

## Purpose

Disponibiliza, desde a primeira sprint, as especialidades e os sintomas de exemplo que a triagem e o direcionamento usam, por meio de uma carga inicial repetível e de consultas somente leitura.

## ADDED Requirements

### Requirement: Carga inicial de especialidades e sintomas
O sistema DEVE oferecer ao Administrador uma carga inicial com as especialidades Clínica Geral (CLI), Cardiologia (CAR), Ortopedia (ORT), Neurologia (NEU) e Pediatria (PED), e com o catálogo de sintomas consolidado em `docs/domain-model.md`. Cada sintoma DEVE conter nome, grupo, pontuação inteira de 1 a 3 e relação ordenada de direcionamento para especialidade(s); não DEVE possuir cor/prioridade padrão. A carga DEVE ser idempotente: executada de novo, NÃO DEVE duplicar registros nem sobrescrever dados alterados depois. Especialidades alternativas NÃO DEVEM ser usadas como fallback condicionado à especialidade ou disponibilidade de médicos.

#### Scenario: Ambiente recém-preparado
- **QUANDO** o Administrador executa a carga inicial em um ambiente vazio
- **ENTÃO** as especialidades e os sintomas do catálogo de referência ficam disponíveis e ativos, e "Dor ou pressão no peito" aparece com grupo Cardiovascular, pontuação 2 e destino Cardiologia

#### Scenario: Carga executada de novo
- **QUANDO** a carga inicial é executada em um ambiente que já tem esses registros
- **ENTÃO** nenhum registro é duplicado

#### Scenario: Dado alterado depois da carga
- **QUANDO** a pontuação ou relação de direcionamento de um sintoma for alterada depois da primeira carga e a carga for executada de novo
- **ENTÃO** os dados alterados são mantidos

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
Qualquer usuário autenticado e ativo DEVE poder consultar os sintomas ativos, agrupados por grupo, com nome, grupo, pontuação e destinos ordenados. Sintomas inativos NÃO DEVEM ser retornados.

#### Scenario: Consulta pela Recepção/Triagem
- **QUANDO** um usuário Recepção/Triagem consulta os sintomas
- **ENTÃO** o sistema retorna apenas os sintomas ativos, agrupados por grupo, com nome, pontuação numérica e destinos de especialidade

#### Scenario: Sintoma inativo
- **QUANDO** um sintoma está inativo
- **ENTÃO** ele não aparece na consulta de sintomas

#### Scenario: Consulta sem autenticação
- **QUANDO** a consulta de sintomas é chamada sem token
- **ENTÃO** o backend responde como não autenticado

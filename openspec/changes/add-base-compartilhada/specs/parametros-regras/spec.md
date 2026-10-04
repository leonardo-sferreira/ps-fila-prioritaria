# Delta de especificação

## Purpose

Mantém configuráveis, sem alterar código, os parâmetros operacionais usados pelas regras de classificação, chamada e painel, conforme RNF09 e a seção 22.1 do documento formal.

## ADDED Requirements

### Requirement: Parâmetros com valores iniciais
O sistema DEVE manter os seguintes parâmetros, com os valores iniciais indicados: idade mínima de idoso (60), idade máxima de criança (11), quantidade de amarelas por ciclo (2), quantidade de azuis por ciclo (1), máximo de tentativas de chamada (3), tamanho da previsão do painel (5), intervalo mínimo entre chamadas da mesma senha (10 segundos) e especialidade padrão (Clínica Geral). As regras do sistema DEVEM ler os valores dos parâmetros em vez de usar valores fixos no código.

#### Scenario: Ambiente recém-preparado
- **QUANDO** a carga inicial é executada em um ambiente sem parâmetros
- **ENTÃO** todos os parâmetros acima existem com os valores iniciais indicados

#### Scenario: Carga não sobrescreve valor alterado
- **QUANDO** um parâmetro já existe com valor diferente do inicial e a carga inicial é executada de novo
- **ENTÃO** o valor existente é mantido e nenhum parâmetro é duplicado

### Requirement: Consulta dos parâmetros
Qualquer usuário autenticado e ativo DEVE poder consultar os parâmetros com seus valores atuais. A consulta NÃO DEVE estar disponível sem autenticação.

#### Scenario: Consulta autenticada
- **QUANDO** um usuário autenticado de qualquer perfil consulta os parâmetros
- **ENTÃO** o sistema retorna todos os parâmetros com seus valores atuais

#### Scenario: Consulta sem autenticação
- **QUANDO** a consulta de parâmetros é chamada sem token
- **ENTÃO** o backend responde como não autenticado

#### Scenario: Usuário inativo
- **QUANDO** um usuário desativado, com token ainda válido, consulta os parâmetros
- **ENTÃO** o backend responde como não autenticado

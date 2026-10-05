# Delta de especificação

## Purpose

Mantém configuráveis, sem alterar código, os parâmetros operacionais usados pelas regras de classificação, chamada e painel, conforme RNF09 e a seção 22.1 do documento formal.

## ADDED Requirements

### Requirement: Parâmetros com valores iniciais
O sistema DEVE manter os parâmetros clínicos e operacionais configuráveis previstos na baseline: idade mínima de idoso (60), idade máxima de criança (11), quantidades do ciclo amarelo/azul (2 e 1), tamanho da previsão do painel (5), escores e faixas clínicas aplicáveis e especialidade padrão apenas para casos sem destino sintomático conforme regra de direcionamento. As chamadas obedecem à regra fixa da baseline: intervalo de 30 segundos, até 3 chamadas por oportunidade e retorno ao fim da fila sem resposta, sem remoção automática. O fuso `America/Sao_Paulo` não é editável. Parâmetros não definidos na baseline NÃO DEVEM ser inventados nesta change.

#### Scenario: Ambiente recém-preparado
- **QUANDO** a carga inicial é executada em um ambiente sem parâmetros
- **ENTÃO** existem os parâmetros configuráveis previstos na baseline com os valores iniciais nela definidos, sem parâmetro editável de fuso ou intervalo de chamadas

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

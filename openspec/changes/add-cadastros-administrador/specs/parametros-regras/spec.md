# Delta de especificação

## Purpose

Mantém configuráveis, sem alterar código, os parâmetros operacionais usados pelas regras de classificação, chamada e painel, conforme RNF09 e a seção 22.1 do documento formal.

## ADDED Requirements

### Requirement: Parâmetros com valores iniciais
O sistema DEVE manter os parâmetros configuráveis definidos para idade, ciclo, tamanho da previsão e especialidade padrão. Os limiares clínicos iniciais são moderado 3 e alto 6, configuráveis na change clínica. As chamadas seguem 30 segundos, até 3 chamadas por oportunidade e uma reentrada única; esses valores aprovados pela baseline não são editáveis como parâmetros operacionais pelo Administrador. O fuso `America/Sao_Paulo` também não é editável.

#### Scenario: Consulta dos parâmetros
- **QUANDO** um usuário autenticado consulta os parâmetros
- **ENTÃO** o sistema retorna todos os parâmetros com seus valores atuais

#### Scenario: Consulta sem autenticação
- **QUANDO** a consulta de parâmetros é chamada sem token
- **ENTÃO** o backend responde como não autenticado

### Requirement: Alteração restrita ao Administrador e validada
Somente o Administrador DEVE poder alterar parâmetros configuráveis. Valores numéricos DEVEM ser inteiros dentro dos limites: idades de 0 a 120, com a idade máxima de criança menor que a idade mínima de idoso; quantidades do ciclo de 1 a 10; tamanho da previsão de 1 a 20. A especialidade padrão, quando aplicável, DEVE ser ativa. Toda alteração DEVE ser auditada. A API NÃO DEVE permitir alterar o intervalo de 30 segundos, o limite de 3 tentativas por oportunidade, o número de reentradas ou o fuso.

#### Scenario: Valores de chamada fixados pela baseline
- **QUANDO** o Administrador tenta alterar o intervalo, o máximo de tentativas ou o fuso
- **ENTÃO** o sistema recusa, mantendo 30 segundos, até 3 tentativas por oportunidade, uma reentrada e `America/Sao_Paulo`

#### Scenario: Valores-limite do tamanho da previsão
- **QUANDO** o Administrador informa tamanho da previsão 0, 1, 20 e 21
- **ENTÃO** 1 e 20 são aceitos; 0 e 21 são recusados com a indicação do intervalo aceito, mantendo o valor anterior

#### Scenario: Idades incoerentes
- **QUANDO** o Administrador define a idade máxima de criança igual ou maior que a idade mínima de idoso
- **ENTÃO** o sistema recusa a alteração

#### Scenario: Especialidade padrão inativa
- **QUANDO** o Administrador escolhe como especialidade padrão uma especialidade inativa
- **ENTÃO** o sistema recusa a alteração

#### Scenario: Não administrador tenta alterar
- **QUANDO** um usuário Recepção/Triagem ou Médico tenta alterar um parâmetro
- **ENTÃO** o backend responde como acesso negado e nada é alterado

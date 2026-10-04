# Delta de especificação

## Purpose

Mantém configuráveis, sem alterar código, os parâmetros operacionais usados pelas regras de classificação, chamada e painel, conforme RNF09 e a seção 22.1 do documento formal.

## ADDED Requirements

### Requirement: Parâmetros com valores iniciais
O sistema DEVE manter os seguintes parâmetros, com os valores iniciais indicados: idade mínima de idoso (60), idade máxima de criança (11), quantidade de amarelas por ciclo (2), quantidade de azuis por ciclo (1), máximo de tentativas de chamada (3), tamanho da previsão do painel (5), intervalo mínimo entre chamadas da mesma senha (10 segundos) e especialidade padrão (Clínica Geral).

#### Scenario: Consulta dos parâmetros
- **QUANDO** um usuário autenticado consulta os parâmetros
- **ENTÃO** o sistema retorna todos os parâmetros com seus valores atuais

#### Scenario: Consulta sem autenticação
- **QUANDO** a consulta de parâmetros é chamada sem token
- **ENTÃO** o backend responde como não autenticado

### Requirement: Alteração restrita ao Administrador e validada
Somente o Administrador DEVE poder alterar parâmetros. Valores numéricos DEVEM ser inteiros dentro dos limites: idades de 0 a 120, com a idade máxima de criança menor que a idade mínima de idoso; amarelas por ciclo de 1 a 10; azuis por ciclo de 1 a 10; tentativas de 1 a 10; tamanho da previsão de 1 a 20; intervalo entre chamadas de 1 a 300 segundos. A especialidade padrão DEVE ser uma especialidade ativa. Toda alteração DEVE ser auditada.

#### Scenario: Alteração válida
- **QUANDO** o Administrador altera o máximo de tentativas de 3 para 4
- **ENTÃO** o novo valor passa a valer nas próximas operações e a alteração é auditada

#### Scenario: Valores-limite do tamanho da previsão
- **QUANDO** o Administrador informa tamanho da previsão 0, 1, 20 e 21
- **ENTÃO** 1 e 20 são aceitos; 0 e 21 são recusados com a indicação do intervalo aceito, mantendo o valor anterior

#### Scenario: Valores-limite do intervalo entre chamadas
- **QUANDO** o Administrador informa intervalo entre chamadas 0, 1, 300 e 301 segundos
- **ENTÃO** 1 e 300 são aceitos; 0 e 301 são recusados com a indicação do intervalo aceito, mantendo o valor anterior (RF35)

#### Scenario: Idades incoerentes
- **QUANDO** o Administrador define a idade máxima de criança igual ou maior que a idade mínima de idoso
- **ENTÃO** o sistema recusa a alteração

#### Scenario: Especialidade padrão inativa
- **QUANDO** o Administrador escolhe como especialidade padrão uma especialidade inativa
- **ENTÃO** o sistema recusa a alteração

#### Scenario: Não administrador tenta alterar
- **QUANDO** um usuário Recepção/Triagem ou Médico tenta alterar um parâmetro
- **ENTÃO** o backend responde como acesso negado e nada é alterado

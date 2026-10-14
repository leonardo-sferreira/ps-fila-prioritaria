# Delta de especificação

## Purpose

Define a composição futura do escore clínico e a prioridade da ficha, sem antecipar as faixas numéricas que converterão o escore total em cores.

## ADDED Requirements

### Requirement: Pontuação dos sintomas e composição futura do escore
Cada Sintoma DEVE possuir `pontuacao` inteira de 1 a 3 e NÃO DEVE possuir cor ou prioridade fixa. Em etapa futura, o escore de sintomas DEVE ser a soma das pontuações de todos os sintomas selecionados, e o `escore_total` DEVE compor os componentes clínicos aprovados, incluindo sinais fisiológicos quando implementados.

#### Scenario: Vários sintomas contribuem para o escore futuro
- **QUANDO** uma ficha futura contém sintomas com pontuações 3, 2 e 1
- **ENTÃO** o componente de sintomas do escore totaliza 6 sem atribuir cor fixa a cada sintoma

### Requirement: Pontuação futura dos sinais vitais
Em etapa futura, o sistema DEVE atribuir de 0 a 3 pontos a cada sinal vital conforme faixas aprovadas e configuráveis. Os valores já aprovados para cada componente DEVEM permanecer independentes da futura conversão de `escore_total` em prioridade.

#### Scenario: Componente fisiológico pontuado
- **QUANDO** um sinal vital se enquadra em uma faixa configurada de 2 pontos
- **ENTÃO** o componente fisiológico contribui com 2 pontos para a composição futura do escore

### Requirement: Pontuação aprovada da glicemia
Na etapa futura de sinais vitais, glicemia abaixo de 54 mg/dL com sinais de gravidade DEVE pontuar 3; abaixo de 54 sem sinais DEVE pontuar 2; de 54 a 59 com sinais DEVE pontuar 2; e de 54 a 59 sem sinais DEVE pontuar 1. Esses pontos compõem o escore futuro e NÃO definem, isoladamente, prioridade final.

#### Scenario: Glicemia baixa com sinais de gravidade
- **QUANDO** a glicemia é 53 mg/dL com sinais de gravidade
- **ENTÃO** o componente glicêmico recebe 3 pontos sem inferir cor final da ficha

#### Scenario: Glicemia limítrofe sem sinais de gravidade
- **QUANDO** a glicemia é 54 mg/dL sem sinais de gravidade
- **ENTÃO** o componente glicêmico recebe 1 ponto sem inferir cor final da ficha

### Requirement: Faixas pendentes para prioridade final
A classificação futura DEVE resultar em prioridade Azul, Amarela ou Vermelha a partir de `escore_total`. As faixas numéricas que mapeiam o escore para essas prioridades DEVEM ser definidas e aprovadas antes da implementação da classificação final. Nenhum limiar provisório DEVE ser inferido de sintomas, sinais vitais ou catálogo.

#### Scenario: Implementação bloqueada sem faixas aprovadas
- **QUANDO** a etapa de classificação final for iniciada sem faixas aprovadas para o escore total
- **ENTÃO** o mapeamento para Azul, Amarela ou Vermelha não é implementado

### Requirement: Conflito documental de thresholds
`docs/domain-model.md` ainda contém os limiares 3/6, mas esses valores NÃO DEVEM ser tratados como regra vigente nesta change. O documento não é alterado nesta etapa; a divergência DEVE ser resolvida antes da implementação da classificação final.

#### Scenario: Planejamento da classificação futura
- **QUANDO** as faixas de prioridade forem definidas futuramente
- **ENTÃO** a decisão resolve explicitamente a divergência documental antes de código de classificação ser implementado

### Requirement: Condição prioritária futura
Em etapa futura, a ficha DEVE registrar condição prioritária por idade ou gestação conforme regras aprovadas, sem que essa condição por si só defina a prioridade final. A precedência entre condições e o uso na fila permanecem parte da etapa futura.

#### Scenario: Condição preservada separadamente
- **QUANDO** uma condição prioritária futura é identificada
- **ENTÃO** ela é registrada separadamente da futura prioridade calculada

### Requirement: Prioridades calculada e atual futuras
Após as faixas finais serem aprovadas, a ficha DEVE guardar prioridade calculada e prioridade atual. A prioridade atual PODE divergir da calculada somente pelo ajuste manual autorizado e justificado, em etapa futura; alterações de componentes clínicos DEVEM disparar o recálculo segundo as regras então aprovadas.

#### Scenario: Ajuste e recálculo futuros
- **QUANDO** a etapa futura permitir ajuste manual e depois os componentes clínicos forem alterados
- **ENTÃO** o comportamento segue as regras de ajuste e recálculo aprovadas para essa etapa

### Requirement: Configuração futura de risco
Em etapa futura, o Administrador DEVE poder configurar as faixas de pontuação dos componentes fisiológicos e as faixas aprovadas de classificação final, com validações de coerência e auditoria quando essas capacidades estiverem disponíveis. Esta fatia não implementa essa configuração.

#### Scenario: Configuração não pertence à fatia atual
- **QUANDO** a fatia atual de ficha, sintomas e observação é verificada
- **ENTÃO** não exige tela, endpoint ou regra de configuração de risco

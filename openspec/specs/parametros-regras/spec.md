# parametros-regras Specification

## Purpose
Permite ao Administrador ajustar os parâmetros de regra e as faixas de pontuação dos sinais vitais dentro de limites seguros.

## Requirements

### Requirement: Parâmetros configuráveis
O Administrador DEVE poder consultar todos os parâmetros com o valor atual e os limites, e alterar somente os editáveis, dentro do mínimo e do máximo de cada um. As idades DEVEM manter `IDADE_MAXIMA_CRIANCA` menor que `IDADE_MINIMA_TABELA_ADULTA`, que DEVE ser menor ou igual a `IDADE_MINIMA_IDOSO`. `LIMIAR_AMARELA` DEVE ser menor que `LIMIAR_VERMELHA`. `ESPECIALIDADE_PADRAO` DEVE apontar para uma especialidade ativa. Parâmetros internos, como a posição do ciclo, NÃO DEVEM ser editáveis. O fuso horário NÃO é parâmetro.

#### Scenario: Alteração válida
- **QUANDO** o Administrador muda `HORAS_EXPIRACAO` de 24 para 36
- **ENTÃO** o valor é gravado e a alteração é auditada

#### Scenario: Fora do limite
- **QUANDO** o valor fica abaixo do mínimo ou acima do máximo do parâmetro
- **ENTÃO** a alteração é recusada sem auditoria

#### Scenario: Idades incoerentes
- **QUANDO** o Administrador define `IDADE_MAXIMA_CRIANCA` igual ou maior que `IDADE_MINIMA_TABELA_ADULTA`
- **ENTÃO** a alteração é recusada

#### Scenario: Parâmetro interno
- **QUANDO** o Administrador tenta alterar `POSICAO_CICLO_PRE_TRIAGEM`
- **ENTÃO** a alteração é recusada

### Requirement: Faixas de pontuação dos sinais vitais
O Administrador DEVE poder consultar as faixas de cada sinal vital e alterar o mínimo, o máximo e os pontos (0 a 3) de uma faixa. O mínimo DEVE ser menor ou igual ao máximo, e limite vazio representa extremo aberto. Uma faixa NÃO DEVE se sobrepor a outra do mesmo sinal vital e da mesma condição de gravidade. Faixas NÃO DEVEM ser criadas nem excluídas pela tela.

#### Scenario: Ajustar uma faixa
- **QUANDO** o Administrador muda a faixa de 0 ponto da SpO2 de "≥ 96" para "≥ 95" e a de 1 ponto de "94–95" para "93–94"
- **ENTÃO** as duas alterações são aceitas e auditadas, e a classificação passa a usar os valores novos

#### Scenario: Faixas sobrepostas
- **QUANDO** a alteração faria duas faixas da mesma SpO2 cobrirem o valor 95
- **ENTÃO** a alteração é recusada e nada muda

### Requirement: Valores iniciais dos parâmetros
Os parâmetros DEVEM nascer com os valores da baseline: `IDADE_MINIMA_IDOSO` 60, `IDADE_MAXIMA_CRIANCA` 11, `amarelas_por_ciclo` 2, `azuis_por_ciclo` 1, `CICLO_PRE_TRIAGEM_PRIORITARIOS` 2, `CICLO_PRE_TRIAGEM_NORMAIS` 1, `tamanho_previsao` 5, `INTERVALO_CHAMADA_SEGUNDOS` 30, `TENTATIVAS_CHAMADA` 3 e `HORAS_EXPIRACAO` 24, cada um dentro dos seus limites editáveis. A criação DEVE inserir só os parâmetros que faltam, sem sobrescrever valor alterado pelo Administrador. O fuso `America/Sao_Paulo` é fixo e NÃO DEVE existir como parâmetro.

#### Scenario: Ambiente sem parâmetros
- **QUANDO** a operação precisa de um parâmetro que ainda não existe
- **ENTÃO** ele é criado com o valor da baseline

#### Scenario: Valor alterado é mantido
- **QUANDO** o Administrador mudou `HORAS_EXPIRACAO` para 36 e a criação dos valores iniciais roda de novo
- **ENTÃO** o valor continua 36 e nenhum parâmetro é duplicado

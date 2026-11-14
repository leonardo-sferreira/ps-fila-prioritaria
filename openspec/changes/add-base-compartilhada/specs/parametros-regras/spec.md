## ADDED Requirements

### Requirement: Valores iniciais dos parâmetros
Os parâmetros DEVEM nascer com os valores da baseline: `IDADE_MINIMA_IDOSO` 60, `IDADE_MAXIMA_CRIANCA` 11, `amarelas_por_ciclo` 2, `azuis_por_ciclo` 1, `CICLO_PRE_TRIAGEM_PRIORITARIOS` 2, `CICLO_PRE_TRIAGEM_NORMAIS` 1, `tamanho_previsao` 5, `INTERVALO_CHAMADA_SEGUNDOS` 30, `TENTATIVAS_CHAMADA` 3 e `HORAS_EXPIRACAO` 24, cada um dentro dos seus limites editáveis. A criação DEVE inserir só os parâmetros que faltam, sem sobrescrever valor alterado pelo Administrador. O fuso `America/Sao_Paulo` é fixo e NÃO DEVE existir como parâmetro.

#### Scenario: Ambiente sem parâmetros
- **QUANDO** a operação precisa de um parâmetro que ainda não existe
- **ENTÃO** ele é criado com o valor da baseline

#### Scenario: Valor alterado é mantido
- **QUANDO** o Administrador mudou `HORAS_EXPIRACAO` para 36 e a criação dos valores iniciais roda de novo
- **ENTÃO** o valor continua 36 e nenhum parâmetro é duplicado

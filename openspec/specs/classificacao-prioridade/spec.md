# classificacao-prioridade Specification

## Purpose

Calcula o escore clínico da ficha (sintomas e sinais vitais), converte-o na cor Azul, Amarela ou Vermelha pela escala experimental da Rev. 2.1 e registra a condição prioritária e o ajuste manual justificado.

## Requirements

### Requirement: Escore clínico da ficha
O sistema DEVE calcular `escore_total` como a soma da `pontuacao` (1 a 3) de cada sintoma distinto da ficha, do catálogo ou digitado pela Recepção/Triagem, mais os pontos (0 a 3) de cada sinal vital medido, segundo as faixas configuradas. Um sintoma NÃO DEVE ser somado mais de uma vez. Idade, condição prioritária e gestação NÃO DEVEM somar pontos. O cálculo DEVE acontecer no Xano.

#### Scenario: Soma de sintomas e sinais vitais
- **QUANDO** a ficha tem sintomas de 2, 2 e 2 pontos e os sinais vitais somam 2 pontos
- **ENTÃO** `escore_total` é 8

#### Scenario: Sintoma digitado soma ao escore
- **QUANDO** a ficha tem febre (1) do catálogo, o sintoma digitado "dor no joelho" com 2 pontos e sinais vitais com 0 pontos
- **ENTÃO** `escore_total` é 3

#### Scenario: Sintoma digitado de 3 pontos
- **QUANDO** a ficha tem um sintoma digitado com 3 pontos e o restante soma 0
- **ENTÃO** a prioridade calculada é Vermelha pela exceção

#### Scenario: Sintomas sem pontos de sinais vitais
- **QUANDO** a ficha tem febre (1) e mal-estar (1) e todos os sinais vitais pontuam 0
- **ENTÃO** `escore_total` é 2

### Requirement: Pontuação dos sinais vitais
Para pacientes elegíveis à tabela adulta, cada sinal vital DEVE receber pontos pelas faixas configuradas, com extremos inclusivos e temperatura com uma casa decimal. Os valores iniciais DEVEM ser: PA sistólica 111–219 → 0, 101–110 → 1, 91–100 → 2, ≤90 ou ≥220 → 3; FC 51–90 → 0, 41–50 ou 91–110 → 1, 111–130 → 2, ≤40 ou ≥131 → 3; FR 12–20 → 0, 9–11 → 1, 21–24 → 2, ≤8 ou ≥25 → 3; temperatura 36,1–38,0 → 0, 35,1–36,0 ou 38,1–39,0 → 1, ≥39,1 → 2, ≤35,0 → 3; SpO₂ ≥96 → 0, 94–95 → 1, 92–93 → 2, ≤91 → 3. O escore NÃO DEVE ser rotulado como NEWS2.

#### Scenario: Bordas da frequência cardíaca
- **QUANDO** a FC é 90, 91, 110, 111, 130 ou 131 bpm
- **ENTÃO** recebe 0, 1, 1, 2, 2 e 3 pontos, respectivamente

#### Scenario: Bordas da PA sistólica
- **QUANDO** a PA sistólica é 90, 91, 100, 101, 110, 111, 219 ou 220 mmHg
- **ENTÃO** recebe 3, 2, 2, 1, 1, 0, 0 e 3 pontos, respectivamente

#### Scenario: Bordas da frequência respiratória
- **QUANDO** a FR é 8, 9, 11, 12, 20, 21, 24 ou 25 irpm
- **ENTÃO** recebe 3, 1, 1, 0, 0, 2, 2 e 3 pontos, respectivamente

#### Scenario: Bordas da temperatura
- **QUANDO** a temperatura é 35,0, 35,1, 36,0, 36,1, 38,0, 38,1, 39,0 ou 39,1 °C
- **ENTÃO** recebe 3, 1, 1, 0, 0, 1, 1 e 2 pontos, respectivamente

#### Scenario: Bordas da SpO₂
- **QUANDO** a SpO₂ é 91, 92, 93, 94, 95 ou 96 %
- **ENTÃO** recebe 3, 2, 2, 1, 1 e 0 pontos, respectivamente

### Requirement: Pontuação da glicemia
A glicemia é opcional. Quando medida, DEVE pontuar: abaixo de 54 mg/dL com sinais de gravidade → 3; abaixo de 54 sem sinais → 2; de 54 a 59 com sinais → 2; de 54 a 59 sem sinais → 1; 60 ou mais → 0 (convenção de simulação, sem regra de hiperglicemia). Glicemia não medida NÃO DEVE bloquear o cálculo nem somar pontos.

#### Scenario: Glicemia 53 sem sinais de gravidade
- **QUANDO** a glicemia é 53 mg/dL sem sinais de gravidade e não há outro item de 3 pontos
- **ENTÃO** a glicemia soma 2 pontos e não gera Vermelha por si só

#### Scenario: Glicemia 53 com sinais de gravidade
- **QUANDO** a glicemia é 53 mg/dL com sinais de gravidade
- **ENTÃO** a glicemia soma 3 pontos e a ficha é Vermelha pela exceção

#### Scenario: Glicemia não medida
- **QUANDO** os cinco sinais vitais obrigatórios foram informados e a glicemia não
- **ENTÃO** o cálculo automático acontece normalmente

### Requirement: Cor calculada pela escala experimental
A prioridade calculada DEVE ser Vermelha quando qualquer sintoma ou sinal vital da ficha tiver 3 pontos; caso contrário, Azul para `escore_total` de 0 a 4, Amarela de 5 a 9 e Vermelha a partir de 10. Os limiares 5 e 10 DEVEM ser configuráveis. A ficha DEVE guardar `escore_total`, o indicador de item crítico e a prioridade calculada.

#### Scenario: Limite 4/5
- **QUANDO** o escore é 4 sem item de 3 pontos
- **ENTÃO** a prioridade calculada é Azul; com escore 5 sem item de 3 pontos, é Amarela

#### Scenario: Limite 9/10
- **QUANDO** o escore é 9 sem item de 3 pontos
- **ENTÃO** a prioridade calculada é Amarela; com escore 10 sem item de 3 pontos, é Vermelha

#### Scenario: Sintoma isolado de 3 pontos
- **QUANDO** a ficha tem apenas convulsão em atividade (3) e sinais vitais com 0 pontos
- **ENTÃO** o escore é 3 e a prioridade calculada é Vermelha pela exceção

#### Scenario: Sinal vital crítico
- **QUANDO** a SpO₂ é 91 % e o restante soma 0
- **ENTÃO** a prioridade calculada é Vermelha pela exceção

#### Scenario: Temperatura de 2 pontos não é crítica
- **QUANDO** a temperatura é 39,1 °C e o restante soma 0
- **ENTÃO** a prioridade calculada é Azul

### Requirement: Cálculo bloqueado sem dados ou fora da tabela adulta
O cálculo automático DEVE acontecer somente para paciente com 16 anos ou mais (idade mínima configurável) que não esteja gestante, com PA sistólica, FC, FR, temperatura e SpO₂ informados e com ao menos um sintoma ou observação. Fora disso, a prioridade calculada DEVE ficar vazia, sem converter dado ausente em zero, e o sistema DEVE informar o motivo (sinal vital pendente ou tabela adulta não aplicável). Para menores de 16 anos e gestantes os sinais vitais DEVEM continuar registráveis, e a prioridade DEVE ser definida por classificação manual justificada.

#### Scenario: Sinal vital obrigatório ausente
- **QUANDO** a SpO₂ não foi informada
- **ENTÃO** a prioridade calculada fica vazia e a resposta indica a SpO₂ como pendente

#### Scenario: Paciente de 10 anos
- **QUANDO** o paciente tem 10 anos e todos os sinais vitais foram informados
- **ENTÃO** nenhuma faixa adulta é aplicada, a prioridade calculada fica vazia e a resposta exige classificação manual justificada

#### Scenario: Gestante
- **QUANDO** a ficha está marcada como gestante
- **ENTÃO** nenhuma faixa adulta é aplicada e a resposta exige classificação manual justificada

#### Scenario: Paciente com 16 anos
- **QUANDO** o paciente tem exatamente 16 anos, não está gestante e todos os sinais vitais obrigatórios foram informados
- **ENTÃO** o cálculo automático acontece

### Requirement: Condição prioritária
A ficha DEVE registrar a condição prioritária: GESTANTE quando marcada como gestante; senão IDOSO para idade a partir de 60 anos; senão CRIANCA para idade até 11 anos; senão NENHUMA. A idade DEVE ser calculada pela data de nascimento na data de chegada, no fuso `America/Sao_Paulo`, com limites configuráveis. A condição NÃO DEVE alterar o escore nem a cor.

#### Scenario: Idoso
- **QUANDO** o paciente tem 68 anos e não está gestante
- **ENTÃO** a condição prioritária é IDOSO e a cor continua sendo a calculada pelo escore

#### Scenario: Criança no limite
- **QUANDO** o paciente completa 12 anos no dia da chegada
- **ENTÃO** a condição prioritária não é CRIANCA

### Requirement: Ajuste manual da prioridade
A Recepção/Triagem DEVE poder definir a prioridade atual da ficha em `EM_TRIAGEM` ou `AGUARDANDO` como Vermelha, Amarela ou Azul, com justificativa obrigatória não vazia. O ajuste DEVE ser gravado em auditoria com evento `PRIORIDADE_ALTERADA`, valores anterior e novo, usuário e justificativa, na mesma transação. Quando existe prioridade calculada, a prioridade escolhida DEVE ser diferente dela. Quando não existe prioridade calculada, o ajuste é a classificação manual excepcional. O ajuste PODE vir na mesma operação de uma alteração clínica da ficha; nesse caso ele é aplicado depois do recálculo e não é descartado por ele. Em `AGUARDANDO`, o ajuste DEVE atualizar a senha conforme a capability `senha-comprovante`.

#### Scenario: Ajuste com justificativa
- **QUANDO** a Recepção/Triagem muda uma ficha calculada Azul para Amarela com justificativa
- **ENTÃO** a prioridade atual é Amarela, a calculada continua Azul e a auditoria registra a mudança e a justificativa

#### Scenario: Ajuste sem justificativa
- **QUANDO** a justificativa está vazia ou só tem espaços
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Classificação manual de inelegível
- **QUANDO** a ficha de uma gestante não tem prioridade calculada e a Recepção/Triagem define Amarela com justificativa
- **ENTÃO** a prioridade atual é Amarela e a auditoria registra a classificação manual

#### Scenario: Ajuste igual à calculada
- **QUANDO** a prioridade escolhida é igual à prioridade calculada
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Ajuste em ficha aguardando
- **QUANDO** a Recepção/Triagem muda para Vermelha, com justificativa, a ficha `AGUARDANDO` `A-CAR-001`
- **ENTÃO** a prioridade atual é Vermelha, a senha passa a `V-CAR-001` e a ficha continua `AGUARDANDO`

#### Scenario: Ficha fora da triagem
- **QUANDO** se tenta ajustar a prioridade de ficha que não está `EM_TRIAGEM` nem `AGUARDANDO`
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Perfil sem permissão
- **QUANDO** Médico, Administrador ou pessoa sem sessão válida tenta ajustar a prioridade
- **ENTÃO** o backend recusa sem alterar a ficha nem registrar auditoria

### Requirement: Recálculo descarta o ajuste manual
Qualquer alteração de sintomas, observação, sinais vitais ou gestação DEVE recalcular escore, item crítico, prioridade calculada e condição prioritária. A prioridade atual DEVE passar a ser a nova prioridade calculada (vazia quando o cálculo estiver bloqueado) e a justificativa de ajuste anterior DEVE ser descartada. A auditoria da alteração DEVE registrar a prioridade atual anterior.

#### Scenario: Ajuste descartado
- **QUANDO** a ficha tem prioridade atual ajustada para Amarela e a Recepção/Triagem altera um sinal vital
- **ENTÃO** a prioridade atual volta a ser a calculada, a justificativa é limpa e a auditoria guarda a Amarela anterior

#### Scenario: Recálculo para cálculo bloqueado
- **QUANDO** a gestação é marcada em ficha que tinha prioridade calculada
- **ENTÃO** a prioridade calculada e a atual ficam vazias até a classificação manual

### Requirement: Faixas e parâmetros configuráveis
As faixas de pontuação dos sinais vitais DEVEM ficar na tabela `faixa_sinal_vital`, com limite mínimo e máximo inclusivos e limites abertos representados sem valor arbitrário. Os limiares da escala (5 e 10), a idade mínima da tabela adulta (16), a idade de idoso (60) e a idade máxima de criança (11) DEVEM ficar na tabela `parametro`. A carga inicial DEVE ser idempotente e NÃO DEVE criar faixas para menores de 16 anos ou gestantes. Faixa ou parâmetro ausente DEVE bloquear o cálculo automático, sem assumir valor padrão.

#### Scenario: Carga repetida
- **QUANDO** a carga inicial é executada duas vezes
- **ENTÃO** cada faixa e parâmetro existe uma única vez

#### Scenario: Faixa ausente
- **QUANDO** um valor de sinal vital não se enquadra em nenhuma faixa configurada
- **ENTÃO** o cálculo automático é bloqueado e o motivo é informado

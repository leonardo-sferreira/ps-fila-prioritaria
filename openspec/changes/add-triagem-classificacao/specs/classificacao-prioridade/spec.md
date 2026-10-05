# Delta de especificação

## Purpose

Calcula automaticamente a cor de prioridade da ficha a partir dos sintomas e do fator de risco dos sinais vitais, identifica a condição prioritária e permite o ajuste manual justificado pela Recepção/Triagem.

## ADDED Requirements

### Requirement: Pontuação dos sinais vitais
O sistema DEVE atribuir de 0 a 3 pontos a cada sinal vital, conforme a tabela configurável de faixas. Os valores iniciais DEVEM ser:

| Parâmetro | 3 pontos | 2 pontos | 1 ponto | 0 pontos |
|---|---|---|---|---|
| PA sistólica (mmHg) | ≤ 90 ou ≥ 220 | 91–100 | 101–110 | 111–219 |
| FC (bpm) | ≤ 40 ou ≥ 131 | 111–130 | 41–50 ou 91–110 | 51–90 |
| FR (irpm) | ≤ 8 ou ≥ 25 | 21–24 | 9–11 | 12–20 |
| Temperatura (°C) | ≤ 35,0 | ≥ 39,1 | 35,1–36,0 ou 38,1–39,0 | 36,1–38,0 |
| SpO2 (%) | ≤ 91 | 92–93 | 94–95 | ≥ 96 |
| Glicemia (mg/dL) | > 400 ou < 54 com sinais de gravidade | 251–400, < 54 sem sinais de gravidade, 54–59 com sinais de gravidade | 181–250, 60–69, 54–59 sem sinais de gravidade | 70–180 ou não medida |

#### Scenario: Valores-limite da PA sistólica
- **QUANDO** a PA sistólica é 90, 91, 100, 101, 110, 111, 219 e 220
- **ENTÃO** a pontuação é, respectivamente, 3, 2, 2, 1, 1, 0, 0 e 3

#### Scenario: Valores-limite da FC
- **QUANDO** a FC é 40, 41, 50, 51, 90, 91, 110, 111, 130 e 131
- **ENTÃO** a pontuação é, respectivamente, 3, 1, 1, 0, 0, 1, 1, 2, 2 e 3

#### Scenario: Valores-limite da FR
- **QUANDO** a FR é 8, 9, 11, 12, 20, 21, 24 e 25
- **ENTÃO** a pontuação é, respectivamente, 3, 1, 1, 0, 0, 2, 2 e 3

#### Scenario: Valores-limite da temperatura
- **QUANDO** a temperatura é 35,0; 35,1; 36,0; 36,1; 38,0; 38,1; 39,0 e 39,1
- **ENTÃO** a pontuação é, respectivamente, 3, 1, 1, 0, 0, 1, 1 e 2

#### Scenario: Valores-limite da SpO2
- **QUANDO** a SpO2 é 91, 92, 93, 94, 95 e 96
- **ENTÃO** a pontuação é, respectivamente, 3, 2, 2, 1, 1 e 0

#### Scenario: Valores-limite da glicemia
- **QUANDO** a glicemia é 53 com sinais de gravidade, 53 sem, 54 com, 59 sem, 60, 69, 70, 180, 181, 250, 251, 400 e 401
- **ENTÃO** a pontuação é, respectivamente, 3, 2, 2, 1, 1, 1, 0, 0, 1, 1, 2, 2 e 3

### Requirement: Escore e classificação de risco
O escore total DEVE somar os pontos de todos os sintomas selecionados (cada qual de 1 a 3) aos pontos de todos os sinais vitais medidos. Não há máximo fixo de 18. Os limiares iniciais permanecem moderado a partir de 3 e alto a partir de 6, configuráveis; qualquer item clínico isolado com 3 pontos eleva o risco a alto. Baixo → Azul, moderado → Amarela, alto → Vermelha.

#### Scenario: Valores-limite do escore
- **QUANDO** a soma de sintomas e sinais vitais resulta em 2, 3, 5 e 6, sem nenhum item isolado com 3 pontos
- **ENTÃO** a classificação é, respectivamente, baixo, moderado, moderado e alto

#### Scenario: Soma de sintomas e sinais vitais
- **QUANDO** uma ficha tem sintomas de 2 e 1 pontos e sinais vitais que somam 2
- **ENTÃO** o escore total é 5 e a classificação é moderada com os limiares iniciais

#### Scenario: Item clínico isolado com 3 pontos
- **QUANDO** um sintoma ou sinal vital recebe 3 pontos, mesmo que os demais componentes somem 0
- **ENTÃO** o escore inclui esse item e a classificação é alto

### Requirement: Prioridade calculada
A prioridade calculada DEVE corresponder diretamente à classificação do escore total (baixo → Azul, moderado → Amarela, alto → Vermelha). Sintomas não têm cor/prioridade própria. Se houver apenas observação, os pontos de sintomas são zero e a classificação usa os sinais vitais. A prioridade calculada DEVE ser refeita sempre que sintomas ou sinais vitais mudarem.

#### Scenario: Vários sintomas entram na soma
- **QUANDO** a ficha tem "Tosse sem falta de ar" (1 ponto) e "Falta de ar" (2 pontos), além de sinais vitais que somam 2
- **ENTÃO** os sintomas somam 3, o escore total é 5 e a prioridade calculada é Amarela

#### Scenario: Recálculo após mudança de sinais vitais
- **QUANDO** a SpO2 de uma ficha com prioridade calculada Azul é corrigida para 91
- **ENTÃO** a prioridade calculada passa a Vermelha

### Requirement: Condição prioritária
O sistema DEVE marcar a ficha com condição prioritária quando o paciente tiver idade maior ou igual à idade mínima de idoso, idade menor ou igual à idade máxima de criança (idade em anos completos na data de chegada) ou quando a ficha estiver marcada como gestante. A condição prioritária NÃO DEVE alterar a cor (RN11).

#### Scenario: Valores-limite de idade
- **QUANDO** com os parâmetros iniciais (60 e 11), o paciente tem 11, 12, 59 e 60 anos completos na data de chegada
- **ENTÃO** a condição prioritária é, respectivamente, sim (criança), não, não e sim (idoso)

#### Scenario: Cor preservada
- **QUANDO** um paciente idoso tem prioridade calculada Azul
- **ENTÃO** a ficha fica com prioridade Azul e condição prioritária "idoso"

### Requirement: Destino pediátrico sem substituir a classificação
A idade menor ou igual a `idade_maxima_crianca` DEVE permitir direcionamento à especialidade Pediatria na change de direcionamento, sem eliminar sintomas/sinais vitais do cálculo nem substituir a classificação calculada. A condição criança e os demais marcadores prioritários reordenam somente dentro da mesma classificação.

#### Scenario: Criança mantém cálculo clínico
- **QUANDO** uma criança dentro do limite configurado tem sintomas de 2 pontos e sinais vitais que somam 1
- **ENTÃO** o escore total é 3, a classificação é moderada/Amarela e o destino clínico pode ser Pediatria

### Requirement: Prioridade atual e ajuste manual
A ficha DEVE guardar a prioridade calculada e a prioridade atual, que é a usada na fila. A prioridade atual é igual à calculada, a não ser que a Recepção/Triagem a ajuste. O ajuste DEVE exigir justificativa de ao menos 10 caracteres, ser permitido em EM_TRIAGEM ou AGUARDANDO e gerar auditoria com valor anterior, valor novo e justificativa (RF10, RN09). Quando sintomas ou sinais vitais mudarem, a prioridade atual DEVE voltar a ser igual à nova prioridade calculada, e o descarte do ajuste anterior DEVE ser auditado.

#### Scenario: Ajuste justificado
- **QUANDO** a Recepção/Triagem muda a prioridade de Amarela para Vermelha com a justificativa "Paciente com piora visível durante a espera"
- **ENTÃO** a prioridade atual passa a Vermelha, a calculada continua Amarela e a auditoria registra a mudança com a justificativa

#### Scenario: Ajuste sem justificativa
- **QUANDO** a Recepção/Triagem tenta mudar a prioridade sem justificativa ou com menos de 10 caracteres
- **ENTÃO** o sistema recusa e a prioridade atual não muda

#### Scenario: Ajuste em ficha chamada
- **QUANDO** a Recepção/Triagem tenta ajustar a prioridade de uma ficha CHAMADO
- **ENTÃO** o sistema recusa o ajuste

#### Scenario: Nova classificação descarta o ajuste
- **QUANDO** uma ficha com ajuste manual para Vermelha tem os sintomas alterados e a nova prioridade calculada é Amarela
- **ENTÃO** a prioridade atual passa a Amarela e a auditoria registra o descarte do ajuste

### Requirement: Configuração do fator de risco
O Administrador DEVE poder consultar e alterar as faixas de pontuação e os limiares de risco moderado e alto. Para cada sinal vital, as faixas NÃO DEVEM se sobrepor nem deixar lacunas dentro da faixa plausível, e os pontos DEVEM estar entre 0 e 3. Os limiares DEVEM ser inteiros positivos, com o moderado menor que o alto; não há teto de escore 18. As alterações DEVEM ser auditadas e valer apenas para classificações feitas depois delas.

#### Scenario: Alteração válida de limiar
- **QUANDO** o Administrador altera o limiar de risco alto de 6 para 7
- **ENTÃO** um escore 6 sem parâmetro isolado com 3 pontos passa a ser classificado como moderado nas próximas classificações

#### Scenario: Faixas sobrepostas
- **QUANDO** o Administrador define para a FC as faixas 51–90 (0 pontos) e 85–110 (1 ponto)
- **ENTÃO** o sistema recusa e informa a sobreposição

#### Scenario: Limiares incoerentes
- **QUANDO** o Administrador define o limiar moderado igual ou maior que o alto
- **ENTÃO** o sistema recusa a alteração

#### Scenario: Não administrador tenta alterar
- **QUANDO** um usuário Recepção/Triagem tenta alterar uma faixa
- **ENTÃO** o backend responde como acesso negado

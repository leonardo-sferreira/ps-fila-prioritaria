# Delta de especificação

## MODIFIED Requirements

### Requirement: Sinais vitais e gestação da ficha
A Recepção/Triagem DEVE poder registrar e editar, na ficha em `EM_TRIAGEM` ou `AGUARDANDO`, PA sistólica (mmHg), FC (bpm), FR (irpm), temperatura (°C, uma casa decimal), SpO₂ (%), glicemia (mg/dL, opcional) com indicador de sinais de gravidade, e a marcação de gestante. O envio DEVE ser tratado como o conjunto final desses campos; campo enviado vazio DEVE ser gravado como não medido. Valores fora dos limites de digitação aceitos (PA 40–300, FC 20–250, FR 4–80, temperatura 25,0–45,0, SpO₂ 50–100, glicemia 10–1500) ou com precisão maior que a prevista DEVEM ser recusados sem alterar a ficha. Qualquer alteração DEVE disparar o recálculo da classificação; em `AGUARDANDO`, também a reavaliação de destino e senha definida na capability `direcionamento`.

#### Scenario: Registro completo
- **QUANDO** a Recepção/Triagem informa os cinco sinais vitais obrigatórios e a glicemia
- **ENTÃO** a ficha guarda os valores e devolve o escore e a prioridade recalculados

#### Scenario: Valor impossível
- **QUANDO** a SpO₂ informada é 120
- **ENTÃO** o backend recusa e nenhum campo da ficha é alterado

#### Scenario: Temperatura com duas casas decimais
- **QUANDO** a temperatura informada é 36,05
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Campo limpo
- **QUANDO** a Recepção/Triagem apaga a FC já registrada
- **ENTÃO** a FC passa a não medida e o cálculo automático fica bloqueado até ser informada

#### Scenario: Ficha fora da triagem
- **QUANDO** se tenta alterar sinais vitais de ficha que não está `EM_TRIAGEM` nem `AGUARDANDO`
- **ENTÃO** o backend recusa sem alterar a ficha

### Requirement: Sintoma digitado na ficha
Além dos sintomas do catálogo, a Recepção/Triagem DEVE poder registrar na ficha em `EM_TRIAGEM` ou `AGUARDANDO` sintomas digitados que não estão no catálogo, cada um com descrição de 3 a 80 caracteres (após `trim`) e pontuação inteira de 1 a 3. O envio DEVE ser tratado como a lista final de sintomas digitados da ficha, com no máximo 10 itens. O sintoma digitado DEVE valer somente para aquela ficha: NÃO DEVE entrar no catálogo nem aparecer em `GET /sintomas`. Ele DEVE contar como sintoma para a RN04, entrar no escore e disparar o recálculo e a auditoria como os sintomas do catálogo. Descrição repetida na mesma ficha ou igual ao nome de um sintoma do catálogo, comparando sem diferenciar maiúsculas e acentos, DEVE ser recusada.

#### Scenario: Registro de sintoma digitado
- **QUANDO** a Recepção/Triagem adiciona "dor no joelho" com 2 pontos
- **ENTÃO** a ficha guarda o sintoma digitado, o escore inclui os 2 pontos e a auditoria registra a alteração

#### Scenario: Sintoma digitado atende a RN04
- **QUANDO** a ficha tem apenas um sintoma digitado, sem sintoma do catálogo e sem observação
- **ENTÃO** o salvamento é aceito

#### Scenario: Pontuação inválida
- **QUANDO** o sintoma digitado vem com pontuação 0, 4 ou sem pontuação
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Descrição curta ou longa demais
- **QUANDO** a descrição tem menos de 3 ou mais de 80 caracteres após `trim`
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Nome igual a sintoma do catálogo
- **QUANDO** a descrição digitada é "FEBRE" e o catálogo tem "Febre"
- **ENTÃO** o backend recusa e a ficha não é alterada

#### Scenario: Repetido na mesma ficha
- **QUANDO** a lista enviada tem "Dor no joelho" e "dor no joelho"
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Mais de 10 sintomas digitados
- **QUANDO** a lista enviada tem 11 sintomas digitados
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Não entra no catálogo
- **QUANDO** outra ficha consulta `GET /sintomas` depois do registro de um sintoma digitado
- **ENTÃO** o sintoma digitado não aparece na lista

#### Scenario: Sintoma digitado em ficha aguardando
- **QUANDO** a Recepção/Triagem adiciona um sintoma digitado de 3 pontos a uma ficha `AGUARDANDO`
- **ENTÃO** o escore e a prioridade são recalculados, mas a especialidade de destino não muda por causa dele

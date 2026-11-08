## ADDED Requirements

### Requirement: Sinais vitais e gestação da ficha
A Recepção/Triagem DEVE poder registrar e editar, na ficha em `EM_TRIAGEM`, PA sistólica (mmHg), FC (bpm), FR (irpm), temperatura (°C, uma casa decimal), SpO₂ (%), glicemia (mg/dL, opcional) com indicador de sinais de gravidade, e a marcação de gestante. O envio DEVE ser tratado como o conjunto final desses campos; campo enviado vazio DEVE ser gravado como não medido. Valores fora dos limites de digitação aceitos (PA 40–300, FC 20–250, FR 4–80, temperatura 25,0–45,0, SpO₂ 50–100, glicemia 10–1500) ou com precisão maior que a prevista DEVEM ser recusados sem alterar a ficha. Qualquer alteração DEVE disparar o recálculo da classificação.

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
- **QUANDO** se tenta alterar sinais vitais de ficha que não está `EM_TRIAGEM`
- **ENTÃO** o backend recusa sem alterar a ficha

### Requirement: Sintoma digitado na ficha
Além dos sintomas do catálogo, a Recepção/Triagem DEVE poder registrar na ficha em `EM_TRIAGEM` sintomas digitados que não estão no catálogo, cada um com descrição de 3 a 80 caracteres (após `trim`) e pontuação inteira de 1 a 3. O envio DEVE ser tratado como a lista final de sintomas digitados da ficha, com no máximo 10 itens. O sintoma digitado DEVE valer somente para aquela ficha: NÃO DEVE entrar no catálogo nem aparecer em `GET /sintomas`. Ele DEVE contar como sintoma para a RN04, entrar no escore e disparar o recálculo e a auditoria como os sintomas do catálogo. Descrição repetida na mesma ficha ou igual ao nome de um sintoma do catálogo, comparando sem diferenciar maiúsculas e acentos, DEVE ser recusada.

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

### Requirement: Acesso autorizado e auditoria da ficha
`GET /fichas/{id}`, `PATCH /fichas/{id}`, o ajuste de prioridade e `GET /sintomas` DEVEM exigir sessão válida do perfil Recepção/Triagem, verificada no backend. Cada alteração de sintomas, observação, sinais vitais ou gestação DEVE gerar registro em `historico_alteracao` na mesma transação, com usuário, valores anterior e novo e a prioridade atual anterior.

#### Scenario: Sem sessão
- **QUANDO** alguém consulta ou altera uma ficha sem sessão válida
- **ENTÃO** o backend recusa sem retornar dados da ficha nem alterá-la

#### Scenario: Perfil sem permissão
- **QUANDO** Médico ou Administrador tenta alterar sinais vitais
- **ENTÃO** o backend recusa sem alterar a ficha nem registrar auditoria

#### Scenario: Auditoria da alteração clínica
- **QUANDO** a Recepção/Triagem altera sinais vitais
- **ENTÃO** a auditoria registra o usuário, os valores anteriores e novos e a prioridade atual anterior

## MODIFIED Requirements

### Requirement: Nova chegada e ficha não finalizada
Cada nova chegada DEVE gerar nova ficha e preservar o histórico. Uma segunda ficha NÃO DEVE ser criada se o paciente já tiver ficha em `EM_TRIAGEM`, `AGUARDANDO` ou `CHAMADO`. Quando a ficha existente está `EM_TRIAGEM` e a abertura não informa ticket, o sistema DEVE devolver essa mesma ficha, indicando que já existia, para a Recepção/Triagem continuar a triagem (decisão do PO, 08/11/2026), sem criar ficha nem registrar novo cadastro. Quando a ficha existente está `AGUARDANDO` ou `CHAMADO`, ou a abertura informa ticket, a operação DEVE ser recusada com mensagem clara. Fichas em `ATENDIDO`, `DESISTENCIA` ou `CANCELADO` são finais e NÃO DEVEM impedir nova chegada. O sistema NÃO DEVE criar estados adicionais para essa regra.

#### Scenario: Ficha não finalizada bloqueia nova abertura
- **QUANDO** o paciente possui ficha em `AGUARDANDO` ou `CHAMADO` e uma nova ficha é solicitada
- **ENTÃO** nenhuma segunda ficha é criada e a Recepção/Triagem vê que o paciente já está na fila

#### Scenario: Ficha em triagem é reaberta
- **QUANDO** o paciente possui ficha em `EM_TRIAGEM` e a Recepção/Triagem clica em "Continuar" sem ticket
- **ENTÃO** a mesma ficha é aberta para edição, sem criar outra nem registrar novo cadastro na auditoria

#### Scenario: Chegada após estado final
- **QUANDO** a última ficha do paciente está em `ATENDIDO`, `DESISTENCIA` ou `CANCELADO` e ocorre nova chegada
- **ENTÃO** uma nova ficha é criada e a ficha finalizada permanece no histórico


### Requirement: Consulta da ficha para edição
`GET /fichas/{id}` DEVE retornar os dados necessários para editar e classificar a ficha: paciente relacionado com idade, observação geral, sintomas associados do catálogo, sintomas digitados com pontuação, sinais vitais, glicemia e indicador de gravidade, gestação, condição prioritária, escore total com a parte de sintomas e a de sinais vitais, pontos de cada sinal vital, indicador de item crítico, prioridade calculada, prioridade atual, justificativa do ajuste e, quando o cálculo estiver bloqueado, a lista de pendências. A resposta NÃO DEVE expor `ficha_sintoma.observacao` como campo editável da Triagem.

#### Scenario: Recarregar ficha preenchida
- **QUANDO** a Recepção/Triagem consulta uma ficha com sintomas e observação
- **ENTÃO** recebe a mesma coleção de sintomas e a observação geral persistida

#### Scenario: Recarregar ficha classificada
- **QUANDO** a Recepção/Triagem consulta uma ficha com sinais vitais e prioridade ajustada
- **ENTÃO** recebe os sinais vitais, o escore detalhado, a prioridade calculada, a atual e a justificativa persistidas

#### Scenario: Recarregar ficha com cálculo bloqueado
- **QUANDO** a ficha não tem SpO₂ informada
- **ENTÃO** a resposta traz prioridade calculada vazia e a SpO₂ na lista de pendências

## REMOVED Requirements

### Requirement: Etapa posterior de dados clínicos da ficha
**Reason**: Sinais vitais, glicemia e gestação passam a ser implementados nesta change (cancelamento continua fora).
**Migration**: Ver "Sinais vitais e gestação da ficha" e a capability `classificacao-prioridade`.

### Requirement: Integrações futuras de autorização e auditoria
**Reason**: Autenticação (`verificar_acesso`) e auditoria (`registrar_alteracao`) já existem e passam a ser usadas na ficha.
**Migration**: Ver "Acesso autorizado e auditoria da ficha".

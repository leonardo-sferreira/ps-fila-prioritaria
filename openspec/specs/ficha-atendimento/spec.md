# ficha-atendimento Specification

## Purpose

Registra a passagem do paciente pelo PS desde a abertura da ficha até as etapas clínicas posteriores, começando por sintomas e queixa geral editáveis.

## Requirements

### Requirement: Abertura de ficha na fatia atual
O sistema DEVE abrir `Ficha_Atendimento` para paciente existente, com `status=EM_TRIAGEM` e `chegada_em` definido pelo backend. `ticket_id` PODE ser informado, mas a abertura NÃO DEVE depender de Totem ou ticket. `POST /fichas` PODE criar a ficha inicialmente sem sintomas e sem observação; RN04 não é exigida na abertura. Quando informado, o ticket DEVE estar chamado, ter presença confirmada e ser válido para a operação; sua associação, passagem a ATENDIDO e auditoria DEVEM ser atômicas com a abertura. Qualquer operador autorizado da Recepção/Triagem PODE concluir a abertura, independentemente de quem chamou.

#### Scenario: Abertura sem ticket
- **QUANDO** a Recepção/Triagem abre ficha para paciente existente sem ticket
- **ENTÃO** a ficha é criada em `EM_TRIAGEM` com horário definido pelo backend

#### Scenario: Abertura inicialmente vazia
- **QUANDO** a Recepção/Triagem abre uma ficha sem sintomas e sem observação
- **ENTÃO** a ficha permanece em `EM_TRIAGEM` e pode ser preenchida posteriormente sem criar estado adicional

#### Scenario: Paciente inexistente
- **QUANDO** alguém tenta abrir ficha para paciente inexistente
- **ENTÃO** nenhuma ficha é criada

#### Scenario: Abertura com ticket chamado
- **QUANDO** a Recepção/Triagem abre ficha para paciente identificado com ticket chamado válido
- **ENTÃO** a ficha referencia o ticket e este passa a ATENDIDO na mesma operação

#### Scenario: Ticket inválido ou ficha ativa existente
- **QUANDO** o ticket não está chamado com presença confirmada ou o paciente já tem ficha não finalizada
- **ENTÃO** nenhuma ficha adicional é criada e o ticket não muda de estado

### Requirement: Responsável temporariamente ausente
Enquanto `add-autenticacao-perfis` não estiver implementada, `aberta_por` PODE ser nulo na abertura desta fatia. O sistema NÃO DEVE usar usuário artificial, ID fixo, token falso ou autenticação simulada. Após a autenticação ser implementada, essa integração DEVE ser reavaliada; esta tolerância temporária NÃO define o contrato permanente do domínio.

#### Scenario: Abertura sem autenticação disponível
- **QUANDO** uma ficha é aberta na fatia atual sem usuário autenticado disponível
- **ENTÃO** `aberta_por` permanece nulo sem criar usuário ou credencial artificial

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

### Requirement: Consulta de sintomas ativos
`GET /sintomas` DEVE retornar somente sintomas ativos necessários à triagem, incluindo identificador, nome, descrição quando existir, grupo e `pontuacao` inteira entre 1 e 3. Sintoma NÃO DEVE possuir cor ou prioridade fixa; a classificação usa a soma das pontuações selecionadas (capability `classificacao-prioridade`).

#### Scenario: Catálogo utilizável
- **QUANDO** a Recepção/Triagem consulta os sintomas
- **ENTÃO** recebe apenas sintomas ativos com grupo e pontuação numérica, sem `prioridade_padrao`

#### Scenario: Sintoma inativo
- **QUANDO** um sintoma está inativo
- **ENTÃO** ele não é retornado para seleção em nova ficha

### Requirement: Carga atual do catálogo de sintomas
Nesta fatia, o sistema DEVE adequar o schema de Sintoma e carregar de forma idempotente o catálogo acadêmico existente, com nome, descrição quando existente, grupo, `pontuacao` de 1 a 3 e situação ativa. Uma segunda carga NÃO DEVE duplicar registros. `docs/domain-model.md` é somente a fonte existente do catálogo e não é alterado nesta change.

#### Scenario: Carga repetida do catálogo
- **QUANDO** a carga oficial é executada duas vezes no ambiente com a tabela inicialmente vazia
- **ENTÃO** os sintomas ativos ficam disponíveis para `GET /sintomas` sem duplicação e sem dados inventados

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

### Requirement: Sintomas e observação geral editáveis
`PATCH /fichas/{id}` DEVE aceitar parcialmente `sintoma_ids` e `observacao`. Quando enviado, `sintoma_ids` representa a coleção final: IDs novos criam vínculos, IDs ausentes removem vínculos e IDs existentes são preservados, sem repetição. Campo omitido NÃO DEVE alterar seu componente. A observação editável é exclusivamente `ficha_atendimento.observacao`.

#### Scenario: Substituir coleção de sintomas
- **QUANDO** a ficha possui sintomas 1 e 5 e recebe `sintoma_ids` 5 e 9
- **ENTÃO** o vínculo com 1 é removido, 5 é preservado e 9 é criado sem duplicidade

#### Scenario: Alterar somente observação
- **QUANDO** a ficha possui sintomas e recebe PATCH apenas com nova observação
- **ENTÃO** seus sintomas são preservados e a observação geral é atualizada

#### Scenario: Alterar somente sintomas
- **QUANDO** a ficha possui observação não vazia e recebe PATCH apenas com `sintoma_ids`
- **ENTÃO** a observação é preservada e a coleção de sintomas é atualizada de forma coerente

#### Scenario: Sintoma inativo ou inexistente
- **QUANDO** o PATCH contém sintoma inativo ou inexistente
- **ENTÃO** nenhuma alteração parcial é persistida

### Requirement: Preenchimento válido da ficha
Quando PATCH altera sintomas e/ou observação, o estado resultante DEVE conter ao menos um sintoma ou observação geral não vazia após trim (RN04). A validação DEVE considerar os valores persistidos dos componentes omitidos. A ficha continua em `EM_TRIAGEM` enquanto é preenchida; NÃO DEVE existir status `RASCUNHO`.

#### Scenario: Somente sintomas
- **QUANDO** a ficha recebe um ou mais sintomas e observação vazia
- **ENTÃO** o preenchimento é aceito

#### Scenario: Somente observação
- **QUANDO** a ficha recebe observação geral não vazia e coleção de sintomas vazia
- **ENTÃO** o preenchimento é aceito

#### Scenario: Componentes preservados no estado resultante
- **QUANDO** PATCH altera somente sintomas ou somente observação e o outro componente persistido satisfaz RN04
- **ENTÃO** o preenchimento é aceito considerando o estado resultante completo

#### Scenario: Remover último conteúdo válido
- **QUANDO** PATCH remove o último sintoma sem observação resultante ou limpa a última observação sem sintomas resultantes
- **ENTÃO** nenhuma alteração inválida é persistida

#### Scenario: Observação somente com whitespace
- **QUANDO** PATCH informa somente whitespace como observação e não há sintomas resultantes
- **ENTÃO** nenhuma alteração inválida é persistida

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

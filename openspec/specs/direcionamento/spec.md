# direcionamento Specification

## Purpose
Direciona automaticamente cada ficha para a especialidade indicada pelos sintomas, com desempate definido, mantendo o destino clínico independente da especialidade de referência e da disponibilidade do Médico, e conclui a triagem com a confirmação.

## Requirements

### Requirement: Especialidade de destino pelos sintomas
O sistema DEVE determinar a especialidade de destino da ficha pelos sintomas do catálogo selecionados e pela relação `sintoma_especialidade`. Paciente com idade até a máxima de criança (inicialmente 11 anos) na data de chegada DEVE ir para Pediatria, antes de qualquer outro critério e sem alterar escore ou cor. Para os demais, cada especialidade ligada a algum sintoma da ficha é candidata, e o desempate DEVE seguir esta ordem: 1º maior pontuação individual de sintoma ligado à especialidade; 2º maior soma dos pontos dos sintomas ligados a ela (um mesmo sintoma pode contar para várias candidatas); 3º menor número de fichas `AGUARDANDO` na especialidade; 4º menor ID da especialidade. A cor da ficha e a disponibilidade de Médicos NÃO DEVEM ser usadas no desempate.

#### Scenario: Sintoma de uma especialidade
- **QUANDO** a ficha de um adulto contém "Dor ou pressão no peito" (2, Cardiologia)
- **ENTÃO** o destino é Cardiologia

#### Scenario: Maior pontuação individual vence
- **QUANDO** a ficha de um adulto tem "Palpitações" (2, Cardiologia) e "Convulsão em atividade" (3, Neurologia)
- **ENTÃO** o destino é Neurologia

#### Scenario: Empate na maior pontuação decidido pela soma
- **QUANDO** a ficha de um adulto tem "Dor ou pressão no peito" (2) e "Palpitações" (2), de Cardiologia, e "Falta de ar" (2), de Clínica Geral
- **ENTÃO** o destino é Cardiologia, pela soma 4 contra 2

#### Scenario: Empate decidido pela fila menor
- **QUANDO** as candidatas empatam na maior pontuação e na soma, e uma tem menos fichas `AGUARDANDO`
- **ENTÃO** o destino é a especialidade com a fila menor

#### Scenario: Empate total decidido pelo menor ID
- **QUANDO** as candidatas empatam em todos os critérios anteriores
- **ENTÃO** o destino é a especialidade de menor ID

#### Scenario: Criança vai para Pediatria
- **QUANDO** o paciente tem 11 anos na data de chegada e a ficha tem "Convulsão em atividade" (Neurologia)
- **ENTÃO** o destino é Pediatria e a cor continua a da classificação

#### Scenario: Doze anos segue os sintomas
- **QUANDO** o paciente tem 12 anos na data de chegada e a ficha tem "Convulsão em atividade"
- **ENTÃO** o destino é Neurologia

### Requirement: Especialidade padrão sem sintoma do catálogo
Quando a ficha de paciente acima da idade de criança não tiver nenhum sintoma do catálogo ligado a especialidade (só sintomas digitados, só observação, ou ambos), o destino DEVE ser a especialidade padrão configurada no parâmetro `ESPECIALIDADE_PADRAO` (inicialmente Clínica Geral). Sintomas digitados NÃO DEVEM influir no destino, embora continuem no escore.

#### Scenario: Ficha só com observação
- **QUANDO** a ficha de um adulto tem apenas observação
- **ENTÃO** o destino é Clínica Geral

#### Scenario: Ficha só com sintoma digitado
- **QUANDO** a ficha de um adulto tem apenas o sintoma digitado "dor no joelho"
- **ENTÃO** o destino é Clínica Geral

#### Scenario: Sintoma digitado não muda o destino
- **QUANDO** a ficha de um adulto tem "Fratura exposta" (Ortopedia) e um sintoma digitado de 3 pontos
- **ENTÃO** o destino é Ortopedia

#### Scenario: Especialidade padrão não configurada
- **QUANDO** é preciso usar a especialidade padrão e o parâmetro não existe ou aponta para especialidade inativa
- **ENTÃO** a confirmação é recusada sem alterar a ficha

### Requirement: Destino independente de elegibilidade médica
A especialidade de destino da ficha DEVE permanecer a indicada pelos sintomas, independentemente da especialidade de referência dos Médicos ou da disponibilidade momentânea. O sistema NÃO DEVE substituir o destino por alternativa apenas porque não há Médico elegível naquele instante. A elegibilidade e atribuição operacional a Médico pertencem a `add-fila-chamada-medico`.

#### Scenario: Médico de outra especialidade atende
- **QUANDO** a ficha está na fila de Cardiologia e há um Médico elegível cuja especialidade de referência é Clínica Geral
- **ENTÃO** a ficha permanece na fila de Cardiologia e pode ser distribuída a esse Médico

### Requirement: Fila correta sem Médico elegível imediato
Se nenhum Médico estiver elegível, a ficha DEVE continuar na fila de sua especialidade clínica, sem fallback para outra especialidade e sem exigir confirmação extra.

#### Scenario: Fila aguarda elegibilidade
- **QUANDO** não há Médico elegível no momento da confirmação da triagem
- **ENTÃO** a ficha entra na fila da especialidade indicada pelos sintomas e não é redirecionada para alternativa

### Requirement: Confirmação da triagem
A Recepção/Triagem DEVE concluir a triagem com a ação "Confirmar e gerar senha", que exige ficha `EM_TRIAGEM` com prioridade atual definida (calculada ou ajustada manualmente) e com ao menos um sintoma ou observação, define a especialidade de destino, gera a senha e leva a ficha a `AGUARDANDO`, tudo numa única operação. A especialidade sugerida e a atribuída DEVEM ser gravadas iguais ao destino. A confirmação DEVE registrar auditoria com destino, senha e prioridade. O backend DEVE exigir sessão do perfil Recepção/Triagem. A ficha DEVE mostrar, antes da confirmação, a especialidade de destino prevista.

#### Scenario: Confirmação bem-sucedida
- **QUANDO** a Recepção/Triagem confirma uma ficha `EM_TRIAGEM` Amarela com "Dor ou pressão no peito"
- **ENTÃO** a ficha passa a `AGUARDANDO` em Cardiologia com senha `A-CAR-NNN`, e a auditoria registra a confirmação

#### Scenario: Ficha sem cor
- **QUANDO** a Recepção/Triagem confirma uma ficha sem prioridade atual (sinal vital faltando ou gestante sem classificação manual)
- **ENTÃO** o backend recusa, a ficha continua `EM_TRIAGEM` e nenhuma senha é gerada

#### Scenario: Ficha já confirmada
- **QUANDO** se tenta confirmar uma ficha que não está `EM_TRIAGEM`
- **ENTÃO** o backend recusa sem gerar nova senha

#### Scenario: Prévia do destino
- **QUANDO** a Recepção/Triagem abre uma ficha `EM_TRIAGEM`
- **ENTÃO** a tela mostra a especialidade para onde a ficha irá se confirmada agora

#### Scenario: Perfil sem permissão
- **QUANDO** Médico, Administrador ou pessoa sem sessão válida tenta confirmar uma triagem
- **ENTÃO** o backend recusa sem alterar a ficha

### Requirement: Carga inicial de especialidades e ligações
O sistema DEVE carregar de forma idempotente as especialidades Cardiologia (CAR), Clínica Geral (CLI), Neurologia (NEU), Ortopedia (ORT) e Pediatria (PED), a ligação de cada sintoma do catálogo de `docs/domain-model.md` à sua especialidade de destino e o parâmetro `ESPECIALIDADE_PADRAO` apontando para Clínica Geral. Executar a carga de novo NÃO DEVE duplicar registros nem sobrescrever o que já existe.

#### Scenario: Carga repetida
- **QUANDO** a carga é executada duas vezes
- **ENTÃO** cada especialidade, ligação e parâmetro existe uma única vez

### Requirement: Reavaliação da ficha em AGUARDANDO
A Recepção/Triagem DEVE poder alterar sintomas do catálogo, sintomas digitados, observação, sinais vitais, gestação e ajuste manual da prioridade de uma ficha em `AGUARDANDO`. Cada alteração DEVE, numa única operação: recalcular a classificação pelas regras vigentes; refazer o destino pelo requisito "Especialidade de destino pelos sintomas" e pela especialidade padrão, sem contar a própria ficha no critério de fila; atualizar a especialidade sugerida e a atribuída; e atualizar a senha conforme o requisito "Troca de senha na reavaliação". A ficha DEVE continuar em `AGUARDANDO` com o mesmo `chegada_em`. Se o resultado ficar sem prioridade atual, a alteração DEVE ser recusada sem mudar nada, informando as pendências, a menos que a mesma operação traga ajuste manual válido com justificativa. A auditoria da alteração DEVE registrar também a especialidade e a senha anteriores e novas. Fichas em `CHAMADO`, `ATENDIDO`, `DESISTENCIA` ou `CANCELADO` NÃO DEVEM ser alteradas. O backend DEVE exigir sessão do perfil Recepção/Triagem.

#### Scenario: Piora muda a cor
- **QUANDO** uma ficha `AGUARDANDO` Amarela em Cardiologia recebe SpO₂ que eleva o cálculo para Vermelha
- **ENTÃO** a prioridade atual passa a Vermelha, a ficha continua em Cardiologia e `AGUARDANDO`, e `chegada_em` não muda

#### Scenario: Novo sintoma muda a especialidade
- **QUANDO** uma ficha `AGUARDANDO` de adulto em Cardiologia com "Palpitações" (2) recebe "Convulsão em atividade" (3)
- **ENTÃO** a especialidade sugerida e a atribuída passam a Neurologia e a auditoria registra Cardiologia como anterior

#### Scenario: Própria ficha fora do critério de fila
- **QUANDO** a reavaliação empata duas candidatas até a soma, e a ficha reavaliada é a única `AGUARDANDO` em uma delas
- **ENTÃO** o critério de fila compara as filas sem contar a própria ficha

#### Scenario: Edição deixa a ficha sem cor
- **QUANDO** a gestação é marcada em ficha `AGUARDANDO` sem ajuste manual na mesma operação
- **ENTÃO** o backend recusa, informa as pendências e a ficha, a senha e a auditoria ficam como antes

#### Scenario: Edição com ajuste na mesma operação
- **QUANDO** a gestação é marcada em ficha `AGUARDANDO` junto com prioridade Amarela e justificativa
- **ENTÃO** a alteração é aceita, a prioridade atual é Amarela e a auditoria registra a alteração clínica e o ajuste

#### Scenario: Ficha chamada
- **QUANDO** se tenta alterar sintomas, sinais vitais ou prioridade de ficha `CHAMADO`
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Perfil sem permissão
- **QUANDO** Médico, Administrador ou pessoa sem sessão válida tenta alterar ficha `AGUARDANDO`
- **ENTÃO** o backend recusa sem alterar a ficha nem registrar auditoria

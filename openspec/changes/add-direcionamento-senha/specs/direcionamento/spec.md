# Delta de especificação

## Purpose

Coloca cada ficha classificada na fila da especialidade mais adequada que tenha médico disponível, com fallback para alternativas configuradas, e mantém esse destino atualizado quando os dados mudam.

## ADDED Requirements

### Requirement: Especialidade sugerida
O sistema DEVE identificar a especialidade sugerida da ficha assim: entre os sintomas com a prioridade padrão mais grave, considerar suas especialidades ativas e escolher a de menor ordem configurada; em caso de empate, vale o sintoma registrado primeiro na ficha. Se a ficha não tiver sintomas com especialidade ativa, a sugerida DEVE ser a especialidade padrão dos parâmetros.

#### Scenario: Sintoma mais grave define a especialidade
- **QUANDO** a ficha tem "Tosse" (Azul, Clínica Geral) e "Dor no peito" (Vermelha, Cardiologia ordem 1)
- **ENTÃO** a especialidade sugerida é Cardiologia

#### Scenario: Ficha só com observação
- **QUANDO** a ficha não tem sintomas, apenas observação
- **ENTÃO** a especialidade sugerida é a especialidade padrão (inicialmente Clínica Geral)

### Requirement: Especialidade atribuída com fallback
O sistema DEVE atribuir a especialidade sugerida se ela tiver ao menos um médico disponível no momento. Caso contrário, DEVE percorrer as alternativas da sugerida na ordem configurada e atribuir a primeira que esteja ativa e tenha médico disponível. A ficha DEVE registrar a especialidade sugerida e a atribuída (RN18). Especialidades sem médico disponível NÃO DEVEM receber a ficha por esse caminho (CA05).

#### Scenario: Preferencial disponível
- **QUANDO** a sugerida é Cardiologia e há cardiologista disponível
- **ENTÃO** a atribuída é Cardiologia

#### Scenario: Fallback para alternativa
- **QUANDO** a sugerida é Cardiologia, não há cardiologista disponível e Clínica Geral é a primeira alternativa, com médico disponível
- **ENTÃO** a atribuída é Clínica Geral e a ficha mantém Cardiologia como sugerida (CA04)

#### Scenario: Primeira alternativa também indisponível
- **QUANDO** as alternativas de Cardiologia são [Clínica Geral, Neurologia] e só Neurologia tem médico disponível
- **ENTÃO** a atribuída é Neurologia

### Requirement: Nenhuma fila disponível
Se nem a sugerida nem as alternativas tiverem médico disponível, o sistema NÃO DEVE atribuir a especialidade automaticamente. Ele DEVE informar à Recepção/Triagem "Nenhum médico disponível para esta especialidade ou suas alternativas" e DEVE permitir que ela confirme a entrada na fila da especialidade sugerida. A ficha fica marcada como direcionada sem médico disponível.

#### Scenario: Aviso sem confirmação
- **QUANDO** não há médico disponível na sugerida nem nas alternativas e a Recepção/Triagem confirma a triagem sem aceitar o aviso
- **ENTÃO** o sistema recusa, mostra o aviso e a ficha continua em EM_TRIAGEM

#### Scenario: Entrada confirmada sem médico
- **QUANDO** a Recepção/Triagem aceita o aviso
- **ENTÃO** a ficha entra na fila da sugerida, marcada como direcionada sem médico disponível

### Requirement: Confirmação da triagem
A Recepção/Triagem DEVE concluir a triagem com a ação "Confirmar e gerar senha", que valida a completude da ficha, executa o direcionamento, gera a senha e leva a ficha de EM_TRIAGEM para AGUARDANDO, tudo numa única operação. A confirmação DEVE ser auditada.

#### Scenario: Confirmação bem-sucedida
- **QUANDO** a Recepção/Triagem confirma uma ficha completa com médico disponível na sugerida
- **ENTÃO** a ficha passa a AGUARDANDO com especialidade atribuída e senha

#### Scenario: Ficha incompleta
- **QUANDO** a Recepção/Triagem confirma uma ficha sem sinais vitais obrigatórios
- **ENTÃO** o sistema recusa, indica o que falta e não gera senha

#### Scenario: Médico tenta confirmar
- **QUANDO** um usuário Médico tenta confirmar uma triagem
- **ENTÃO** o backend responde como acesso negado

### Requirement: Redirecionamento de fichas aguardando
Para fichas AGUARDANDO, o sistema DEVE refazer o direcionamento quando: (a) sintomas ou prioridade mudarem e a especialidade sugerida mudar; ou (b) o Administrador alterar ou remover uma disponibilidade, ou desativar um médico, deixando a especialidade atribuída sem médico disponível. O horário de chegada DEVE ser preservado, e a auditoria DEVE registrar a especialidade de origem e a de destino. Se não houver destino com médico disponível, a ficha DEVE permanecer onde está. Fichas CHAMADO NÃO DEVEM ser redirecionadas.

#### Scenario: Sintomas mudam a especialidade
- **QUANDO** uma ficha AGUARDANDO em Clínica Geral recebe o sintoma "Convulsão" (Vermelha, Neurologia) e há neurologista disponível
- **ENTÃO** a ficha passa para a fila de Neurologia, com o mesmo horário de chegada, e a auditoria registra Clínica Geral → Neurologia

#### Scenario: Último médico da especialidade fica indisponível
- **QUANDO** o Administrador remove a disponibilidade do único cardiologista e há fichas AGUARDANDO em Cardiologia
- **ENTÃO** essas fichas vão para a primeira alternativa com médico disponível, preservando a ordem de chegada entre elas

#### Scenario: Sem destino disponível
- **QUANDO** a especialidade atribuída fica sem médico e nenhuma alternativa tem médico disponível
- **ENTÃO** as fichas permanecem na fila atual

#### Scenario: Ficha já chamada
- **QUANDO** a disponibilidade de um médico é removida enquanto uma ficha está CHAMADO por ele
- **ENTÃO** a ficha chamada não é redirecionada

### Requirement: Redirecionamento sob demanda
O Administrador DEVE poder acionar "Reavaliar direcionamento" para uma especialidade, que aplica a regra de redirecionamento às fichas AGUARDANDO dela.

#### Scenario: Reavaliação após o fim de um plantão
- **QUANDO** o horário de disponibilidade do único médico da Ortopedia terminou e o Administrador aciona "Reavaliar direcionamento" em Ortopedia
- **ENTÃO** as fichas AGUARDANDO em Ortopedia vão para a primeira alternativa com médico disponível

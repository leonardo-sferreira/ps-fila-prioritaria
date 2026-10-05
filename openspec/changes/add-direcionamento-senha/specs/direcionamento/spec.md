# Delta de especificação

## Purpose

Direciona automaticamente cada ficha para a especialidade mais adequada ao conjunto de sintomas, mantendo o destino clínico independente da especialidade de referência e disponibilidade do Médico.

## ADDED Requirements

### Requirement: Especialidade sugerida
O sistema DEVE determinar o destino automaticamente pelas relações entre os sintomas selecionados e suas especialidades de destino no catálogo oficial de `docs/domain-model.md`. A pontuação do sintoma participa do escore clínico, mas não é cor. Quando os sintomas selecionados apontarem para diferentes destinos, o algoritmo de desempate precisa de decisão de produto antes da implementação; não inferir cor nem disponibilidade de Médico como desempate. Sem sintoma direcionável, usar a especialidade padrão configurada. Para criança dentro do limite configurado, direcionar a Pediatria sem alterar escore/classificação.

#### Scenario: Sintoma direciona a Cardiologia
- **QUANDO** a ficha contém "Dor ou pressão no peito" do catálogo oficial
- **ENTÃO** o destino inclui Cardiologia, sem tratar o sintoma como cor

#### Scenario: Ficha só com observação
- **QUANDO** a ficha não tem sintomas, apenas observação
- **ENTÃO** a especialidade sugerida é a especialidade padrão (inicialmente Clínica Geral)

### Requirement: Destino independente de elegibilidade médica
A especialidade de destino da ficha DEVE permanecer a indicada pelos sintomas, independentemente da especialidade de referência dos Médicos ou da disponibilidade momentânea. O sistema NÃO DEVE substituir o destino por alternativa apenas porque não há Médico elegível naquele instante. A elegibilidade e atribuição operacional a Médico pertencem a `add-fila-chamada-medico`.

#### Scenario: Médico de outra especialidade atende
- **QUANDO** a ficha está na fila de Cardiologia e há um Médico elegível cuja especialidade de referência é Clínica Geral
- **ENTÃO** a ficha permanece na fila de Cardiologia e pode ser distribuída a esse Médico

### Requirement: Fila correta sem Médico elegível imediato
Se nenhum Médico estiver elegível, a ficha DEVE continuar na fila de sua especialidade clínica, sem fallback para outra especialidade. A interface pode informar que aguarda distribuição, sem exigir confirmação para preservar o destino.

#### Scenario: Fila aguarda elegibilidade
- **QUANDO** não há Médico elegível no momento da confirmação da triagem
- **ENTÃO** a ficha entra na fila da especialidade indicada pelos sintomas e não é redirecionada para alternativa

### Requirement: Confirmação da triagem
A Recepção/Triagem DEVE concluir a triagem com a ação "Confirmar e gerar senha", que valida a completude da ficha, executa o direcionamento, gera a senha e leva a ficha de EM_TRIAGEM para AGUARDANDO, tudo numa única operação. A confirmação DEVE ser auditada.

#### Scenario: Confirmação bem-sucedida
- **QUANDO** a Recepção/Triagem confirma uma ficha completa
- **ENTÃO** a ficha passa a AGUARDANDO com destino clínico determinado pelos sintomas e senha, independentemente da disponibilidade ou especialidade de referência dos Médicos

#### Scenario: Ficha incompleta
- **QUANDO** a Recepção/Triagem confirma uma ficha sem sinais vitais obrigatórios
- **ENTÃO** o sistema recusa, indica o que falta e não gera senha

#### Scenario: Médico tenta confirmar
- **QUANDO** um usuário Médico tenta confirmar uma triagem
- **ENTÃO** o backend responde como acesso negado

### Requirement: Redirecionamento de fichas aguardando
Para fichas EM_TRIAGEM ou AGUARDANDO ainda não chamadas, o sistema DEVE recalcular o destino quando sintomas mudarem; mudança de Médico, disponibilidade, status ou plantão NÃO DEVE alterar destino clínico. Mudanças de destino e de senha DEVEM ser auditadas, preservando o horário de chegada. Fichas CHAMADO NÃO DEVEM ser redirecionadas.

#### Scenario: Sintomas mudam a especialidade
- **QUANDO** uma ficha AGUARDANDO em Clínica Geral recebe o sintoma "Convulsão em atividade" (3 pontos, Neurologia)
- **ENTÃO** a ficha passa para a fila de Neurologia, com o mesmo horário de chegada, e a auditoria registra Clínica Geral → Neurologia

#### Scenario: Médico fica indisponível sem mudar destino
- **QUANDO** o Administrador encerra a disponibilidade do último médico cadastrado como Cardiologia e existem fichas aguardando em Cardiologia
- **ENTÃO** as fichas permanecem em Cardiologia para distribuição a qualquer Médico elegível

#### Scenario: Ficha já chamada
- **QUANDO** a disponibilidade de um médico é removida enquanto uma ficha está CHAMADO por ele
- **ENTÃO** a ficha chamada não é redirecionada

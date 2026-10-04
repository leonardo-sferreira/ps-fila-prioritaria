# Delta de especificação

## Purpose

Informa aos pacientes na sala de espera a senha chamada, para onde ir e a previsão das próximas chamadas, sem expor nenhum dado pessoal.

## ADDED Requirements

### Requirement: Acesso público somente leitura
O painel DEVE ser acessível sem login e DEVE apenas exibir informações; NÃO DEVE existir nenhuma ação que altere dados a partir dele.

#### Scenario: Abertura do painel sem login
- **QUANDO** alguém abre a página do painel sem estar autenticado
- **ENTÃO** o painel é exibido normalmente

### Requirement: Privacidade
O painel e o endpoint que o alimenta NÃO DEVEM retornar nem exibir nome, CPF, data de nascimento, telefone, sintomas, sinais vitais ou qualquer outro dado pessoal ou clínico; somente senhas, números de ticket, cores, especialidades e horários de chamada (RN35, RNF06).

#### Scenario: Conferência da resposta do painel
- **QUANDO** o endpoint do painel é consultado com fichas chamadas e aguardando
- **ENTÃO** a resposta não contém nenhum campo de nome, CPF, nascimento, telefone, sintoma ou sinal vital

### Requirement: Senha atual em destaque
O painel DEVE exibir, com o maior destaque visual, a chamada mais recente (primeira chamada ou repetição), com senha, cor e especialidade. Toda chamada nova ou repetida DEVE provocar um destaque visual e um aviso sonoro curto.

#### Scenario: Nova chamada
- **QUANDO** um médico chama `V-CLI-003`
- **ENTÃO** em até 5 segundos o painel mostra `V-CLI-003 — Clínica Geral` em destaque e emite o aviso sonoro

#### Scenario: Repetição de chamada
- **QUANDO** o médico repete a chamada de `A-CAR-014`
- **ENTÃO** a senha volta ao destaque e o aviso é emitido de novo, com a indicação "2ª chamada"

### Requirement: Últimas chamadas
O painel DEVE listar as últimas chamadas (no mínimo as 4 anteriores à atual), com senha, especialidade e horário, da mais recente para a mais antiga.

#### Scenario: Histórico curto
- **QUANDO** ocorreram 6 chamadas
- **ENTÃO** o painel mostra a atual em destaque e as 4 anteriores na lista de últimas chamadas

### Requirement: Previsão das próximas senhas
Para cada especialidade exibida, o painel DEVE mostrar a previsão das próximas senhas calculada pela mesma regra da chamada real, com o tamanho configurado (inicial 5), e com a indicação de que é uma previsão sujeita a mudança. Com menos fichas elegíveis, DEVE mostrar só as existentes; sem nenhuma, DEVE indicar que a fila está vazia.

#### Scenario: Cinco ou mais aguardando
- **QUANDO** Clínica Geral tem 8 fichas AGUARDANDO
- **ENTÃO** o painel mostra exatamente 5 senhas previstas para Clínica Geral (CA10)

#### Scenario: Coerência com a chamada
- **QUANDO** a fila não muda entre a atualização do painel e o "Chamar próximo" de um médico dessa especialidade
- **ENTÃO** a senha chamada é a primeira que estava prevista no painel (CA11)

#### Scenario: Entrada de um Vermelho
- **QUANDO** uma ficha Vermelha entra na fila de Clínica Geral
- **ENTÃO** na atualização seguinte ela aparece na primeira posição da previsão (CA12)

#### Scenario: Desistência sai da previsão
- **QUANDO** uma ficha é marcada como DESISTÊNCIA ou CANCELADO
- **ENTÃO** ela não aparece mais na previsão (CA13)

### Requirement: Tickets da pré-triagem
O painel DEVE exibir o número do ticket da pré-triagem chamado mais recentemente pela Recepção/Triagem (inclusive rechamadas), com a indicação "Triagem".

#### Scenario: Ticket chamado para a triagem
- **QUANDO** a Recepção/Triagem chama o ticket 42
- **ENTÃO** o painel mostra "Triagem — senha 42" em até 5 segundos

### Requirement: Atualização contínua e resiliência
O painel DEVE se atualizar automaticamente em até 5 segundos após qualquer mudança na fila ou nas chamadas, sem ação do usuário, e DEVE continuar exibindo a última informação obtida, com indicação discreta de "reconectando", se a comunicação falhar.

#### Scenario: Falha temporária de rede
- **QUANDO** o painel perde a conexão com o servidor por 30 segundos
- **ENTÃO** continua mostrando o último estado, com a indicação de reconexão, e volta a se atualizar sozinho quando a conexão retorna

### Requirement: Filtro por especialidade
O painel DEVE aceitar a seleção de quais especialidades exibir, pelo endereço da página; sem seleção, exibe todas as especialidades ativas.

#### Scenario: Painel da ortopedia
- **QUANDO** o painel é aberto com a seleção apenas de Ortopedia
- **ENTÃO** a senha atual, as últimas chamadas e a previsão consideram somente Ortopedia

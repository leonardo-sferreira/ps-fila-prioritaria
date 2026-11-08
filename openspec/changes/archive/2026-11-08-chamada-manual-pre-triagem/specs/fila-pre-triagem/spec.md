## MODIFIED Requirements

### Requirement: Oportunidades de chamada
Cada chamada de um ticket DEVE ser uma ação da Recepção/Triagem; o sistema NÃO DEVE repetir chamadas nem encerrar oportunidades automaticamente. Cada oportunidade DEVE ter no máximo o número configurável de chamadas (inicialmente 3). Depois de cada chamada DEVE transcorrer um intervalo antes de liberar a próxima ação sobre o ticket: o intervalo configurável inicial de 30 segundos depois da primeira chamada da oportunidade e o intervalo de repetição configurável inicial de 10 segundos depois de cada chamada seguinte. Transcorrido o intervalo da chamada atual, a Recepção/Triagem DEVE poder chamar novamente (enquanto houver chamadas disponíveis na oportunidade) ou registrar que o paciente não compareceu. O registro de não comparecimento na primeira oportunidade DEVE devolver o mesmo ticket a AGUARDANDO ao fim da fila, com uma única nova oportunidade e contagem de chamadas reiniciada; na segunda oportunidade DEVE encerrar o ticket como NAO_COMPARECEU. O Xano DEVE validar prazo, limite e estado em cada ação.

#### Scenario: Avanço automático
- **QUANDO** termina o intervalo de uma chamada sem nenhuma ação da Recepção/Triagem
- **ENTÃO** o ticket permanece CHAMADO, com a mesma contagem de chamadas, até que a Recepção chame novamente, registre não comparecimento, confirme presença ou registre desistência

#### Scenario: Chamar novamente depois da primeira chamada
- **QUANDO** a Recepção/Triagem pede nova chamada 30 segundos ou mais depois da primeira chamada da oportunidade
- **ENTÃO** o ticket recebe a segunda chamada, com novo horário de chamada e autor registrado

#### Scenario: Chamar novamente depois da segunda chamada
- **QUANDO** a Recepção/Triagem pede nova chamada 10 segundos ou mais depois da segunda chamada
- **ENTÃO** o ticket recebe a terceira chamada

#### Scenario: Repetição prematura
- **QUANDO** se pede nova chamada antes de 30 segundos da primeira chamada, ou antes de 10 segundos de uma chamada seguinte
- **ENTÃO** o backend recusa sem alterar o ticket nem a contagem de chamadas

#### Scenario: Limite de tentativas
- **QUANDO** se pede uma quarta chamada na mesma oportunidade
- **ENTÃO** o backend recusa sem alterar a contagem

#### Scenario: Não compareceu antes do intervalo
- **QUANDO** se registra não comparecimento antes de transcorrer o intervalo da chamada atual
- **ENTÃO** o backend recusa sem alterar o ticket

#### Scenario: Primeira ausência
- **QUANDO** a Recepção/Triagem registra não comparecimento na primeira oportunidade, depois do intervalo da chamada atual
- **ENTÃO** o mesmo ticket volta a AGUARDANDO ao fim da fila, sem novo número, com a segunda oportunidade e a contagem de chamadas zerada

#### Scenario: Segunda ausência
- **QUANDO** a Recepção/Triagem registra não comparecimento na segunda oportunidade, depois do intervalo da chamada atual
- **ENTÃO** o ticket passa a NAO_COMPARECEU e sai da fila ativa

#### Scenario: Presença confirmada
- **QUANDO** a Recepção confirma presença durante a chamada
- **ENTÃO** o backend persiste a confirmação, recusa novas chamadas e o registro de não comparecimento, e permite a identificação e abertura da ficha

#### Scenario: Intervalos configurados ausentes ou inválidos
- **QUANDO** algum intervalo ou o limite de chamadas não está configurado ou não é um inteiro positivo
- **ENTÃO** o backend recusa a ação sem alterar o ticket

#### Scenario: Tela fechada
- **QUANDO** nenhuma tela autorizada da fila está aberta
- **ENTÃO** o ticket chamado permanece como está até a próxima ação de um operador

### Requirement: Operação autorizada e acompanhamento
A Recepção/Triagem DEVE poder consultar a fila, visualizar senha, chamada atual e quanto falta para liberar as próximas ações, chamar próximo, chamar novamente, registrar não comparecimento, confirmar presença, registrar desistência e iniciar identificação após presença. A tela DEVE atualizar automaticamente os dados a partir do Xano, sem executar ações sobre os tickets. "Chamar novamente" e "Não compareceu" DEVEM aparecer liberados somente depois do intervalo da chamada atual, e "Chamar novamente" NÃO DEVE aparecer quando a oportunidade já atingiu o limite de chamadas. O backend DEVE validar autenticação e perfil em cada operação e registrar alterações relevantes em auditoria. Qualquer operador autorizado DEVE poder retomar chamada ativa.

#### Scenario: Perfil sem permissão
- **QUANDO** Médico tenta chamar ticket, chamar novamente ou registrar não comparecimento
- **ENTÃO** o backend recusa a operação sem alterar a fila

#### Scenario: Sessão inválida
- **QUANDO** uma operação é solicitada sem sessão válida
- **ENTÃO** o backend recusa o acesso sem retornar dados protegidos ou alterar a fila

#### Scenario: Botões durante o intervalo
- **QUANDO** um ticket chamado ainda está dentro do intervalo da chamada atual
- **ENTÃO** a tela mostra a contagem regressiva e mantém "Chamar novamente" e "Não compareceu" indisponíveis

#### Scenario: Espera após terceira chamada
- **QUANDO** o não comparecimento é solicitado antes de transcorrer o intervalo de repetição desde a terceira chamada
- **ENTÃO** o backend recusa sem alterar o ticket

#### Scenario: Botões depois da terceira chamada
- **QUANDO** termina o intervalo da terceira chamada da oportunidade
- **ENTÃO** a tela oferece "Não compareceu" e não oferece "Chamar novamente"

#### Scenario: Retomada por outro operador
- **QUANDO** outro operador autorizado da Recepção/Triagem acessa um ticket CHAMADO
- **ENTÃO** DEVE poder retomar suas ações sem transferência e os eventos DEVEM identificar o autor de cada operação

#### Scenario: Retorno da classe prevista
- **QUANDO** a classe prevista volta a ter ticket após chamada alternativa
- **ENTÃO** a próxima seleção usa a posição preservada do ciclo

# Delta de especificação

## Purpose

Define a regra única que ordena a fila de cada especialidade, a mesma usada para escolher o próximo paciente e para prever as próximas chamadas.

## ADDED Requirements

### Requirement: Fichas elegíveis
Somente fichas AGUARDANDO da especialidade atribuída DEVEM participar da ordenação da fila dessa especialidade. Fichas EM_TRIAGEM, CHAMADO, ATENDIDO, DESISTÊNCIA e CANCELADO NÃO DEVEM participar (RF32).

#### Scenario: Ficha cancelada sai da fila
- **QUANDO** uma ficha AGUARDANDO é cancelada
- **ENTÃO** ela deixa de aparecer na ordenação e na previsão

### Requirement: Vermelhos primeiro
Se houver fichas Vermelhas elegíveis, a próxima ficha DEVE ser uma Vermelha, antes de qualquer Amarela ou Azul, independentemente da ordem de chegada (RN20, CA06).

#### Scenario: Vermelho chega depois
- **QUANDO** a fila tem uma Amarela que chegou às 10:00 e uma Vermelha que chegou às 10:30
- **ENTÃO** a próxima é a Vermelha

### Requirement: Ciclo amarelo/azul por especialidade
Sem Vermelhas elegíveis, o sistema DEVE seguir, em cada especialidade, um ciclo contínuo de A amarelas para B azuis (parâmetros iniciais A = 2, B = 1): as posições 1 a A preveem Amarela, e as posições A+1 a A+B preveem Azul. Se a cor prevista não tiver ficha elegível, DEVE ser escolhida a outra cor, sem bloquear a fila (RN22). O ciclo DEVE avançar uma posição somente quando a ficha escolhida for da cor prevista. Chamadas de Vermelhas NÃO DEVEM avançar nem reiniciar o ciclo. O tempo de espera NÃO DEVE mudar a cor (RN13).

#### Scenario: Ciclo completo com as duas cores
- **QUANDO** há muitas Amarelas e muitas Azuis e nenhuma Vermelha, com o ciclo na posição 1
- **ENTÃO** as seis próximas chamadas são Amarela, Amarela, Azul, Amarela, Amarela, Azul (CA07)

#### Scenario: Vermelho no meio do ciclo
- **QUANDO** o ciclo está na posição 2 (prevê Amarela) e chega uma Vermelha
- **ENTÃO** a próxima é a Vermelha e, depois dela, a próxima é Amarela (o ciclo continua na posição 2)

#### Scenario: Só Azuis
- **QUANDO** a fila tem apenas Azuis e o ciclo está na posição 1
- **ENTÃO** as Azuis são chamadas continuamente e o ciclo continua na posição 1

#### Scenario: Azul esperando quando o ciclo prevê Azul
- **QUANDO** só havia Amarelas, o ciclo chegou à posição 3 (prevê Azul) sem Azuis e chega uma Azul
- **ENTÃO** a próxima chamada é a Azul

### Requirement: Condição prioritária e ordem de chegada dentro da cor
Dentro da cor escolhida, fichas com condição prioritária DEVEM vir antes das demais (RN10, CA08). Dentro do mesmo grupo, vale o horário de chegada mais antigo (RN12, RN23, CA09). Em empate de horário, vale a ficha aberta primeiro.

#### Scenario: Idoso azul à frente de azul não prioritário
- **QUANDO** um Azul não prioritário chegou às 09:00 e um Azul idoso chegou às 09:30
- **ENTÃO** o idoso é escolhido primeiro entre os Azuis

#### Scenario: Condição prioritária não ultrapassa a cor
- **QUANDO** um Azul idoso e um Amarelo não prioritário aguardam e o ciclo prevê Amarela
- **ENTÃO** o Amarelo é escolhido

#### Scenario: Dois prioritários da mesma cor
- **QUANDO** dois Amarelos prioritários aguardam, um desde 10:00 e outro desde 10:05
- **ENTÃO** o que chegou às 10:00 é escolhido primeiro

### Requirement: Previsão das próximas senhas
O sistema DEVE fornecer, para cada especialidade, a previsão das próximas N senhas (N = tamanho da previsão, inicial 5), simulando chamadas sucessivas com a mesma regra e o estado atual do ciclo (RN25). A previsão DEVE conter só senha e cor, NÃO DEVE reservar posição (RN26) e DEVE refletir o estado da fila no momento da consulta (RF35). Com menos de N fichas elegíveis, DEVE listar só as existentes (CA10).

#### Scenario: Previsão coincide com a chamada
- **QUANDO** a fila não muda entre a consulta da previsão e o "Chamar próximo" de um médico que atende só essa especialidade
- **ENTÃO** a senha chamada é a primeira da previsão (CA11)

#### Scenario: Nova Vermelha recalcula a previsão
- **QUANDO** uma ficha Vermelha entra na fila depois de uma consulta da previsão
- **ENTÃO** a consulta seguinte mostra a Vermelha na primeira posição (CA12)

#### Scenario: Menos de cinco elegíveis
- **QUANDO** a fila tem 3 fichas elegíveis
- **ENTÃO** a previsão lista exatamente 3 senhas

#### Scenario: Previsão sem dados pessoais
- **QUANDO** a previsão é consultada
- **ENTÃO** a resposta não contém nome, CPF nem outro dado pessoal

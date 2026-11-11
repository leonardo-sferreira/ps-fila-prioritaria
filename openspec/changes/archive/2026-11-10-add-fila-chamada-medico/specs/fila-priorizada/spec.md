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
Dentro de uma especialidade, se houver fichas Vermelhas elegíveis, a candidata dessa fila DEVE ser uma Vermelha, antes de qualquer Amarela ou Azul, independentemente da ordem de chegada (RF24, RN20, CA06). A escolha entre especialidades segue os requisitos de seleção e apoio abaixo.

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
Dentro da cor escolhida, fichas com condição prioritária (idoso, criança ou gestante) DEVEM vir antes das demais (RF26, RN10, CA08), sem precedência entre os três tipos. Dentro do mesmo grupo, vale a ordem efetiva mais antiga da fila: `chegada_em` na entrada inicial ou posição de reentrada ao fim da mesma especialidade; em empate, menor ID da ficha (RF27, RN12, RN23, CA09).

#### Scenario: Idoso azul à frente de azul não prioritário
- **QUANDO** um Azul não prioritário chegou às 09:00 e um Azul idoso chegou às 09:30
- **ENTÃO** o idoso é escolhido primeiro entre os Azuis

#### Scenario: Condição prioritária não ultrapassa a cor
- **QUANDO** um Azul idoso e um Amarelo não prioritário aguardam e o ciclo prevê Amarela
- **ENTÃO** o Amarelo é escolhido

#### Scenario: Dois prioritários da mesma cor
- **QUANDO** dois Amarelos prioritários aguardam, um desde 10:00 e outro desde 10:05
- **ENTÃO** o que chegou às 10:00 é escolhido primeiro

#### Scenario: Reentrada ao fim da mesma fila
- **QUANDO** uma ficha Amarela retorna à fila após a primeira oportunidade sem comparecimento e outra Amarela do mesmo grupo ainda aguarda
- **ENTÃO** a ficha retornada fica atrás da outra na ordem efetiva, preservando `chegada_em` e a senha

### Requirement: Seleção entre especialidades próprias
Para cada especialidade, o sistema DEVE obter uma candidata pela ordem interna. Entre especialidades próprias N:N do médico, uma Vermelha candidata DEVE preceder as demais próprias; entre Vermelhas próprias, valem `chegada_em` e menor ID da ficha. Sem Vermelha própria, o sistema DEVE percorrer as especialidades próprias com candidatas Amarelas/Azuis em rodízio determinístico por médico, preservando o ciclo interno de cada fila (Rev. 2.1, §7.2, §14.1, D03).

#### Scenario: Vermelhas em duas próprias
- **QUANDO** um médico tem Cardiologia e Neurologia como próprias, ambas com Vermelha candidata
- **ENTÃO** chama a Vermelha de chegada mais antiga e, em empate, a de menor ID da ficha

#### Scenario: Rodízio próprio com ciclos independentes
- **QUANDO** Cardiologia e Neurologia são próprias, ambas têm candidatas Amarelas/Azuis, e a última chamada própria foi de Cardiologia
- **ENTÃO** a próxima especialidade própria considerada é Neurologia, cuja candidata segue a posição do ciclo de Neurologia

#### Scenario: Especialidade própria vazia no rodízio
- **QUANDO** a próxima especialidade do rodízio não tem ficha AGUARDANDO
- **ENTÃO** o sistema a pula e considera a próxima própria com candidata, sem avançar o ciclo da fila vazia

### Requirement: Apoio a filas descobertas e cobertas
Uma fila DEVE ser considerada descoberta quando não há médico próprio com usuário e cadastro ativos, plantão e disponibilidade vigentes e sessão apta a chamar. PAUSA/AUSENTE retiram cobertura; EM_ATENDIMENTO não. A melhor candidata descoberta DEVE ser escolhida por cor, condição prioritária, ordem efetiva e ID. Ela DEVE superar a próxima própria apenas por cor mais grave; empate de cor favorece a própria. Sem ficha própria, o médico DEVE apoiar primeiro uma descoberta e, sem ela, outra fila coberta (Rev. 2.1, §7.1–7.2, §14.1, D04–D05).

#### Scenario: Vermelha descoberta supera Azul própria
- **QUANDO** a próxima própria é Azul e uma fila descoberta tem Vermelha candidata
- **ENTÃO** a Vermelha descoberta é escolhida

#### Scenario: Empate de cor favorece própria
- **QUANDO** a próxima própria é Amarela e a melhor descoberta também é Amarela
- **ENTÃO** a própria é escolhida, independentemente de condição prioritária ou chegada da descoberta

#### Scenario: Pausa descobre a fila
- **QUANDO** o único médico próprio de uma especialidade entra em PAUSA ou AUSENTE durante plantão vigente
- **ENTÃO** a especialidade passa a ser descoberta para a próxima seleção

#### Scenario: Atendimento mantém cobertura
- **QUANDO** o único médico próprio está EM_ATENDIMENTO com plantão, disponibilidade e sessão vigentes
- **ENTÃO** a especialidade continua coberta

#### Scenario: Próprias vazias e descoberta disponível
- **QUANDO** todas as filas próprias estão vazias e há uma descoberta com ficha
- **ENTÃO** o sistema chama a melhor candidata descoberta

#### Scenario: Somente outra fila coberta tem ficha
- **QUANDO** próprias e descobertas estão vazias, mas uma fila coberta por outro médico tem ficha AGUARDANDO
- **ENTÃO** o médico pode apoiar essa fila, escolhendo por cor, condição prioritária, ordem efetiva e ID

### Requirement: Previsão das próximas senhas
O sistema DEVE fornecer, para cada especialidade, a previsão das próximas N senhas (N = tamanho da previsão, inicial 5), simulando chamadas sucessivas com a mesma regra e o estado atual do ciclo (RN25). A previsão DEVE conter só senha e cor, NÃO DEVE reservar posição (RN26) e DEVE refletir o estado da fila no momento da consulta (RF35). Com menos de N fichas elegíveis, DEVE listar só as existentes (CA10).

#### Scenario: Previsão coincide com a seleção da fila
- **QUANDO** a fila não muda entre a consulta e a seleção da próxima ficha dessa mesma especialidade
- **ENTÃO** a ficha selecionada é a primeira da previsão daquela fila (CA11); isso não define a ordem global de escolha entre especialidades

#### Scenario: Nova Vermelha recalcula a previsão
- **QUANDO** uma ficha Vermelha entra na fila depois de uma consulta da previsão
- **ENTÃO** a consulta seguinte mostra a Vermelha na primeira posição (CA12)

#### Scenario: Menos de cinco elegíveis
- **QUANDO** a fila tem 3 fichas elegíveis
- **ENTÃO** a previsão lista exatamente 3 senhas

#### Scenario: Previsão sem dados pessoais
- **QUANDO** a previsão é consultada
- **ENTÃO** a resposta não contém nome, CPF nem outro dado pessoal

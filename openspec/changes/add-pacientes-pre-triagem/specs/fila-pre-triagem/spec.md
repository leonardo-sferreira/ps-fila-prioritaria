# Delta de especificação

## Purpose

Organiza a chegada dos pacientes antes da triagem: emite tickets numerados em ordem de chegada e permite à Recepção/Triagem chamá-los um a um, sem prioridade clínica.

## ADDED Requirements

### Requirement: Emissão de ticket pelo totem
O sistema DEVE emitir tickets com número sequencial que reinicia em 1 a cada dia, no fuso do PS, e registrar o horário de emissão. A emissão DEVE exigir a chave do totem e NÃO DEVE exigir nem guardar dados pessoais.

#### Scenario: Primeiro ticket do dia
- **QUANDO** o totem solicita um ticket e ainda não houve emissão no dia
- **ENTÃO** o sistema emite o ticket número 1, com status AGUARDANDO

#### Scenario: Tickets seguintes
- **QUANDO** o totem solicita um ticket depois de o ticket 41 ter sido emitido no dia
- **ENTÃO** o sistema emite o ticket número 42

#### Scenario: Virada do dia
- **QUANDO** o último ticket de 29/09 foi o 80 e o totem solicita um ticket às 00:00 de 30/09
- **ENTÃO** o sistema emite o ticket número 1

#### Scenario: Emissões simultâneas
- **QUANDO** duas solicitações de ticket chegam ao mesmo tempo
- **ENTÃO** os dois tickets recebem números diferentes e consecutivos

#### Scenario: Chave do totem ausente ou inválida
- **QUANDO** a emissão é solicitada sem a chave do totem ou com chave errada
- **ENTÃO** o sistema recusa como não autenticado e nenhum ticket é emitido

### Requirement: Simulador de totem
O sistema DEVE oferecer uma tela de simulador de totem com um botão "Retirar senha" que emite um ticket e mostra o número em destaque. A chave do totem NÃO DEVE ser enviada ao navegador.

#### Scenario: Retirar senha no simulador
- **QUANDO** alguém aciona "Retirar senha" no simulador
- **ENTÃO** a tela mostra o número do ticket emitido

### Requirement: Fila pré-triagem visível à Recepção/Triagem
O sistema DEVE mostrar à Recepção/Triagem os tickets do dia com status AGUARDANDO, em ordem de emissão, e os tickets CHAMADO, com o horário de emissão. Somente os perfis Recepção/Triagem e Administrador DEVEM ter acesso a essa lista.

#### Scenario: Lista da fila
- **QUANDO** a Recepção/Triagem abre a fila pré-triagem
- **ENTÃO** vê os tickets aguardando do mais antigo para o mais recente

#### Scenario: Médico tenta ver a fila pré-triagem
- **QUANDO** um usuário Médico consulta a fila pré-triagem
- **ENTÃO** o backend responde como acesso negado

### Requirement: Chamar o próximo ticket
A Recepção/Triagem DEVE poder chamar o próximo ticket, que é sempre o AGUARDANDO mais antigo do dia. O ticket passa a CHAMADO, vinculado ao usuário que chamou. Cada usuário DEVE ter no máximo um ticket CHAMADO por vez, e dois usuários NÃO DEVEM receber o mesmo ticket.

#### Scenario: Chamada em ordem de emissão
- **QUANDO** os tickets 5, 6 e 7 estão aguardando e a Recepção/Triagem aciona "Chamar próximo"
- **ENTÃO** o ticket 5 passa a CHAMADO

#### Scenario: Duas estações ao mesmo tempo
- **QUANDO** dois usuários Recepção/Triagem acionam "Chamar próximo" ao mesmo tempo, com os tickets 5 e 6 aguardando
- **ENTÃO** um recebe o ticket 5 e o outro o ticket 6

#### Scenario: Fila vazia
- **QUANDO** não há tickets aguardando e a Recepção/Triagem aciona "Chamar próximo"
- **ENTÃO** o sistema informa "Não há pacientes aguardando a triagem"

#### Scenario: Usuário já tem ticket chamado
- **QUANDO** o usuário já tem um ticket CHAMADO e aciona "Chamar próximo"
- **ENTÃO** o sistema recusa e pede que ele conclua o ticket atual

### Requirement: Concluir o ticket chamado
Para o ticket que chamou, a Recepção/Triagem DEVE poder rechamar (repetir o aviso), marcar "Não compareceu" (status NAO_COMPARECEU) ou marcar "Paciente identificado" informando o paciente (status ATENDIDO). Somente quem chamou o ticket DEVE poder concluí-lo.

#### Scenario: Paciente identificado
- **QUANDO** a Recepção/Triagem pesquisa o CPF do paciente do ticket 5 e aciona "Paciente identificado"
- **ENTÃO** o ticket 5 passa a ATENDIDO, vinculado ao paciente, e sai da fila

#### Scenario: Não compareceu
- **QUANDO** a Recepção/Triagem marca o ticket chamado como "Não compareceu"
- **ENTÃO** o ticket sai da fila com status NAO_COMPARECEU

#### Scenario: Outro usuário tenta concluir
- **QUANDO** um usuário tenta concluir um ticket chamado por outro usuário
- **ENTÃO** o sistema recusa a operação

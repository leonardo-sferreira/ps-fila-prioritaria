# Delta de especificação

## Purpose

Identifica cada ficha na fila priorizada por uma senha que indica cor e especialidade sem expor dados pessoais, e fornece o comprovante impresso entregue ao paciente.

## ADDED Requirements

### Requirement: Formato da senha
A senha DEVE seguir o formato `COR-ESP-NNN`: COR é V (Vermelha), A (Amarela) ou B (Azul); ESP é a sigla da especialidade atribuída; NNN é o número sequencial com no mínimo 3 dígitos, completado com zeros à esquerda. O número DEVE ser sequencial por especialidade, compartilhado entre as cores, e reiniciar em 1 a cada dia, no fuso do PS. Duas fichas NÃO DEVEM receber o mesmo número na mesma especialidade e no mesmo dia.

#### Scenario: Primeira senha do dia
- **QUANDO** a primeira ficha do dia em Clínica Geral é confirmada com prioridade Vermelha
- **ENTÃO** a senha é `V-CLI-001`

#### Scenario: Numeração compartilhada entre cores
- **QUANDO** depois de `V-CLI-001` uma ficha Azul é confirmada em Clínica Geral
- **ENTÃO** a senha é `B-CLI-002`

#### Scenario: Numeração independente por especialidade
- **QUANDO** depois de `B-CLI-002` a primeira ficha do dia em Cardiologia é confirmada com prioridade Amarela
- **ENTÃO** a senha é `A-CAR-001`

#### Scenario: Acima de 999
- **QUANDO** a ficha número 1000 do dia em Clínica Geral é confirmada com prioridade Azul
- **ENTÃO** a senha é `B-CLI-1000`

#### Scenario: Confirmações simultâneas
- **QUANDO** duas fichas da mesma especialidade são confirmadas ao mesmo tempo
- **ENTÃO** recebem números diferentes

### Requirement: Senha acompanha cor e especialidade
Enquanto a ficha estiver AGUARDANDO, se a prioridade atual ou a especialidade atribuída mudar, o sistema DEVE gerar uma nova senha com a nova cor e a nova especialidade (novo número na especialidade de destino), sem alterar o horário de chegada. A senha anterior DEVE ficar registrada na auditoria e deixar de valer.

#### Scenario: Ajuste de prioridade muda a senha
- **QUANDO** a ficha `B-CLI-002`, AGUARDANDO, tem a prioridade ajustada para Amarela e o último número de Clínica Geral no dia é 7
- **ENTÃO** a senha passa a `A-CLI-008` e a auditoria registra `B-CLI-002` → `A-CLI-008`

### Requirement: Comprovante
O sistema DEVE gerar um comprovante para impressão, em largura de impressora térmica de 80 mm, com senha em destaque, cor da prioridade por extenso, especialidade, data/hora de entrada e o aviso "Após 3 chamadas sem comparecimento, a senha será considerada desistência". O comprovante NÃO DEVE conter nome nem CPF. Somente a Recepção/Triagem DEVE poder emiti-lo.

#### Scenario: Comprovante emitido
- **QUANDO** a triagem é confirmada
- **ENTÃO** a tela abre o comprovante com senha, prioridade, especialidade, data/hora e aviso, sem nome nem CPF

#### Scenario: Reimpressão
- **QUANDO** a Recepção/Triagem aciona "Reimprimir" em uma ficha AGUARDANDO
- **ENTÃO** o comprovante é gerado de novo com a senha atual, sem criar nova ficha nem novo número

#### Scenario: Comprovante de ficha finalizada
- **QUANDO** alguém pede o comprovante de uma ficha ATENDIDO, DESISTÊNCIA ou CANCELADO
- **ENTÃO** o sistema recusa, porque a senha não está mais ativa

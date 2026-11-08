# Delta de especificação

## Purpose

Identifica cada ficha na fila da especialidade por uma senha que indica cor e especialidade sem expor dados pessoais, e fornece o comprovante impresso entregue ao paciente.

## ADDED Requirements

### Requirement: Formato da senha
A senha DEVE seguir o formato `COR-ESP-NNN`: COR é V (Vermelha), A (Amarela) ou B (Azul) conforme a prioridade atual da ficha na confirmação; ESP é a sigla de 3 letras da especialidade de destino (CAR, CLI, NEU, ORT, PED); NNN é o número sequencial com no mínimo 3 dígitos. O número DEVE reiniciar diariamente em `America/Sao_Paulo` e ser único por especialidade e dia, compartilhado entre as cores. A senha e o número DEVEM ser gravados na ficha.

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

#### Scenario: Virada do dia
- **QUANDO** a primeira ficha de Clínica Geral é confirmada depois da meia-noite em `America/Sao_Paulo`
- **ENTÃO** o número volta a 001

### Requirement: Comprovante
O sistema DEVE disponibilizar comprovante para impressão em largura de 80 mm, com a senha em destaque, a prioridade por extenso, a especialidade de destino e a data/hora de entrada, e o aviso de que o paciente deve acompanhar o painel, que cada senha é chamada até 3 vezes por oportunidade com intervalo de 30 segundos e que, sem resposta, volta uma única vez ao fim da fila. O comprovante NÃO DEVE conter nome, CPF, data de nascimento, sintomas nem sinais vitais. Somente a Recepção/Triagem PODE emitir ou reimprimir, e somente para ficha `AGUARDANDO` ou `CHAMADO`.

#### Scenario: Comprovante após a confirmação
- **QUANDO** a triagem é confirmada
- **ENTÃO** a tela abre o comprovante com senha, prioridade, especialidade, data/hora e aviso, sem dados pessoais nem clínicos

#### Scenario: Reimpressão
- **QUANDO** a Recepção/Triagem aciona "Reimprimir" em uma ficha `AGUARDANDO`
- **ENTÃO** o comprovante é gerado de novo com a mesma senha, sem criar ficha nem novo número

#### Scenario: Comprovante de ficha não confirmada ou finalizada
- **QUANDO** alguém pede o comprovante de uma ficha `EM_TRIAGEM`, `ATENDIDO`, `DESISTENCIA` ou `CANCELADO`
- **ENTÃO** o sistema recusa, porque não há senha ativa

#### Scenario: Perfil sem permissão
- **QUANDO** Médico, Administrador ou pessoa sem sessão válida pede o comprovante
- **ENTÃO** o backend recusa sem retornar dados da ficha

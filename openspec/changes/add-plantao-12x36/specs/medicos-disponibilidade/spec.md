## ADDED Requirements

### Requirement: Escala 12x36 de plantões
Ao registrar um novo plantão, o Administrador DEVE poder informar uma data final para criar uma escala 12x36: o mesmo horário a cada 2 dias, da data inicial até a data final, com no máximo 90 dias. Cada dia DEVE virar um período próprio, auditado como `PLANTAO_CRIADO`. Se qualquer período da escala se sobrepuser a outro do mesmo médico, NENHUM período DEVE ser criado.

#### Scenario: Escala de uma semana
- **QUANDO** o Administrador registra 12/11/2026 das 07:00 às 19:00 com escala até 18/11/2026 para a médica Ana
- **ENTÃO** são criados plantões em 12, 14, 16 e 18/11, das 07:00 às 19:00

#### Scenario: Conflito em um dos dias
- **QUANDO** a médica Ana já tem plantão em 16/11/2026 das 10:00 às 14:00 e o Administrador registra a mesma escala
- **ENTÃO** o backend recusa com `PLANTAO_SOBREPOSTO` e nenhum plantão da escala é criado

#### Scenario: Prazo acima do limite
- **QUANDO** a data final está a mais de 90 dias da inicial
- **ENTÃO** o backend recusa sem criar plantões

## MODIFIED Requirements

### Requirement: Abertura de ficha na fatia atual
O sistema DEVE abrir `Ficha_Atendimento` para paciente existente, com `status=EM_TRIAGEM` e `chegada_em` definido pelo backend. `ticket_id` PODE ser informado, mas a abertura NÃO DEVE depender de Totem ou ticket. `POST /fichas` PODE criar a ficha inicialmente sem sintomas e sem observação; RN04 não é exigida na abertura. Quando informado, o ticket DEVE estar chamado, ter presença confirmada e ser válido para a operação; sua associação, passagem a ATENDIDO e auditoria DEVEM ser atômicas com a abertura. Qualquer operador autorizado da Recepção/Triagem PODE concluir a abertura, independentemente de quem chamou.

#### Scenario: Abertura sem ticket
- **QUANDO** a Recepção/Triagem abre ficha para paciente existente sem ticket
- **ENTÃO** a ficha é criada em `EM_TRIAGEM` com horário definido pelo backend

#### Scenario: Abertura inicialmente vazia
- **QUANDO** a Recepção/Triagem abre uma ficha sem sintomas e sem observação
- **ENTÃO** a ficha permanece em `EM_TRIAGEM` e pode ser preenchida posteriormente sem criar estado adicional

#### Scenario: Paciente inexistente
- **QUANDO** alguém tenta abrir ficha para paciente inexistente
- **ENTÃO** nenhuma ficha é criada

#### Scenario: Abertura com ticket chamado
- **QUANDO** a Recepção/Triagem abre ficha para paciente identificado com ticket chamado válido
- **ENTÃO** a ficha referencia o ticket e este passa a ATENDIDO na mesma operação

#### Scenario: Ticket inválido ou ficha ativa existente
- **QUANDO** o ticket não está chamado com presença confirmada ou o paciente já tem ficha não finalizada
- **ENTÃO** nenhuma ficha adicional é criada e o ticket não muda de estado

# Delta de especificação

## MODIFIED Requirements

### Requirement: Ajuste manual da prioridade
A Recepção/Triagem DEVE poder definir a prioridade atual da ficha em `EM_TRIAGEM` ou `AGUARDANDO` como Vermelha, Amarela ou Azul, com justificativa obrigatória não vazia. O ajuste DEVE ser gravado em auditoria com evento `PRIORIDADE_ALTERADA`, valores anterior e novo, usuário e justificativa, na mesma transação. Quando existe prioridade calculada, a prioridade escolhida DEVE ser diferente dela. Quando não existe prioridade calculada, o ajuste é a classificação manual excepcional. O ajuste PODE vir na mesma operação de uma alteração clínica da ficha; nesse caso ele é aplicado depois do recálculo e não é descartado por ele. Em `AGUARDANDO`, o ajuste DEVE atualizar a senha conforme a capability `senha-comprovante`.

#### Scenario: Ajuste com justificativa
- **QUANDO** a Recepção/Triagem muda uma ficha calculada Azul para Amarela com justificativa
- **ENTÃO** a prioridade atual é Amarela, a calculada continua Azul e a auditoria registra a mudança e a justificativa

#### Scenario: Ajuste sem justificativa
- **QUANDO** a justificativa está vazia ou só tem espaços
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Classificação manual de inelegível
- **QUANDO** a ficha de uma gestante não tem prioridade calculada e a Recepção/Triagem define Amarela com justificativa
- **ENTÃO** a prioridade atual é Amarela e a auditoria registra a classificação manual

#### Scenario: Ajuste igual à calculada
- **QUANDO** a prioridade escolhida é igual à prioridade calculada
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Ajuste em ficha aguardando
- **QUANDO** a Recepção/Triagem muda para Vermelha, com justificativa, a ficha `AGUARDANDO` `A-CAR-001`
- **ENTÃO** a prioridade atual é Vermelha, a senha passa a `V-CAR-001` e a ficha continua `AGUARDANDO`

#### Scenario: Ficha fora da triagem
- **QUANDO** se tenta ajustar a prioridade de ficha que não está `EM_TRIAGEM` nem `AGUARDANDO`
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Perfil sem permissão
- **QUANDO** Médico, Administrador ou pessoa sem sessão válida tenta ajustar a prioridade
- **ENTÃO** o backend recusa sem alterar a ficha nem registrar auditoria

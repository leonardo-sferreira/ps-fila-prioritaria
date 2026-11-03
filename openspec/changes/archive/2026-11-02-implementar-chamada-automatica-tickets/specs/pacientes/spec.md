## MODIFIED Requirements

### Requirement: Continuidade da identificação para a Ficha
A interface de Recepção/Triagem DEVE oferecer `Continuar` para Paciente encontrado ou recém-cadastrado, abrindo a Ficha conforme a capability `ficha-atendimento`. Se houver ticket chamado, DEVE encaminhá-lo à abertura; sem ticket, o fluxo existente DEVE permanecer disponível. A ação NÃO DEVE criar ticket, classificação, senha ou seleção persistente fora da Ficha aberta.

#### Scenario: Paciente identificado segue para a Ficha
- **QUANDO** a Recepção/Triagem seleciona `Continuar` para Paciente identificado
- **ENTÃO** a interface abre a Ficha criada para o Paciente e direciona a pessoa usuária para sua edição

#### Scenario: Abertura da Ficha é recusada
- **QUANDO** a abertura da Ficha para o Paciente identificado é recusada
- **ENTÃO** a interface informa o erro e não cria ticket, classificação, senha ou seleção persistente adicional

#### Scenario: Continuidade com ticket
- **QUANDO** o paciente é identificado no contexto de ticket chamado válido
- **ENTÃO** a abertura recebe o ticket correspondente

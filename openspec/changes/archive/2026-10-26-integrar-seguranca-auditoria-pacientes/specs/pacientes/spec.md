# Delta de especificação

## MODIFIED Requirements

### Requirement: Acesso ao cadastro de pacientes por perfil
A Recepção/Triagem DEVE pesquisar, cadastrar e atualizar Pacientes. Administrador DEVE apenas pesquisar por CPF quando necessário. Médico NÃO DEVE acessar o cadastro. O backend DEVE aplicar essa matriz em cada endpoint, antes de retornar dados ou gravar alterações.

#### Scenario: Recepção/Triagem acessa operações permitidas
- **QUANDO** uma Recepção/Triagem autenticada pesquisa, cadastra ou atualiza um Paciente com dados válidos
- **ENTÃO** o backend executa a operação permitida

#### Scenario: Administrador pesquisa paciente
- **QUANDO** um Administrador autenticado pesquisa um CPF válido
- **ENTÃO** o backend retorna somente o resultado da pesquisa, sem criar ou alterar Paciente

#### Scenario: Médico tenta pesquisar paciente
- **QUANDO** um usuário Médico autenticado pesquisa um CPF
- **ENTÃO** o backend retorna 403 e não retorna dados

#### Scenario: Administrador tenta cadastrar
- **QUANDO** um Administrador autenticado tenta cadastrar Paciente
- **ENTÃO** o backend retorna 403 e nada é alterado

#### Scenario: Administrador tenta alterar paciente
- **QUANDO** um Administrador autenticado tenta alterar Paciente
- **ENTÃO** o backend retorna 403 e nada é alterado

### Requirement: Cadastro de Paciente
O sistema DEVE cadastrar Paciente com CPF válido e único, nome completo e data de nascimento obrigatórios e telefone opcional. Nascimento futuro ou idade acima de 130 anos DEVEM ser rejeitados. O cadastro cria Paciente ativo e o respectivo registro de auditoria de forma atômica.

#### Scenario: Cadastro bem-sucedido
- **QUANDO** a Recepção/Triagem informa dados válidos de CPF não cadastrado
- **ENTÃO** o Paciente é criado ativo e existe auditoria `CADASTRO` com o usuário responsável, valores novo e identificador do Paciente

#### Scenario: CPF duplicado
- **QUANDO** a Recepção/Triagem tenta cadastrar CPF já existente, inclusive em formatação diferente
- **ENTÃO** o sistema retorna 400 com o erro de negócio `CPF_DUPLICADO` e informa que o CPF já está cadastrado

#### Scenario: Campos ou data inválidos
- **QUANDO** falta nome ou nascimento, ou a data é futura ou ultrapassa o limite de idade
- **ENTÃO** o sistema retorna 400, indica dado inválido e não cria Paciente nem auditoria

#### Scenario: Falha de auditoria no cadastro
- **QUANDO** o cadastro válido não consegue gravar sua auditoria
- **ENTÃO** o Paciente não é confirmado e nenhum registro parcial de auditoria permanece

### Requirement: Atualização cadastral parcial
A Recepção/Triagem DEVE atualizar parcialmente nome, data de nascimento e telefone por `PATCH /pacientes/{id}`. CPF NÃO DEVE ser alterado. Corpo vazio, CPF no corpo ou dado inválido DEVEM retornar 400; Paciente inexistente DEVE retornar 404. Alteração real e respectiva auditoria DEVEM ser atômicas.

#### Scenario: Alteração parcial real
- **QUANDO** a Recepção/Triagem envia campo atualizável diferente
- **ENTÃO** o sistema atualiza o Paciente, retorna 200 com `alterado: true` e registra a alteração com os valores anterior e novo

#### Scenario: Dados idênticos
- **QUANDO** a Recepção/Triagem envia somente valores iguais aos atuais
- **ENTÃO** o sistema retorna 200 com `alterado: false` sem atualizar ou auditar

#### Scenario: CPF no corpo ou corpo vazio
- **QUANDO** a Recepção/Triagem envia CPF no corpo ou nenhum campo atualizável
- **ENTÃO** o sistema retorna 400 sem atualizar ou auditar

#### Scenario: Dados inválidos
- **QUANDO** a Recepção/Triagem envia nome inválido ou data de nascimento futura ou acima do limite de idade
- **ENTÃO** o sistema retorna 400 sem atualizar ou auditar

#### Scenario: Paciente inexistente
- **QUANDO** a Recepção/Triagem atualiza identificador inexistente
- **ENTÃO** o sistema retorna 404 sem criar auditoria

#### Scenario: Falha de auditoria na alteração
- **QUANDO** uma atualização real não consegue gravar sua auditoria
- **ENTÃO** o Paciente conserva os valores anteriores e nenhum registro parcial de auditoria permanece

### Requirement: Privacidade e autorização
Os dados de Paciente DEVEM ser retornados somente em operações autenticadas de perfis autorizados. O backend DEVE validar token, usuário existente e situação ativa em toda consulta, cadastro ou atualização.

#### Scenario: Usuário não autenticado
- **QUANDO** alguém sem token consulta ou altera Pacientes
- **ENTÃO** o backend retorna 401 e não retorna dados nem executa alteração

#### Scenario: Token inválido ou expirado
- **QUANDO** alguém consulta ou altera Pacientes com token inválido ou expirado
- **ENTÃO** o backend retorna 401 e não retorna dados nem executa alteração

#### Scenario: Usuário desativado com token emitido antes
- **QUANDO** um usuário é desativado depois de receber token e chama uma operação de Paciente
- **ENTÃO** o backend retorna 401 e não retorna dados nem executa alteração

## REMOVED Requirements

### Requirement: Confirmação visual sem efeito clínico
**Reason**: A confirmação somente visual foi uma decisão temporária da Sprint 1 e diverge do fluxo consolidado, no qual a identificação segue para a abertura da Ficha.

**Migration**: Substituir a confirmação sem efeito pela continuidade descrita no requisito adicionado nesta delta. Nenhum ticket, classificação, senha ou seleção clínica deve ser criado nessa transição.

## ADDED Requirements

### Requirement: Continuidade da identificação para a Ficha
A interface de Recepção/Triagem DEVE oferecer `Continuar` para Paciente encontrado ou recém-cadastrado, abrindo a Ficha conforme a capability `ficha-atendimento`. A ação NÃO DEVE criar ou alterar ticket, classificação, senha ou seleção persistente fora da Ficha aberta.

#### Scenario: Paciente identificado segue para a Ficha
- **QUANDO** a Recepção/Triagem seleciona `Continuar` para Paciente identificado
- **ENTÃO** a interface abre a Ficha criada para o Paciente e direciona a pessoa usuária para sua edição

#### Scenario: Abertura da Ficha é recusada
- **QUANDO** a abertura da Ficha para o Paciente identificado é recusada
- **ENTÃO** a interface informa o erro e não cria ticket, classificação, senha ou seleção persistente adicional

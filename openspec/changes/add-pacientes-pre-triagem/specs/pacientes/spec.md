# Delta de especificação

## Purpose

Mantém um cadastro único de pacientes identificado pelo CPF, ponto de partida obrigatório de todo atendimento (RN01, RN02).

## ADDED Requirements

### Requirement: Acesso ao cadastro de pacientes por perfil
A Recepção/Triagem DEVE poder pesquisar, cadastrar e atualizar pacientes. O Administrador DEVE poder apenas consultá-los. O Médico NÃO DEVE ter acesso ao cadastro de pacientes.

#### Scenario: Médico tenta pesquisar paciente
- **QUANDO** um usuário Médico pesquisa um CPF
- **ENTÃO** o backend responde como acesso negado

#### Scenario: Administrador tenta cadastrar
- **QUANDO** um usuário Administrador tenta cadastrar ou alterar um paciente
- **ENTÃO** o backend responde como acesso negado e nada é alterado

### Requirement: Pesquisa por CPF
O sistema DEVE pesquisar pacientes pelo CPF, aceitando o número com ou sem pontuação. CPF com formato ou dígitos verificadores inválidos DEVE ser recusado antes da pesquisa.

#### Scenario: CPF encontrado
- **QUANDO** a Recepção/Triagem pesquisa "123.456.789-09" e esse paciente existe
- **ENTÃO** o sistema retorna o cadastro existente, sem criar outro (CA01)

#### Scenario: Mesmo CPF sem pontuação
- **QUANDO** a Recepção/Triagem pesquisa "12345678909"
- **ENTÃO** o sistema encontra o mesmo paciente da pesquisa com pontuação

#### Scenario: CPF não encontrado
- **QUANDO** a Recepção/Triagem pesquisa um CPF válido que não está cadastrado
- **ENTÃO** o sistema informa "Paciente não encontrado" e oferece o cadastro com o CPF já preenchido

#### Scenario: CPF inválido
- **QUANDO** a Recepção/Triagem pesquisa "111.111.111-11" ou um número com menos de 11 dígitos
- **ENTÃO** o sistema recusa com a mensagem "CPF inválido"

### Requirement: Cadastro de paciente
O sistema DEVE cadastrar pacientes com CPF (válido e único), nome completo e data de nascimento obrigatórios e telefone opcional. A data de nascimento NÃO DEVE estar no futuro nem indicar idade acima de 130 anos. Todo paciente novo é criado ativo, e o cadastro DEVE ser auditado.

#### Scenario: Cadastro bem-sucedido
- **QUANDO** a Recepção/Triagem informa CPF válido não cadastrado, nome completo e data de nascimento
- **ENTÃO** o paciente é criado ativo e a auditoria registra o cadastro

#### Scenario: CPF já cadastrado
- **QUANDO** a Recepção/Triagem tenta cadastrar um CPF que já existe, mesmo digitado com outra pontuação
- **ENTÃO** o sistema recusa com a mensagem "CPF já cadastrado" e oferece abrir o cadastro existente

#### Scenario: Campos obrigatórios ou data inválida
- **QUANDO** falta nome ou data de nascimento, ou a data está no futuro
- **ENTÃO** o sistema recusa e indica o campo inválido

### Requirement: Atualização de dados cadastrais
A Recepção/Triagem DEVE poder atualizar nome, data de nascimento e telefone de um paciente (RF05). O CPF NÃO DEVE ser alterável. Toda atualização DEVE ser auditada com valor anterior e novo.

#### Scenario: Atualização de telefone
- **QUANDO** a Recepção/Triagem altera o telefone do paciente
- **ENTÃO** o dado é salvo e a auditoria registra o telefone anterior e o novo

#### Scenario: Tentativa de alterar CPF
- **QUANDO** a atualização envia um CPF diferente do cadastrado
- **ENTÃO** o sistema recusa e informa que o CPF não pode ser alterado

### Requirement: Privacidade dos dados do paciente
Os dados do paciente (CPF, nome, nascimento, telefone) DEVEM ser retornados somente em operações autenticadas para os perfis autorizados.

#### Scenario: Consulta sem autenticação
- **QUANDO** a pesquisa por CPF é chamada sem token
- **ENTÃO** o backend responde como não autenticado e não retorna dados

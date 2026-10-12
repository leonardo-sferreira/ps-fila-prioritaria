# Delta de especificação

## Purpose

Permitir que a Recepção/Triagem identifique, cadastre e atualize Pacientes pelo CPF, preservando unicidade, privacidade, autorização e auditoria.

## ADDED Requirements

### Requirement: Acesso ao cadastro de pacientes por perfil
A Recepção/Triagem DEVE pesquisar, cadastrar e atualizar Pacientes. Administrador DEVE apenas consultar. Médico NÃO DEVE acessar o cadastro.

#### Scenario: Médico tenta pesquisar paciente
- **QUANDO** um usuário Médico pesquisa um CPF
- **ENTÃO** o backend retorna 403 e não retorna dados

#### Scenario: Administrador tenta cadastrar
- **QUANDO** um Administrador tenta cadastrar ou alterar Paciente
- **ENTÃO** o backend retorna 403 e nada é alterado

### Requirement: Pesquisa por CPF
O sistema DEVE pesquisar Pacientes por CPF, aceitando número com ou sem pontuação e normalizando-o antes da consulta. CPF inválido DEVE ser recusado antes da pesquisa.

#### Scenario: CPF encontrado
- **QUANDO** a Recepção/Triagem pesquisa CPF válido de Paciente existente
- **ENTÃO** o sistema retorna o mesmo cadastro sem criar outro (CA01)

#### Scenario: Formatos equivalentes
- **QUANDO** a Recepção/Triagem pesquisa o mesmo CPF com e sem pontuação
- **ENTÃO** o sistema retorna o mesmo Paciente

#### Scenario: CPF não encontrado
- **QUANDO** a Recepção/Triagem pesquisa CPF válido inexistente
- **ENTÃO** o sistema informa que o Paciente não foi encontrado e oferece cadastro com o CPF preenchido

#### Scenario: CPF inválido
- **QUANDO** a Recepção/Triagem pesquisa CPF com tamanho, sequência ou dígitos verificadores inválidos
- **ENTÃO** o sistema retorna 400 com mensagem de CPF inválido

### Requirement: Cadastro de Paciente
O sistema DEVE cadastrar Paciente com CPF válido e único, nome completo e data de nascimento obrigatórios e telefone opcional. Nascimento futuro ou idade acima de 130 anos DEVEM ser rejeitados. O cadastro cria Paciente ativo e é auditado.

#### Scenario: Cadastro bem-sucedido
- **QUANDO** a Recepção/Triagem informa dados válidos de CPF não cadastrado
- **ENTÃO** o Paciente é criado ativo e o cadastro é auditado

#### Scenario: CPF duplicado
- **QUANDO** a Recepção/Triagem tenta cadastrar CPF já existente, inclusive em formatação diferente
- **ENTÃO** o sistema retorna 400 com o erro de negócio `CPF_DUPLICADO` e informa que o CPF já está cadastrado

#### Scenario: Campos ou data inválidos
- **QUANDO** falta nome ou nascimento, ou a data é futura ou ultrapassa o limite de idade
- **ENTÃO** o sistema retorna 400 e indica dado inválido

### Requirement: Atualização cadastral parcial
A Recepção/Triagem DEVE atualizar parcialmente nome, data de nascimento e telefone por `PATCH /pacientes/{id}`. CPF NÃO DEVE ser alterado. Corpo vazio, CPF no corpo ou dado inválido DEVEM retornar 400; Paciente inexistente DEVE retornar 404.

#### Scenario: Alteração parcial real
- **QUANDO** a Recepção/Triagem envia campo atualizável diferente
- **ENTÃO** o sistema atualiza o Paciente, retorna 200 com `alterado: true` e registra auditoria

#### Scenario: Dados idênticos
- **QUANDO** a Recepção/Triagem envia somente valores iguais aos atuais
- **ENTÃO** o sistema retorna 200 com `alterado: false` sem atualizar ou auditar

#### Scenario: CPF no corpo ou corpo vazio
- **QUANDO** a Recepção/Triagem envia CPF no corpo ou nenhum campo atualizável
- **ENTÃO** o sistema retorna 400

#### Scenario: Paciente inexistente
- **QUANDO** a Recepção/Triagem atualiza identificador inexistente
- **ENTÃO** o sistema retorna 404

### Requirement: Privacidade e autorização
Os dados de Paciente DEVEM ser retornados somente em operações autenticadas de perfis autorizados.

#### Scenario: Usuário não autenticado
- **QUANDO** alguém sem token consulta ou altera Pacientes
- **ENTÃO** o backend retorna 401 e não retorna dados

### Requirement: Confirmação visual sem efeito clínico
A interface de Recepção/Triagem DEVE oferecer `Continuar` ao exibir Paciente encontrado, somente como confirmação visual nesta Sprint. A ação NÃO DEVE criar ou abrir Ficha, criar ou alterar ticket, iniciar classificação ou persistir seleção para etapa posterior.

#### Scenario: Paciente identificado confirma visualmente
- **QUANDO** a Recepção/Triagem seleciona `Continuar` para Paciente encontrado
- **ENTÃO** nenhum objeto clínico ou operacional é criado ou alterado

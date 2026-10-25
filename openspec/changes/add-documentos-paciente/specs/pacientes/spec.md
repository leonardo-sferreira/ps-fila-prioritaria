# Delta de especificação

## ADDED Requirements

### Requirement: Documentos do Paciente
O Paciente DEVE ser marcado como brasileiro (padrão) ou estrangeiro no cadastro. O RG DEVE ter, após remover espaços das pontas, de 5 a 14 caracteres, somente letras e números (sem pontos, traços ou espaços), com `X` aceito, e DEVE ser informado junto com a UF emissora, uma das 27 siglas brasileiras. O RG NÃO DEVE ser único nem chave de pesquisa. A CRNM DEVE ter, após remover espaços das pontas, de 7 a 10 caracteres, somente letras e números, DEVE ser gravada em maiúsculas e DEVE ser única entre os Pacientes. A CRNM só se aplica a estrangeiros. RG e CRNM NÃO DEVEM ser exibidos no painel público nem retornados em operações sem autorização.

#### Scenario: Valores-limite do tamanho do RG
- **QUANDO** a Recepção/Triagem informa RG com 4, 5, 14 e 15 caracteres, todos com UF válida
- **ENTÃO** o sistema recusa 4 e 15 caracteres com 400 `RG_INVALIDO` e aceita 5 e 14 caracteres

#### Scenario: RG com caracteres inválidos
- **QUANDO** a Recepção/Triagem informa RG com ponto, traço, espaço interno ou símbolo, como `12.345.678-9`
- **ENTÃO** o sistema retorna 400 `RG_INVALIDO` e nada é gravado

#### Scenario: RG com X final
- **QUANDO** a Recepção/Triagem informa RG `12345678X` com UF `SP`
- **ENTÃO** o RG é aceito

#### Scenario: UF inválida ou informada sem RG
- **QUANDO** a Recepção/Triagem informa UF fora das 27 siglas, RG sem UF ou UF sem RG
- **ENTÃO** o sistema retorna 400 `RG_UF_INVALIDA` e nada é gravado

#### Scenario: Mesmo RG em pacientes diferentes
- **QUANDO** a Recepção/Triagem cadastra um Paciente com RG `123456789` / UF `MG` e já existe outro Paciente com RG `123456789` / UF `SP`
- **ENTÃO** o cadastro é aceito, porque o RG não é único

#### Scenario: Valores-limite do tamanho da CRNM
- **QUANDO** a Recepção/Triagem cadastra estrangeiro com CRNM de 6, 7, 10 e 11 caracteres
- **ENTÃO** o sistema recusa 6 e 11 caracteres com 400 `CRNM_INVALIDA` e aceita 7 e 10 caracteres

#### Scenario: CRNM duplicada
- **QUANDO** a Recepção/Triagem cadastra estrangeiro com CRNM já existente, inclusive com letras em caixa diferente
- **ENTÃO** o sistema retorna 400 `CRNM_DUPLICADA` e nada é gravado

#### Scenario: CRNM informada para brasileiro
- **QUANDO** a Recepção/Triagem cadastra Paciente não marcado como estrangeiro informando CRNM
- **ENTÃO** o sistema retorna 400 `CRNM_SOMENTE_ESTRANGEIRO` e nada é gravado

#### Scenario: Documentos fora do painel público
- **QUANDO** um paciente com RG ou CRNM é chamado e aparece no painel público
- **ENTÃO** o painel não exibe RG nem CRNM, assim como não exibe CPF nem nome completo

### Requirement: Pesquisa por CRNM
O sistema DEVE pesquisar Pacientes estrangeiros pela CRNM, sem diferenciar maiúsculas e minúsculas e ignorando espaços nas pontas. CRNM em formato inválido DEVE ser recusada antes da pesquisa.

#### Scenario: CRNM encontrada
- **QUANDO** a Recepção/Triagem pesquisa CRNM de Paciente estrangeiro existente, em maiúsculas ou minúsculas
- **ENTÃO** o sistema retorna o mesmo cadastro sem criar outro

#### Scenario: CRNM não encontrada
- **QUANDO** a Recepção/Triagem pesquisa CRNM válida inexistente
- **ENTÃO** o sistema informa que o Paciente não foi encontrado e oferece cadastro de estrangeiro com a CRNM preenchida

#### Scenario: CRNM inválida na pesquisa
- **QUANDO** a Recepção/Triagem pesquisa CRNM com tamanho ou caracteres inválidos
- **ENTÃO** o sistema retorna 400 `CRNM_INVALIDA`

## MODIFIED Requirements

### Requirement: Cadastro de Paciente
O sistema DEVE cadastrar Paciente com nome completo e data de nascimento obrigatórios e telefone opcional, conforme o tipo de paciente e o requisito "Documentos do Paciente". Paciente brasileiro DEVE ter CPF válido e único e RG com UF emissora, exceto criança — idade na data do cadastro até o parâmetro `idade_maxima_crianca` (valor inicial 11 anos) —, para quem o RG é opcional. Paciente estrangeiro DEVE ter CRNM válida e única; CPF e RG são opcionais para ele, e o CPF informado DEVE ser válido e único. Nascimento futuro ou idade acima de 130 anos DEVEM ser rejeitados. O cadastro cria Paciente ativo e é auditado.

#### Scenario: Cadastro bem-sucedido
- **QUANDO** a Recepção/Triagem informa dados válidos de brasileiro com CPF não cadastrado, RG e UF
- **ENTÃO** o Paciente é criado ativo e o cadastro é auditado

#### Scenario: Brasileiro adulto sem RG
- **QUANDO** a Recepção/Triagem cadastra brasileiro de 12 anos ou mais com CPF válido sem RG ou sem UF
- **ENTÃO** o sistema retorna 400 `RG_OBRIGATORIO` e nada é gravado

#### Scenario: Criança brasileira sem RG
- **QUANDO** a Recepção/Triagem cadastra brasileiro com CPF válido, sem RG, que completa 11 anos no dia do cadastro
- **ENTÃO** o Paciente é criado ativo com RG e UF vazios

#### Scenario: Limite de idade do RG opcional
- **QUANDO** a Recepção/Triagem cadastra, sem RG, um brasileiro com 11 anos e outro que completa 12 anos no dia do cadastro
- **ENTÃO** o de 11 anos é aceito e o de 12 anos recebe 400 `RG_OBRIGATORIO`

#### Scenario: Brasileiro sem CPF
- **QUANDO** a Recepção/Triagem cadastra Paciente não marcado como estrangeiro sem CPF
- **ENTÃO** o sistema retorna 400 com mensagem de CPF inválido e nada é gravado

#### Scenario: Estrangeiro só com CRNM
- **QUANDO** a Recepção/Triagem cadastra estrangeiro com CRNM válida não cadastrada, sem CPF e sem RG
- **ENTÃO** o Paciente é criado ativo, marcado como estrangeiro, com CPF e RG vazios

#### Scenario: Estrangeiro sem CRNM
- **QUANDO** a Recepção/Triagem cadastra estrangeiro sem CRNM
- **ENTÃO** o sistema retorna 400 `CRNM_OBRIGATORIA` e nada é gravado

#### Scenario: Estrangeiro com CPF
- **QUANDO** a Recepção/Triagem cadastra estrangeiro com CRNM válida e CPF válido não cadastrado
- **ENTÃO** o Paciente é criado com CRNM e CPF, e o CPF passa a valer para a pesquisa por CPF

#### Scenario: CPF duplicado
- **QUANDO** a Recepção/Triagem tenta cadastrar CPF já existente, inclusive em formatação diferente, para brasileiro ou estrangeiro
- **ENTÃO** o sistema retorna 400 com o erro de negócio `CPF_DUPLICADO` e informa que o CPF já está cadastrado

#### Scenario: Campos ou data inválidos
- **QUANDO** falta nome ou nascimento, ou a data é futura ou ultrapassa o limite de idade
- **ENTÃO** o sistema retorna 400 e indica dado inválido

### Requirement: Atualização cadastral parcial
A Recepção/Triagem DEVE atualizar parcialmente nome, data de nascimento, telefone e RG com UF emissora por `PATCH /pacientes/{id}`. RG e UF omitidos NÃO DEVEM ser alterados. Para brasileiro acima de `idade_maxima_crianca`, RG e UF NÃO DEVEM ser apagados; para criança brasileira e para estrangeiro, RG vazio DEVE limpar RG e UF juntos. CPF, CRNM e a marcação de estrangeiro NÃO DEVEM ser alterados. Corpo vazio, CPF, CRNM ou marcação de estrangeiro no corpo, ou dado inválido DEVEM retornar 400; Paciente inexistente DEVE retornar 404.

#### Scenario: Alteração parcial real
- **QUANDO** a Recepção/Triagem envia campo atualizável diferente
- **ENTÃO** o sistema atualiza o Paciente, retorna 200 com `alterado: true` e registra auditoria

#### Scenario: Completar RG de paciente antigo
- **QUANDO** a Recepção/Triagem envia RG `98765432` e UF `RJ` para brasileiro cadastrado antes desta change, ainda sem RG
- **ENTÃO** o sistema grava RG e UF e retorna 200 com `alterado: true`

#### Scenario: Apagar RG de brasileiro
- **QUANDO** a Recepção/Triagem envia RG vazio para brasileiro de 12 anos ou mais
- **ENTÃO** o sistema retorna 400 `RG_OBRIGATORIO` e mantém o RG atual

#### Scenario: Limpar RG de estrangeiro
- **QUANDO** a Recepção/Triagem envia RG vazio para estrangeiro com RG
- **ENTÃO** o sistema limpa RG e UF e retorna 200 com `alterado: true`

#### Scenario: RG omitido
- **QUANDO** a Recepção/Triagem envia somente novo telefone para Paciente com RG
- **ENTÃO** o RG e a UF permanecem inalterados

#### Scenario: Dados idênticos
- **QUANDO** a Recepção/Triagem envia somente valores iguais aos atuais
- **ENTÃO** o sistema retorna 200 com `alterado: false` sem atualizar ou auditar

#### Scenario: CPF no corpo ou corpo vazio
- **QUANDO** a Recepção/Triagem envia CPF, CRNM ou a marcação de estrangeiro no corpo, ou nenhum campo atualizável
- **ENTÃO** o sistema retorna 400

#### Scenario: Paciente inexistente
- **QUANDO** a Recepção/Triagem atualiza identificador inexistente
- **ENTÃO** o sistema retorna 404

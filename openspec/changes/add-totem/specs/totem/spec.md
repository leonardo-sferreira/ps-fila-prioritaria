# Delta de especificação

## Purpose

Permite que o paciente emita no Totem um ticket impessoal, de um dos tipos Pediátrico, Preferencial ou Normal, sequencial por tipo e registrado diretamente na fila de Recepção/Triagem.

## ADDED Requirements

### Requirement: Emissão de ticket impessoal
O sistema DEVE emitir um ticket numérico sequencial por dia operacional e por tipo e registrá-lo como aguardando na fila de Recepção/Triagem, sem solicitar ou armazenar dados pessoais.

#### Scenario: Primeiro ticket do dia
- **QUANDO** o Totem solicita o primeiro ticket Normal do dia em `America/Sao_Paulo`
- **ENTÃO** recebe o número 1 do tipo Normal e o sistema registra esse ticket como aguardando

#### Scenario: Tickets seguintes
- **QUANDO** um ticket Normal numerado 41 já foi emitido no dia e o Totem pede outro ticket Normal
- **ENTÃO** recebe o próximo número sequencial do tipo, 42, distinto de todos os tickets Normais daquele dia

#### Scenario: Virada do dia operacional
- **QUANDO** um novo ticket é solicitado após a virada do dia em `America/Sao_Paulo`
- **ENTÃO** a sequência diária daquele tipo reinicia em 1 sem reutilizar a identidade do ticket anterior

#### Scenario: Emissões simultâneas
- **QUANDO** dois tickets do mesmo tipo são solicitados ao mesmo tempo
- **ENTÃO** cada um recebe um número diferente e nenhum número do tipo se repete no dia

### Requirement: Tipo do ticket
O Totem DEVE oferecer três tipos de ticket — Pediátrico, Preferencial e Normal — e o sistema DEVE registrar o tipo escolhido no ticket. Cada tipo DEVE ter sequência diária própria, exibida com o prefixo do tipo: `C` para Pediátrico, `P` para Preferencial e `N` para Normal. O tipo NÃO DEVE alterar cor, classificação nem condição prioritária da ficha calculadas na triagem.

#### Scenario: Emissão de cada tipo
- **QUANDO** o paciente escolhe Pediátrico, Preferencial ou Normal e solicita o ticket
- **ENTÃO** o ticket é registrado com o tipo escolhido e o código exibido usa o prefixo correspondente, como `C-001`, `P-001` ou `N-001`

#### Scenario: Sequências independentes por tipo
- **QUANDO** no mesmo dia já foram emitidos os tickets `N-001` a `N-030` e nenhum Pediátrico, e o paciente pede um ticket Pediátrico
- **ENTÃO** recebe `C-001`, sem consumir nem alterar a sequência Normal

#### Scenario: Tipo ausente ou inválido
- **QUANDO** uma solicitação de emissão chega ao backend sem tipo ou com tipo diferente de Pediátrico, Preferencial e Normal
- **ENTÃO** o backend recusa a emissão e nenhum ticket é criado

### Requirement: Experiência pública sem dados pessoais
O Totem DEVE permitir emissão sem sessão de equipe e exibir o código do ticket emitido (prefixo do tipo e número) e instrução para aguardar chamada da Recepção/Triagem. A operação DEVE ser protegida no backend; segredo de emissão NÃO DEVE ser enviado ao navegador.

#### Scenario: Emissão pela tela do Totem
- **QUANDO** o paciente escolhe o tipo e solicita um ticket pela tela pública
- **ENTÃO** a tela mostra o código emitido, como `P-007`, e orientação para aguardar, sem pedir login, nome ou CPF

#### Scenario: Segredo ausente ou inválido
- **QUANDO** uma solicitação de emissão chega ao backend sem credencial de dispositivo válida
- **ENTÃO** o backend recusa a emissão e nenhum ticket é criado

#### Scenario: Dados pessoais não fazem parte do ticket
- **QUANDO** um ticket é emitido e consultado pela fila de Recepção/Triagem
- **ENTÃO** o ticket contém somente seus dados operacionais, incluindo o tipo, sem nome, CPF ou vínculo com paciente

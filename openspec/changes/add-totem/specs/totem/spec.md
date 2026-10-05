# Delta de especificação

## Purpose

Permite que o paciente emita no Totem um ticket impessoal, sequencial e registrado diretamente na fila de Recepção/Triagem.

## ADDED Requirements

### Requirement: Emissão de ticket impessoal
O sistema DEVE emitir um ticket numérico sequencial por dia operacional e registrá-lo como aguardando na fila de Recepção/Triagem, sem solicitar ou armazenar dados pessoais.

#### Scenario: Primeiro ticket do dia
- **QUANDO** o Totem solicita o primeiro ticket do dia em `America/Sao_Paulo`
- **ENTÃO** recebe o número 1 e o sistema registra esse ticket como aguardando

#### Scenario: Tickets seguintes
- **QUANDO** um ticket numerado 41 já foi emitido no dia e o Totem pede outro
- **ENTÃO** recebe o próximo número sequencial, 42, distinto de todos os tickets daquele dia

#### Scenario: Virada do dia operacional
- **QUANDO** um novo ticket é solicitado após a virada do dia em `America/Sao_Paulo`
- **ENTÃO** a sequência diária reinicia em 1 sem reutilizar a identidade do ticket anterior

### Requirement: Experiência pública sem dados pessoais
O Totem DEVE permitir emissão sem sessão de equipe e exibir o número do ticket emitido e instrução para aguardar chamada da Recepção/Triagem. A operação DEVE ser protegida no backend; segredo de emissão NÃO DEVE ser enviado ao navegador.

#### Scenario: Emissão pela tela do Totem
- **QUANDO** o paciente solicita um ticket pela tela pública
- **ENTÃO** a tela mostra o número emitido e orientação para aguardar, sem pedir login, nome ou CPF

#### Scenario: Segredo ausente ou inválido
- **QUANDO** uma solicitação de emissão chega ao backend sem credencial de dispositivo válida
- **ENTÃO** o backend recusa a emissão e nenhum ticket é criado

#### Scenario: Dados pessoais não fazem parte do ticket
- **QUANDO** um ticket é emitido e consultado pela fila de Recepção/Triagem
- **ENTÃO** o ticket contém somente seus dados operacionais, sem nome, CPF ou vínculo com paciente

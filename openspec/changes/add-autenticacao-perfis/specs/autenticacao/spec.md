# Delta de especificação

## Purpose

Garante que somente membros autenticados da equipe acessem o sistema e que cada um só execute as ações permitidas ao seu perfil (Recepção/Triagem, Médico ou Administrador).

## ADDED Requirements

### Requirement: Login com e-mail e senha
O sistema DEVE autenticar usuários da equipe por e-mail e senha e, em caso de sucesso, DEVE emitir um token de acesso com prazo de validade e retornar nome e perfil do usuário.

#### Scenario: Login bem-sucedido
- **QUANDO** um usuário ativo informa e-mail e senha corretos
- **ENTÃO** o sistema retorna um token de acesso, o nome e o perfil do usuário

#### Scenario: Credenciais inválidas
- **QUANDO** alguém informa um e-mail inexistente ou uma senha incorreta
- **ENTÃO** o sistema recusa o login com a mesma mensagem genérica ("E-mail ou senha inválidos") nos dois casos, sem revelar qual dado está errado

#### Scenario: Campos obrigatórios ausentes
- **QUANDO** o login é enviado sem e-mail ou sem senha
- **ENTÃO** o sistema recusa a requisição, indica o campo faltante e não emite token

#### Scenario: Usuário inativo
- **QUANDO** um usuário desativado informa e-mail e senha corretos
- **ENTÃO** o sistema recusa o login com a mensagem "Usuário inativo. Procure o administrador." e não emite token

### Requirement: Redirecionamento por perfil
Após o login, o sistema DEVE levar o usuário para a área inicial do seu perfil e DEVE impedir a navegação para áreas de outros perfis.

#### Scenario: Recepção/Triagem entra no sistema
- **QUANDO** um usuário com perfil Recepção/Triagem faz login
- **ENTÃO** o sistema exibe a área inicial da Recepção/Triagem

#### Scenario: Médico entra no sistema
- **QUANDO** um usuário com perfil Médico faz login
- **ENTÃO** o sistema exibe a área inicial do Médico

#### Scenario: Administrador entra no sistema
- **QUANDO** um usuário com perfil Administrador faz login
- **ENTÃO** o sistema exibe a área inicial do Administrador

#### Scenario: Acesso a área sem estar autenticado
- **QUANDO** alguém sem sessão válida tenta abrir qualquer área interna
- **ENTÃO** o sistema redireciona para a tela de login

#### Scenario: Acesso a área de outro perfil
- **QUANDO** um usuário autenticado tenta abrir a área de um perfil diferente do seu
- **ENTÃO** o sistema não exibe o conteúdo e o redireciona para a área inicial do seu próprio perfil

### Requirement: Controle de acesso no backend
Toda operação protegida DEVE ser autorizada no backend a cada requisição, verificando token válido, usuário ativo e perfil permitido. O frontend NÃO DEVE ser o único mecanismo de controle de acesso.

#### Scenario: Requisição sem token
- **QUANDO** uma operação protegida é chamada sem token de acesso
- **ENTÃO** o backend responde como não autenticado e não executa a operação

#### Scenario: Token inválido ou expirado
- **QUANDO** uma operação protegida é chamada com token adulterado ou vencido
- **ENTÃO** o backend responde como não autenticado e não executa a operação

#### Scenario: Perfil sem permissão
- **QUANDO** um usuário autenticado chama uma operação não permitida ao seu perfil
- **ENTÃO** o backend responde como acesso negado e não executa a operação

#### Scenario: Usuário desativado com token ainda válido
- **QUANDO** um usuário é desativado e depois usa um token emitido antes da desativação
- **ENTÃO** o backend responde como não autenticado e não executa a operação

### Requirement: Expiração da sessão
O token de acesso DEVE expirar após um período configurável (padrão de 12 horas, a duração de um plantão). Com o token expirado, o usuário DEVE fazer login de novo.

#### Scenario: Sessão expirada durante o uso
- **QUANDO** o usuário realiza uma ação depois que o token expirou
- **ENTÃO** o sistema informa que a sessão expirou e redireciona para a tela de login

### Requirement: Logout
O sistema DEVE permitir que o usuário encerre a sessão. Depois do logout, a interface DEVE descartar o token e voltar à tela de login.

#### Scenario: Logout
- **QUANDO** um usuário autenticado aciona "Sair"
- **ENTÃO** a sessão é encerrada, o token é descartado pela interface e a tela de login é exibida

#### Scenario: Voltar após logout
- **QUANDO** após o logout o usuário tenta voltar a uma área interna, por exemplo pelo botão "voltar" do navegador
- **ENTÃO** o sistema redireciona para a tela de login

### Requirement: Registro de sessões
O sistema DEVE registrar cada sessão da equipe com usuário, horário de login, horário de logout e expiração. Sessão ativa significa `logout_em` nulo e `expira_em` futuro; sem logout, a sessão é considerada encerrada quando expira. O status operacional (DISPONIVEL, EM_ATENDIMENTO, PAUSA ou AUSENTE) é estado distinto durante a sessão e pertence a `add-acompanhamento-administrador`: PAUSA/AUSENTE não encerram sessão nem equivalem a logout. Encerramento do plantão é evento operacional separado.

#### Scenario: Login registra sessão
- **QUANDO** um usuário faz login com sucesso
- **ENTÃO** o sistema registra uma sessão com o usuário e o horário de login

#### Scenario: Logout encerra a sessão
- **QUANDO** o usuário faz logout
- **ENTÃO** o sistema registra o horário de logout na sessão correspondente

#### Scenario: Login recusado não registra sessão
- **QUANDO** uma tentativa de login é recusada
- **ENTÃO** nenhuma sessão é registrada

#### Scenario: Pausa não encerra a sessão
- **QUANDO** uma pessoa autenticada altera seu status operacional para PAUSA ou AUSENTE
- **ENTÃO** a sessão permanece ativa enquanto `logout_em` for nulo e `expira_em` estiver no futuro

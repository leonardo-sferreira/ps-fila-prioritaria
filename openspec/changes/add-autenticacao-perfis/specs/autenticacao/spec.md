# Delta de especificação

## Purpose

Garante que somente membros autenticados da equipe acessem o sistema e que cada um só execute as ações permitidas ao seu perfil (Recepção/Triagem, Médico ou Administrador).

## ADDED Requirements

### Requirement: Login com e-mail e senha
O sistema DEVE autenticar usuários da equipe por e-mail e senha seguidos de um código de verificação enviado por e-mail. Com e-mail e senha corretos de um usuário ativo, o sistema DEVE enviar o código e NÃO DEVE emitir o token nessa etapa. Com o código conferido, o sistema DEVE emitir um token de acesso com prazo de validade e retornar nome e perfil do usuário.

#### Scenario: E-mail e senha corretos
- **QUANDO** um usuário ativo informa e-mail e senha corretos
- **ENTÃO** o sistema envia um código de 6 dígitos para o e-mail do usuário, informa que o código foi enviado e não retorna token

#### Scenario: Login bem-sucedido
- **QUANDO** o usuário informa o código correto, dentro da validade, depois de e-mail e senha corretos
- **ENTÃO** o sistema retorna um token de acesso, o nome e o perfil do usuário

#### Scenario: Credenciais inválidas
- **QUANDO** alguém informa um e-mail inexistente ou uma senha incorreta
- **ENTÃO** o sistema recusa o login com a mesma mensagem genérica ("E-mail ou senha inválidos") nos dois casos, sem revelar qual dado está errado

#### Scenario: Campos obrigatórios ausentes
- **QUANDO** o login é enviado sem e-mail ou sem senha
- **ENTÃO** o sistema recusa a requisição, indica o campo faltante e não emite token

#### Scenario: Usuário inativo
- **QUANDO** um usuário desativado informa e-mail e senha corretos
- **ENTÃO** o sistema recusa o login com a mensagem "Usuário inativo. Procure o administrador.", não envia código e não emite token

### Requirement: Código de verificação no login
O código do login DEVE ter 6 dígitos numéricos, DEVE valer por 10 minutos e DEVE ser de uso único. Cada código DEVE aceitar no máximo 5 tentativas de verificação; ao atingir o limite, ele DEVE ser invalidado. Um novo código DEVE poder ser pedido 60 segundos após o último, sem informar a senha de novo, enquanto o primeiro passo do login tiver sido feito há menos de 10 minutos; pedir um novo código DEVE invalidar o anterior. Os valores DEVEM ser configuráveis e são os mesmos da redefinição de senha. A sessão só DEVE ser registrada quando o código for conferido. O código NÃO DEVE ser gravado em texto aberto nem aparecer em respostas da API ou em logs.

#### Scenario: Código correto dentro da validade
- **QUANDO** o usuário informa o código correto 9 minutos e 59 segundos após o envio
- **ENTÃO** o sistema emite o token, registra a sessão e leva o usuário à área do seu perfil

#### Scenario: Código expirado
- **QUANDO** o usuário informa o código correto 10 minutos ou mais após o envio
- **ENTÃO** o sistema recusa com a mensagem "Código inválido ou expirado" e não emite token

#### Scenario: Código incorreto e limite de tentativas
- **QUANDO** o usuário erra o código 5 vezes
- **ENTÃO** as 5 tentativas são recusadas com "Código inválido ou expirado", e na 6ª o código, mesmo correto, também é recusado até que um novo seja pedido

#### Scenario: Reenvio antes de 60 segundos
- **QUANDO** o usuário pede um novo código 59 segundos depois do anterior
- **ENTÃO** o sistema não envia outro código e informa quanto tempo falta para reenviar

#### Scenario: Reenvio após 60 segundos invalida o código anterior
- **QUANDO** o usuário pede um novo código 60 segundos ou mais depois do anterior, dentro dos 10 minutos do primeiro passo
- **ENTÃO** o sistema envia um novo código e o anterior deixa de ser aceito

#### Scenario: Reenvio depois de 10 minutos
- **QUANDO** o usuário pede um novo código 10 minutos ou mais depois do primeiro passo do login
- **ENTÃO** o sistema não envia código e pede que o usuário informe e-mail e senha de novo

#### Scenario: Usuário desativado entre as etapas
- **QUANDO** o usuário é desativado depois de receber o código e então o informa
- **ENTÃO** o sistema recusa o login, não emite token e não registra sessão

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
- **QUANDO** um usuário faz login com sucesso, com o código conferido
- **ENTÃO** o sistema registra uma sessão com o usuário e o horário de login

#### Scenario: Logout encerra a sessão
- **QUANDO** o usuário faz logout
- **ENTÃO** o sistema registra o horário de logout na sessão correspondente

#### Scenario: Login recusado não registra sessão
- **QUANDO** uma tentativa de login é recusada, ou a senha confere mas o código não é informado ou é recusado
- **ENTÃO** nenhuma sessão é registrada

#### Scenario: Pausa não encerra a sessão
- **QUANDO** uma pessoa autenticada altera seu status operacional para PAUSA ou AUSENTE
- **ENTÃO** a sessão permanece ativa enquanto `logout_em` for nulo e `expira_em` estiver no futuro

### Requirement: Redefinição de senha pelo próprio usuário
O sistema DEVE permitir que um usuário da equipe redefina a própria senha sem estar logado ("Esqueci minha senha"), em três etapas: solicitar o código informando o e-mail, verificar o código e definir a nova senha. O código DEVE ter 6 dígitos numéricos, DEVE ser enviado ao e-mail cadastrado, DEVE valer por 10 minutos e DEVE ser de uso único; solicitar um novo código DEVE invalidar o anterior, e um novo envio só DEVE ser aceito 60 segundos após o último. Cada código DEVE aceitar no máximo 5 tentativas de verificação; ao atingir o limite, ele DEVE ser invalidado. A resposta da solicitação DEVE ser a mesma para e-mail cadastrado, não cadastrado ou de usuário inativo, e só usuário ativo DEVE receber o código. A nova senha DEVE ter no mínimo 8 caracteres e DEVE encerrar as sessões abertas do usuário. O código NÃO DEVE ser gravado em texto aberto nem aparecer em respostas da API ou em logs.

#### Scenario: Solicitação com e-mail de usuário ativo
- **QUANDO** alguém solicita a redefinição informando o e-mail de um usuário ativo
- **ENTÃO** o sistema envia um código de 6 dígitos para esse e-mail e responde "Se o e-mail estiver cadastrado, enviamos um código"

#### Scenario: Solicitação com e-mail inexistente ou de usuário inativo
- **QUANDO** alguém solicita a redefinição com e-mail não cadastrado ou de usuário desativado
- **ENTÃO** o sistema dá a mesma resposta da solicitação válida, sem enviar e-mail e sem revelar se o e-mail existe

#### Scenario: Reenvio antes de 60 segundos
- **QUANDO** um novo código é solicitado para o mesmo e-mail 59 segundos depois do anterior
- **ENTÃO** o sistema não envia outro código e informa quanto tempo falta para reenviar

#### Scenario: Reenvio após 60 segundos invalida o código anterior
- **QUANDO** um novo código é solicitado 60 segundos ou mais depois do anterior
- **ENTÃO** o sistema envia um novo código e o anterior deixa de ser aceito

#### Scenario: Código correto dentro da validade
- **QUANDO** o usuário informa o código correto 9 minutos e 59 segundos após o envio
- **ENTÃO** o sistema aceita o código e libera a definição da nova senha

#### Scenario: Código expirado
- **QUANDO** o usuário informa o código correto 10 minutos ou mais após o envio
- **ENTÃO** o sistema recusa com a mensagem "Código inválido ou expirado"

#### Scenario: Código incorreto e limite de tentativas
- **QUANDO** o usuário erra o código 5 vezes
- **ENTÃO** as 5 tentativas são recusadas com "Código inválido ou expirado", e na 6ª o código, mesmo correto, também é recusado até que um novo seja solicitado

#### Scenario: Nova senha válida
- **QUANDO** o usuário, com código verificado, define nova senha de 8 ou mais caracteres
- **ENTÃO** a senha anterior deixa de funcionar, o código não pode ser usado de novo, as sessões abertas do usuário são encerradas e o login com a nova senha funciona

#### Scenario: Nova senha curta
- **QUANDO** o usuário define nova senha com 7 caracteres
- **ENTÃO** o sistema recusa a alteração e a senha anterior continua valendo

#### Scenario: Usuário desativado depois de pedir o código
- **QUANDO** o usuário é desativado pelo Administrador depois de receber o código e tenta defini-lo
- **ENTÃO** o sistema recusa a redefinição e o usuário continua sem conseguir fazer login

# Delta de especificação

## Purpose

Informar a equipe sobre o tratamento dos dados pessoais e reduzir a exposição de dados de pacientes nas telas internas, mascarando o CPF e encerrando sessões esquecidas abertas.

## ADDED Requirements

### Requirement: Aviso de privacidade público
O sistema DEVE oferecer uma página de aviso de privacidade acessível sem login, aberta por um link "Aviso de privacidade" presente na tela de login, na tela do código do login e nas telas de redefinição de senha. O aviso DEVE informar, para os dados da equipe e para os dados dos pacientes: quais dados são tratados, para que finalidade, com quem são compartilhados, por quanto tempo são guardados e quais são os direitos do titular e como exercê-los. A página DEVE mostrar o texto do documento versionado do aviso, sem alterá-lo, e NÃO DEVE exigir aceite nem registrar a leitura. A página NÃO DEVE exibir dados de nenhum paciente ou usuário.

#### Scenario: Abrir o aviso pela tela de login
- **QUANDO** alguém sem sessão aciona "Aviso de privacidade" na tela de login
- **ENTÃO** o sistema exibe o aviso de privacidade completo, sem pedir login

#### Scenario: Aviso nas demais telas de acesso
- **QUANDO** alguém está na tela do código do login ou em qualquer tela de redefinição de senha
- **ENTÃO** o link "Aviso de privacidade" está disponível e abre o mesmo aviso

#### Scenario: Conteúdo obrigatório
- **QUANDO** o aviso é exibido
- **ENTÃO** ele apresenta, separadamente para equipe e pacientes, os dados tratados, a finalidade, o compartilhamento, o prazo de guarda e os direitos do titular com a forma de exercê-los

#### Scenario: Usuário logado abre o aviso
- **QUANDO** um usuário autenticado abre o endereço do aviso
- **ENTÃO** o aviso é exibido e a sessão continua aberta

#### Scenario: Voltar ao login
- **QUANDO** quem está no aviso aciona "Voltar ao login"
- **ENTÃO** o sistema exibe a tela de login

### Requirement: CPF mascarado nas telas internas
Nas telas internas que exibem o CPF de um paciente sem que ele precise ser digitado ou conferido por inteiro, o sistema DEVE mostrar o CPF no formato `***.DDD.DDD-**`, mantendo só do 4º ao 9º dígito. Os campos em que o CPF é digitado (busca e cadastro) DEVEM continuar mostrando o que foi digitado. Um CPF ausente ou que não tenha 11 dígitos NÃO DEVE ser exibido parcialmente; nesse caso o sistema DEVE mostrar "—".

#### Scenario: CPF no cabeçalho da ficha
- **QUANDO** a Recepção/Triagem abre a ficha de um paciente com CPF 123.456.789-01
- **ENTÃO** o cabeçalho da ficha mostra "CPF: ***.456.789-**"

#### Scenario: CPF guardado só com números
- **QUANDO** o CPF do paciente vem como 12345678901
- **ENTÃO** a tela mostra "***.456.789-**"

#### Scenario: CPF ausente ou incompleto
- **QUANDO** o CPF do paciente está vazio ou tem 10 dígitos
- **ENTÃO** a tela mostra "CPF: —" e não exibe nenhum trecho do valor

#### Scenario: Campo de busca não é mascarado
- **QUANDO** a Recepção/Triagem digita um CPF no campo de busca
- **ENTÃO** o campo mostra o CPF exatamente como foi digitado

### Requirement: Encerramento da sessão por inatividade
Nas áreas internas, o sistema DEVE encerrar a sessão quando o usuário ficar sem interagir com a página (mover o mouse, clicar, digitar ou rolar) pelo tempo de inatividade configurado, com padrão de 1 hora. O tempo DEVE ser configurável no backend e informado à tela junto com os dados da sessão. O encerramento DEVE ter o mesmo efeito do "Sair": registrar o logout da sessão, descartar o token e levar à tela de login com a mensagem "Sua sessão foi encerrada por inatividade." Qualquer interação DEVE reiniciar a contagem. As telas públicas (login, código, redefinição de senha e aviso de privacidade) NÃO DEVEM contar inatividade.

#### Scenario: Inatividade abaixo do limite
- **QUANDO** um usuário autenticado fica 59 minutos e 59 segundos sem interagir com uma área interna, com o limite de 1 hora
- **ENTÃO** a sessão continua aberta e a página continua exibida

#### Scenario: Inatividade no limite
- **QUANDO** um usuário autenticado fica 1 hora sem interagir com uma área interna
- **ENTÃO** o sistema registra o logout, descarta o token e mostra o login com "Sua sessão foi encerrada por inatividade."

#### Scenario: Interação reinicia a contagem
- **QUANDO** o usuário interage com a página 59 minutos depois da última interação
- **ENTÃO** a contagem recomeça e a sessão só é encerrada 1 hora depois dessa nova interação

#### Scenario: Voltar após o encerramento
- **QUANDO**, depois do encerramento por inatividade, alguém tenta voltar à área interna pelo navegador
- **ENTÃO** o sistema redireciona para a tela de login

#### Scenario: Tela pública aberta
- **QUANDO** a tela de login ou o aviso de privacidade fica aberto por mais de 1 hora sem interação
- **ENTÃO** nada é encerrado e a tela continua exibida

#### Scenario: Tempo configurado diferente
- **QUANDO** o tempo de inatividade configurado no backend é 5 minutos
- **ENTÃO** a sessão é encerrada após 5 minutos sem interação, sem mudar o frontend

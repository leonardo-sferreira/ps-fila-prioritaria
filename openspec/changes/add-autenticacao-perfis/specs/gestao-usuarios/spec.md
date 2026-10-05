# Delta de especificação

## Purpose

Permite que o Administrador cadastre e mantenha os usuários da equipe (Recepção/Triagem, Médico e Administrador), definindo quem pode acessar o sistema e com qual perfil.

## ADDED Requirements

### Requirement: Operações exclusivas do Administrador
Listar, criar, editar, redefinir senha e ativar/desativar usuários DEVE ser permitido somente ao perfil Administrador.

#### Scenario: Não administrador tenta gerenciar usuários
- **QUANDO** um usuário com perfil Recepção/Triagem ou Médico chama qualquer operação de gestão de usuários
- **ENTÃO** o backend responde como acesso negado e nada é alterado

### Requirement: Listar usuários
O sistema DEVE permitir que o Administrador visualize a lista de usuários com nome, e-mail, perfil e situação (ativo/inativo). A lista NÃO DEVE exibir senhas nem hashes de senha.

#### Scenario: Listagem
- **QUANDO** o Administrador abre a gestão de usuários
- **ENTÃO** o sistema exibe todos os usuários com nome, e-mail, perfil e situação

#### Scenario: Filtro por perfil e situação
- **QUANDO** o Administrador filtra por perfil ou por situação
- **ENTÃO** o sistema exibe apenas os usuários que atendem ao filtro

### Requirement: Criar usuário
O sistema DEVE permitir que o Administrador crie usuários informando nome, e-mail, perfil e senha inicial. O e-mail DEVE ser único, e a senha DEVE ter no mínimo 8 caracteres. Todo usuário novo é criado como ativo. Usuário permanece entidade de autenticação; perfis Médico e Recepção/Triagem também DEVEM ter seus registros de domínio 1:1. A criação e edição desses cadastros vinculados é feita no fluxo administrativo de `add-cadastros-administrador`, sem deixar usuário funcional sem sua entidade correspondente.

#### Scenario: Criação bem-sucedida
- **QUANDO** o Administrador informa nome, e-mail único, perfil válido e senha com 8 ou mais caracteres
- **ENTÃO** o usuário é criado ativo e consegue fazer login com essas credenciais

#### Scenario: E-mail duplicado
- **QUANDO** o Administrador tenta criar um usuário com e-mail já cadastrado (sem diferenciar maiúsculas e minúsculas)
- **ENTÃO** o sistema recusa com a mensagem "E-mail já cadastrado" e não cria o usuário

#### Scenario: Dados inválidos
- **QUANDO** falta nome, e-mail ou perfil, o e-mail tem formato inválido, o perfil não é um dos três perfis válidos ou a senha tem menos de 8 caracteres
- **ENTÃO** o sistema recusa a criação e indica qual campo está inválido

#### Scenario: Perfil funcional exige cadastro vinculado
- **QUANDO** um usuário com perfil MEDICO ou RECEPCAO_TRIAGEM é ativado para acesso
- **ENTÃO** o fluxo administrativo também mantém o respectivo registro de domínio vinculado 1:1; a aplicação recusa estado ativo incompleto

### Requirement: Editar usuário
O sistema DEVE permitir que o Administrador edite nome, e-mail e perfil de um usuário existente, com as mesmas validações da criação.

#### Scenario: Edição bem-sucedida
- **QUANDO** o Administrador altera o nome, o e-mail ou o perfil de um usuário com dados válidos
- **ENTÃO** as alterações são salvas e valem a partir do próximo login do usuário

#### Scenario: Troca de perfil com sessão aberta
- **QUANDO** o perfil de um usuário é alterado enquanto ele tem uma sessão ativa
- **ENTÃO** a partir da próxima requisição, o backend autoriza esse usuário pelo novo perfil

### Requirement: Redefinir senha
O sistema DEVE permitir que o Administrador defina uma nova senha para um usuário, respeitando o mínimo de 8 caracteres.

#### Scenario: Redefinição bem-sucedida
- **QUANDO** o Administrador define uma nova senha válida para um usuário
- **ENTÃO** a senha anterior deixa de funcionar e o usuário passa a entrar com a nova

#### Scenario: Senha curta
- **QUANDO** o Administrador informa uma nova senha com menos de 8 caracteres
- **ENTÃO** o sistema recusa a alteração e a senha anterior continua valendo

### Requirement: Ativar e desativar usuário
O sistema DEVE permitir que o Administrador ative e desative usuários. Usuários NÃO DEVEM ser excluídos, para preservar o histórico. Um usuário desativado perde o acesso imediatamente.

#### Scenario: Desativação
- **QUANDO** o Administrador desativa um usuário
- **ENTÃO** o usuário não consegue mais fazer login, e as requisições feitas com o token que ele já tinha passam a ser recusadas

#### Scenario: Reativação
- **QUANDO** o Administrador reativa um usuário inativo
- **ENTÃO** o usuário volta a conseguir fazer login com sua senha atual

#### Scenario: Administrador tenta desativar a si mesmo
- **QUANDO** o Administrador tenta desativar a própria conta
- **ENTÃO** o sistema recusa com a mensagem "Não é possível desativar o próprio usuário"

#### Scenario: Último administrador ativo
- **QUANDO** uma desativação ou troca de perfil deixaria o sistema sem nenhum Administrador ativo
- **ENTÃO** o sistema recusa a operação e informa que deve existir ao menos um Administrador ativo

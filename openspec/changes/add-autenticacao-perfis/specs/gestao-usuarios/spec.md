# Delta de especificação

## Purpose

Permite que o Administrador veja todos os usuários da equipe, mantenha os outros administradores e troque o perfil de qualquer funcionário. Médicos e Recepção/Triagem são criados e editados nos cadastros (`add-cadastros-administrador`), que criam o login junto.

## ADDED Requirements

### Requirement: Operações exclusivas do Administrador
Listar usuários, criar, editar e ativar/desativar administradores e trocar perfil DEVEM ser permitidos somente ao perfil Administrador.

#### Scenario: Não administrador tenta gerenciar usuários
- **QUANDO** um usuário com perfil Recepção/Triagem ou Médico chama qualquer operação de gestão de usuários
- **ENTÃO** o backend responde como acesso negado e nada é alterado

### Requirement: Listar usuários
O sistema DEVE permitir que o Administrador visualize a lista de todos os usuários com nome, e-mail, perfil e situação (ativo/inativo), com filtro por perfil e por situação e busca por nome ou e-mail. A lista NÃO DEVE exibir senhas nem hashes de senha.

#### Scenario: Listagem
- **QUANDO** o Administrador abre a gestão de usuários
- **ENTÃO** o sistema exibe todos os usuários com nome, e-mail, perfil e situação, sem senha

#### Scenario: Filtro por perfil e situação
- **QUANDO** o Administrador filtra por perfil ou por situação
- **ENTÃO** o sistema exibe apenas os usuários que atendem ao filtro

### Requirement: Manter administradores
O Administrador DEVE poder criar outro Administrador informando nome, e-mail único (sem diferenciar maiúsculas) e senha inicial de 8 ou mais caracteres, editar nome e e-mail de administradores e ativar ou desativar administradores. Usuários NÃO DEVEM ser excluídos. O Administrador NÃO DEVE desativar a si mesmo, e o sistema NÃO DEVE ficar sem nenhum Administrador ativo. Médicos e Recepção/Triagem são mantidos pelos cadastros, que criam e desativam o login junto. A senha é trocada pelo próprio usuário, em "Esqueci minha senha"; o Administrador NÃO DEVE definir a senha de outro usuário depois da criação.

#### Scenario: Criar administrador
- **QUANDO** o Administrador informa nome, e-mail único e senha com 8 ou mais caracteres
- **ENTÃO** o novo Administrador é criado ativo, consegue fazer login, e a operação é auditada sem a senha

#### Scenario: E-mail duplicado
- **QUANDO** o e-mail já pertence a outro usuário, com ou sem diferença de maiúsculas
- **ENTÃO** a criação ou edição é recusada e nada é alterado

#### Scenario: Senha curta
- **QUANDO** a senha inicial tem menos de 8 caracteres
- **ENTÃO** a criação é recusada

#### Scenario: Desativar a si mesmo
- **QUANDO** o Administrador tenta desativar a própria conta
- **ENTÃO** o sistema recusa com a mensagem "Não é possível desativar o próprio usuário"

#### Scenario: Último administrador ativo
- **QUANDO** uma desativação ou troca de perfil deixaria o sistema sem nenhum Administrador ativo
- **ENTÃO** o sistema recusa a operação e informa que deve existir ao menos um Administrador ativo

#### Scenario: Usuário desativado perde o acesso
- **QUANDO** o Administrador desativa outro administrador
- **ENTÃO** ele não consegue mais fazer login, e as requisições com o token que já tinha passam a ser recusadas

### Requirement: Trocar o perfil de um usuário
O Administrador DEVE poder trocar o perfil de qualquer usuário, inclusive de outro Administrador, mas NÃO DEVE trocar o próprio perfil. A troca DEVE manter os cadastros coerentes, na mesma transação:
- o cadastro do perfil antigo (médico ou Recepção/Triagem) DEVE ser desativado, preservando o histórico;
- ao virar Médico, DEVEM ser informados CRM e ao menos uma especialidade ativa (sala opcional);
- ao virar Recepção/Triagem, DEVE ser informado CPF válido e único (especialidade de referência opcional);
- se o usuário já teve aquele cadastro, ele DEVE ser reativado e atualizado com os dados informados, em vez de duplicado;
- ao virar Administrador, nenhum dado adicional é pedido.

A troca NÃO DEVE ser feita em médico com ficha CHAMADO pendente. A partir da próxima requisição, o backend DEVE autorizar o usuário pelo novo perfil. A troca DEVE ser auditada.

#### Scenario: Recepção vira Médico
- **QUANDO** o Administrador troca o perfil de uma pessoa da Recepção/Triagem para Médico, informando CRM e Cardiologia
- **ENTÃO** o cadastro de Recepção/Triagem é desativado, o cadastro de médico é criado ativo com Cardiologia, e na próxima requisição a pessoa é tratada como Médico

#### Scenario: Faltam os dados do novo perfil
- **QUANDO** a troca para Médico é pedida sem CRM ou sem especialidade, ou a troca para Recepção/Triagem sem CPF válido
- **ENTÃO** a troca é recusada e nada é alterado

#### Scenario: Volta a um perfil anterior
- **QUANDO** um usuário que já foi Médico volta a ser Médico
- **ENTÃO** o cadastro de médico existente é reativado e atualizado, sem criar outro

#### Scenario: Trocar o próprio perfil
- **QUANDO** o Administrador tenta trocar o próprio perfil
- **ENTÃO** a operação é recusada

#### Scenario: Médico com ficha chamada
- **QUANDO** o Administrador tenta trocar o perfil de um médico que tem ficha CHAMADO pendente
- **ENTÃO** a operação é recusada

#### Scenario: Troca de perfil com sessão aberta
- **QUANDO** o perfil de um usuário é alterado enquanto ele tem uma sessão ativa
- **ENTÃO** a partir da próxima requisição, o backend autoriza esse usuário pelo novo perfil

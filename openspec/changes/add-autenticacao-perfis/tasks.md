# Tarefas

## 1. Estrutura do projeto

- [ ] 1.1 Criar a estrutura de pastas `frontend/`, `backend/xano/` e `tests/api/` (design D8) e o `.env.example` com `XANO_API_URL`, `TEST_ADMIN_EMAIL` e `TEST_ADMIN_SENHA` sem valores reais; verificar que as pastas existem e que `.env` está no `.gitignore`
- [ ] 1.2 Inicializar o app Reflex em `frontend/` (`reflex init`) e verificar que `reflex run` abre a página padrão em `http://localhost:3000`
- [ ] 1.3 Configurar o ambiente de testes (`requirements-dev.txt` com pytest, httpx e python-dotenv; `tests/api/conftest.py` lendo o `.env`) e verificar que `pytest tests/api` roda sem erros de importação
- [ ] 1.4 Criar o `README.md` com instruções de setup (variáveis de ambiente, como rodar o frontend e os testes) e verificar seguindo os passos em uma pasta limpa

## 2. Xano — modelo de dados e verificação de acesso

- [ ] 2.1 [Xano] Criar a tabela `usuario` como tabela de autenticação (`nome`, `email` único em minúsculas, `password`, `perfil` enum RECEPCAO_TRIAGEM/MEDICO/ADMINISTRADOR, `ativo` bool padrão true) e verificar no painel que o índice único de `email` recusa duplicatas
- [ ] 2.2 [Xano] Criar a tabela `sessao` (`usuario_id`, `login_em`, `logout_em` nulo, `expira_em`) e verificar a relação com `usuario` no painel
- [ ] 2.3 [Xano] Criar a variável de ambiente `TOKEN_TTL_SEGUNDOS=43200` (D4) e verificar que ela é lida por um endpoint de teste
- [ ] 2.4 [Xano] Criar a função `verificar_acesso(perfis_permitidos)`, que recarrega o usuário, responde 401 se ele não existir ou estiver inativo e 403 se o perfil não for permitido (D3); verificar com o Run & Debug do Xano nos três casos
- [ ] 2.5 [Xano] Inserir o primeiro Administrador manualmente (D10), documentar o passo no README e verificar que o registro existe com `ativo=true`
- [ ] 2.6 Exportar o XanoScript das tabelas e da função para `backend/xano/` e verificar que os arquivos estão no repositório

## 3. Xano — endpoints de autenticação

- [ ] 3.1 [Xano] Implementar `POST auth/login`: valida os campos obrigatórios, usa a mesma mensagem genérica para e-mail e senha inválidos, recusa usuário inativo, emite o token com o TTL configurado, cria a `sessao` e retorna token, nome e perfil; verificar com os testes 3.4
- [ ] 3.2 [Xano] Implementar `GET auth/me` (autenticado + `verificar_acesso` com todos os perfis), que retorna id, nome e perfil; verificar com os testes 3.4
- [ ] 3.3 [Xano] Implementar `POST auth/logout`, que preenche `logout_em` na sessão aberta mais recente; verificar com os testes 3.4
- [ ] 3.4 Escrever `tests/api/test_autenticacao.py` cobrindo: login bem-sucedido, credenciais inválidas (mensagem idêntica), campos ausentes, usuário inativo, `me` sem token, com token adulterado e com usuário desativado após o login, login criando sessão, login recusado sem sessão, logout encerrando a sessão; verificar que `pytest tests/api/test_autenticacao.py` passa
- [ ] 3.5 Exportar o XanoScript dos endpoints para `backend/xano/` e verificar que os arquivos estão no repositório

## 4. Xano — gestão de usuários

- [ ] 4.1 [Xano] Implementar `GET usuarios` (somente ADMINISTRADOR), com filtros opcionais de `perfil` e `ativo`, sem retornar `password`; verificar com os testes 4.5
- [ ] 4.2 [Xano] Implementar `POST usuarios` com as validações de nome, formato e unicidade do e-mail (case-insensitive), perfil válido e senha de 8 ou mais caracteres; verificar com os testes 4.5
- [ ] 4.3 [Xano] Implementar `PATCH usuarios/{id}` (nome, e-mail, perfil) e `PUT usuarios/{id}/senha`, com as mesmas validações e a regra do último administrador ao trocar de perfil (D9); verificar com os testes 4.5
- [ ] 4.4 [Xano] Implementar `PATCH usuarios/{id}/ativo`, que recusa desativar a si mesmo e desativar o último administrador ativo (D9); verificar com os testes 4.5
- [ ] 4.5 Escrever `tests/api/test_gestao_usuarios.py` cobrindo: 403 para Recepção/Triagem e Médico em cada operação, listagem sem senha, filtros, criação válida seguida de login, e-mail duplicado com outra caixa, dados inválidos, edição, troca de perfil valendo na próxima requisição, redefinição de senha (a antiga para de funcionar), senha curta, desativação invalidando o token existente, reativação, autodesativação e último administrador; usar usuários `teste_` desativados no teardown; verificar que `pytest tests/api` passa por completo
- [ ] 4.6 Exportar o XanoScript para `backend/xano/` e verificar que os arquivos estão no repositório

## 5. Reflex — login, sessão e rotas

- [ ] 5.1 [Reflex] Criar `api.py`, um cliente HTTP único que lê `XANO_API_URL`, injeta `Authorization` e converte 401 em "sessão expirada → /login" (D6); verificar que o app sobe sem erros e que uma chamada com token inválido redireciona para `/login`
- [ ] 5.2 [Reflex] Criar o `AuthState` com o token em `rx.LocalStorage`, `nome` e `perfil`, e os eventos `login`, `logout` e `verificar_sessao(perfil_exigido)`; verificar que o token persiste após recarregar a página
- [ ] 5.3 [Reflex] Criar a página `/login` (e-mail, senha, mensagens de erro vindas da API, botão desabilitado durante o envio) que redireciona conforme o perfil (D7); verificar manualmente o login dos três perfis
- [ ] 5.4 [Reflex] Criar as páginas iniciais `/recepcao`, `/medico` e `/admin` com nome, perfil e botão "Sair", protegidas por `on_load=verificar_sessao`; verificar manualmente: sem login → `/login`; perfil errado → área do próprio perfil; "Sair" → `/login`; "voltar" após sair → `/login`

## 6. Reflex — gestão de usuários

- [ ] 6.1 [Reflex] Criar a página `/admin/usuarios` com tabela (nome, e-mail, perfil, situação) e filtros de perfil e situação, protegida para ADMINISTRADOR; verificar manualmente a listagem e os filtros
- [ ] 6.2 [Reflex] Criar o formulário de criação e edição de usuário, com as mensagens de validação da API exibidas no campo correspondente; verificar manualmente a criação, o e-mail duplicado e a senha curta
- [ ] 6.3 [Reflex] Adicionar as ações "Redefinir senha" e "Ativar/Desativar", com confirmação e mensagens de erro (autodesativação, último administrador); verificar manualmente cada caso
- [ ] 6.4 Adicionar ao README o roteiro de verificação manual das seções 5 e 6 e verificar executando-o do início ao fim

## 7. Integração e documentação

- [ ] 7.1 Verificação ponta a ponta: o Administrador cria um usuário Médico, o Médico faz login e vê a própria área, o Administrador o desativa e a próxima ação do Médico o leva a `/login`; verificar executando o fluxo com a app rodando e confirmando as sessões no Xano
- [ ] 7.2 Atualizar `docs/domain-model.md` (Usuário e Sessão) com o que foi implementado e verificar que ele bate com as tabelas do Xano

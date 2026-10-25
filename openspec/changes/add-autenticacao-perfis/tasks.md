# Tarefas

## 1. Estrutura do projeto

- [x] 1.1 Manter a estrutura existente (design D8 revisado): `frontend/ps_fila_prioritaria/`, `frontend/tests/` e `backend/xano/`; incluir `XANO_AUTH_API_URL` no `frontend/.env.example` sem valor real; verificar que `.env` está no `.gitignore`
  - Evidência (25/10/2026): `.env.example` atualizado; `git check-ignore` confirma `frontend/.env` ignorado.
- [x] 1.2 App Reflex já inicializado em `frontend/`; verificar que `reflex run` abre o app em `http://localhost:3000`
  - Evidência: `reflex run` subiu e `/login` respondeu 200; `reflex compile --dry` sem erros.
- [x] 1.3 Configurar o ambiente de testes de API em `frontend/tests` com credenciais de teste lidas do `.env` (`TEST_ADMIN_EMAIL`, `TEST_ADMIN_SENHA`, sem valores no repositório) e verificar que os testes rodam sem erros de importação
  - Evidência (25/10/2026): `frontend/tests/test_api_autenticacao.py` lê `XANO_AUTH_API_URL` e `TEST_ADMIN_*`, `TEST_RECEPCAO_*`, `TEST_MEDICO_*` do `.env` (ignora os testes sem elas) e usa os certificados do sistema operacional, como o teste de integração existente.
- [x] 1.4 README com instruções de setup já existe (seção "Executar localmente"); o passo do primeiro Administrador entra na tarefa 2.5

## 2. Xano — modelo de dados e verificação de acesso

- [x] 2.1 [Xano] Conferir a tabela `usuario` como tabela de autenticação (`nome`, `email` único em minúsculas, `password` mínimo 8, `perfil` enum RECEPCAO_TRIAGEM/MEDICO/ADMINISTRADOR, `ativo` padrão true)
  - Evidência (25/10/2026): `usuario.xs` com `auth = true` e índice único em `email`; o `workspace pull` da `v1` é idêntico ao repositório.
- [x] 2.2 [Xano] Conferir a tabela `sessao` (`usuario_id` → `usuario`, `login_em`, `logout_em` nulo, `expira_em`)
  - Evidência: `sessao.xs` no servidor igual ao repositório (inclui `status_operacional`, usado depois por `add-acompanhamento-administrador`).
- [x] 2.3 [Xano] Criar a variável de ambiente `TOKEN_TTL_SEGUNDOS=43200` (D4) e verificar que ela é lida pelo `auth/login`
  - Evidência: variável criada na `v1` (confirmada por `workspace pull --env`); login dos três perfis devolve token, o que só ocorre com a variável lida (sem ela o endpoint recusa).
- [ ] 2.4 [Xano] Criar a função `auth/verificar_acesso(usuario_id, perfis_permitidos)`, que recarrega o usuário, responde 401 se ele não existir ou estiver inativo e 403 se o perfil não for permitido (D3); verificar nos três casos
  - Parcial: função publicada; caso de usuário ativo verificado (`auth/me` 200 para o Administrador). Faltam usuário inativo (depende de desativar, grupo 4) e perfil não permitido (só há endpoint restrito por perfil a partir do grupo 4).
- [x] 2.5 [Xano] Inserir o primeiro Administrador manualmente (D10), documentar o passo no README e verificar que o registro existe com `ativo=true`
  - Evidência: PO criou Administrador, Recepção/Triagem e Médico de teste pelo painel (25/10/2026); login do Administrador funciona; passo documentado no README ("Primeiro administrador").
- [x] 2.6 Exportar o XanoScript das tabelas e da função para `backend/xano/` e verificar que os arquivos estão no repositório
  - Evidência: `function/auth/verificar_acesso.xs` e `api/autenticacao/*.xs` versionados com os GUIDs do servidor.

## 3. Xano — endpoints de autenticação

- [ ] 3.1 [Xano] Implementar `POST auth/login`: valida os campos obrigatórios, usa a mesma mensagem genérica para e-mail e senha inválidos, recusa usuário inativo, emite o token com o TTL configurado, cria a `sessao` e retorna token, nome e perfil; verificar com os testes 3.4
  - Parcial: verificado ao vivo (8 testes de `test_api_autenticacao.py` passando): login válido dos três perfis com token/nome/perfil, e-mail com maiúsculas e espaços, senha errada e e-mail inexistente com a mesma mensagem, campos ausentes. Faltam usuário inativo (grupo 4) e conferir o registro em `sessao` (não há consulta de sessões nesta change; conferir no painel ou na `add-acompanhamento-administrador`).
- [ ] 3.2 [Xano] Implementar `GET auth/me` (autenticado + `verificar_acesso` com todos os perfis), que retorna id, nome e perfil; verificar com os testes 3.4
  - Parcial: verificado ao vivo com token válido (200, sem `password`), sem token (401) e com token adulterado (401). Falta usuário desativado com token ainda válido (grupo 4).
- [ ] 3.3 [Xano] Implementar `POST auth/logout`, que preenche `logout_em` na sessão aberta mais recente; verificar com os testes 3.4
  - Parcial: verificado ao vivo com token válido (200 `{"encerrada": true}`) e sem token (401). Falta conferir `logout_em` preenchido na tabela `sessao` (painel do Xano).
- [ ] 3.4 Escrever `tests/api/test_autenticacao.py` cobrindo: login bem-sucedido, credenciais inválidas (mensagem idêntica), campos ausentes, usuário inativo, `me` sem token, com token adulterado e com usuário desativado após o login, login criando sessão, login recusado sem sessão, logout encerrando a sessão; verificar que `pytest tests/api/test_autenticacao.py` passa
- [x] 3.5 Exportar o XanoScript dos endpoints para `backend/xano/` e verificar que os arquivos estão no repositório
  - Evidência: `backend/xano/api/autenticacao/` (api_group, auth_login_post, auth_me_get, auth_logout_post) com GUIDs do servidor.

## 4. Xano — gestão de usuários

- [ ] 4.1 [Xano] Implementar `GET usuarios` (somente ADMINISTRADOR), com filtros opcionais de `perfil` e `ativo`, sem retornar `password`; verificar com os testes 4.5
- [ ] 4.2 [Xano] Implementar `POST usuarios` com as validações de nome, formato e unicidade do e-mail (case-insensitive), perfil válido e senha de 8 ou mais caracteres; verificar com os testes 4.5
- [ ] 4.3 [Xano] Implementar `PATCH usuarios/{id}` (nome, e-mail, perfil) e `PUT usuarios/{id}/senha`, com as mesmas validações e a regra do último administrador ao trocar de perfil (D9); verificar com os testes 4.5
- [ ] 4.4 [Xano] Implementar `PATCH usuarios/{id}/ativo`, que recusa desativar a si mesmo e desativar o último administrador ativo (D9); verificar com os testes 4.5
- [ ] 4.5 Escrever `tests/api/test_gestao_usuarios.py` cobrindo: 403 para Recepção/Triagem e Médico em cada operação, listagem sem senha, filtros, criação válida seguida de login, e-mail duplicado com outra caixa, dados inválidos, edição, troca de perfil valendo na próxima requisição, redefinição de senha (a antiga para de funcionar), senha curta, desativação invalidando o token existente, reativação, autodesativação e último administrador; usar usuários `teste_` desativados no teardown; verificar que `pytest tests/api` passa por completo
- [ ] 4.6 Exportar o XanoScript para `backend/xano/` e verificar que os arquivos estão no repositório

## 5. Reflex — login, sessão e rotas

- [x] 5.1 [Reflex] Criar `api.py`, um cliente HTTP pequeno que lê a URL do grupo no `.env` (`XANO_AUTH_API_URL`) e injeta `Authorization`; o `AuthState` converte 401 em "sessão expirada → /login" (D6); verificar que o app sobe sem erros e que uma chamada com token inválido redireciona para `/login`
  - Evidência: `frontend/ps_fila_prioritaria/api.py`; app compila e sobe; `test_auth_state.py` cobre 401 → limpa sessão e vai para `/login`.
- [ ] 5.2 [Reflex] Criar o `AuthState` com o token em `rx.LocalStorage`, `nome` e `perfil`, e os eventos `entrar`, `sair` e `verificar_sessao(perfil_exigido)`; verificar que o token persiste após recarregar a página
  - Parcial: implementado e coberto por 10 testes de estado (20 execuções); falta a verificação manual de recarga com um usuário real.
- [ ] 5.3 [Reflex] Criar a página `/login` (e-mail, senha, mensagens de erro vindas da API, botão desabilitado durante o envio) que redireciona conforme o perfil (D7); verificar manualmente o login dos três perfis
  - Parcial: página conforme o Figma (tela A), sem o link "Esqueci minha senha" até o grupo 6A existir; falta o login manual dos três perfis.
- [ ] 5.4 [Reflex] Criar as páginas iniciais `/recepcao`, `/medico` e `/admin` com nome, perfil e botão "Sair", protegidas por `on_load=verificar_sessao`; verificar manualmente: sem login → `/login`; perfil errado → área do próprio perfil; "Sair" → `/login`; "voltar" após sair → `/login`
  - Parcial: páginas criadas; as telas existentes `/recepcao/pacientes` e `/recepcao/ficha/[id]` também ficaram protegidas para Recepção/Triagem. Verificado no navegador: `/recepcao` sem login mostra o login. Faltam os demais itens manuais com usuário real.

## 6. Reflex — gestão de usuários

- [ ] 6.1 [Reflex] Criar a página `/admin/usuarios` com tabela (nome, e-mail, perfil, situação) e filtros de perfil e situação, protegida para ADMINISTRADOR; verificar manualmente a listagem e os filtros
- [ ] 6.2 [Reflex] Criar o formulário de criação e edição de usuário, com as mensagens de validação da API exibidas no campo correspondente; verificar manualmente a criação, o e-mail duplicado e a senha curta
- [ ] 6.3 [Reflex] Adicionar as ações "Redefinir senha" e "Ativar/Desativar", com confirmação e mensagens de erro (autodesativação, último administrador); verificar manualmente cada caso
- [ ] 6.4 Adicionar ao README o roteiro de verificação manual das seções 5 e 6 e verificar executando-o do início ao fim

## 6A. Redefinição de senha pelo próprio usuário (D12)

- [ ] 6A.1 [PO] Escolher o provedor de e-mail transacional, criar a conta com remetente verificado e cadastrar `EMAIL_API_KEY` e `EMAIL_REMETENTE` como variáveis de ambiente do Xano; verificar um envio de teste pelo painel do provedor
- [ ] 6A.2 [PO] Publicar a tabela `codigo_redefinicao_senha` (D12) e as variáveis `CODIGO_SENHA_TTL_SEGUNDOS=600`, `CODIGO_SENHA_REENVIO_SEGUNDOS=60` e `CODIGO_SENHA_TENTATIVAS=5`; verificar o `.xs` exportado em `backend/xano/table/`
- [ ] 6A.3 [Xano] Implementar `POST auth/senha/solicitar`, com resposta idêntica para qualquer e-mail, envio só para usuário ativo, bloqueio de reenvio antes de 60 s e invalidação do código anterior; verificar com os testes 6A.6
- [ ] 6A.4 [Xano] Implementar `POST auth/senha/verificar` (código com hash, validade, limite de 5 tentativas, token de redefinição de uso único) e `POST auth/senha/redefinir` (senha de 8 ou mais caracteres, código marcado como usado, sessões abertas encerradas, recusa para usuário desativado); verificar com os testes 6A.6
- [ ] 6A.5 [Reflex] Criar as telas do fluxo "Esqueci minha senha" conforme o Figma (A1 a A4: e-mail, código, código inválido, nova senha e sucesso) com o link na tela de login e o contador de reenvio; verificar manualmente o fluxo completo com um e-mail real de teste
- [ ] 6A.6 Escrever `tests/api/test_redefinicao_senha.py` cobrindo todos os cenários do requisito "Redefinição de senha pelo próprio usuário", com os valores-limite de 59/60 s no reenvio, 9 min 59 s/10 min na validade, 5ª/6ª tentativa e senha de 7/8 caracteres, simulando o envio de e-mail no ambiente de teste; verificar que passam
- [ ] 6A.7 Exportar o XanoScript dos endpoints para `backend/xano/` e verificar que os arquivos estão no repositório

## 7. Integração e documentação

- [ ] 7.1 Verificação ponta a ponta: o Administrador cria um usuário Médico, o Médico faz login e vê a própria área, o Administrador o desativa e a próxima ação do Médico o leva a `/login`; verificar executando o fluxo com a app rodando e confirmando as sessões no Xano
- [ ] 7.2 Atualizar `docs/domain-model.md` (Usuário e Sessão) com o que foi implementado e verificar que ele bate com as tabelas do Xano

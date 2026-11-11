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
- [x] 2.4 [Xano] Criar a função `auth/verificar_acesso(usuario_id, perfis_permitidos)`, que recarrega o usuário, responde 401 se ele não existir ou estiver inativo e 403 se o perfil não for permitido (D3); verificar nos três casos
  - Evidência (26/10/2026, validação manual no Xano): usuário de teste ativo com perfil permitido foi autorizado; o mesmo usuário com perfil fora de `perfis_permitidos` retornou 403; após emitir token válido e desativar um usuário de teste, `GET auth/me` retornou 401. O usuário de teste foi restaurado ao estado ativo.
- [x] 2.5 [Xano] Inserir o primeiro Administrador manualmente (D10), documentar o passo no README e verificar que o registro existe com `ativo=true`
  - Evidência: PO criou Administrador, Recepção/Triagem e Médico de teste pelo painel (25/10/2026); login do Administrador funciona; passo documentado no README ("Primeiro administrador").
- [x] 2.6 Exportar o XanoScript das tabelas e da função para `backend/xano/` e verificar que os arquivos estão no repositório
  - Evidência: `function/auth/verificar_acesso.xs` e `api/autenticacao/*.xs` versionados com os GUIDs do servidor.

## 3. Xano — endpoints de autenticação

- [ ] 3.1 [Xano] Implementar `POST auth/login`: valida os campos obrigatórios, usa a mesma mensagem genérica para e-mail e senha inválidos, recusa usuário inativo, emite o token com o TTL configurado, cria a `sessao` e retorna token, nome e perfil; verificar com os testes 3.4
  - Atenção (25/10/2026): com o código no login (D13), o `auth/login` deixa de devolver o token; a mudança está na tarefa 3A.3.
  - Parcial: verificado ao vivo (8 testes de `test_api_autenticacao.py` passando): login válido dos três perfis com token/nome/perfil, e-mail com maiúsculas e espaços, senha errada e e-mail inexistente com a mesma mensagem, campos ausentes. Faltam usuário inativo (grupo 4) e conferir o registro em `sessao` (não há consulta de sessões nesta change; conferir no painel ou na `add-acompanhamento-administrador`).
- [ ] 3.2 [Xano] Implementar `GET auth/me` (autenticado + `verificar_acesso` com todos os perfis), que retorna id, nome e perfil; verificar com os testes 3.4
  - Parcial: verificado ao vivo com token válido (200, sem `password`), sem token (401) e com token adulterado (401). Falta usuário desativado com token ainda válido (grupo 4).
- [ ] 3.3 [Xano] Implementar `POST auth/logout`, que preenche `logout_em` na sessão aberta mais recente; verificar com os testes 3.4
  - Parcial: verificado ao vivo com token válido (200 `{"encerrada": true}`) e sem token (401). Falta conferir `logout_em` preenchido na tabela `sessao` (painel do Xano).
- [ ] 3.4 Escrever `tests/api/test_autenticacao.py` cobrindo: login bem-sucedido, credenciais inválidas (mensagem idêntica), campos ausentes, usuário inativo, `me` sem token, com token adulterado e com usuário desativado após o login, login criando sessão, login recusado sem sessão, logout encerrando a sessão; verificar que `pytest tests/api/test_autenticacao.py` passa
- [x] 3.5 Exportar o XanoScript dos endpoints para `backend/xano/` e verificar que os arquivos estão no repositório
  - Evidência: `backend/xano/api/autenticacao/` (api_group, auth_login_post, auth_me_get, auth_logout_post) com GUIDs do servidor.

## 3A. Código de verificação no login (D13)

- [x] 3A.1 Criar na Brevo os modelos de e-mail do código de login e da redefinição de senha, com a identidade visual do PS, e versionar o HTML em `backend/brevo/`; verificar que aparecem na lista de modelos da conta
  - Evidência (25/10/2026): `ps_codigo_acesso_login` (templateId 6) e `ps_redefinicao_senha` (templateId 7) criados pela API da Brevo, ativos, com o remetente de `BREVO_REMETENTE`; parâmetros `nome`, `codigo` e `minutos`; prévias aprovadas pelo PO.
- [x] 3A.2 [PO] Publicar a tabela `codigo_verificacao` (D12, finalidades `LOGIN` e `REDEFINICAO_SENHA`) e as variáveis `CODIGO_TTL_SEGUNDOS=600`, `CODIGO_REENVIO_SEGUNDOS=60` e `CODIGO_TENTATIVAS=5`; verificar o `.xs` exportado em `backend/xano/table/` e as variáveis por `workspace pull --env`
  - Evidência (25/10/2026): `table/codigo_verificacao.xs` publicado na `v1` (com o campo `iniciado_em`, que guarda o início do pedido para a janela de reenvio do login); `CODIGO_TTL_SEGUNDOS=600`, `CODIGO_REENVIO_SEGUNDOS=60` e `CODIGO_TENTATIVAS=5` confirmadas por `workspace pull --env`.
- [x] 3A.3 [Xano] Alterar `POST auth/login`: com senha correta e usuário ativo, invalidar o código `LOGIN` anterior, gerar um novo (hash), enviar o modelo 6 e responder `{codigo_enviado: true}`, sem token e sem sessão; verificar com os testes 3A.6
  - Evidência: publicado; ao vivo, senha correta dos três perfis responde `codigo_enviado` sem `token`. A emissão e o envio ficam na função `auth/emitir_codigo`, reutilizada pelo reenvio e, depois, pela redefinição de senha.
- [x] 3A.4 [Xano] Implementar `POST auth/login/verificar` (código com hash, validade, limite de 5 tentativas, recusa de usuário desativado; emite o token com `TOKEN_TTL_SEGUNDOS`, cria a `sessao` e devolve token, nome e perfil) e `POST auth/login/reenviar` (só dentro dos 10 minutos do primeiro passo, bloqueio antes de 60 s, invalida o código anterior); verificar com os testes 3A.6
  - Evidência: publicados, com a conferência na função `auth/conferir_codigo`; ao vivo: código errado (6 tentativas recusadas, sem token), código ausente (400), reenvio cedo (429 "Aguarde N segundos…") e reenvio sem login pendente (403).
  - Validado pelo PO em 25/10/2026: fluxo completo com e-mail real nos testes manuais.
- [x] 3A.5 [Reflex] Criar a tela `/login/codigo` no padrão da tela A2 do Figma (6 dígitos, botão desabilitado durante o envio, contador de reenvio de 60 s, aviso "Não recebeu? Confira a caixa de spam", "Voltar ao login"); o `AuthState` guarda só o e-mail entre as etapas, nunca a senha; atualizar `test_auth_state.py`; verificar manualmente o login dos três perfis com e-mail real
  - Evidência: tela `/login/codigo` e `AuthState` (`verificar_codigo`, `reenviar_codigo`, contador em segundo plano, guarda `exigir_login_pendente`) criados; `reflex compile` sem erros; 17 testes de estado passando.
  - Validado pelo PO em 25/10/2026: fluxo completo com e-mail real nos testes manuais.
- [ ] 3A.6 Atualizar `test_api_autenticacao.py` (o login passa a responder `codigo_enviado`) e cobrir: código errado, limite de 5 tentativas, reenvio antes de 60 s, reenvio sem login pendente e nenhuma sessão criada sem código; o caminho feliz até o token, a validade de 9 min 59 s/10 min e o reenvio após 10 minutos ficam no roteiro manual (D13); verificar que passam
  - Parcial: `test_api_autenticacao.py` com 11 testes ao vivo passando. Falta conferir que nenhuma sessão é criada sem o código (não há consulta de sessões nesta change; conferir no painel do Xano).
- [x] 3A.7 Exportar o XanoScript dos endpoints para `backend/xano/` e verificar que os arquivos estão no repositório
  - Evidência: `codigo_verificacao.xs`, `function/auth/emitir_codigo.xs`, `function/auth/conferir_codigo.xs`, `auth_login_verificar_post.xs` e `auth_login_reenviar_post.xs` versionados com os GUIDs do servidor.

## 3B. Recuperação de acesso do Médico

- [x] 3B.1 [Xano] Permitir novo login médico com sessão anterior ativa sem conceder disponibilidade automática; no logout, encerrar todas as sessões ativas desse Médico; verificar com os testes 3B.2
- [x] 3B.2 [Teste] Cobrir em `tests/api/test_recuperacao_sessao_medico.py` o primeiro login, novo login após perda de acesso, PAUSA/AUSENTE preservados na sessão anterior, logout de todas as sessões, expiração e duas verificações concorrentes do mesmo código; verificar também que a nova sessão fica indisponível até ação explícita
  - Evidência (11/11/2026): `unittest discover -s tests/api -p test_recuperacao_sessao_medico.py -v` passou contra a `v1` em 86 s; o cenário sintético confirmou sessões anteriores em PAUSA/AUSENTE, nova sessão sem disponibilidade, ativação manual, logout de todas as sessões, expiração e uso único do código em duas verificações concorrentes.
- [x] 3B.3 [Reflex] Mostrar a disponibilidade da sessão e permitir ativação explícita pela tela médica na change `add-acompanhamento-administrador`; verificar sem navegador por teste de estado e compilação
  - Evidência (11/11/2026): 10 testes de `test_medico_state.py` passaram; `reflex compile --dry` concluiu com sucesso.
- [x] 3B.4 [Documentação] Exportar o XanoScript revisado da autenticação para `backend/xano/` e registrar a verificação da recuperação de acesso nesta change, sem editar o README
  - Evidência (11/11/2026): `auth_login_verificar_post.xs`, `auth_logout_post.xs` e `me_status_patch.xs` conferidos com os documentos publicados na `v1`; função sintética `auth/teste_sessao_unica.xs` publicada e exportada com GUID.

## 4. Xano — gestão de usuários (revisada pelo PO em 11/11/2026, D14)

- [x] 4.1 [Xano] `GET usuarios` (só ADMINISTRADOR): todos os usuários com nome, e-mail, perfil e situação, sem `password`
- [x] 4.2 [Xano] `POST usuarios`: cria só **Administrador** (nome, e-mail único sem diferenciar maiúsculas, senha de 8 ou mais), auditado sem a senha
- [x] 4.3 [Xano] `PATCH usuarios/{id}` (nome e e-mail de administrador) e `PATCH usuarios/{id}/ativo` (só administradores; recusa a si mesmo e o último administrador ativo, D9)
- [x] 4.4 [Xano] `PATCH usuarios/{id}/perfil` (D14):
  - desativa o cadastro antigo e reativa ou cria o novo, com os dados exigidos;
  - recusa o próprio perfil, o último administrador e o médico com ficha CHAMADO;
  - auditado.

  Com a função `usuarios/deixa_sem_admin`. Verificar com `xano_validate_xanoscript`
  - Evidência (11/11/2026): `api/cadastros/usuarios_get.xs`, `usuarios_post.xs`, `usuarios_id_patch.xs`, `usuarios_id_ativo_patch.xs`, `usuarios_id_perfil_patch.xs` e `function/usuarios/deixa_sem_admin.xs` (3 testes inline) válidos no `xano_validate_xanoscript`; `--dry-run` na `v1` mostra só 6 criações.
- [x] 4.5 Testes:
  - teste inline da regra de último administrador;
  - testes de estado da tela com a API simulada.

  Verificar que a suíte unitária passa
  - Evidência (11/11/2026): 3 testes inline em `usuarios/deixa_sem_admin` (rodam no `unit_test run_all` após o push); 10 testes de estado em `frontend/tests/test_usuarios_state.py` passando; suíte do frontend com 235 aprovados. Só falham os testes de API que fazem login com as contas de teste de Recepção e Médico (credencial), sem relação com esta tarefa.
- [x] 4.6 Publicar na `v1` (`--dry-run` antes; o PO roda o push) e rodar `xano unit_test run_all`
  - Evidência (11/11/2026): o PO publicou os 10 documentos na `v1` (6 criados, 4 atualizados; GUIDs sincronizadas no repositório); `xano unit_test run_all`: 105 passaram, 0 falharam, incluindo os 3 de `usuarios/deixa_sem_admin`.

## 5. Reflex — login, sessão e rotas

- [x] 5.1 [Reflex] Criar `api.py`, um cliente HTTP pequeno que lê a URL do grupo no `.env` (`XANO_AUTH_API_URL`) e injeta `Authorization`; o `AuthState` converte 401 em "sessão expirada → /login" (D6); verificar que o app sobe sem erros e que uma chamada com token inválido redireciona para `/login`
  - Evidência: `frontend/ps_fila_prioritaria/api.py`; app compila e sobe; `test_auth_state.py` cobre 401 → limpa sessão e vai para `/login`.
- [x] 5.2 [Reflex] Criar o `AuthState` com o token em `rx.LocalStorage`, `nome` e `perfil`, e os eventos `entrar`, `sair` e `verificar_sessao(perfil_exigido)`; verificar que o token persiste após recarregar a página
  - Evidência: 10 testes de estado; roteiro manual executado pelo PO em 25/10/2026 (inclui recarregar a página logado).
- [x] 5.3 [Reflex] Criar a página `/login` (e-mail, senha, mensagens de erro vindas da API, botão desabilitado durante o envio) que redireciona conforme o perfil (D7); verificar manualmente o login dos três perfis
  - Evidência: página conforme o Figma (tela A); login validado manualmente pelo PO em 25/10/2026. O link "Esqueci minha senha" entra com o grupo 6A.
- [x] 5.4 [Reflex] Criar as páginas iniciais `/recepcao`, `/medico` e `/admin` com nome, perfil e botão "Sair", protegidas por `on_load=verificar_sessao`; verificar manualmente: sem login → `/login`; perfil errado → área do próprio perfil; "Sair" → `/login`; "voltar" após sair → `/login`
  - Evidência: `/recepcao` sem login mostra o login (verificado em navegador headless); roteiro manual completo executado pelo PO em 25/10/2026. As telas `/recepcao/pacientes` e `/recepcao/ficha/[id]` também ficaram protegidas para Recepção/Triagem.

## 6. Reflex — gestão de usuários (revisada pelo PO em 11/11/2026, D14)

- [x] 6.1 [Reflex] Página `/admin/usuarios` (aba "Usuários" no menu do Administrador):
  - tabela com nome, e-mail, perfil e situação, filtros de perfil e situação e busca;
  - protegida para ADMINISTRADOR.

  Verificar que o app compila e abre
- [x] 6.2 [Reflex] "Novo administrador", edição de administrador e "Ativar/Desativar" (só em administradores; médicos e Recepção apontam para os cadastros), com as mensagens da API
- [x] 6.3 [Reflex] "Trocar perfil" em qualquer usuário, exceto o próprio:
  - o diálogo pede os dados do perfil novo (CRM e especialidades para Médico; CPF para Recepção/Triagem);
  - confirmação antes de salvar.
  - Evidência (11/11/2026): `estados/usuarios.py` e `paginas/usuarios.py`; aba "Usuários" em `ABAS_ADMIN`; rota protegida por `verificar_sessao("ADMINISTRADOR")`; mensagens `ULTIMO_ADMINISTRADOR`, `PROPRIO_PERFIL` e `USUARIO_EDITADO_NOS_CADASTROS` em `comum.py`; página renderiza e `reflex compile --dry` concluiu.
- [ ] 6.4 Roteiro manual das seções 5 e 6 executado pelo PO

## 6A. Redefinição de senha pelo próprio usuário (D12)

- [x] 6A.1 [PO] Configurar a Brevo: chave de API e remetente verificado como variáveis de ambiente do Xano (`BREVO_API_KEY`, `BREVO_REMETENTE`); verificar um envio de teste
  - Evidência (25/10/2026): `BREVO_API_KEY` válida (`GET /v3/account` 200, plano free); `BREVO_REMETENTE` cadastrado; envio de teste `POST /v3/smtp/email` 201 recebido pelo PO, porém na pasta de spam ("por brevosend.com"), porque o domínio do remetente não autentica a Brevo (SPF/DKIM).
- [x] 6A.2 [PO] Tabela e variáveis dos códigos: feitas na tarefa 3A.2 (tabela `codigo_verificacao` compartilhada, D12); verificar que a finalidade `REDEFINICAO_SENHA` está no enum
  - Evidência (25/10/2026): o enum `finalidade` da `codigo_verificacao` publicada tem `REDEFINICAO_SENHA`; as variáveis são as da 3A.2.
- [x] 6A.3 [Xano] Implementar `POST auth/senha/solicitar`, com resposta idêntica para qualquer e-mail, envio só para usuário ativo (modelo 7 da Brevo), bloqueio de reenvio antes de 60 s e invalidação do código anterior; verificar com os testes 6A.6
  - Evidência: publicado; ao vivo, e-mail inexistente e e-mail de usuário ativo recebem a mesma resposta ("Se o e-mail estiver cadastrado, enviamos um código"), campo vazio dá 400 e um segundo pedido imediato dá 429 "Aguarde N segundos…".
- [x] 6A.4 [Xano] Implementar `POST auth/senha/verificar` (código com hash, validade, limite de 5 tentativas; só confere, sem usar o código) e `POST auth/senha/redefinir` (e-mail, código e nova senha de 8 ou mais caracteres; código marcado como usado, sessões abertas encerradas, recusa para usuário desativado); verificar com os testes 6A.6
  - Evidência: publicados (D12 revisado: sem token de redefinição); ao vivo, código errado recusado nas 6 tentativas, senha de 7 caracteres recusada antes de usar o código, código errado não troca a senha e a senha anterior continua entrando.
  - Validado pelo PO em 25/10/2026: fluxo completo com e-mail real nos testes manuais.
- [x] 6A.5 [Reflex] Criar as telas do fluxo "Esqueci minha senha" conforme o Figma (A1 a A4: e-mail, código, código inválido, nova senha e sucesso) com o link na tela de login, o contador de reenvio e o aviso "Não recebeu? Confira a caixa de spam"; verificar manualmente o fluxo completo com um e-mail real de teste
  - Evidência: telas `/senha` (A1), `/senha/codigo` (A2/A2b), `/senha/nova` (A3) e `/senha/sucesso` (A4) e o link "Esqueci minha senha" no login, com o mesmo cartão das telas de login; A1 e login conferidas com o Figma por captura de tela; 9 testes de estado em `test_senha_state.py`.
  - Validado pelo PO em 25/10/2026: fluxo completo com e-mail real nos testes manuais.
- [ ] 6A.6 Escrever `frontend/tests/test_api_redefinicao_senha.py` cobrindo todos os cenários do requisito "Redefinição de senha pelo próprio usuário", com os valores-limite de 59/60 s no reenvio, 9 min 59 s/10 min na validade, 5ª/6ª tentativa e senha de 7/8 caracteres, simulando o envio de e-mail no ambiente de teste; verificar que passam
  - Parcial: 4 testes ao vivo passando (resposta genérica, reenvio cedo, tentativas, senha curta e senha anterior mantida). Os limites de tempo e o caminho feliz ficam no roteiro manual, como na D13, porque o código só chega por e-mail.
- [x] 6A.7 Exportar o XanoScript dos endpoints para `backend/xano/` e verificar que os arquivos estão no repositório
  - Evidência: `auth_senha_solicitar_post.xs`, `auth_senha_verificar_post.xs`, `auth_senha_redefinir_post.xs` e `conferir_codigo.xs` (opção `consumir`) versionados com os GUIDs do servidor.

## 7. Integração e documentação

- [ ] 7.1 Verificação ponta a ponta: o Administrador cria um usuário Médico (pelos cadastros), o Médico faz login e vê a própria área, o Administrador troca o perfil dele para Recepção/Triagem e a próxima requisição já usa o novo perfil, e depois o desativa e a próxima ação o leva a `/login`; verificar executando o fluxo com a app rodando e confirmando as sessões no Xano
- [ ] 7.2 Atualizar `docs/domain-model.md` (Usuário e Sessão) com o que foi implementado e verificar que ele bate com as tabelas do Xano

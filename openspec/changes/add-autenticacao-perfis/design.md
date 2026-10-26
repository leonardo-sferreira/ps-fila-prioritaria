# Design técnico

## Contexto

O projeto não tem código ainda (ver proposal.md, seção Por quê). A stack já está definida: frontend em **Reflex** (Python) e backend e banco no **Xano** (XanoScript). O Reflex consome a API REST do Xano. Esta change cria a base que todas as próximas changes vão reutilizar: tabela de usuários, verificação de perfil e proteção de rotas.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Um único ponto de verificação de perfil no Xano, reutilizado por todos os endpoints futuros.
- Estrutura de pastas e configuração do projeto definidas nesta change, para que as próximas não precisem decidir de novo.
- Testes de API automatizados que exercitem as regras de autorização.

**Fora dos objetivos:**
- Hierarquia de permissões configurável (papéis × permissões); os três perfis são fixos.
- Revogação individual de tokens (blacklist); a desativação é tratada pela checagem de `ativo` a cada requisição.

## Decisões

### D1. Autenticação nativa do Xano (tabela de autenticação + JWT)
A tabela `usuario` é marcada como tabela de autenticação do Xano, com campo `password` (hash gerenciado pelo Xano). Os endpoints `auth/login` e `auth/me` usam as funções nativas de criação e validação do token.
- **Por quê:** o Xano já faz hash de senha e emissão e validação de token com segurança; reimplementar isso seria risco sem ganho.
- **Alternativa considerada:** auth própria no Reflex, com banco separado. Descartada porque violaria "regras e persistência no Xano" e duplicaria a responsabilidade.

### D2. Perfil como enum na própria tabela `usuario`
Campo `perfil` do tipo enum: `RECEPCAO_TRIAGEM`, `MEDICO`, `ADMINISTRADOR`; mais `ativo` (bool), `nome` e `email` (único, gravado em minúsculas). Recepção/Triagem é um único perfil. `usuario` mantém somente dados de autenticação/autorização; os perfis Médico e Recepção/Triagem têm entidades de domínio próprias 1:1, criadas/atualizadas em fluxo administrativo conjunto na change `add-cadastros-administrador`.
- **Por quê:** cada usuário tem exatamente um perfil (domain-model), e os perfis são fixos.
- **Alternativa:** tabela `perfil` com N:N. Descartada por ser complexidade sem requisito que a justifique.

### D3. Função reutilizável `verificar_acesso(perfis_permitidos)` no Xano
Todo endpoint protegido exige autenticação (validação nativa do token) e chama, no início, uma função que (1) recarrega o usuário do banco pelo id do token, (2) recusa com 401 se ele não existir ou estiver inativo e (3) recusa com 403 se `perfil` não estiver em `perfis_permitidos`.
- **Por quê:** recarregar o usuário a cada requisição faz a desativação e a troca de perfil valerem na hora (specs: "Usuário desativado com token ainda válido" e "Troca de perfil com sessão aberta"), sem precisar de blacklist de tokens. O custo é uma leitura por requisição, desprezível no volume do projeto.
- **Alternativa:** confiar no perfil gravado no token. Descartada porque o token ficaria desatualizado por até 12 h.

### D4. Expiração do token configurável, padrão de 12 h
O tempo de expiração vem de uma variável de ambiente do Xano (`TOKEN_TTL_SEGUNDOS`, padrão 43200).
- **Por quê:** cobre um plantão inteiro sem forçar novo login no meio do atendimento; é configurável, como pede o projeto.

### D5. Tabela `sessao` para login e logout
Campos: `usuario_id`, `login_em`, `logout_em` (nulo enquanto aberta), `expira_em`. O `auth/login` cria o registro e o `auth/logout` preenche `logout_em` na sessão aberta mais recente do usuário. Uma sessão está ativa quando `logout_em` é nulo e `expira_em` está no futuro. O status operacional PAUSA/AUSENTE e o encerramento do plantão não encerram a sessão; ficam distintos conforme `add-acompanhamento-administrador`.
- **Por quê:** é a base da futura tela "Pessoas logadas e status" e evita migração depois. O status operacional (almoço etc.) será adicionado na change `add-acompanhamento-administrador`.

### D6. Token no Reflex guardado em `rx.LocalStorage`, com guarda de rota em `on_load`
Um `AuthState` guarda o token (em `rx.LocalStorage`, para sobreviver a um recarregamento da página), o nome e o perfil. Cada página interna usa um `on_load` que chama `auth/me`: sem token ou com resposta 401, redireciona para `/login`; com perfil diferente do exigido pela página, redireciona para a área inicial do perfil. Enquanto a sessão não é confirmada, a página mostra só o carregamento (não exibe o conteúdo). Um cliente HTTP pequeno (`frontend/ps_fila_prioritaria/api.py`) monta a URL a partir do `.env` e injeta o header `Authorization`; nesta change ele é usado pelo `AuthState`. Como cada grupo de API do Xano tem a própria URL base, o login usa a variável `XANO_AUTH_API_URL` (grupo `Autenticacao`, canonical `ps-fila-prioritaria-auth`), ao lado das já existentes `XANO_API_URL` (Pacientes) e `XANO_TRIAGEM_API_URL`.
- **Por quê:** a guarda no frontend existe só por usabilidade; a segurança real é a D3.
- **Alternativa:** cookie HttpOnly. Descartada porque o Xano emite o token no corpo da resposta, e o Reflex precisaria de um proxy só para isso.

### D7. Rotas do frontend
`/login`, `/recepcao` (área inicial Recepção/Triagem), `/medico`, `/admin` e `/admin/usuarios`. As áreas iniciais nesta change mostram apenas o nome do usuário, o perfil e o botão "Sair".

### D8. Estrutura do repositório (revisada em 25/10/2026, princípio YAGNI)
Mantém-se a estrutura que já existe, sem criar pastas novas para uso futuro:
```
frontend/ps_fila_prioritaria/   app Reflex (módulo único + api.py, criado nesta change)
frontend/tests/                 testes pytest (estado do Reflex e integração com o Xano)
frontend/.env.example           URLs dos grupos de API do Xano (sem valores reais)
backend/xano/                   XanoScript versionado (tabelas, funções, endpoints)
```
- **Alternativa descartada:** a estrutura original desta change (`pages/`, `state/`, `tests/api/` na raiz), que criaria pastas sem uso imediato e duplicaria o que já existe.

### D9. Regras de "último administrador" e "desativar a si mesmo" no backend
As duas validações ficam nos endpoints de edição e desativação no Xano, não só na tela.

### D10. Primeiro administrador criado manualmente
O primeiro Administrador é inserido direto na tabela `usuario`, pelo painel do Xano, seguindo um passo documentado no README. Não haverá endpoint público de cadastro.
- **Por quê:** um endpoint de "criar primeiro admin" seria uma porta aberta permanente.

### D11. Testes de API com pytest + httpx
Os testes rodam contra o workspace de desenvolvimento do Xano (URL e credenciais vindas de `.env`) e cobrem os cenários das specs: login, perfis, 401/403, desativação e regras de último administrador. A parte do Reflex é verificada por um roteiro manual nas tasks.

### D12. Redefinição de senha com código por e-mail (decisão do PO em 25/10/2026)
- **Dados:** nova tabela `codigo_verificacao` (`usuario_id`, `finalidade` enum `LOGIN`/`REDEFINICAO_SENHA`, `codigo_hash`, `iniciado_em` (início do pedido, mantido nos reenvios), `criado_em`, `expira_em`, `tentativas`, `usado_em` nulo), compartilhada com o código do login (D13). Só existe um código válido por usuário e finalidade: solicitar outro marca o anterior como usado. O código é gravado com hash, como a senha. Mudança de esquema passa pelo PO. (Revisado em 25/10/2026: antes era `codigo_redefinicao_senha`, ainda não publicada; uma tabela só evita duplicar a mesma regra.)
- **Endpoints públicos (sem token):** `POST auth/senha/solicitar` (e-mail) responde sempre igual; `POST auth/senha/verificar` (e-mail e código) só confere o código, sem usá-lo, para liberar a tela da nova senha (as tentativas erradas contam); `POST auth/senha/redefinir` (e-mail, código e nova senha) confere o código de novo, troca a senha, marca o código como usado e preenche `logout_em` nas sessões abertas do usuário. A senha curta é recusada antes de usar o código.
- **Revisado em 25/10/2026 (YAGNI):** antes, o `verificar` devolveria um token de redefinição de uso único. Descartado porque seria um segundo tipo de token, que o `auth/verificar_acesso` não distingue do token de login; o próprio código, que já vale 10 minutos e é de uso único, cumpre esse papel.
- **Compromisso aceito:** como pede a spec, um novo pedido antes de 60 s responde "Aguarde N segundos", o que revela, só nessa janela, que o e-mail tem um pedido recente.
- **Envio do e-mail:** o Xano chama a API HTTP da **Brevo** (decisão do PO em 25/10/2026; plano gratuito, 300 e-mails/dia), endpoint de e-mail transacional. A chave fica na variável de ambiente `BREVO_API_KEY` (validada em 25/10/2026: conta ativa, plano free) e o remetente verificado em `BREVO_REMETENTE`, nunca no repositório. As variáveis `sendgrid_*` já existentes no workspace não são usadas por esta change. É uma tecnologia nova no projeto, justificada porque o Xano não envia e-mail sozinho e a decisão do PO exige o código por e-mail.
- **Valores (configuráveis por variável de ambiente, não por tela), os mesmos para login e redefinição (decisão do PO):** validade do código `CODIGO_TTL_SEGUNDOS=600`, intervalo de reenvio `CODIGO_REENVIO_SEGUNDOS=60`, tentativas `CODIGO_TENTATIVAS=5`.
- **Modelos de e-mail (criados na Brevo em 25/10/2026):** `ps_codigo_acesso_login` (templateId **6**) e `ps_redefinicao_senha` (templateId **7**), ambos com os parâmetros `nome`, `codigo` e `minutos` (este calculado de `CODIGO_TTL_SEGUNDOS`). O HTML fica versionado em `backend/brevo/`; ao mudar o texto, atualizar o arquivo e o modelo na Brevo juntos. O envio usa `POST https://api.brevo.com/v3/smtp/email` com `templateId` e `params`, chamado direto no endpoint (no ConectaRH, `function.run` aninhado para envio de e-mail se mostrou instável).
- **Alternativa:** link com token na URL em vez de código. Descartada porque o PO pediu código e porque links em e-mail tendem a ser abertos em outro dispositivo, fora do computador da recepção.
- **Alternativa:** guardar o código em `usuario`. Descartada para não misturar autenticação com um fluxo temporário e para manter histórico de tentativas.

### D13. Código de verificação no login (decisão do PO em 25/10/2026)
O login passa a ter duas etapas. `POST auth/login` continua conferindo e-mail, senha e usuário ativo com as mesmas mensagens, mas, em vez de emitir o token, gera um código `LOGIN` em `codigo_verificacao`, envia o modelo 6 e responde `{codigo_enviado: true}`. `POST auth/login/verificar` (e-mail e código) confere o código (hash, validade, 5 tentativas), recarrega o usuário (recusa se foi desativado no meio), emite o token com `TOKEN_TTL_SEGUNDOS`, cria a `sessao` e devolve `{token, nome, perfil}`. `POST auth/login/reenviar` (e-mail) só gera novo código se houver um código `LOGIN` criado nos últimos `CODIGO_TTL_SEGUNDOS` e respeitando `CODIGO_REENVIO_SEGUNDOS`; fora disso, o usuário volta a informar a senha. A sessão só é registrada na segunda etapa.
- **Por quê:** é a forma mais simples de exigir posse do e-mail sem guardar a senha no frontend entre as etapas; reaproveita tabela, regras e envio da D12.
- **Reflex:** depois da primeira etapa, o `AuthState` guarda só o e-mail (nunca a senha) e leva para `/login/codigo`, tela no mesmo padrão da A2 do Figma (6 dígitos, contador de reenvio, aviso de spam, "Voltar ao login").
- **Alternativa:** devolver da primeira etapa um identificador temporário do desafio. Descartada por ora (YAGNI): o e-mail mais o código bastam e não abrem consulta nova.
- **Testes:** sem acesso à caixa de entrada nos testes automáticos, os testes de API cobrem a primeira etapa e as recusas (código errado, expirado, limite de tentativas, reenvio cedo); o caminho feliz até o token é verificado manualmente com e-mail real. Os testes de estado do Reflex simulam as respostas da API.

## Riscos / Compromissos

- [Login depende do e-mail chegar] → Se a Brevo falhar ou o e-mail atrasar, ninguém entra. Mitigação: reenvio após 60 s e aviso de spam na tela; o plano gratuito tem 300 e-mails/dia, o que cobre os logins da equipe no escopo acadêmico.

- [E-mail do provedor cair em spam ou atrasar] → Remetente verificado no provedor; a tela permite reenviar após 60 s; o Administrador continua podendo redefinir a senha.
- [Enumeração de e-mails pela tela de redefinição] → Resposta idêntica para qualquer e-mail (spec) e mesmo tempo de resposta aproximado, sem enviar e-mail quando o usuário não existe.
- [Força bruta no código de 6 dígitos] → No máximo 5 tentativas por código e validade de 10 minutos.

- [O token fica em LocalStorage, exposto a XSS] → O Reflex escapa o conteúdo por padrão; não renderizar HTML vindo do usuário; expiração de 12 h limita a janela de uso.
- [Testes de API alteram dados do workspace] → Usar a fonte de dados de teste/dev do Xano e usuários com prefixo `teste_`, removidos ou desativados no teardown.
- [Sem bloqueio por tentativas de login, a força bruta é possível] → Aceito no escopo acadêmico; registrado como fora do escopo na proposta. O rate limiting do Xano pode ser ligado depois sem mudar a spec.
- [Plano gratuito do Xano com limites de requisição] → A leitura extra por requisição (D3) é baixa; monitorar se os testes ficarem lentos.
- [XanoScript versionado pode divergir do workspace] → Sempre exportar e commitar após mudar algo no Xano; a task de cada grupo inclui esse passo.

## Plano de migração

Não se aplica (sistema novo). Rollback: remover as tabelas e endpoints criados no workspace de desenvolvimento.

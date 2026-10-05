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
Um `AuthState` guarda o token (em `rx.LocalStorage`, para sobreviver a um recarregamento da página), o nome e o perfil. Cada página interna usa um `on_load` que chama `auth/me`: sem token ou com resposta 401, redireciona para `/login`; com perfil diferente do exigido pela página, redireciona para a área inicial do perfil. Um cliente HTTP único (`api.py`) injeta o header `Authorization` e trata os erros 401 e 403 de forma centralizada.
- **Por quê:** a guarda no frontend existe só por usabilidade; a segurança real é a D3.
- **Alternativa:** cookie HttpOnly. Descartada porque o Xano emite o token no corpo da resposta, e o Reflex precisaria de um proxy só para isso.

### D7. Rotas do frontend
`/login`, `/recepcao` (área inicial Recepção/Triagem), `/medico`, `/admin` e `/admin/usuarios`. As áreas iniciais nesta change mostram apenas o nome do usuário, o perfil e o botão "Sair".

### D8. Estrutura do repositório
```
frontend/            app Reflex (rxconfig.py, frontend/ com pages/, state/, api.py)
backend/xano/        XanoScript versionado (tabelas, funções, endpoints)
tests/api/           testes pytest contra a API do Xano
.env.example         XANO_API_URL, credenciais de teste (sem valores reais)
```

### D9. Regras de "último administrador" e "desativar a si mesmo" no backend
As duas validações ficam nos endpoints de edição e desativação no Xano, não só na tela.

### D10. Primeiro administrador criado manualmente
O primeiro Administrador é inserido direto na tabela `usuario`, pelo painel do Xano, seguindo um passo documentado no README. Não haverá endpoint público de cadastro.
- **Por quê:** um endpoint de "criar primeiro admin" seria uma porta aberta permanente.

### D11. Testes de API com pytest + httpx
Os testes rodam contra o workspace de desenvolvimento do Xano (URL e credenciais vindas de `.env`) e cobrem os cenários das specs: login, perfis, 401/403, desativação e regras de último administrador. A parte do Reflex é verificada por um roteiro manual nas tasks.

## Riscos / Compromissos

- [O token fica em LocalStorage, exposto a XSS] → O Reflex escapa o conteúdo por padrão; não renderizar HTML vindo do usuário; expiração de 12 h limita a janela de uso.
- [Testes de API alteram dados do workspace] → Usar a fonte de dados de teste/dev do Xano e usuários com prefixo `teste_`, removidos ou desativados no teardown.
- [Sem bloqueio por tentativas de login, a força bruta é possível] → Aceito no escopo acadêmico; registrado como fora do escopo na proposta. O rate limiting do Xano pode ser ligado depois sem mudar a spec.
- [Plano gratuito do Xano com limites de requisição] → A leitura extra por requisição (D3) é baixa; monitorar se os testes ficarem lentos.
- [XanoScript versionado pode divergir do workspace] → Sempre exportar e commitar após mudar algo no Xano; a task de cada grupo inclui esse passo.

## Plano de migração

Não se aplica (sistema novo). Rollback: remover as tabelas e endpoints criados no workspace de desenvolvimento.

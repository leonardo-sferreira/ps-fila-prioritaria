# Proposta: Login, perfis e gestão de usuários

| Campo | Valor |
|---|---|
| Change | `add-autenticacao-perfis` |
| Sprint e entrega | Sprint 1, segunda 05/10 (`autenticacao`). `gestao-usuarios` ainda sem sprint |
| Fatias no Trello | [Setup] Base técnica · Fatia 1 — Login |
| Dupla | Leonardo Machado (API e dados) · Nicolas (tela) |
| Depende de | — (primeira change) |
| Situação | Em revisão |
| RFs novos ou esclarecidos (Confluence, 04/10/2026) | RF39 (`gestao-usuarios`); RF01 e RF02 (`autenticacao`) |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/`. Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

Todas as telas do sistema (triagem, fila do médico, administração) dependem de saber **quem** está usando o sistema e **com qual perfil**. Sem autenticação e controle de acesso no backend, nenhuma outra fatia vertical pode ser entregue com segurança. Por isso esta é a primeira change: ela funda o acesso ao sistema e cria os usuários que as próximas changes vão usar.

## What Changes

- Login da equipe com e-mail e senha, validado no Xano, que devolve um token de acesso.
- Três perfis fixos: **Recepção/Triagem** (um perfil funcional único), **Médico** e **Administrador**. `Usuario` é a entidade de autenticação; Médico e Recepção/Triagem também possuem entidades próprias 1:1, geridas junto com o usuário na change administrativa. Após o login, cada perfil é levado para sua área inicial no Reflex.
- Logout, que encerra a sessão do usuário.
- Controle de acesso por perfil aplicado **no backend**: endpoints protegidos rejeitam requisições sem token, com token inválido ou expirado, de usuário inativo ou de perfil não autorizado.
- Registro de sessão (login, logout e expiração), distinto do status operacional e do encerramento do plantão, que são tratados em `add-acompanhamento-administrador`.
- Gestão de usuários pelo Administrador: listar, criar, editar (nome, e-mail, perfil), redefinir senha e ativar/desativar.
- **Redefinição de senha pelo próprio usuário ("Esqueci minha senha")**, com código de verificação de 6 dígitos enviado por e-mail (decisão do PO em 25/10/2026). O código vale por 10 minutos, pode ser reenviado após 60 segundos e aceita até 5 tentativas. A resposta é a mesma para e-mail cadastrado ou não, e a nova senha encerra as sessões abertas. A redefinição pelo Administrador continua existindo.
- Criação do primeiro Administrador por procedimento documentado, já que ainda não existe usuário para criá-lo pela tela.
- Estrutura inicial do projeto: app Reflex, workspace Xano e testes de API.

### Fora do escopo

- Especialidades e disponibilidade dos médicos (vínculo Médico ↔ Especialidade fica para a change `add-cadastros-administrador`).
- Status operacional da equipe (disponível, em atendimento, pausa, ausente) e a tela de acompanhamento do Administrador (fila geral, pessoas logadas, auditoria): change `add-acompanhamento-administrador`.
- Trilha de auditoria completa (`Histórico_Alteração`), criada em `add-cadastros-administrador`; esta change só registra as sessões.
- ~~Recuperação de senha por e-mail ("esqueci minha senha")~~: passou a fazer parte do escopo em 25/10/2026 (ver What Changes).
- Recuperação de senha por SMS ou por pergunta de segurança; alteração de senha pelo usuário logado ("trocar minha senha").
- Bloqueio por tentativas de login, autenticação em dois fatores e login único (SSO).
- Qualquer funcionalidade de paciente, triagem, fila ou chamada.

## Capacidades

### Novas capacidades
- `autenticacao`: login, logout, sessão e controle de acesso por perfil (Recepção/Triagem, Médico, Administrador) aplicado no backend.
- `gestao-usuarios`: cadastro e manutenção dos usuários da equipe pelo Administrador, incluindo perfil e ativação/desativação.

### Capacidades modificadas
_Nenhuma (não existem specs anteriores)._

## Impacto

- **Xano:** novas tabelas `usuario` (tabela de autenticação) e `sessao`; endpoints de autenticação (`login`, `logout`, `me`) e de gestão de usuários; função reutilizável de verificação de perfil, que será usada por todos os endpoints das próximas changes. Para a redefinição de senha: tabela `codigo_redefinicao_senha` (mudança de esquema pelo PO), endpoints públicos `auth/senha/solicitar`, `auth/senha/verificar` e `auth/senha/redefinir`, e envio de e-mail por provedor transacional (D12).
- **Reflex:** criação do app, tela de login, proteção de rotas, telas iniciais por perfil e telas de gestão de usuários; fluxo "Esqueci minha senha" (telas A1 a A4 do Figma).
- **Dependência externa nova:** Brevo (e-mail transacional) acessada por API HTTP, com chave guardada em variável de ambiente do Xano (D12).
- **Testes:** suíte de testes de API em Python (pytest) contra um ambiente de desenvolvimento do Xano.
- **Configuração:** URL da API do Xano por variável de ambiente, sem credenciais no repositório.
- **Documentação:** `docs/domain-model.md` (Usuário e Sessão) atualizado conforme o que for implementado.
- **Rastreabilidade (documento formal v1.0):** RF01 (autenticar usuários), RF02 (controlar permissões por perfil), RNF05 (segurança) e a matriz de permissões da seção 3.1. O registro de sessões atende à visão "Pessoas logadas e status" do contexto do PO; ela não existe no documento formal.

## Perguntas em aberto

- [x] Login por e-mail: decidido pelo PO em 04/10/2026. A spec já está assim; o card da Fatia 1 no Trello fala em e-mail ou CPF e precisa ser ajustado. · DECIDIDO PO
- [ ] A `gestao-usuarios` (tela e API do Administrador) entra em qual sprint? Hoje não há card. · PENDENTE PO
- [ ] Ajustar as tasks 1.4, 2.1 e 2.2: o README e as tabelas `usuario` e `sessao` já existem. · dupla da fatia
- [x] Redefinição de senha pelo próprio usuário com código por e-mail: decidida pelo PO em 25/10/2026. · DECIDIDO PO
- [x] Escolher o provedor de e-mail transacional (D12): Brevo, decidido pelo PO em 25/10/2026. · DECIDIDO PO
- [ ] Cadastrar `BREVO_REMETENTE` (e-mail verificado na Brevo) no Xano. · PENDENTE PO
- [ ] Registrar no Confluence: o RF39 prevê só a redefinição pelo Administrador. · PENDENTE PO

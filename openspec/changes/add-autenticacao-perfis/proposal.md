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
- Criação do primeiro Administrador por procedimento documentado, já que ainda não existe usuário para criá-lo pela tela.
- Estrutura inicial do projeto: app Reflex, workspace Xano e testes de API.

### Fora do escopo

- Especialidades e disponibilidade dos médicos (vínculo Médico ↔ Especialidade fica para a change `add-cadastros-administrador`).
- Status operacional da equipe (disponível, em atendimento, pausa, ausente) e a tela de acompanhamento do Administrador (fila geral, pessoas logadas, auditoria): change `add-acompanhamento-administrador`.
- Trilha de auditoria completa (`Histórico_Alteração`), criada em `add-cadastros-administrador`; esta change só registra as sessões.
- Recuperação de senha por e-mail ("esqueci minha senha"): o Administrador redefine a senha.
- Bloqueio por tentativas de login, autenticação em dois fatores e login único (SSO).
- Qualquer funcionalidade de paciente, triagem, fila ou chamada.

## Capacidades

### Novas capacidades
- `autenticacao`: login, logout, sessão e controle de acesso por perfil (Recepção/Triagem, Médico, Administrador) aplicado no backend.
- `gestao-usuarios`: cadastro e manutenção dos usuários da equipe pelo Administrador, incluindo perfil e ativação/desativação.

### Capacidades modificadas
_Nenhuma (não existem specs anteriores)._

## Impacto

- **Xano:** novas tabelas `usuario` (tabela de autenticação) e `sessao`; endpoints de autenticação (`login`, `logout`, `me`) e de gestão de usuários; função reutilizável de verificação de perfil, que será usada por todos os endpoints das próximas changes.
- **Reflex:** criação do app, tela de login, proteção de rotas, telas iniciais por perfil e telas de gestão de usuários.
- **Testes:** suíte de testes de API em Python (pytest) contra um ambiente de desenvolvimento do Xano.
- **Configuração:** URL da API do Xano por variável de ambiente, sem credenciais no repositório.
- **Documentação:** `docs/domain-model.md` (Usuário e Sessão) atualizado conforme o que for implementado.
- **Rastreabilidade (documento formal v1.0):** RF01 (autenticar usuários), RF02 (controlar permissões por perfil), RNF05 (segurança) e a matriz de permissões da seção 3.1. O registro de sessões atende à visão "Pessoas logadas e status" do contexto do PO; ela não existe no documento formal.

## Perguntas em aberto

- [x] Login por e-mail: decidido pelo PO em 04/10/2026. A spec já está assim; o card da Fatia 1 no Trello fala em e-mail ou CPF e precisa ser ajustado. · DECIDIDO PO
- [ ] A `gestao-usuarios` (tela e API do Administrador) entra em qual sprint? Hoje não há card. · PENDENTE PO
- [ ] Ajustar as tasks 1.4, 2.1 e 2.2: o README e as tabelas `usuario` e `sessao` já existem. · dupla da fatia

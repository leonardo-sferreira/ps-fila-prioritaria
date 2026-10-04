# Proposta: Pacientes por CPF e fila de pré-triagem

| Campo | Valor |
|---|---|
| Change | `add-pacientes-pre-triagem` |
| Sprint e entrega | Sprint 1, segunda 05/10 (`pacientes`). `fila-pre-triagem` ainda sem sprint |
| Fatias no Trello | Fatia 2 — Cadastro de paciente |
| Dupla | Luisa (API e dados) · Nicolas (tela) |
| Depende de | `add-autenticacao-perfis` (token e perfil) e `add-base-compartilhada` (`registrar_alteracao` e `FUSO_HORARIO`, Sprint 1) |
| Situação | Em revisão |
| RFs novos ou esclarecidos (Confluence, 04/10/2026) | RF40 e RF41 (`fila-pre-triagem`); RF22 (a Recepção/Triagem acessa a sua fila) |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/`. Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

O fluxo do PS começa antes da triagem: o paciente retira um ticket no totem e aguarda a Recepção/Triagem chamá-lo. Depois, a Recepção/Triagem identifica o paciente pelo CPF para abrir a ficha. Sem a fila pré-triagem e o cadastro de pacientes, a triagem (próxima change) não tem quem atender.

## What Changes

- **Emissão de ticket:** um ponto de emissão de ticket com número sequencial diário, acionado pelo totem. Como o totem não é desenvolvido pela equipe, esta change entrega uma tela simples de **simulador de totem** que chama esse ponto de emissão.
- **Fila pré-triagem:** a Recepção/Triagem vê os tickets aguardando, chama o próximo (em ordem de emissão, sem prioridade), rechama e marca "não compareceu" ou "paciente identificado".
- **Pacientes:** pesquisa por CPF, cadastro quando não encontrado e atualização de dados cadastrais (RF03, RF04, RF05, RN01, RN02, UC01). CPF obrigatório, válido e único; nome completo e data de nascimento obrigatórios; telefone opcional; situação ativo/inativo.
- Consulta de pacientes, somente leitura, para o Administrador (matriz de permissões da seção 3.1).
- Auditoria do cadastro e da alteração de pacientes.

### Fora do escopo

- Abertura de ficha, sintomas e sinais vitais: `add-triagem-classificacao`.
- Exibição do ticket chamado no painel público: `add-painel-publico`.
- Totem físico, impressão do ticket no totem e integração com hardware.
- Desativação de pacientes pela interface: o campo existe, mas não há tela para isso nesta change.
- Busca de pacientes por nome.

## Capacidades

### Novas capacidades
- `fila-pre-triagem`: emissão de ticket e chamada dos tickets pela Recepção/Triagem.
- `pacientes`: pesquisa, cadastro e atualização de pacientes por CPF.

### Capacidades modificadas
_Nenhuma._

## Impacto

- **Xano:** tabelas `ticket_pre_triagem` e `paciente`; endpoints `POST totem/tickets` (protegido por chave do totem), `GET/POST pre-triagem/...` (RECEPCAO_TRIAGEM) e `GET/POST/PATCH pacientes` (RECEPCAO_TRIAGEM; leitura para ADMINISTRADOR).
- **Reflex:** página `/totem` (simulador), painel "Fila pré-triagem" e telas de pesquisa e cadastro de paciente em `/recepcao`.
- **Configuração:** variável `TOTEM_CHAVE` no Xano e no backend do Reflex (nunca no navegador).
- **Testes:** `tests/api/test_pre_triagem.py` e `tests/api/test_pacientes.py`.
- **Depende de:** `add-autenticacao-perfis` e `add-cadastros-administrador` (auditoria).
- **Divergência com o documento formal:** o processo formal (seção 4) começa com o paciente informando o CPF direto na recepção; o totem e a fila pré-triagem vêm do contexto do PO (Figma de 26–27/09/2026) e ainda não estão no Confluence.

## Perguntas em aberto

- [x] Base de auditoria e fuso na Sprint 1: decidido pelo PO em 04/10/2026 (`add-base-compartilhada`). · DECIDIDO PO
- [ ] Atualizar paciente com `PATCH` (spec) ou `PUT` (card da Fatia 2)? O campo é `telefone` (spec) ou "contato" (card)? · PENDENTE PO
- [ ] Simulador de totem e `fila-pre-triagem`: sprint, evolução futura ou fora do escopo? Hoje só há o card de Figma do totem. · PENDENTE PO
- [ ] O intervalo mínimo de 10 s e o limite de 3 chamadas do RF35 também valem para "Rechamar" na fila pré-triagem, ou só para a chamada do médico? · PENDENTE PO

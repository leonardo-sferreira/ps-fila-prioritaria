# Proposta: Pacientes por CPF e fila de pré-triagem

| Campo | Valor |
|---|---|
| Change | `add-pacientes-pre-triagem` |
| Sprint e entrega | Sprint 1, segunda 05/10 (`pacientes`). `fila-pre-triagem` ainda sem sprint |
| Fatias no Trello | Fatia 2 — Cadastro de paciente |
| Dupla | Luisa (API e dados) · Nicolas (tela) |
| Depende de | `add-autenticacao-perfis` (perfil único Recepção/Triagem), `add-base-compartilhada` (auditoria e `FUSO_HORARIO`) e `add-totem` (emissão dos tickets) |
| Situação | Em revisão |
| RFs novos ou esclarecidos (Confluence, 04/10/2026) | RF40 e RF41 (`fila-pre-triagem`); RF22 (a Recepção/Triagem acessa a sua fila) |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/`. Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

O fluxo do PS começa antes da triagem: o paciente retira um ticket no totem e aguarda a Recepção/Triagem chamá-lo. Depois, a Recepção/Triagem identifica o paciente pelo CPF para abrir a ficha. Sem a fila pré-triagem e o cadastro de pacientes, a triagem (próxima change) não tem quem atender.

## What Changes

- **Fila de Recepção/Triagem:** consome os tickets emitidos pela change `add-totem`, lista em ordem de emissão, chama e rechama cada ticket (30 s entre chamadas, até 3 por oportunidade), devolve o mesmo ticket ao fim da fila uma vez e permite identificar o paciente ou registrar desistência explícita.
- **Pacientes:** pesquisa por CPF, cadastro quando não encontrado e atualização de dados cadastrais (RF03, RF04, RF05, RN01, RN02, UC01). CPF obrigatório, válido e único; nome completo e data de nascimento obrigatórios; telefone opcional; situação ativo/inativo.
- Consulta de pacientes, somente leitura, para o Administrador (matriz de permissões da seção 3.1).
- Auditoria do cadastro e da alteração de pacientes.

### Fora do escopo

- Abertura de ficha, sintomas e sinais vitais: `add-triagem-classificacao`.
- Exibição do ticket chamado no painel público: `add-painel-publico`.
- Emissão do ticket e experiência pública do Totem: `add-totem`.
- Impressão física do ticket e integração com hardware.
- Desativação de pacientes pela interface: o campo existe, mas não há tela para isso nesta change.
- Busca de pacientes por nome.

## Capacidades

### Novas capacidades
- `fila-pre-triagem`: emissão de ticket e chamada dos tickets pela Recepção/Triagem.
- `pacientes`: pesquisa, cadastro e atualização de pacientes por CPF.

### Capacidades modificadas
_Nenhuma._

## Impacto

- **Xano:** operação da fila de tickets de `add-totem` e cadastro de `paciente`; endpoints `GET/POST pre-triagem/...` e `GET/POST/PATCH pacientes` (RECEPCAO_TRIAGEM; leitura para ADMINISTRADOR).
- **Reflex:** painel "Fila de Recepção/Triagem" e telas de pesquisa/cadastro de paciente em `/recepcao`; não inclui tela Totem.
- **Testes:** `tests/api/test_pre_triagem.py` e `tests/api/test_pacientes.py`.
- **Depende de:** `add-autenticacao-perfis` e `add-cadastros-administrador` (auditoria).
- A fila recebe tickets sem dados pessoais emitidos por `add-totem`; RF/RN/UC/CA são referências de rastreabilidade e não devem receber texto inventado.

## Perguntas em aberto

- [x] Base de auditoria e fuso na Sprint 1: decidido pelo PO em 04/10/2026 (`add-base-compartilhada`). · DECIDIDO PO
- [ ] Atualizar paciente com `PATCH` (spec) ou `PUT` (card da Fatia 2)? O campo é `telefone` (spec) ou "contato" (card)? · PENDENTE PO
- [x] Totem no escopo e em change própria `add-totem`; esta change mantém somente a operação da fila de Recepção/Triagem. · BASELINE
- [x] Chamadas de Recepção/Triagem seguem 30 segundos, até 3 por oportunidade e uma reentrada única, assim como a fila médica. · BASELINE

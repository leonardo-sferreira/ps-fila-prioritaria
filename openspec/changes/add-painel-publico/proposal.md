# Proposta: Painel público de chamadas

| Campo | Valor |
|---|---|
| Change | `add-painel-publico` |
| Sprint e entrega | Sprint 5, segunda 02/11 |
| Fatias no Trello | Fatia 9 — Painel público |
| Dupla | Luisa (API) · Nicolas (tela) |
| Depende de | `add-fila-chamada-medico` (chamadas, Sala e previsão por fila); `add-pacientes-pre-triagem` para o ticket chamado; `add-cadastros-administrador` para Sala |
| Situação | Em revisão |
| RFs novos ou esclarecidos (Confluence, 04/10/2026) | RF50 (complementos do painel); RF35 |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/`. Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

Os pacientes que aguardam precisam saber quando e para onde ir, sem ter seus dados expostos. O painel público é a única interface do sistema voltada ao paciente e mostra, em tempo quase real, a senha chamada e a previsão das próximas, com o mesmo algoritmo da chamada real.

## What Changes

- **Página pública do painel**, sem login, para TV na sala de espera (RF33, UC11).
- **Senha atual em destaque**, com especialidade e Sala operacional associada quando houver, e aviso visual e sonoro a cada chamada nova ou repetida.
- **Últimas chamadas** (histórico curto).
- **Previsão das próximas N senhas por especialidade** (inicial 5), vinda da função de previsão da fila (RF34, RF35, RN25, RN26, CA10–CA12).
- **Ticket da pré-triagem chamado pela Recepção/Triagem**, para o paciente saber que é a vez dele na triagem.
- **Filtro por especialidade** na URL, para ter vários painéis.
- **Privacidade:** nenhum nome, CPF ou dado pessoal; só senhas e especialidades (RN35, RNF06).

### Fora do escopo

- Chamada por voz sintetizada (só um aviso sonoro curto).
- Cadastro/manutenção de salas, que pertence a `add-cadastros-administrador`.
- Qualquer mudança nas regras da fila (a previsão vem de `add-fila-chamada-medico`).

## Capacidades

### Novas capacidades
- `painel-publico`: exibição pública das chamadas, das últimas chamadas e da previsão das próximas senhas.

### Capacidades modificadas
_Nenhuma._

## Impacto

- **Xano:** endpoint público somente leitura `GET painel?especialidades=`, que agrega as últimas `chamada`, Sala quando aplicável, previsões por especialidade (`prever_fila`) e tickets pré-triagem chamados, só com campos não pessoais. Não estabelece interleaving global entre especialidades, ainda pendente em `add-fila-chamada-medico`.
- **Reflex:** página `/painel` em tela cheia, com polling, destaque e som.
- **Testes:** `tests/api/test_painel.py` (conteúdo, privacidade e coerência com a chamada).
- **Depende de:** `add-fila-chamada-medico` (chamadas e previsão) e `add-pacientes-pre-triagem` (tickets).

## Perguntas em aberto

- [x] Especialidade e Sala são conceitos distintos; chamadas médicas mostram a Sala associada quando houver. · BASELINE
- [ ] A ordenação global entre filas de especialidades diferentes depende da decisão pendente registrada em `add-fila-chamada-medico`; este painel apresenta previsões separadas por especialidade até lá. · DEPENDÊNCIA FUNCIONAL

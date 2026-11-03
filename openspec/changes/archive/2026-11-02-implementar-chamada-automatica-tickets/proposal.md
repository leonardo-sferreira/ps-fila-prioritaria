# Proposta: chamada de tickets

| Campo | Valor |
|---|---|
| Change | `implementar-chamada-automatica-tickets` |
| Sprint / card Trello | A definir |
| Depende de | autenticação e auditoria para operações protegidas; emissão do Totem apenas para integração ponta a ponta |
| Situação | Em implementação; limitação de concorrência aceita pelo PO |

## Why

A emissão do Totem não inclui a operação da fila. A Recepção/Triagem precisa chamar os tickets de forma ordenada e associá-los à ficha após identificação.

## What Changes

- Seleção iniciada pela Recepção, confirmação de presença e tentativas e encerramento automáticos com validação no Xano; reentrada, desistência explícita e interface operacional na Recepção/Triagem.
- Associação atômica do ticket chamado à ficha, mantendo abertura sem ticket.
- Fora do escopo: emissão do Totem, fila médica, classificação, sinais vitais, painel público e infraestrutura externa.

## Capacidades

### Novas capacidades
- `fila-pre-triagem`: seleção e operação dos tickets.

### Capacidades modificadas
- `pacientes`: continuidade com ticket chamado quando existir.
- `ficha-atendimento`: associação validada e transição do ticket na abertura.

## Impacto

Xano: dados operacionais, concorrência, autorização e APIs. Reflex: área de Recepção, identificação e abertura de ficha. Testes de regras e integração. A referência solicitada é Rev. 2.1, RF41–RF43 (§23; RF42 e RF43 provisórios), §§4.1, 8, 19 (D11, D12, D17) e §18 item 4; texto formal indisponível nesta exploração, sem atribuição de conteúdo não verificado.

## Perguntas em aberto

Nenhuma decisão de produto pendente. A operação sequencial é necessária: a exclusividade entre requisições simultâneas não foi comprovada.

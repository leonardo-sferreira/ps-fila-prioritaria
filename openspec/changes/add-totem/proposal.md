# Proposta: Emissão de tickets no Totem

| Campo | Valor |
|---|---|
| Change | `add-totem` |
| Sprint e entrega | A definir |
| Fatias no Trello | A definir |
| Dupla | A definir |
| Depende de | `add-base-compartilhada` (fuso oficial e parâmetros necessários) |
| Situação | Proposta documental |
| Rastreabilidade formal | RF40–RF41 quando aplicáveis; confirmar texto exato no Confluence sem inventar requisito |

## Why

O Totem faz parte do escopo aprovado e deve emitir um ticket sem dados pessoais, registrando-o na fila de Recepção/Triagem. Hoje a emissão está misturada à change de pacientes/pré-triagem, que descreve apenas um simulador; separar esta capacidade deixa clara a responsabilidade funcional própria do Totem.

## What Changes

- Disponibilizar uma experiência pública de Totem em que o paciente escolhe o tipo de ticket — Pediátrico, Preferencial ou Normal — e solicita um ticket numérico sequencial diário.
- Numerar cada tipo em sequência diária própria, exibida com prefixo: `C-001` (Pediátrico), `P-001` (Preferencial) e `N-001` (Normal). Decisão do PO em 25/10/2026.
- Registrar o ticket com seu tipo no Xano e enviá-lo à fila de Recepção/Triagem, sem CPF, nome ou qualquer dado pessoal.
- Exibir ao paciente o código emitido (prefixo e número) e confirmação de que deve aguardar chamada da Recepção/Triagem.
- Proteger a operação de emissão contra chamadas não autorizadas, mantendo segredo no servidor e nunca no navegador.
- Usar o fuso oficial `America/Sao_Paulo` para o dia operacional.
- Deixar a operação da fila (chamar, rechamar, retorno ao fim, identificar ou desistência) para futura change própria de operação da fila da Recepção/Triagem.

### Fora do escopo

- Cadastro ou identificação de paciente.
- Chamada, desistência ou operação da fila pela Recepção/Triagem, incluindo a ordem de chamada por tipo (Pediátrico antes de Preferencial; ciclo configurável de 2 prioritários : 1 normal, conforme `docs/domain-model.md`), que pertence à futura change de operação da fila pré-triagem.
- Conferir se o tipo declarado corresponde ao paciente identificado; o tipo não altera cor nem condição prioritária calculadas na triagem.
- Impressão física, integração com hardware ou modo offline, salvo decisão futura registrada em design.
- Dados clínicos ou identificação pessoal no ticket.

## Capabilities

### Novas capacidades
- `totem`: emissão de ticket impessoal e registro na fila de Recepção/Triagem.

### Capacidades modificadas
- Nenhuma. A futura capacidade de operação da fila consumirá os tickets emitidos.

## Impact

- **Xano:** contrato de emissão e registro de ticket com tipo, numeração diária por tipo no fuso oficial e proteção da operação. Exige campo `tipo` e índice único `(data, tipo, numero)` em `ticket_pre_triagem`; a mudança de esquema passa pelo PO.
- **Reflex:** experiência pública de Totem com escolha do tipo, sem autorização por perfil de equipe nem dados pessoais.
- **Parâmetros:** o ciclo da fila pré-triagem (2 prioritários : 1 normal) entra na carga inicial de `add-base-compartilhada`; esta change não o consome.
- **Segurança:** segredo usado para emissão fica no servidor; autorização e persistência são responsabilidade do Xano.
- **Dependências:** a futura capacidade de operação da fila consumirá os tickets emitidos; esta change permanece limitada à emissão pública.

## Perguntas em aberto

- Confirmar sprint, fatia do Trello e responsáveis na planning.
- Confirmar no Confluence a rastreabilidade RF40–RF41 para a emissão de tickets.
- **Divergência com o documento formal:** o Confluence descreve o ticket sem prioridade e chamado só por ordem de emissão. Os tipos Pediátrico/Preferencial/Normal e o ciclo da pré-triagem (decisão do PO em 25/10/2026) precisam ser registrados lá pelo PO.
- Definir se o Totem deve imprimir ticket ou operar somente com exibição na tela.

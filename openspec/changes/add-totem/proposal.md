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

- Disponibilizar uma experiência pública de Totem para solicitar ticket numérico sequencial diário.
- Registrar o ticket no Xano e enviá-lo à fila de Recepção/Triagem, sem CPF, nome ou qualquer dado pessoal.
- Exibir ao paciente o número emitido e confirmação de que deve aguardar chamada da Recepção/Triagem.
- Proteger a operação de emissão contra chamadas não autorizadas, mantendo segredo no servidor e nunca no navegador.
- Usar o fuso oficial `America/Sao_Paulo` para o dia operacional.
- Deixar a operação da fila (chamar, rechamar, retorno ao fim, identificar ou desistência) para `add-pacientes-pre-triagem`.

### Fora do escopo

- Cadastro ou identificação de paciente.
- Chamada, desistência ou operação da fila pela Recepção/Triagem.
- Impressão física, integração com hardware ou modo offline, salvo decisão futura registrada em design.
- Dados clínicos ou identificação pessoal no ticket.

## Capabilities

### Novas capacidades
- `totem`: emissão de ticket impessoal e registro na fila de Recepção/Triagem.

### Capacidades modificadas
- Nenhuma. `add-pacientes-pre-triagem` dependerá desta capacidade para receber tickets emitidos.

## Impact

- **Xano:** contrato de emissão e registro de ticket, com numeração diária no fuso oficial e proteção da operação.
- **Reflex:** experiência pública de Totem, sem autorização por perfil de equipe nem dados pessoais.
- **Segurança:** segredo usado para emissão fica no servidor; autorização e persistência são responsabilidade do Xano.
- **Dependências:** `add-pacientes-pre-triagem` passa a consumir os tickets emitidos; a operação da fila continua nessa change.

## Perguntas em aberto

- Confirmar sprint, fatia do Trello e responsáveis na planning.
- Confirmar no Confluence a rastreabilidade RF40–RF41 para a emissão de tickets.
- Definir se o Totem deve imprimir ticket ou operar somente com exibição na tela.

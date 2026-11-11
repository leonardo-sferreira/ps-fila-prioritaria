# Proposta: expiração automática após 24 horas

| Campo | Valor |
|---|---|
| Change | `add-expiracao-24h` |
| Sprint / card Trello | Sprint 4; card a definir |
| Depende de | `add-fichas-do-dia` (a lista mostra o efeito da limpeza) |
| Situação | Proposta (pedido do PO em 10/11/2026), aguardando revisão |
| Rastreabilidade formal | Regra nova; registrar na Documentação de Requisitos (Rev. 2.2) |

## Why

Fichas e tickets abandonados ficam presos para sempre. Uma ficha aberta e nunca confirmada continua "em triagem" e impede o paciente de ter uma nova ficha (RN03). Uma senha esquecida continua na fila do médico, e um ticket do Totem nunca chamado continua na fila de pré-triagem.

O PO pediu que tudo que não for concluído em 24 horas seja encerrado como desistência.

## What Changes

- **Expiração após 24 horas**, contadas da chegada (ficha) ou da emissão (ticket). O prazo é o parâmetro configurável `HORAS_EXPIRACAO`, inicialmente 24.
- **Fichas:** as que estão `EM_TRIAGEM`, `AGUARDANDO` ou `CHAMADO` há mais de 24 horas passam a `DESISTENCIA` e saem da fila do médico. O paciente fica livre para uma nova ficha.
- **Tickets do Totem:** os que estão `AGUARDANDO` ou `CHAMADO` há mais de 24 horas passam a `DESISTENCIA` e saem da fila de pré-triagem.
- **Tarefa agendada no Xano**, a cada hora. Nenhuma tela dispara a limpeza.
- **Auditoria:** cada encerramento fica no histórico como evento `EXPIRACAO`, com usuário vazio (ação do sistema) e a justificativa "Encerrada após 24 h sem conclusão".
- **Máquina de estados da ficha:** `EM_TRIAGEM` e `AGUARDANDO` passam a poder ir para `DESISTENCIA`, só por expiração.

### Fora do escopo

- Chamadas continuam manuais. A regra "nada acontece automaticamente" vale para a operação das filas (chamar, repetir, não compareceu). A expiração é limpeza de registros abandonados, não uma chamada.
- Tela para reverter uma expiração. A ficha fica no histórico, e o paciente pode abrir uma nova ficha.
- Tela de configuração do parâmetro, que pertence a `add-cadastros-administrador`.

## Capabilities

### New Capabilities
_Nenhuma._

### Modified Capabilities
- `ficha-atendimento`: ficha não concluída em 24 horas é encerrada como desistência.
- `fila-pre-triagem`: ticket não concluído em 24 horas é encerrado como desistência.

## Impacto

- **Xano:**
  - nova tarefa `task/expirar_registros.xs`, que roda a cada hora e chama uma função;
  - nova função `manutencao/expirar_registros`, com teste;
  - o parâmetro `HORAS_EXPIRACAO` passa a ser criado pela inicialização existente dos parâmetros da fila.
  - Nenhuma tabela é alterada: `DESISTENCIA` já existe nos dois enums, e `historico_alteracao.usuario_id` já aceita vazio.
- **Reflex:** nenhuma mudança. A lista "Fichas do dia" já mostra "Desistência" no filtro "Finalizadas".
- **Documentos:** `docs/domain-model.md` (máquina de estados, regra do ticket, parâmetro) e `docs/project-overview.md`.

## Perguntas em aberto

- [ ] Ficha `CHAMADO` (o médico chamou e o paciente está na sala) também expira em 24 h? Proposta: sim, para não deixar nada preso. Na prática, uma chamada não dura 24 h.
- [ ] A ficha `EM_TRIAGEM` nunca confirmada deveria virar `CANCELADO` em vez de `DESISTENCIA`, já que nunca entrou na fila? Proposta: `DESISTENCIA`, como o PO pediu, com a justificativa da expiração no histórico.

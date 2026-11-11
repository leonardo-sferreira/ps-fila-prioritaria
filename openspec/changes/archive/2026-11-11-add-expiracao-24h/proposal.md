# Proposta: dispensa de fichas e tickets parados há mais de 24 horas

| Campo | Valor |
|---|---|
| Change | `add-expiracao-24h` |
| Sprint / card Trello | Sprint 4; card a definir |
| Depende de | `add-fichas-do-dia` (a lista mostra o efeito da dispensa) |
| Situação | Em implementação (pedido do PO em 10/11/2026; revisada no mesmo dia: o plano gratuito do Xano não permite tarefa agendada, e o PO decidiu que a dispensa é uma ação do Administrador) |
| Rastreabilidade formal | Regra nova; registrar na Documentação de Requisitos (Rev. 2.2) |

## Why

Fichas e tickets abandonados ficam presos para sempre:
- uma ficha aberta e nunca confirmada continua "em triagem" e impede o paciente de ter uma nova ficha (RN03);
- uma senha esquecida continua na fila do médico;
- um ticket do Totem nunca chamado continua na fila de pré-triagem.

O PO pediu que tudo que passar de 24 horas sem conclusão possa ser encerrado como desistência. Como o plano gratuito do Xano não roda tarefas agendadas, o Administrador dispara a dispensa: vê o que está parado e dispensa tudo de uma vez.

## What Changes

- **Painel do Administrador:** novo cartão "Fichas e tickets parados", na área inicial do Administrador:
  - lista o que passou do prazo, com senha ou ticket, situação e chegada ou emissão;
  - botão **"Dispensar todos"**, com confirmação.
- **Prazo configurável** `HORAS_EXPIRACAO` (inicialmente 24), contado da chegada (ficha) ou da emissão (ticket). Exatamente no prazo ainda não conta como parado.
- **O que é dispensado:**
  - fichas `EM_TRIAGEM`, `AGUARDANDO` ou `CHAMADO` passam a `DESISTENCIA` e saem da fila; o paciente fica livre para uma nova ficha;
  - tickets do Totem `AGUARDANDO` ou `CHAMADO` passam a `DESISTENCIA` e saem da fila de pré-triagem.
- **Auditoria:** cada encerramento fica no histórico como evento `EXPIRACAO`, em nome do Administrador que dispensou, com o estado anterior e a justificativa.
- **Máquina de estados da ficha:** `EM_TRIAGEM` e `AGUARDANDO` passam a poder ir para `DESISTENCIA`, só por essa dispensa.
- **Xano:** `GET expiracao` (prévia) e `POST expiracao` (dispensa), só para o perfil Administrador.

### Fora do escopo

- Dispensa automática ou agendada. Exigiria plano pago do Xano.
- Dispensa seletiva (escolher item por item). A ação dispensa tudo o que passou do prazo.
- Reverter uma dispensa. A ficha fica no histórico, e o paciente pode abrir uma nova.
- Tela de configuração do parâmetro, que pertence a `add-cadastros-administrador`.

## Capabilities

### New Capabilities
_Nenhuma._

### Modified Capabilities
- `ficha-atendimento`: ficha parada além do prazo pode ser dispensada pelo Administrador como desistência.
- `fila-pre-triagem`: ticket parado além do prazo pode ser dispensado pelo Administrador como desistência.

## Impacto

- **Xano:**
  - função pura `manutencao/expirou`, com testes;
  - função `manutencao/expirar_registros`, com prévia e aplicação;
  - endpoints `api/triagem/expiracao_get.xs` e `api/triagem/expiracao_post.xs`;
  - `HORAS_EXPIRACAO` em `inicializar_parametros_fila`.
  - Nenhuma tabela é alterada.
- **Reflex:** estado `estados/expiracao.py` e cartão na área do Administrador (`paginas/areas.py`).
- **Documentos:** `docs/domain-model.md` e `docs/project-overview.md`.

## Perguntas em aberto

- [x] Ficha `CHAMADO` também é dispensada? Sim, para nada ficar preso (decisão do PO, 10/11/2026).
- [x] Ficha `EM_TRIAGEM` vira `DESISTENCIA` ou `CANCELADO`? `DESISTENCIA`, como o PO pediu.
- [x] Disparo automático ou manual? Manual, pelo Administrador, porque o plano do Xano não tem tarefas (decisão do PO, 10/11/2026).

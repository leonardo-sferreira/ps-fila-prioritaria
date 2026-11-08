# Design: chamada manual na fila de pré-triagem

## Context

A change arquivada `implementar-chamada-automatica-tickets` deixou:

- `POST tickets/{ticket_id}/acao` com as ações `PRESENTE`, `DESISTENCIA`, `REPETIR`, `AUSENCIA` e `AVANCAR`. `REPETIR` e `AUSENCIA` já existem, mas a tela só usa `AVANCAR`, que decide sozinha entre nova chamada e fim da oportunidade. `AUSENCIA` hoje só é aceita com as 3 chamadas feitas.
- Todas as ações usam um único prazo: `chamado_em + INTERVALO_CHAMADA_SEGUNDOS`.
- `GET tickets` devolve `agora` e `intervalo_segundos` para a tela calcular a contagem.
- Em `FilaTicketsState`, `monitorar` recarrega a cada 10 s, desconta 1 s por segundo e chama `atualizar_automaticamente`, que envia `AVANCAR` quando a contagem chega a zero.
- Os parâmetros são criados por `inicializar_parametros_fila`, chamada dentro da transação de `tickets/proximo` e de `tickets/{id}/acao`.

## Goals / Non-Goals

**Goals:**
- Reaproveitar `REPETIR` e `AUSENCIA` como as ações dos botões "Chamar novamente" e "Não compareceu".
- Calcular o intervalo da chamada atual no Xano a partir da contagem de chamadas que o ticket já tem, sem coluna nova.

**Non-Goals:**
- Alterar `tickets/proximo`, `PRESENTE` ou `DESISTENCIA`.
- Criar tela de administração de parâmetros.

## Decisions

### D1 — Intervalo pela contagem de chamadas
O intervalo da chamada atual é `INTERVALO_CHAMADA_SEGUNDOS` quando `tentativas <= 1` e `INTERVALO_REPETICAO_SEGUNDOS` quando `tentativas >= 2`. O prazo continua sendo `chamado_em + intervalo`, já que `REPETIR` atualiza `chamado_em`.
- *Alternativa:* guardar o prazo em uma coluna `liberado_em`. Descartada: duplica o que já se deriva de `chamado_em` e `tentativas`.

### D2 — `REPETIR` e `AUSENCIA` com o mesmo prazo; remover `AVANCAR`
- `REPETIR`: exige ticket CHAMADO, sem presença, prazo vencido e `tentativas < TENTATIVAS_CHAMADA`. Soma uma chamada, grava `chamado_em = now` e `chamado_por`.
- `AUSENCIA`: exige ticket CHAMADO, sem presença e prazo vencido, em qualquer chamada (deixa de exigir `tentativas == limite`). Na 1ª oportunidade grava `AGUARDANDO`, `oportunidade = 2`, `tentativas = 0`, `fila_em = now`; na 2ª grava `NAO_COMPARECEU`.
- `AVANCAR` sai da lista de ações aceitas e passa a ser recusada com `ACAO_INVALIDA`. Mantê-la permitiria a qualquer cliente continuar o avanço automático, que o PO pediu para eliminar.
- A auditoria continua sendo gravada pela chamada já existente a `registrar_alteracao`.

### D3 — Novo parâmetro criado pela função existente
`INTERVALO_REPETICAO_SEGUNDOS` (valor inicial `10`, tipo `INTEIRO`) entra na lista de `inicializar_parametros_fila`. Como `tickets/proximo` executa a função antes de qualquer ticket virar CHAMADO, o parâmetro existe quando a primeira repetição é pedida. `GET tickets` passa a devolver também `intervalo_repeticao_segundos` (0 quando ausente) e não chama a função, para não gravar em uma consulta.

### D4 — Tela só calcula e mostra
Em `carregar`, `segundos_restantes` usa o intervalo da D1 conforme `tentativas`. Também calcula `pode_chamar_novamente` (`tentativas < limite`); para isso `GET tickets` devolve `tentativas_maximas` (valor de `TENTATIVAS_CHAMADA`). `monitorar` mantém a recarga a cada 10 s e o desconto de 1 s, e deixa de chamar qualquer ação; `atualizar_automaticamente` é removido. O cartão do ticket chamado mostra a contagem e, quando ela chega a zero, os botões "Chamar novamente" (se `pode_chamar_novamente`) e "Não compareceu", que enviam `REPETIR` e `AUSENCIA`. Se o relógio da tela adiantar, o Xano recusa com `AGUARDE_INTERVALO` e a tela mostra a mensagem.
- *Alternativa:* o Xano devolver `liberado_em` pronto por ticket. Descartada: exigiria laço extra no `GET` e a tela já faz a conta com `agora`.

## Risks / Trade-offs

- [Operador esquece um ticket chamado] → O ticket fica CHAMADO no topo da tela, com destaque, até alguém agir; é o comportamento pedido (nada automático).
- [Relógio do navegador diferente do Xano] → A contagem usa `agora` do Xano a cada recarga; se mesmo assim o clique chegar cedo, o backend recusa sem alterar o ticket.
- [Tela antiga ainda aberta enviando `AVANCAR` durante a publicação] → Recebe `ACAO_INVALIDA` e nada muda; basta recarregar a página.

## Migration Plan

1. Publicar no Xano (`v1`) `function/inicializar_parametros_fila.xs`, `api/triagem/tickets_acao_post.xs` e `api/triagem/tickets_get.xs`, com `--dry-run` antes e push restrito a esses arquivos.
2. Publicar o Reflex (`reflex run` local).
3. Reversão: republicar as versões anteriores dos três `.xs` (estão no Git) e voltar o commit do Reflex; o parâmetro novo pode ficar na tabela sem efeito.

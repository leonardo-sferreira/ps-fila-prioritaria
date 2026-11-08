# Tarefas

Decisão do PO em 08/11/2026: a chamada na pré-triagem passa a ser manual. Ver `proposal.md` e `design.md` (D1–D4).

## 1. Documentos de domínio

- [x] 1.1 Atualizar `docs/project-overview.md` (fluxo item 2, escopo e regras de chamada) e `docs/domain-model.md` (regras do Ticket, máquina de estados e tabela de parâmetros com `INTERVALO_REPETICAO_SEGUNDOS` = 10) para a chamada manual: 30 s depois da 1ª chamada, 10 s depois das seguintes, até 3 por oportunidade, "Não compareceu" pela Recepção; deixar explícito que a regra do Médico não muda. Ajustar o resumo de invariantes em `openspec/config.yaml`. Verificar com busca por "automátic" nos três arquivos que nenhuma regra antiga da pré-triagem ficou
  - Evidência (08/11/2026): a busca só encontra regras sem relação com a chamada (promoção, direcionamento, seleção do próximo) e as frases novas que negam a automação; `openspec validate` aceita a change.

## 2. Xano

- [x] 2.1 Em `function/inicializar_parametros_fila.xs`, acrescentar `INTERVALO_REPETICAO_SEGUNDOS` com valor `10` (D3; usado pela 2.2 e 2.3). Verificar com `xano_validate_xanoscript`
- [x] 2.2 Em `api/triagem/tickets_acao_post.xs`, aplicar D1 e D2: intervalo por `tentativas`, `REPETIR` só com prazo vencido e abaixo do limite, `AUSENCIA` com prazo vencido em qualquer chamada (1ª oportunidade volta ao fim da fila, 2ª vira `NAO_COMPARECEU`) e `AVANCAR` recusada com `ACAO_INVALIDA`. Verificar com `xano_validate_xanoscript`
- [x] 2.3 Em `api/triagem/tickets_get.xs`, devolver também `intervalo_repeticao_segundos` e `tentativas_maximas` (D3, D4; usados pela 3.1). Verificar com `xano_validate_xanoscript`
  - Evidência 2.1–2.3 (08/11/2026): `xano_validate_xanoscript` — 3 arquivos válidos, 0 avisos.
- [x] 2.4 Publicar os três arquivos na `v1` (`--dry-run` antes, push restrito a eles) e conferir com `xano workspace pull` que o servidor ficou igual ao repositório
  - Evidência (08/11/2026): o `--dry-run` mostrou só as 3 atualizações esperadas (1 função, 2 endpoints), sem remoções; o PO rodou o push restrito na `v1` e o `xano workspace pull` confirmou `INTERVALO_REPETICAO_SEGUNDOS` nos três objetos, `tentativas_maximas` em `GET tickets` e nenhuma ocorrência de `AVANCAR` ou `TENTATIVAS_NAO_ESGOTADAS`.

## 3. Reflex

- [x] 3.1 Em `FilaTicketsState`: remover `atualizar_automaticamente` e a chamada a ele em `monitorar`; em `carregar`, calcular `segundos_restantes` pelo intervalo da chamada atual e `pode_chamar_novamente`; criar `chamar_novamente(id)` e `nao_compareceu(id)` reaproveitando `acao` com `REPETIR` e `AUSENCIA`. Substituir `tests/test_chamada_automatica.py` por casos de valor-limite: contagem com 1 chamada (30 s), com 2 e 3 chamadas (10 s), `pode_chamar_novamente` falso na 3ª, `monitorar`/recarga sem enviar ação e envio de `REPETIR`/`AUSENCIA`. Verificar que a suíte unitária passa
  - Evidência (08/11/2026): `tests/test_chamada_manual.py` substitui `test_chamada_automatica.py` (30 s com 1 chamada, 10 s com 2 e 3, limites 29/30 e 9/10, botão some na 3ª, parâmetros ausentes, `REPETIR`/`AUSENCIA`, `monitorar` sem ação); suíte unitária com 132 passando.
- [x] 3.2 No cartão do ticket chamado (`cartao_chamado`), trocar "próxima etapa em N s" por "Chamar novamente e Não compareceu liberam em N s"; com a contagem em zero, mostrar "Chamar novamente" (só se `pode_chamar_novamente`) e "Não compareceu", mantendo Marcar presente, Identificar e Desistência. Verificar que `reflex export` compila
  - Evidência (08/11/2026): botões ficam desabilitados durante a contagem; "Chamar novamente" some quando `pode_chamar_novamente` é falso; `reflex export` compila.

## 4. Verificação ponta a ponta

- [ ] 4.1 Com um ticket de teste e um usuário da Recepção: chamar, conferir botões bloqueados nos primeiros 30 s; chamar novamente e conferir 10 s; terceira chamada e conferir que só resta "Não compareceu"; registrar não comparecimento e ver o ticket no fim da fila como 2ª oportunidade; repetir até `NAO_COMPARECEU`; conferir que, sem clique, o ticket fica parado em CHAMADO. Pedidos fora do prazo, quarta chamada e `AVANCAR` devem ser recusados pela API sem alterar o ticket (roteiro manual, pois o login exige código por e-mail)

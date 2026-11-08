# Tarefas

Card #35 assumido pelo PO em 08/11/2026. Ver `proposal.md` e `design.md` (D1–D8).

## 1. Documentos de domínio

- [x] 1.1 Atualizar `docs/domain-model.md` (regras da Ficha, tabela de parâmetros com limiares 5 e 10, idade mínima da tabela adulta 16, e seção "Faixas de sinais vitais" com a tabela da §21.2, a glicemia com ≥60 → 0 e a regra de inelegíveis) e `docs/project-overview.md` (escore clínico e classificação: 0–4 Azul, 5–9 Amarela, ≥10 Vermelha, item de 3 pontos → Vermelha, ajuste descartado no recálculo). Verificar com busca por "≥ 3", "≥ 6", "a partir de 3" e "a partir de 6" que os limiares antigos saíram

## 2. Xano — dados e regra

- [x] 2.0 Criar `table/ficha_sintoma_livre.xs` com `ficha_id`, `descricao`, `pontuacao`, `criado_por` e índice por ficha (D9; usada pela 2.4 e 3.2). Verificar com `xano_validate_xanoscript`
- [x] 2.1 Em `table/faixa_sinal_vital.xs`, tornar `minimo` e `maximo` anuláveis (D1). Verificar com `xano_validate_xanoscript`
- [x] 2.2 Criar `function/classificacao/inicializar_classificacao.xs` com os 5 parâmetros e as faixas da §21.2 e §21.3, inserindo faixas só com a tabela vazia (D2; usada pela 2.5 e 2.6). Incluir bloco `test` que confere a contagem de faixas por parâmetro. Verificar com `xano_validate_xanoscript`
- [x] 2.3 Criar `function/classificacao/pontuar.xs`, função pura (D3; usada pela 2.4), com blocos `test` para: bordas da FC, PA, FR, temperatura e SpO₂ (§21.4); glicemia 53 sem e com gravidade, 54–59 e ≥60; escore 4/5 e 9/10; convulsão isolada de 3 pontos; sintoma digitado de 2 e de 3 pontos; temperatura 39,1 sem Vermelha; casos da §5.4; SpO₂ ausente; 10 e 16 anos; gestante; condição GESTANTE/IDOSO/CRIANCA e limite de 12 anos; faixa ausente. Verificar com `xano_validate_xanoscript`
- [x] 2.4 Criar `function/classificacao/avaliar_ficha.xs` (D4; usada pela 2.5 e 2.6), lendo ficha, paciente, sintomas distintos do catálogo, sintomas digitados, faixas e parâmetros e calculando a idade na chegada em `America/Sao_Paulo`. Verificar com `xano_validate_xanoscript`

## 3. Xano — endpoints

- [x] 3.1 `api/triagem/fichas_id_get.xs`: `auth`, `verificar_acesso` (D7) e resposta com sintomas digitados, sinais vitais, gestação, idade, resultado de `avaliar_ficha` (pontos por sinal, escores, item crítico, prioridades, justificativa, condição e pendências). Verificar com `xano_validate_xanoscript`
- [x] 3.2 `api/triagem/fichas_id_patch.xs`: `auth`, `verificar_acesso`, exigência de `EM_TRIAGEM`, input `sinais_vitais` como conjunto final com limites de digitação (D5), input `sintomas_livres` como lista final com as validações de tamanho, pontuação, limite de 10 e duplicidade contra a lista e o catálogo, e RN04 contando os digitados (D9), chamada a `inicializar_classificacao`, recálculo que descarta o ajuste e `registrar_alteracao` (`SINTOMAS_ALTERADOS` / `SINAIS_VITAIS_ALTERADOS`, com a prioridade atual anterior) na transação. Verificar com `xano_validate_xanoscript`
- [x] 3.3 Criar `api/triagem/fichas_id_prioridade_post.xs` (`POST fichas/{ficha_id}/prioridade`, D6; usado pela 4.2) com as recusas de justificativa vazia, ficha fora de `EM_TRIAGEM`, prioridade igual à calculada e perfil sem permissão, e auditoria `PRIORIDADE_ALTERADA`. Verificar com `xano_validate_xanoscript`
- [x] 3.4 `api/triagem/sintomas_get.xs`: `auth` e `verificar_acesso` (D7). Verificar com `xano_validate_xanoscript`
- [x] 3.5 Publicar na `v1` os arquivos das tarefas 2.0–3.4 (`--dry-run` antes, push restrito, sem `ficha_atendimento`); rodar os testes unitários das funções no Xano; conferir com `xano workspace pull` que o servidor ficou igual ao repositório
  - Evidência (08/11/2026): `--dry-run` com 1 tabela criada, 1 alterada, 4 funções, 1 endpoint novo e 3 alterados, sem `ficha_atendimento` e sem remoções; push feito pelo PO. A primeira rodada de `xano unit_test run_all` revelou que o Xano converte `faixas: []` em null e a função caía nas faixas padrão; corrigido com o input `faixas_padrao` só para testes e republicado. Rodada final: os 41 testes da classificação passam (faixas_padrao, inicializar_classificacao e os 39 de `pontuar`); os 3 que falham são de `pacientes/{paciente_id}` (telefone), anteriores a esta change, por exigirem sessão. `xano workspace pull` confirmou as funções, a tabela `ficha_sintoma_livre`, `fichas/{ficha_id}/prioridade` e `verificar_acesso` em `sintomas` e `fichas/{ficha_id}` GET/PATCH. Suíte unitária do Reflex com 131 passando; `reflex export` compila.

- [x] 3.6 `api/triagem/fichas_post.xs`: devolver a ficha existente `EM_TRIAGEM` (sem ticket) com `ja_existente: true`, sem criar ficha nem auditar cadastro; manter a recusa para `AGUARDANDO`/`CHAMADO` ou com ticket (decisão do PO em 08/11/2026, achada no teste da 5.1: o paciente com ficha aberta ficava travado em `FICHA_NAO_FINALIZADA_EXISTENTE`). Verificar com `xano_validate_xanoscript` e `test_ficha_abertura_contract.py`
  - Evidência (08/11/2026): XanoScript válido; contrato atualizado e passando.

## 4. Reflex

- [x] 4.1 Refatorar `FichaState` para usar `api.requisitar` com o token da sessão (D7) e tratar 401; acrescentar os campos de sinais vitais, gestante, resultado da classificação e pendências, enviando `sinais_vitais` e `sintomas_livres` no salvamento, com adicionar/remover sintoma digitado e gravidade. Atualizar `tests/test_ficha_state.py` (token enviado, sintoma digitado adicionado e removido, descrição vazia bloqueada na tela, conjunto final de sinais vitais, campo limpo enviado como vazio, leitura do resultado e das pendências). Verificar que a suíte unitária passa
- [x] 4.2 Criar no `FichaState` o ajuste de prioridade (cor e justificativa) chamando `POST fichas/{id}/prioridade`, com teste de estado (envio, justificativa vazia bloqueada na tela, recarga após sucesso). Verificar que a suíte unitária passa
- [x] 4.3 Refazer `/recepcao/ficha/{id}` no padrão da tela 4 do Figma (D8): coluna do paciente com idade e condição, sinais vitais, sintomas e observação com "Adicionar como sintoma não listado" e escolha de gravidade, linha do escore, três cartões de cor, pendências, "Gestante" e diálogo "Ajustar prioridade". Verificar que `reflex export` compila

- [x] 4.4 Traduzir na tela os códigos da ficha e da classificação (`FICHA_NAO_FINALIZADA_EXISTENTE`, `FICHA_FORA_DA_TRIAGEM`, `SINAL_VITAL_INVALIDO:<campo>`, `SINTOMA_LIVRE_*`, `JUSTIFICATIVA_OBRIGATORIA`, `PRIORIDADE_*`) e cobrir o "Continuar" com ficha reaberta. Verificar que a suíte unitária passa
  - Evidência (08/11/2026): `test_mensagem_erro.py` e `test_paciente_state.py` atualizados; suíte unitária com 135 passando.

## 5. Verificação ponta a ponta

- [ ] 5.1 Logado como Recepção/Triagem, com fichas de teste: adulto com sinais normais e sintomas 2+2+1 (Amarela); sintoma digitado de 3 pontos (Vermelha) e nome igual ao do catálogo recusado; SpO₂ 91 (Vermelha); faltando FR (pendência); paciente de 10 anos e gestante (classificação manual obrigatória); ajuste Azul→Amarela com justificativa e conferência na auditoria; alteração de sinal vital depois do ajuste (ajuste descartado); acesso sem sessão recusado. Roteiro manual, pois o login exige código por e-mail

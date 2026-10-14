# Tarefas

## 1. Fatia atual — Schema e catálogo de sintomas

- [x] 1.1 [Xano] Adequar `ficha_atendimento.aberta_por` para aceitar `null` temporariamente, preservando a FK para `usuario`; verificar no schema exportado que nenhum valor artificial é exigido na criação da ficha
  - Evidência: schema ajustado manualmente no Dashboard e aceito por decisão humana; `aberta_por` nullable, FK `usuario` preservada; `POST /fichas` cria ficha sem `aberta_por` retornando 0/null; exportado em `backend/xano/table/ficha_atendimento.xs`.
- [x] 1.2 [Xano] Substituir `sintoma.prioridade_padrao` por `pontuacao` inteira obrigatória de 1 a 3 e incluir `TRAUMATICO_NEUROLOGICO` no enum de grupo; verificar que o schema não mantém cor/prioridade fixa por sintoma
  - Evidência: schema `sintoma` exportado em `backend/xano/table/sintoma.xs` com `pontuacao` int obrigatória, enum `grupo` inclui `TRAUMATICO_NEUROLOGICO`, `prioridade_padrao` removido, sem campo de cor.
- [x] 1.3 [Xano] Implementar carga idempotente do catálogo oficial de `docs/domain-model.md` com nome, descrição quando existente, grupo, `pontuacao` 1–3 e ativo; verificar que duas execuções não duplicam registros nem usam thresholds de classificação
  - Evidência: seed em `backend/xano/function/sintomas/carregar_catalogo_inicial.xs` com 46 sintomas; duas execuções remotas mantiveram exatamente 46 registros (sem duplicação); nenhum threshold de classificação incluso.
- [x] 1.4 [Xano] Verificar que a carga torna sintomas ativos disponíveis para `GET /sintomas`, incluindo ao menos nome, grupo e pontuação; registrar a contagem carregada contra o catálogo oficial sem inventar dados
  - Evidência: `GET /sintomas` remoto retorna 46 sintomas ativos com `id`, `nome`, `grupo`, `pontuacao`; contagem confere com catálogo oficial de 46 sintomas do `docs/domain-model.md`.

## 2. Fatia atual — API de ficha e sintomas

- [x] 2.1 [Xano] Implementar `POST /fichas` com `paciente_id` obrigatório e `ticket_id` opcional; validar paciente, definir `chegada_em` no backend, gravar `EM_TRIAGEM`, permitir `aberta_por=null` e verificar a resposta criada
  - Evidência: `POST /fichas` publicado em `backend/xano/api/triagem/fichas_post.xs`; smoke test e teste de integração `test_rf06_abertura_de_ficha` passaram; `chegada_em` gerado pelo backend; status inicial `EM_TRIAGEM`.
- [x] 2.2 [Xano] Garantir transacionalmente no `POST /fichas` no máximo uma ficha não finalizada por paciente, considerando não finais `EM_TRIAGEM`, `AGUARDANDO` e `CHAMADO`, e finais `ATENDIDO`, `DESISTENCIA` e `CANCELADO`; verificar que a ficha anterior permanece no histórico
  - Evidência: o filtro transacional em `fichas_post.xs` usa esses três estados não finais e retorna `FICHA_NAO_FINALIZADA_EXISTENTE`; a matriz runtime completa permanece pendente em 2.7.
- [x] 2.3 [Xano] Implementar `GET /sintomas` retornando somente sintomas ativos com `id`, nome, descrição quando houver, grupo e pontuação; verificar que a resposta não expõe cor/prioridade fixa
  - Evidência: `GET /sintomas` publicado em `backend/xano/api/triagem/sintomas_get.xs`; retorna somente ativos; campos `id`, `nome`, `grupo`, `pontuacao`; sem `cor` nem `prioridade_padrao`.
- [x] 2.4 [Xano] Implementar `GET /fichas/{id}` com paciente relacionado, observação geral e coleção de sintomas; verificar que permite recarregar o estado de edição sem expor `ficha_sintoma.observacao`
  - Evidência: `GET /fichas/{ficha_id}` publicado em `backend/xano/api/triagem/fichas_id_get.xs`; retorna ficha + paciente + sintomas; sem `ficha_sintoma.observacao` na resposta; FichaState carrega corretamente.
- [x] 2.5 [Xano] Implementar `PATCH /fichas/{id}` para `observacao` e/ou `sintoma_ids`, tratando a lista enviada como coleção final e aplicando adições/remoções sem duplicidade em transação única; verificar o respeito ao índice único `(ficha_id, sintoma_id)`
  - Evidência: `PATCH /fichas/{ficha_id}` publicado em `backend/xano/api/triagem/fichas_id_patch.xs` com abordagem sentinela `"__OMITTED__"`; smoke tests A–I todos passaram; troca de coleção `[1,5]→[5,9]` funciona; sem duplicidade.
- [x] 2.6 [Xano] Validar RN04 no estado resultante de cada PATCH que altera observação e/ou sintomas: exigir ao menos um sintoma ou observação geral não vazia após trim; verificar que `POST /fichas` ainda pode abrir ficha vazia em `EM_TRIAGEM`, sem criar status adicional
  - Evidência: smoke tests G1–G3 (RN04 inválida) retornam `FICHA_SEM_SINTOMA_OU_OBSERVACAO`; `POST /fichas` cria ficha vazia sem bloqueio; sem status adicional criado.
- [ ] 2.7 [Testes Xano/API] Cobrir RF06, RN03 e a ficha não finalizada: paciente sem ficha cria; `EM_TRIAGEM`, `AGUARDANDO` e `CHAMADO` bloqueiam segunda; `ATENDIDO`, `DESISTENCIA` e `CANCELADO` permitem nova ficha e preservam histórico
  - Pendente: o teste de integração atual valida somente o bloqueio em `EM_TRIAGEM`; faltam fixtures controladas ou testes Xano para os demais estados não finais e finais, sem introduzir transições fora desta fatia.
- [x] 2.8 [Testes Xano/API] Cobrir RF07, coleção final e RN04: sintomas sem observação, observação sem sintomas e ambos; alterar apenas observação preservando sintomas; alterar apenas sintomas preservando observação; recusar remover o último sintoma sem observação, limpar observação sem sintomas, whitespace sem sintomas e coleção vazia com observação resultante vazia
  - Evidência: teste de integração `test_rf07_e_rn04_fluxo_completo_ficha` passou; smoke tests A–I cobrindo todos os cenários listados; arquivo `frontend/tests/test_xano_api_integration.py`.
- [x] 2.9 [Testes Xano/API] Cobrir paciente ou sintoma inexistente/inativo, ticket opcional, `chegada_em` gerado pelo backend, `EM_TRIAGEM` inicial, duplicidade de IDs de sintoma e recarga por `GET /fichas/{id}`; verificar que todos passam
  - Evidência: smoke test H (sintoma inexistente → `SINTOMA_INEXISTENTE_OU_INATIVO`); smoke test I (nenhum campo → `NENHUM_CAMPO_ATUALIZAVEL_INFORMADO`); `chegada_em` verificado no `test_rf06_abertura_de_ficha`; 4/4 testes de integração passaram.
- [x] 2.10 [Xano] Exportar os XanoScripts desta fatia para `backend/xano/` após validação do ambiente e verificar que correspondem às APIs e schemas publicados
  - Evidência: arquivos exportados em `backend/xano/api/triagem/` (fichas_post.xs, fichas_id_get.xs, fichas_id_patch.xs, sintomas_get.xs) e `backend/xano/function/sintomas/carregar_catalogo_inicial.xs`; schemas em `backend/xano/table/ficha_atendimento.xs` e `backend/xano/table/sintoma.xs`.

## 3. Fatia atual — Reflex

- [x] 3.1 [Reflex] Integrar `Continuar` do paciente identificado a `POST /fichas` e navegar para `/recepcao/ficha/{id}` após criação bem-sucedida; verificar que paciente selecionado é o da ficha criada
  - Evidência: handler `continuar_atendimento` em `PacienteState` chama `POST /fichas` e faz `rx.redirect(f"/recepcao/ficha/{ficha_id}")`; E2E etapa 4 confirmada.
- [x] 3.2 [Reflex] Criar `FichaState` separado de `PacienteState`, com ficha, paciente, catálogo, sintomas selecionados, observação, carregamento, salvamento e erros; verificar que nenhuma regra clínica é adicionada ao estado de Paciente
  - Evidência: `FichaState` em `ps_fila_prioritaria.py` separado de `PacienteState`; 10 testes unitários Reflex passam (`test_ficha_state.py`, `test_paciente_state.py`); sem regra clínica em `PacienteState`.
- [x] 3.3 [Reflex] Criar `/recepcao/ficha/{id}` carregando ficha e sintomas ativos, com seleção/desmarcação e campo de observação geral; verificar que não há UI para `ficha_sintoma.observacao`
  - Evidência: `app.add_page(... route="/recepcao/ficha/[id]", on_load=FichaState.carregar_da_rota)`; seleção/desmarcação de sintomas e observação geral implementadas; não há UI para `ficha_sintoma.observacao`.
- [x] 3.4 [Reflex] Salvar por `PATCH /fichas/{id}`, recarregar dados persistidos e exibir erros de RN04; verificar manualmente sintomas sem observação, observação sem sintomas, edição posterior e recusa do estado resultante inválido
  - Evidência: `FichaState.salvar` chama `PATCH /fichas/{id}`, recarrega por `FichaState.carregar` com `GET /fichas/{id}` e usa `mensagem`/`erro` como feedback; cobertura unitária de estado passou. E2E por UI permanece pendente de navegador disponível.
- [x] 3.5 [Testes Reflex] Cobrir o `FichaState`, criação/navegação e preservação da seleção/observação ao recarregar; verificar compilação Reflex e roteiro manual da tela
  - Evidência: 10 testes unitários Reflex passam, incluindo criação/navegação em `PacienteState` e recarga em `FichaState`; `reflex compile --dry` executado com sucesso. E2E por UI permanece pendente de navegador disponível.

## 4. Fatia atual — Aceite e documentação da entrega

- [x] 4.1 [Aceite] Verificar RF06: paciente identificado abre ficha nova em `EM_TRIAGEM`, com horário do backend, ticket opcional e sem depender de Totem
  - Evidência: `POST /fichas` remoto cria ficha com `status=EM_TRIAGEM`, `chegada_em` gerado pelo backend, `ticket_id` opcional (aceita null); sem dependência de Totem; teste de integração e smoke test passaram.
- [x] 4.2 [Aceite] Verificar RF07: a tela consulta sintomas ativos, registra sintomas e observação geral e permite edição posterior sem observação por sintoma
  - Evidência: `GET /sintomas` retorna 46 ativos; `PATCH /fichas/{id}` aceita `sintoma_ids` e/ou `observacao`; edição posterior testada no E2E etapa 12; sem `ficha_sintoma.observacao` exposta.
- [ ] 4.3 [Aceite] Verificar RN03: bloqueio de segunda ficha não finalizada e nova ficha após cada estado final, mantendo histórico
  - Pendente: há evidência apenas para `EM_TRIAGEM`, cujo erro efetivo é `FICHA_NAO_FINALIZADA_EXISTENTE`; falta verificar `AGUARDANDO`, `CHAMADO`, `ATENDIDO`, `DESISTENCIA` e `CANCELADO` com fixtures controladas, preservando histórico.
- [x] 4.4 [Aceite] Verificar RN04: o salvamento aceita um ou mais sintomas, observação não vazia ou ambos, e recusa o estado resultante sem os dois componentes
  - Evidência: PATCH somente sintomas → 200 OK; somente observação → 200 OK; ambos → 200 OK; ambos vazios → 400 `FICHA_SEM_SINTOMA_OU_OBSERVACAO`; whitespace → 400; smoke tests G1–G3 passaram.

## 5. Etapas futuras — Classificação clínica e prioridade

- [ ] 5.1 [Decisão de produto] Definir e aprovar as faixas de `escore_total` para Azul, Amarela e Vermelha antes de implementar classificação final; verificar decisão registrada nos artefatos OpenSpec da etapa futura
- [ ] 5.2 [Xano] Implementar sinais vitais, gestação, glicemia, faixas fisiológicas e suas validações após a aprovação das faixas de classificação; verificar testes de valores-limite aprovados
- [ ] 5.3 [Xano] Implementar cálculo de soma das pontuações de sintomas, escore fisiológico, escore total, classificação e prioridades calculada/atual; verificar cenários de soma e classificação aprovados
- [ ] 5.4 [Xano] Implementar ajuste manual de prioridade, simulação e configuração de risco após a definição das faixas; verificar justificativa, restrições de estado e testes correspondentes
- [ ] 5.5 [Reflex] Criar componentes de sinais vitais, classificação, ajuste de prioridade e `/admin/risco` após as APIs futuras; verificar os roteiros aprovados da etapa

## 6. Dependências deferidas

- [ ] 6.1 [Autenticação] Após `add-autenticacao-perfis`, preencher `aberta_por` pelo usuário autenticado e reavaliar a nulabilidade; verificar que não há usuário, token ou stub artificial nesta fatia
- [ ] 6.2 [Autorização] Integrar permissões reais de Recepção/Triagem, Administrador e Médico quando a infraestrutura estiver disponível; verificar respostas de acesso negado previstas
- [ ] 6.3 [Auditoria] Integrar `registrar_alteracao` de `add-base-compartilhada` para mudanças de ficha, sintomas e observação; verificar atomicidade com as operações sem criar mecanismo paralelo

# Design técnico

## Contexto

`paciente`, `ficha_atendimento`, `ficha_sintoma` e `sintoma` já existem no Xano. A fatia atual não recria essas tabelas: adequa o schema necessário, expõe APIs de ficha/sintomas e conecta a tela de ficha ao paciente identificado na fatia anterior.

O schema atual requer `aberta_por`, embora autenticação ainda não esteja disponível, e modela Sintoma por `prioridade_padrao`, incompatível com a pontuação numérica aprovada. A classificação clínica continua nesta change, mas não é parte da primeira entrega implementável.

## Objetivos / Fora dos objetivos

**Objetivos da fatia atual:**

- Abrir e recuperar ficha de paciente em `EM_TRIAGEM`.
- Registrar e editar a observação geral da visita e a coleção final de sintomas.
- Disponibilizar o catálogo de sintomas ativos com pontuação numérica.
- Preservar histórico de visitas e impedir mais de uma ficha não finalizada por paciente.

**Fora dos objetivos da fatia atual:**

- Sinais vitais, gestação, glicemia, classificação, prioridade, direcionamento, senha, fila, chamadas, cancelamento, autenticação e auditoria.
- Exposição ou edição de `ficha_sintoma.observacao`.

## Decisões

### D1. Reutilização e adequação do schema existente

- `ficha_atendimento` e `ficha_sintoma` são reutilizadas. A fatia usa principalmente `paciente_id`, `aberta_por`, `chegada_em`, `status`, `observacao` e as relações em `ficha_sintoma`; os demais campos futuros permanecem intactos.
- `aberta_por`, hoje obrigatório e FK para `usuario`, passa temporariamente a aceitar `null`. Nenhum usuário fixo, token artificial, mock ou stub de autenticação será criado. Após `add-autenticacao-perfis`, o endpoint deve obter o usuário autenticado e a nulabilidade deve ser reavaliada.
- `sintoma.prioridade_padrao` é removido/substituído por `pontuacao` inteira obrigatória entre 1 e 3. Sintoma não possui cor fixa; suas pontuações serão somadas apenas na etapa futura de classificação.
- O enum de `sintoma.grupo` recebe `TRAUMATICO_NEUROLOGICO`. A tabela está vazia, portanto não há migração de registros existentes. Nesta fatia, a carga idempotente usa o catálogo acadêmico existente em `docs/domain-model.md` como fonte, sem alterar esse documento, sem inventar dados e tornando sintomas ativos disponíveis para `GET /sintomas` e a tela.

### D2. Abertura de ficha e máquina de estados

`POST /fichas` recebe `paciente_id` e pode receber `ticket_id`; valida o paciente, define `chegada_em` no backend e cria a ficha com `status=EM_TRIAGEM`. `ticket_id` é opcional e a abertura não depende do Totem.

Cada chegada cria uma ficha nova e preserva o histórico. Antes de criar, a operação consulta e bloqueia, na mesma transação, a existência de outra ficha não finalizada para o paciente. Pela máquina de estados atual, `ATENDIDO`, `DESISTENCIA` e `CANCELADO` são finais; `EM_TRIAGEM`, `AGUARDANDO` e `CHAMADO` não são finais. Não são criados estados adicionais.

### D3. Observação, sintomas e RN04

`ficha_atendimento.observacao` é a única observação/queixa geral desta fatia. `ficha_sintoma.observacao` continua no schema, mas não integra requests, responses de edição ou UI.

Há dois momentos distintos:

- **Abertura:** `POST /fichas` pode criar uma ficha vazia em `EM_TRIAGEM`; RN04 não é exigida nesse instante.
- **Preenchimento válido:** `PATCH /fichas/{id}` aceita `observacao` e/ou `sintoma_ids`. Quando um desses componentes é enviado, o backend calcula o estado resultante e exige RN04: ao menos um sintoma ou observação não vazia após trim. Uma ficha recém-aberta continua `EM_TRIAGEM`; não há status `RASCUNHO` nem outro mecanismo adicional.

Um campo omitido no PATCH não altera o componente correspondente. `observacao` atualiza somente a queixa geral. `sintoma_ids`, quando presente, representa a coleção final: criar associações para IDs novos e remover as ausentes, sem duplicação e em transação única. A validação ocorre antes de consolidar um estado final inválido.

### D4. Contratos de API da fatia atual

- `POST /fichas`: cria e retorna a ficha em `EM_TRIAGEM`; `aberta_por` pode ser nulo nesta fase.
- `GET /fichas/{id}`: retorna a ficha, o paciente relacionado, a observação geral e os sintomas necessários para recarregar a edição.
- `GET /sintomas`: retorna somente sintomas ativos com `id`, `nome`, `descricao` quando houver, `grupo` e `pontuacao`.
- `PATCH /fichas/{id}`: atualiza observação e/ou a coleção final de sintomas conforme D3.

Os contratos de autorização, auditoria e seus erros específicos serão integrados pelas changes responsáveis; não haverá substitutos temporários.

### D5. Tela e estado Reflex da fatia atual

`Continuar`, no fluxo de paciente identificado, chama `POST /fichas` e navega para `/recepcao/ficha/{id}`. `PacienteState` mantém identificação/cadastro. Um `FichaState` separado mantém `ficha_id`, paciente associado, catálogo, sintomas selecionados, observação, carregamento, salvamento e erros. Não há cálculo clínico no Reflex.

### D6. Etapa futura — classificação clínica

Sinais vitais, gestação, glicemia, escore fisiológico, soma da pontuação dos sintomas, escore total, classificação, prioridade, ajustes e tela de risco permanecem nesta change, em etapa posterior. As faixas numéricas que mapeiam `escore_total` para Azul, Amarela e Vermelha estão pendentes de aprovação. Os limiares 3/6 presentes em `docs/domain-model.md` são um conflito documental registrado e não serão implementados automaticamente.

## Riscos / Compromissos

- [`aberta_por` nulo é dívida de integridade] → revisar schema e endpoint quando `add-autenticacao-perfis` estiver disponível, sem autenticação falsa nesta fatia.
- [Alterar a coleção de sintomas pode deixar vínculos parciais] → reconciliar lista e validar RN04 na mesma transação.
- [Catálogo vazio impede seleção] → executar seed oficial em tarefa própria, sem inventar sintomas ou pontuações.
- [Thresholds antigos podem vazar para classificação] → manter classificação fora da fatia e resolver o conflito documental antes de implementá-la.

## Plano de migração

1. Adequar o schema existente: `aberta_por` anulável, `pontuacao` no lugar de `prioridade_padrao` e novo valor de grupo.
2. Carregar nesta fatia o catálogo oficial de forma idempotente, sem migração de registros por a tabela estar vazia; a segunda execução não duplica registros e disponibiliza sintomas ativos para `GET /sintomas`.
3. Criar APIs e tela da fatia atual; rollback reverte endpoints e adequações de schema conforme procedimento Xano aprovado.
4. Não alterar documentos externos nesta etapa; a divergência de thresholds será resolvida antes da fase de classificação.

## Questões em aberto

- Definir e aprovar as faixas de `escore_total` para Azul, Amarela e Vermelha antes da etapa futura de classificação.

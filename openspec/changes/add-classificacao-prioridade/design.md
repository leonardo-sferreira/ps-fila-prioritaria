# Design: classificação de prioridade da ficha

## Context

- **Tabela `ficha_atendimento`:** no servidor (`v1`) já tem `gestante`, `pa_sistolica`, `fc`, `fr`, `temperatura`, `spo2`, `glicemia`, `glicemia_sinais_gravidade`, `escore_risco`, `parametro_critico`, `classificacao_risco`, `prioridade_calculada`, `prioridade_atual`, `justificativa_ajuste` e `condicao_prioritaria`. Ela é uma das três tabelas divergentes entre servidor e repositório (card do Backlog), então não deve ser republicada nesta change.
- **Tabela `faixa_sinal_vital`:** existe vazia (`parametro`, `minimo`, `maximo`, `pontos`, `condicao_gravidade`), com `minimo` e `maximo` obrigatórios. A Rev. 2.1 (§21.5) pede representar limites abertos sem teto arbitrário.
- **Tabela `parametro`:** chave-valor, carregada por `inicializar_parametros_fila` (padrão de carga idempotente já usado).
- **Endpoints da ficha:** `GET /fichas/{id}` e `PATCH /fichas/{id}` não têm `auth` nem `verificar_acesso` nem auditoria; `GET /sintomas` também não. `POST /fichas` já usa `verificar_acesso` e `registrar_alteracao`.
- **`PATCH /fichas/{id}`:** usa o marcador `"__OMITTED__"` para diferenciar campo ausente de campo vazio e trata `sintoma_ids` como coleção final.
- **Reflex:** `FichaState` chama o Xano com `httpx` direto, sem token; `FilaTicketsState` já usa `api.requisitar(..., token=auth.token)`.

## Goals / Non-Goals

**Goals:**
- Regra de pontuação em uma função pura do Xano, testável com blocos `test` sem banco.
- Um único ponto que lê a ficha, calcula e devolve o resultado, usado pelo GET (para mostrar) e pelo PATCH (para gravar).

**Non-Goals:**
- Alterar o schema de `ficha_atendimento`.
- Persistir a lista de pendências: ela é recalculada a cada consulta.

## Decisions

### D1 — Limites abertos com `minimo`/`maximo` anuláveis
`faixa_sinal_vital.minimo` e `maximo` passam a anuláveis; `null` significa "sem limite" daquele lado. Os dois extremos são inclusivos. Faixas com "ou" (FC 41–50 ou 91–110; temperatura 35,1–36,0 ou 38,1–39,0) viram duas linhas. A glicemia usa `condicao_gravidade` (`true`, `false` ou `null` = qualquer). O campo `pontos = 3` é o próprio indicador de item crítico, sem coluna extra.
- *Alternativa:* valores sentinela (0 e 9999). Descartada: a §21.5 pede explicitamente não usar teto arbitrário.

### D2 — Carga idempotente em `inicializar_classificacao`
Nova função `classificacao/inicializar_classificacao` cria, se não existirem, os parâmetros `LIMIAR_AMARELA` (5), `LIMIAR_VERMELHA` (10), `IDADE_MINIMA_TABELA_ADULTA` (16), `IDADE_MINIMA_IDOSO` (60) e `IDADE_MAXIMA_CRIANCA` (11), e insere as faixas da §21.2 e §21.3 somente se a tabela `faixa_sinal_vital` estiver vazia. É chamada no início do `PATCH /fichas/{id}` e do ajuste de prioridade (mesmo padrão de `inicializar_parametros_fila`); o GET não grava e, sem faixas ou parâmetros, só informa a pendência.
- *Alternativa:* carga manual pelo painel do Xano. Descartada: não é reproduzível nem versionada.

### D3 — Função pura `classificacao/pontuar`
Entrada: sinais vitais, gestante, idade, lista de pontos dos sintomas distintos, lista de faixas e parâmetros. Saída: pontos por sinal vital, `escore_sintomas`, `escore_sinais`, `escore_total`, `item_critico`, `prioridade_calculada` (ou `null`), `condicao_prioritaria`, `pendencias` (ex.: `SPO2_NAO_INFORMADA`, `TABELA_ADULTA_NAO_APLICAVEL`, `FAIXA_NAO_CONFIGURADA:FC`, `SEM_SINTOMA_OU_OBSERVACAO`). Não acessa o banco, então os casos da §5.4, §14.3 item 4 e §21.4 viram blocos `test` na própria função.
- *Alternativa:* calcular no Reflex. Descartada: regra clínica fica no Xano (AGENTS.md).

### D4 — Função `classificacao/avaliar_ficha`
Lê ficha, paciente, sintomas, faixas e parâmetros, calcula a idade na data de chegada (fuso `America/Sao_Paulo`) e chama `pontuar`. Usada pelo GET (só leitura) e pelo PATCH (que grava `escore_risco`, `parametro_critico`, `classificacao_risco` — BAIXO/MODERADO/ALTO espelhando Azul/Amarela/Vermelha, coluna já existente —, `prioridade_calculada`, `prioridade_atual = prioridade_calculada`, `justificativa_ajuste = null` e `condicao_prioritaria`).

### D5 — `PATCH /fichas/{id}` com `sinais_vitais` como conjunto final
Novo input opcional `json sinais_vitais` (mesmo padrão `"__OMITTED__"`) com `pa_sistolica`, `fc`, `fr`, `temperatura`, `spo2`, `glicemia`, `glicemia_sinais_gravidade` e `gestante`; o objeto enviado substitui todos esses campos (ausente ou vazio = não medido). Valida limites de digitação e uma casa decimal na temperatura antes de gravar. A RN04 continua validada como hoje. Toda alteração exige ficha `EM_TRIAGEM`, roda o recálculo (D4, descartando o ajuste) e chama `registrar_alteracao` na mesma transação, com evento `SINTOMAS_ALTERADOS` quando mudam sintomas ou observação e `SINAIS_VITAIS_ALTERADOS` quando mudam só sinais vitais ou gestação; `valor_anterior` inclui a prioridade atual anterior.
- *Alternativa:* endpoint separado para sinais vitais. Descartada: dois salvamentos para uma mesma tela e dois pontos de recálculo.

### D6 — Ajuste manual em `POST /fichas/{ficha_id}/prioridade`
Input: `prioridade` (VERMELHA, AMARELA, AZUL) e `justificativa`. Exige Recepção/Triagem, ficha `EM_TRIAGEM`, justificativa com texto após `trim` e, quando há prioridade calculada, prioridade diferente dela. Grava `prioridade_atual` e `justificativa_ajuste` e registra `PRIORIDADE_ALTERADA` com justificativa, na mesma transação.

### D7 — Autenticação nos endpoints da ficha
`GET /fichas/{id}`, `PATCH /fichas/{id}`, `POST /fichas/{id}/prioridade` e `GET /sintomas` recebem `auth = "usuario"` e `verificar_acesso` com `RECEPCAO_TRIAGEM`. No Reflex, `FichaState` passa a usar `api.requisitar(..., token=auth.token)` como a fila, e o 401 encerra a sessão local.

### D8 — Tela da ficha no padrão da tela 4 do Figma
Coluna esquerda: ticket (quando houver), status, nome, idade e condição prioritária. Cartão principal: seis campos de sinais vitais com a glicemia opcional e o indicador de gravidade, sintomas e observação (componentes atuais; quando a pesquisa não encontra nada, aparece "Adicionar '<texto>' como sintoma não listado" com a escolha da gravidade 1 leve, 2 moderado ou 3 grave, e o sintoma digitado aparece na lista marcado como "não listado" com a pontuação e opção de remover), linha "Classificação — escore total N (sintomas X · sinais vitais Y)", três cartões Vermelha/Amarela/Azul com a prioridade atual em destaque e a calculada indicada, pendências quando o cálculo estiver bloqueado, "Gestante" e o botão "Ajustar prioridade (justificativa obrigatória)", que abre um diálogo com a cor e a justificativa. Um único "Salvar" envia sintomas, observação e sinais vitais e recarrega o resultado do Xano. "Confirmar e gerar senha", especialidade e "Cancelar ficha" não aparecem (fora do escopo).

### D9 — Sintoma digitado em tabela própria
Nova tabela `ficha_sintoma_livre` (`ficha_id`, `descricao`, `pontuacao` 1–3, `criado_por`, `created_at`), com índice por `ficha_id`. O `PATCH /fichas/{id}` ganha o input opcional `json sintomas_livres` (padrão `"__OMITTED__"`), lista final de `{descricao, pontuacao}`: o Xano valida tamanho, pontuação, limite de 10 e duplicidade (normalizando com `trim`, minúsculas e sem acentos, contra a própria lista e contra `sintoma.nome`), apaga os anteriores da ficha e insere os novos na mesma transação. A RN04 considera sintomas do catálogo + digitados + observação. `avaliar_ficha` soma os digitados; a auditoria usa `SINTOMAS_ALTERADOS` com as listas anterior e nova.
- *Alternativa:* reaproveitar `ficha_sintoma` com `sintoma_id` anulável e descrição livre. Descartada: o índice único `(ficha_id, sintoma_id)` e o `join` com `sintoma` usados hoje deixariam de valer para essas linhas.
- *Alternativa:* criar o sintoma no catálogo como inativo. Descartada: o PO decidiu que vale só para a ficha, e o catálogo ganharia lixo de digitação.

## Risks / Trade-offs

- [Faixas copiadas de referência adulta externa] → Usadas só como pontuação acadêmica, conforme a Rev. 2.1; a tela e os documentos não chamam o escore de NEWS2 nem de protocolo clínico.
- [Divergência da tabela `ficha_atendimento`] → A change não publica essa tabela; só usa colunas já existentes no servidor.
- [Proteger o GET/PATCH quebra chamadas sem token] → Só a própria tela da ficha usa esses endpoints; ela passa a enviar o token na mesma entrega.
- [Sintoma digitado sem especialidade] → Não afeta a cor; o direcionamento (outra change) precisa decidir o destino quando só houver sintomas digitados.
- [Gravidade escolhida pela Recepção] → É uma escolha humana registrada na auditoria, como o ajuste manual.
- [Limites de digitação não aprovados formalmente] → Ficam registrados como pergunta em aberto no proposal e podem ser ajustados antes do apply.

## Migration Plan

1. Publicar no Xano (`v1`), com `--dry-run` antes e push restrito: `table/faixa_sinal_vital.xs`, `table/ficha_sintoma_livre.xs`, as funções `classificacao/*` e os endpoints alterados e novo.
2. A carga das faixas e parâmetros acontece no primeiro salvamento de ficha.
3. Publicar o Reflex.
4. Reversão: republicar as versões anteriores dos endpoints (no Git); as faixas e parâmetros podem ficar nas tabelas sem efeito.

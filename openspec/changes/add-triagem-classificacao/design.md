# Design técnico

## Contexto

As tabelas `sintoma` e `parametro`, a função `registrar_alteracao`, o `paciente` e o ticket já existem (changes 2 e 3). Esta change cria a `ficha_atendimento`, que é a entidade central, e a regra mais sensível do projeto (classificação), que precisa de testes com valores-limite (AGENTS.md).

## Objetivos / Fora dos objetivos

**Objetivos:**
- Uma única função de classificação, sem efeitos colaterais, chamada em todo ponto que altera sintomas, sinais vitais ou gestação.
- Faixas de risco em dados, não em código (RNF09).
- Resultado da classificação visível para a Recepção/Triagem enquanto ela preenche a ficha.

**Fora dos objetivos:**
- Histórico de versões da tabela de faixas (a auditoria registra cada alteração, o que basta).

## Decisões

### D1. Tabelas e campos
- `ficha_atendimento`: `paciente_id`, `ticket_id`, `aberta_por`, `chegada_em`, `status` (baseline), `observacao`, `gestante`, sinais vitais, `escore_sintomas`, `escore_fisiologico`, `escore_total`, `parametro_critico`, `classificacao_risco`, `prioridade_calculada`, `prioridade_atual`, `justificativa_ajuste`, `condicao_prioritaria`; especialidade, senha e chamadas pertencem às changes seguintes.
- `ficha_sintoma`: `ficha_id`, `sintoma_id`, único por par.
- `faixa_sinal_vital`: `parametro` (enum), `minimo`, `maximo` (inclusivos, decimais), `pontos`, `condicao_gravidade` (nulo, verdadeiro ou falso; usado só na glicemia).
- Quando mais de um critério se aplica, `condicao_prioritaria` guarda um só, por precedência: GESTANTE > IDOSO > CRIANCA. Para a fila basta saber se há condição prioritária.

### D2. Função pura `classificar_ficha(sinais, sintomas, gestante, nascimento, chegada)`
Ela lê as faixas e os parâmetros e devolve escore, parâmetro crítico, classificação, prioridade calculada e condição prioritária. Não grava nada. Os endpoints de alteração da ficha a chamam e gravam o resultado junto com a alteração e a auditoria, na mesma transação.
- **Por quê:** os testes com valores-limite exercitam a regra por um endpoint de simulação (`POST triagem/simular-classificacao`, RECEPCAO_TRIAGEM e ADMINISTRADOR), sem criar fichas.
- **Alternativa:** calcular no Reflex para dar resposta imediata. Descartada porque regra de negócio fica no Xano (AGENTS.md).

### D3. Faixas com limites inclusivos e verificação de cobertura
Cada faixa tem `minimo` e `maximo` inclusivos, com precisão de 1 casa (temperatura) ou inteira (demais). Ao salvar as faixas de um parâmetro, o backend ordena por `minimo` e verifica se não há sobreposição e se, para cada valor de `condicao_gravidade`, as faixas cobrem de ponta a ponta a faixa plausível, sem lacuna no passo de precisão (ex.: 36,0 → 36,1). As faixas de um parâmetro são salvas sempre como lista completa.

### D4. Interpretação da glicemia
Usar exatamente a baseline: `<54 mg/dL` com sinais de gravidade = 3 pontos; `<54` sem sinais = 2; `54–59` com sinais = 2; `54–59` sem sinais = 1. Os valores permanecem configurados como faixas clínicas; não há pendência de decisão para esses quatro casos.

### D5. Ciclo da ficha nesta change
A ficha é aberta em EM_TRIAGEM e continua assim até o direcionamento (change 5), que a leva a AGUARDANDO. O endpoint `POST fichas/{id}/concluir-triagem` só valida a completude (queixa e sinais obrigatórios) e retorna a classificação. A transição para AGUARDANDO é acrescentada em `add-direcionamento-senha`.

### D6. Tela de triagem
`/recepcao/ficha/{id}`: cabeçalho com paciente e condição prioritária; seletor dos sintomas do catálogo em `docs/domain-model.md`, exibindo seus pontos; observação; sinais vitais; caixa "Classificação" com soma dos pontos dos sintomas e sinais vitais, risco, cor calculada e cor atual, atualizada a cada campo salvo; botão "Ajustar prioridade" com justificativa; botão "Cancelar ficha". Cor é resultado da classificação, nunca atributo do sintoma.

## Riscos / Compromissos

- [Tabela de faixas mal configurada gera classificação errada] → Validação de cobertura (D3), auditoria e testes de valores-limite com os valores iniciais.
- [Regra acadêmica confundida com protocolo clínico] → Aviso fixo na tela de triagem.
- [Descartar o ajuste manual quando os sintomas mudam pode surpreender o usuário] → A tela avisa antes de salvar ("Isso vai recalcular a prioridade e descartar o ajuste manual").

## Plano de migração

Tabelas novas, mais a carga das faixas iniciais (idempotente). Rollback: remover as tabelas e endpoints.

## Questões em aberto

- Nenhuma decisão pendente quanto à glicemia. Alterações futuras de limiares clínicos são administrativas e não mudam a composição do escore.

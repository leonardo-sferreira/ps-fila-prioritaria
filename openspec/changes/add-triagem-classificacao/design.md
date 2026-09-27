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
- `ficha_atendimento`: `paciente_id`, `ticket_id`, `aberta_por`, `chegada_em`, `status` (enum com os seis estados do domain-model), `observacao`, `gestante`, `pa_sistolica`, `fc`, `fr`, `temperatura`, `spo2`, `glicemia`, `glicemia_sinais_gravidade`, `escore_risco`, `parametro_critico` (bool), `classificacao_risco`, `prioridade_calculada`, `prioridade_atual`, `justificativa_ajuste`, `condicao_prioritaria` (enum `NENHUMA|IDOSO|CRIANCA|GESTANTE`), mais os campos que as changes 5 e 6 vão acrescentar (especialidade, senha, tentativas).
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
O contexto do PO (seção 9.2) só define "< 54 com alteração de consciência" e "54–59 sintomática". Para os casos sem sinais de gravidade, esta change adota uma pontuação um nível abaixo (< 54 sem sinais → 2; 54–59 sem sinais → 1). Isso fica em dados (`condicao_gravidade`) e pode ser ajustado pelo Administrador sem mudar código.

### D5. Ciclo da ficha nesta change
A ficha é aberta em EM_TRIAGEM e continua assim até o direcionamento (change 5), que a leva a AGUARDANDO. O endpoint `POST fichas/{id}/concluir-triagem` só valida a completude (queixa e sinais obrigatórios) e retorna a classificação. A transição para AGUARDANDO é acrescentada em `add-direcionamento-senha`.

### D6. Tela de triagem
`/recepcao/ficha/{id}`: cabeçalho com o paciente (nome, idade, condição prioritária); seletor de sintomas por grupo; observação; sinais vitais; caixa "Classificação" com escore, risco, cor calculada e cor atual, atualizada a cada campo salvo (debounce de 500 ms); botão "Ajustar prioridade", com modal de justificativa; botão "Cancelar ficha". As cores seguem uma paleta única (RNF10) definida num módulo `cores.py`.

## Riscos / Compromissos

- [Tabela de faixas mal configurada gera classificação errada] → Validação de cobertura (D3), auditoria e testes de valores-limite com os valores iniciais.
- [Regra acadêmica confundida com protocolo clínico] → Aviso fixo na tela de triagem.
- [Descartar o ajuste manual quando os sintomas mudam pode surpreender o usuário] → A tela avisa antes de salvar ("Isso vai recalcular a prioridade e descartar o ajuste manual").

## Plano de migração

Tabelas novas, mais a carga das faixas iniciais (idempotente). Rollback: remover as tabelas e endpoints.

## Questões em aberto

- O PO deve confirmar a interpretação da glicemia sem sinais de gravidade (D4); mudar isso só altera dados.

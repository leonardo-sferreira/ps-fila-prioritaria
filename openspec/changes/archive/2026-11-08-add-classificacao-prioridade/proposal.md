# Proposta: classificação de prioridade da ficha

| Campo | Valor |
|---|---|
| Change | `add-classificacao-prioridade` |
| Sprint / card Trello | Sprint 3 (entrega seg 09/11/2026); card #35 "Classificação de prioridade — escore, sinais vitais e ajuste manual" |
| Depende de | `add-triagem-classificacao` (arquivada: ficha, sintomas pontuados, observação); autenticação e auditoria já publicadas (`verificar_acesso`, `registrar_alteracao`) |
| Situação | Proposta (PO assumiu o card em 08/11/2026) |
| Rastreabilidade formal | Documentação de Requisitos Rev. 2.1: RF08, RF09, RF10 e RF12 (§12); §5.2 a §5.4; §14.3 item 4; §17 (limiares 3/6); §19 D06, D07 e D08; §21.1 a §21.5 |

## Why

A ficha já registra sintomas pontuados e observação, mas não calcula a cor. Sem a classificação, a Recepção/Triagem não consegue dizer se o paciente é Vermelho, Amarelo ou Azul, e as próximas etapas (direcionamento, senha e fila do Médico) ficam bloqueadas. A Rev. 2.1 aprovou a escala e as faixas que faltavam (D06–D08, §21), o que destrava a implementação.

## What Changes

- **Sinais vitais e gestação na ficha:** PA sistólica, FC, FR, temperatura, SpO₂ (obrigatórios para o cálculo automático), glicemia (opcional) com indicador de sinais de gravidade, e "gestante". Valores fora do possível ou da precisão prevista são recusados.
- **Sintoma digitado na ficha** (decisão do PO em 08/11/2026): além de pesquisar e selecionar sintomas do catálogo, a Recepção/Triagem pode digitar um sintoma que não está na lista e escolher a gravidade (1, 2 ou 3 pontos). Vale só para aquela ficha, sem cadastro do ADM; entra no escore como os demais (3 pontos → Vermelha pela exceção), conta para a RN04, recalcula a cor, descarta o ajuste e fica na auditoria.
- **Escore:** soma dos pontos de cada sintoma distinto, do catálogo ou digitado (1–3) + pontos de cada sinal vital (0–3) pelas faixas da Rev. 2.1 (§21.2 e §21.3).
- **Cor calculada:** Azul 0–4, Amarela 5–9, Vermelha 10 ou mais; qualquer item com 3 pontos (sintoma ou sinal vital) gera Vermelha. Limiares configuráveis.
- **Sem cálculo automático quando faltar dado ou a tabela adulta não se aplicar:** sinal vital obrigatório ausente, paciente com menos de 16 anos ou gestante. A tela mostra o motivo e exige classificação manual justificada.
- **Condição prioritária** (idoso ≥60, criança ≤11, gestante) registrada pela data de nascimento e pela marcação de gestação; não soma pontos nem muda a cor.
- **Ajuste manual da prioridade:** a Recepção/Triagem escolhe outra cor com justificativa obrigatória; fica na auditoria (`PRIORIDADE_ALTERADA`).
- **Recálculo:** qualquer mudança de sintomas ou sinais vitais recalcula a cor e **descarta o ajuste manual** (decisão do PO em 08/11/2026); a Recepção ajusta de novo se precisar.
- **Faixas e parâmetros carregados no Xano** (tabela `faixa_sinal_vital` e tabela `parametro`), com limites abertos representados sem teto arbitrário.
- **Acesso protegido à ficha:** `GET /fichas/{id}`, `PATCH /fichas/{id}` e `GET /sintomas` passam a exigir sessão da Recepção/Triagem (hoje estão abertos); alterações clínicas geram auditoria.
- **Tela da ficha** no padrão da tela 4 do Figma: sinais vitais, gestação, escore detalhado, três cartões de cor com a atual em destaque e "Ajustar prioridade (justificativa obrigatória)".
- **Documentos:** `docs/domain-model.md` e `docs/project-overview.md` trocam os limiares antigos 3/6 pela escala 0–4 / 5–9 / ≥10 e registram as faixas e a elegibilidade da tabela adulta.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `classificacao-prioridade`: os requisitos marcados como "futuros" (composição do escore, sinais vitais, glicemia, faixas pendentes, conflito 3/6, condição prioritária, prioridades calculada/atual, configuração) são substituídos pelas regras aprovadas na Rev. 2.1 e pela decisão de recálculo.
- `ficha-atendimento`: a ficha passa a registrar sinais vitais e gestação, a consulta devolve os dados de classificação e o acesso passa a exigir sessão autorizada com auditoria; saem os requisitos de "etapa posterior" e "integrações futuras".

## Impact

- **Xano:** `table/faixa_sinal_vital.xs` (limites abertos); nova tabela `ficha_sintoma_livre` (sintomas digitados); nova função de carga dos parâmetros e faixas; novas funções de pontuação e de classificação da ficha; `api/triagem/fichas_id_get.xs`, `fichas_id_patch.xs` e `sintomas_get.xs` (autenticação, sinais vitais, recálculo e auditoria); novo endpoint `POST fichas/{ficha_id}/prioridade`. A tabela `ficha_atendimento` **não muda**: o servidor já tem todas as colunas usadas (e ela está na lista de tabelas divergentes, que não deve ser republicada sem decisão).
- **Reflex:** `FichaState` e a página `/recepcao/ficha/{id}`; chamadas da ficha passam a enviar o token da sessão.
- **Testes:** testes unitários no Xano para a pontuação (bordas da §21.4, limites 4/5 e 9/10, glicemia, item de 3 pontos, inelegíveis, dado ausente) e testes de estado no Reflex.
- **Documentos:** `docs/domain-model.md`, `docs/project-overview.md`.

## Fora do escopo

- Confirmar a classificação, direcionar à especialidade e gerar a senha ("Confirmar e gerar senha" do Figma): change `add-direcionamento-senha`. A ficha continua `EM_TRIAGEM` nesta change.
- Recalcular fichas já `AGUARDANDO` ou mudar de especialidade (RF12 na parte de destino): `add-direcionamento-senha`.
- Tela do Administrador para editar faixas e limiares: os valores ficam configuráveis nas tabelas do Xano.
- Faixas pediátricas, obstétricas ou com oxigenoterapia: não existem tabelas aprovadas (§21.1); esses casos usam classificação manual.
- Cancelamento da ficha (botão "Cancelar ficha" do Figma).
- Reordenação da fila do Médico pela condição prioritária: `add-fila-chamada-medico`.
- Reconciliação da tabela divergente `ficha_atendimento` (card do Backlog).
- Incluir no catálogo oficial um sintoma digitado: decisão futura do Administrador. O sintoma digitado não tem especialidade ligada; a change `add-direcionamento-senha` precisa considerar isso no destino.

## Perguntas em aberto

- Limites de valores "impossíveis" não estão na Rev. 2.1. Proposta (apenas validação de digitação, sem pontuação): PA sistólica 40–300 mmHg, FC 20–250 bpm, FR 4–80 irpm, temperatura 25,0–45,0 °C com uma casa decimal, SpO₂ 50–100 %, glicemia 10–1500 mg/dL. O PO pode ajustar antes do apply.
- Precedência quando há mais de uma condição prioritária (ex.: gestante com 60 anos): proposta GESTANTE, depois IDOSO, depois CRIANÇA. Só afeta o registro; a ordenação na fila do Médico é decidida na change dele.
- A Rev. 2.1 marca o caso "Dor no peito 2 + palpitações 2 = 4 → Azul" como "requer revisão didática". A change segue a escala aprovada (Azul) e mantém o alerta.

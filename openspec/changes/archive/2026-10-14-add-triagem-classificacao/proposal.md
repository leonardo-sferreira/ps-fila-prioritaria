# Proposta: Ficha de atendimento e classificação de prioridade

| Campo | Valor |
|---|---|
| Change | `add-triagem-classificacao` |
| Sprint e entrega | Sprint 2, segunda 12/10 |
| Fatias no Trello | Fatia 3 — Ficha e sintomas · Fatia 4 — Prioridade (etapa posterior) |
| Dupla | Fatia 3: Luisa · Nicolas. Fatia 4: Leonardo Machado · Nicolas |
| Depende de | `add-identificacao-paciente-triagem` (paciente) e catálogo de sintomas; autenticação e auditoria são integrações futuras |
| Situação | Em revisão — fatia atual refinada |
| RFs e RNs desta fatia | RF06, RF07, RN03 e RN04 |

> Esquema físico: `ficha_atendimento`, `ficha_sintoma` e `sintoma` já existem no Xano. Esta change os adequa e expõe as APIs necessárias; não recria as tabelas do zero.

## Why

Após identificar o paciente, a Recepção/Triagem precisa registrar a visita em uma ficha, com sintomas e queixa geral editáveis. A classificação clínica permanece nesta change, mas é uma etapa posterior: a primeira entrega verificável deve funcionar sem antecipar sinais vitais, prioridade, fila ou direcionamento.

## What Changes

### Fatia atual — ficha, sintomas e observação

- **Abertura de ficha:** criar uma ficha para paciente identificado em `EM_TRIAGEM`; o backend define `chegada_em`; `ticket_id` é opcional e não cria dependência de Totem (RF06, RN03).
- **Visitas e histórico:** cada nova chegada cria ficha nova, preservando fichas anteriores; o backend impede transacionalmente mais de uma ficha não finalizada por paciente.
- **Sintomas e queixa geral:** consultar sintomas ativos, associar vários sintomas sem repetição e editar a observação geral em `ficha_atendimento.observacao` (RF07).
- **Preenchimento válido:** no salvamento, a ficha deve conter pelo menos um sintoma ou uma observação/queixa não vazia após normalização (RN04). A criação inicial pode permanecer vazia em `EM_TRIAGEM` enquanto é preenchida.
- **Edição:** `PATCH` recebe a coleção final de `sintoma_ids`; IDs ausentes são removidos e IDs novos são associados de forma atômica. `ficha_sintoma.observacao` não é exposta nem recebida nesta fatia.
- **Catálogo:** nesta fatia, `Sintoma` passa a possuir `pontuacao` inteira de 1 a 3, sem cor/prioridade fixa, e ganha o grupo `TRAUMATICO_NEUROLOGICO`. A carga idempotente do catálogo acadêmico existente é executada agora; nova execução não duplica registros e `GET /sintomas` retorna dados utilizáveis pela tela. Não inventar sintomas, descrições ou pontuações; `docs/domain-model.md` é somente a fonte existente do catálogo e não será alterado.
- **APIs e Reflex:** `POST /fichas`, `GET /fichas/{id}`, `PATCH /fichas/{id}` e `GET /sintomas`; `Continuar` abre a ficha e a tela `/recepcao/ficha/{id}` usa um `FichaState` separado do estado de Paciente.
- **Testes:** cobrir RF06, RF07, RN03 e RN04, incluindo abertura, histórico, sintomas múltiplos, observação, edição e vínculo ao paciente correto.

### Etapas posteriores desta mesma change

- Sinais vitais, gestação, glicemia, escore fisiológico, soma para escore total, classificação, prioridade calculada/atual, ajuste manual, simulação e tela de risco.
- As faixas numéricas que convertem `escore_total` em Azul, Amarela ou Vermelha permanecem pendentes e devem ser aprovadas antes da implementação da classificação. Esta change não adota automaticamente os limiares 3/6 ainda presentes em `docs/domain-model.md`.

### Dependências deferidas

- `aberta_por` torna-se temporariamente anulável nesta fatia: não haverá usuário, token ou autenticação simulados. Após `add-autenticacao-perfis`, o endpoint deve usar o usuário autenticado e a obrigatoriedade do campo deve ser reavaliada.
- Autorização e auditoria via `add-autenticacao-perfis` e `add-base-compartilhada` permanecem dependências futuras, sem stubs nesta Sprint.

### Fora do escopo da fatia atual

- Sinais vitais, classificação, prioridade, ajustes, especialidade, direcionamento, senha, fila, médico, chamadas, cancelamento, autenticação e auditoria.
- Transição de `EM_TRIAGEM` para `AGUARDANDO`; `AGUARDANDO` pertence à etapa posterior de triagem/classificação/direcionamento.

## Capacidades

### Novas capacidades
- `ficha-atendimento`: abertura, sintomas, observação geral e edição da ficha; preserva as etapas futuras de sinais vitais, cancelamento e demais dados clínicos.
- `classificacao-prioridade`: classificação, prioridade, fatores clínicos e ajustes, executados somente em fase posterior desta change após definição das faixas de escore.

### Capacidades modificadas
_Nenhuma._

## Impacto

- **Xano:** adequar `ficha_atendimento` (`aberta_por` anulável), `sintoma` (`pontuacao` 1–3 sem `prioridade_padrao` e novo grupo) e usar `ficha_sintoma`; expor APIs de ficha e sintomas. A tabela `sintoma` está vazia, sem migração de registros existentes.
- **Reflex:** conectar `Continuar` à criação de ficha e criar `/recepcao/ficha/{id}` com `FichaState`, catálogo, seleção, observação e edição.
- **Testes:** testes de API e Reflex para RF06, RF07, RN03 e RN04; classificação não é critério de aceite desta Sprint.
- **Documentação:** há conflito conhecido entre os limiares 3/6 em `docs/domain-model.md` e a decisão atual de faixas pendentes. Esta proposta registra o conflito sem alterar o documento-base; ele precisa ser resolvido antes da fase futura de classificação.

## Perguntas em aberto

- [ ] Definir e aprovar as faixas de `escore_total` para Azul, Amarela e Vermelha antes da implementação da classificação. · PENDENTE PO
- [ ] Após `add-autenticacao-perfis`, reavaliar o preenchimento pelo backend e a obrigatoriedade de `aberta_por`. · DEPENDÊNCIA FUTURA

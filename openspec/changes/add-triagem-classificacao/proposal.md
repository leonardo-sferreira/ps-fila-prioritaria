# Proposta: Ficha de atendimento e classificação de prioridade

| Campo | Valor |
|---|---|
| Change | `add-triagem-classificacao` |
| Sprint e entrega | Sprint 2, segunda 12/10 |
| Fatias no Trello | Fatia 3 — Ficha e sintomas · Fatia 4 — Prioridade |
| Dupla | Fatia 3: Luisa · Nicolas. Fatia 4: Leonardo Machado · Nicolas |
| Depende de | `add-pacientes-pre-triagem` (paciente) e `add-base-compartilhada` (`sintoma` com dados, `parametro` e `registrar_alteracao`, Sprint 1) |
| Situação | Em revisão |
| RFs novos ou esclarecidos (Confluence, 04/10/2026) | RF08 e RF42 (sinais vitais e fator de risco); RF43 (cancelar ficha) |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/`. Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

A triagem é o coração do sistema: é nela que a Recepção/Triagem registra sintomas e sinais vitais e que o sistema decide a cor de prioridade. O PO validou em 27/09/2026 um modelo de fator de risco (NEWS2/MEWS + glicemia) que complementa a prioridade por sintoma. Esta change entrega a ficha de atendimento e a classificação, que o direcionamento e a fila vão consumir.

## What Changes

- **Ficha de atendimento:** aberta pela Recepção/Triagem para um paciente identificado, com horário de chegada, status inicial EM_TRIAGEM e no máximo uma ficha não finalizada por paciente (RF06, RN03, RN30, UC02).
- **Sintomas e observações:** seleção de um ou mais sintomas ativos e observação livre; exige ao menos um sintoma ou uma observação de queixa (RF07, RN04). Sintomas podem ser alterados depois (RF11).
- **Sinais vitais:** PA sistólica, FC, FR, temperatura, SpO2 e glicemia capilar (com indicador de sinais de gravidade), com validação de faixas plausíveis.
- **Fator de risco:** escore de 0 a 18 pela tabela de pontuação configurável, regra do parâmetro isolado com 3 pontos e classificação baixo/moderado/alto (contexto do PO, seção 9).
- **Prioridade calculada:** a pior entre a cor do sintoma mais grave (RN05, RN07, CA02) e a cor sugerida pelo risco; o risco só agrava.
- **Condição prioritária:** idoso e criança pela idade (limites configurados), gestante registrada na ficha (RF09, RN10, RN11).
- **Ajuste manual** da prioridade pela Recepção/Triagem, com justificativa obrigatória e auditoria (RF10, RN08, RN09).
- **Recálculo** quando sintomas ou sinais vitais mudam (RF12), com auditoria.
- **Cancelamento** de ficha com justificativa (estado CANCELADO da seção 18).
- **Configuração do risco:** o Administrador consulta e edita a tabela de pontuação e os limiares.

### Fora do escopo

- Escolha da especialidade, senha e comprovante: `add-direcionamento-senha`. Nesta change a ficha termina a triagem classificada, ainda em EM_TRIAGEM.
- Reposicionamento na fila e no painel após ajuste: acontece a partir de `add-fila-chamada-medico`, que lê a prioridade atual.
- Qualquer valor clínico real: o modelo de risco é acadêmico.

## Capacidades

### Novas capacidades
- `ficha-atendimento`: abertura, sintomas, observações, sinais vitais, gestação e cancelamento da ficha.
- `classificacao-prioridade`: fator de risco, prioridade calculada, condição prioritária, ajuste manual e configuração do risco.

### Capacidades modificadas
_Nenhuma._

## Impacto

- **Xano:** tabelas `ficha_atendimento`, `ficha_sintoma` e `faixa_sinal_vital`; novos parâmetros `limiar_risco_moderado` e `limiar_risco_alto`; função `classificar_ficha` (pura, testável); endpoints de ficha (RECEPCAO_TRIAGEM; leitura para ADMINISTRADOR) e de configuração do risco (ADMINISTRADOR).
- **Reflex:** tela de triagem em `/recepcao/ficha/{id}`, com a classificação atualizada a cada alteração; `/admin/risco`.
- **Testes:** `tests/api/test_classificacao.py`, com os valores-limite de cada faixa, e `tests/api/test_ficha.py`.
- **Depende de:** `add-cadastros-administrador` (sintomas, parâmetros, auditoria) e `add-pacientes-pre-triagem` (paciente, ticket).
- **Divergência com o documento formal:** o documento v1.0 calcula a prioridade só pelos sintomas (RF08). O fator de risco foi validado pelo PO em 27/09/2026 e ainda precisa ser formalizado no Confluence.

## Perguntas em aberto

- [x] Sintomas, parâmetros e auditoria na base da Sprint 1: decidido pelo PO em 04/10/2026 (`add-base-compartilhada`). · DECIDIDO PO
- [ ] Confirmar a interpretação da glicemia sem sinais de gravidade (design, D4). · PENDENTE PO

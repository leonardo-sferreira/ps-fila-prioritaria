# Proposta: Direcionamento por especialidade, senha e comprovante

| Campo | Valor |
|---|---|
| Change | `add-direcionamento-senha` |
| Sprint e entrega | Sprint 3, segunda 19/10 |
| Fatias no Trello | Fatia 6 — Direcionamento e senha |
| Dupla | Luisa (API e dados) · Nicolas (tela) |
| Depende de | `add-cadastros-administrador` (Fatia 5) e `add-triagem-classificacao` (Fatias 3 e 4) |
| Situação | Em revisão |
| Rastreabilidade formal | RF17–RF21 e RF47–RF48 quando aplicáveis; baseline local define que destino clínico não depende da especialidade cadastral do médico |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/`. Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

Depois de classificada, a ficha precisa entrar automaticamente na fila da especialidade mais adequada ao conjunto de sintomas. O destino não muda pela especialidade cadastral do Médico nem por indisponibilidade pontual; a distribuição para Médico elegível é regra operacional separada. O paciente sai da triagem com senha impressa sem dados pessoais.

## What Changes

- **Especialidade da ficha:** definida automaticamente pelo conjunto de sintomas e pela relação de direcionamento oficial; a regra de combinação/desempate de destinos diversos deve ser especificada nesta change antes da implementação. Para crianças dentro do limite configurado, o destino é Pediatria, sem substituir a classificação clínica.
- **Distribuição:** não usar especialidade de referência do Médico como filtro. A distribuição para Médicos elegíveis pertence a `add-fila-chamada-medico`; falta especificar a política entre filas distintas quando houver mais de um destino elegível, sem inventar balanceamento nesta etapa.
- **Ausência de Médico elegível:** não trocar o destino clínico para uma especialidade alternativa. A ficha permanece na fila correta até a regra operacional distribuir a um Médico elegível.
- **Confirmação da triagem:** direciona, gera a senha e leva a ficha a AGUARDANDO (RN19, UC04, UC05).
- **Senha** no formato `COR-ESP-NNN` (V = Vermelha, A = Amarela, B = Azul), com numeração diária por especialidade (RF20, seção 11.1).
- **Comprovante** para impressora térmica com senha, prioridade, especialidade, data/hora de entrada e aviso das três chamadas, sem nome nem CPF; a reimpressão não cria nova entrada (RF21, seção 11.2, seção 20).
- **Redirecionamento:** quando sintomas, prioridade ou disponibilidade mudam com a ficha AGUARDANDO, o direcionamento e a senha são refeitos, preservando o horário de chegada e registrando origem e destino (seção 20).

### Fora do escopo

- Ordenação da fila e chamada: `add-fila-chamada-medico`.
- Exibição da senha no painel: `add-painel-publico`.
- Distribuição/atribuição a Médico elegível e ordenação entre filas distintas: `add-fila-chamada-medico`.
- Sala e exibição da sala na chamada pública: `add-cadastros-administrador` e `add-painel-publico`.

## Capacidades

### Novas capacidades
- `direcionamento`: escolha da especialidade clínica a partir dos sintomas, atribuição da senha e redirecionamento somente quando houver mudança clínica pertinente.
- `senha-comprovante`: geração da senha, comprovante e reimpressão.

### Capacidades modificadas
Altera o comportamento de `ficha-atendimento` e `classificacao-prioridade` (`add-triagem-classificacao`: confirmação leva a AGUARDANDO e redireciona), de `medicos-disponibilidade` (`add-cadastros-administrador`) e de `gestao-usuarios` (`add-autenticacao-perfis`). Declarar esses pontos como deltas `MODIFIED`.

Aviso: o `openspec/specs/` ainda está vazio. Os deltas `MODIFIED` só funcionam depois que a change anterior for arquivada (`/opsx:archive`); arquive as changes na ordem.

## Impacto

- **Xano:** campos `especialidade_sugerida_id`, `especialidade_atribuida_id`, `senha`, `senha_numero`, `sem_medico_no_direcionamento` em `ficha_atendimento`; tabela `contador_senha`; funções `direcionar_ficha` e `gerar_senha`; endpoints `POST fichas/{id}/confirmar-triagem`, `GET fichas/{id}/comprovante` e `POST admin/redirecionar`; os endpoints de alteração de ficha (change 4) e de disponibilidade (change 2) passam a chamar o redirecionamento.
- **Reflex:** etapa "Confirmar e gerar senha" na tela de triagem, aviso de fila sem médico, página de impressão `/recepcao/comprovante/{id}` e botão "Reimprimir".
- **Testes:** `tests/api/test_direcionamento.py` e `tests/api/test_senha.py`.
- **Depende de:** `add-cadastros-administrador` e `add-triagem-classificacao`.
- As referências RF/RN/CA são rótulos de rastreabilidade, não autorização para inventar texto formal ausente. A baseline local mantém a especialidade da ficha estável; disponibilidade médica não altera o destino.

## Perguntas em aberto

- [x] Sala é entidade própria; nunca representar especialidade como local. · BASELINE
- [ ] Definir o desempate quando vários sintomas selecionados indicarem destinos diferentes. · PENDENTE PO

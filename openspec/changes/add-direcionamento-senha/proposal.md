# Proposta: Direcionamento por especialidade, senha e comprovante

| Campo | Valor |
|---|---|
| Change | `add-direcionamento-senha` |
| Sprint e entrega | Sprint 3, segunda 19/10 |
| Fatias no Trello | Fatia 6 — Direcionamento e senha |
| Dupla | Luisa (API e dados) · Nicolas (tela) |
| Depende de | `add-cadastros-administrador` (Fatia 5) e `add-triagem-classificacao` (Fatias 3 e 4) |
| Situação | Em revisão |
| RFs novos ou esclarecidos (Confluence, 04/10/2026) | RF18 (fila por especialidade com médico disponível); RF47 (reimprimir senha); RF48 (redistribuir quando o médico fica indisponível) |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/`. Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

Depois de classificada, a ficha precisa entrar na fila certa: a da especialidade mais adequada aos sintomas que tenha médico disponível, com fallback para alternativas configuradas. O paciente precisa sair da triagem com uma senha impressa que identifique cor e fila sem expor seus dados. Sem isso a fila do médico (próxima change) não tem o que chamar.

## What Changes

- **Especialidade sugerida:** identificada automaticamente a partir dos sintomas mais graves da ficha e da ordem configurada em Sintoma_Especialidade; sem sintomas, vale a especialidade padrão (RF17, RN14).
- **Especialidade atribuída:** a sugerida, se tiver médico disponível agora; senão, a primeira alternativa configurada com médico disponível (RF18, RF19, RN15, RN17, CA04, CA05). A ficha guarda as duas (RN18).
- **Sem nenhuma fila disponível:** a Recepção/Triagem é avisada e pode confirmar a entrada na fila da especialidade sugerida, que aguarda um médico (tratamento operacional da seção 20 do documento formal).
- **Confirmação da triagem:** direciona, gera a senha e leva a ficha a AGUARDANDO (RN19, UC04, UC05).
- **Senha** no formato `COR-ESP-NNN` (V = Vermelha, A = Amarela, B = Azul), com numeração diária por especialidade (RF20, seção 11.1).
- **Comprovante** para impressora térmica com senha, prioridade, especialidade, data/hora de entrada e aviso das três chamadas, sem nome nem CPF; a reimpressão não cria nova entrada (RF21, seção 11.2, seção 20).
- **Redirecionamento:** quando sintomas, prioridade ou disponibilidade mudam com a ficha AGUARDANDO, o direcionamento e a senha são refeitos, preservando o horário de chegada e registrando origem e destino (seção 20).

### Fora do escopo

- Ordenação da fila e chamada: `add-fila-chamada-medico`.
- Exibição da senha no painel: `add-painel-publico`.
- Escolha de um médico específico: a fila é da especialidade (ver design.md, D1).
- Redirecionamento automático só porque o horário de disponibilidade terminou, sem ação do Administrador (ver design.md, Questões em aberto).

## Capacidades

### Novas capacidades
- `direcionamento`: escolha das especialidades sugerida e atribuída, fallback e redirecionamento.
- `senha-comprovante`: geração da senha, comprovante e reimpressão.

### Capacidades modificadas
Altera o comportamento de `ficha-atendimento` e `classificacao-prioridade` (`add-triagem-classificacao`: confirmação leva a AGUARDANDO e redireciona), de `medicos-disponibilidade` (`add-cadastros-administrador`) e de `gestao-usuarios` (`add-autenticacao-perfis`). Declarar esses pontos como deltas `MODIFIED`.

Aviso: o `openspec/specs/` ainda está vazio. Os deltas `MODIFIED` só funcionam depois que a change anterior for arquivada (`/opsx:archive`); arquive as changes na ordem.

## Impacto

- **Xano:** campos `especialidade_sugerida_id`, `especialidade_atribuida_id`, `senha`, `senha_numero`, `sem_medico_no_direcionamento` em `ficha_atendimento`; tabela `contador_senha`; funções `direcionar_ficha` e `gerar_senha`; endpoints `POST fichas/{id}/confirmar-triagem`, `GET fichas/{id}/comprovante` e `POST admin/redirecionar`; os endpoints de alteração de ficha (change 4) e de disponibilidade (change 2) passam a chamar o redirecionamento.
- **Reflex:** etapa "Confirmar e gerar senha" na tela de triagem, aviso de fila sem médico, página de impressão `/recepcao/comprovante/{id}` e botão "Reimprimir".
- **Testes:** `tests/api/test_direcionamento.py` e `tests/api/test_senha.py`.
- **Depende de:** `add-cadastros-administrador` e `add-triagem-classificacao`.
- **Divergência com o documento formal:** RF18 fala em "fila de um médico disponível"; este projeto adota fila por especialidade, atendida por qualquer médico disponível da especialidade (a senha já identifica a especialidade). Deve ser confirmado pelo PO.

## Perguntas em aberto

- [x] Fila por especialidade, atendida por médico disponível (RF18): decidido pelo PO em 04/10/2026. · DECIDIDO PO
- [ ] O card da Fatia 6 fala em "especialidade/sala", mas o projeto não modela sala (o painel mostra a especialidade). · PENDENTE PO
- [ ] Redirecionar sozinho quando acaba o horário de disponibilidade, ou só sob demanda (design, Questões em aberto)? · PENDENTE PO

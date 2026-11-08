# Proposta: Direcionamento por especialidade, senha e comprovante

| Campo | Valor |
|---|---|
| Change | `add-direcionamento-senha` |
| Sprint e entrega | Sprint 3 — entrega segunda 09/11/2026 |
| Card no Trello | #39 "Direcionamento por especialidade e senha de atendimento" (assumido pelo PO em 08/11/2026) |
| Depende de | `add-classificacao-prioridade` (ficha com cor calculada ou ajustada, sinais vitais e sintomas digitados) |
| Situação | Revisada em 08/11/2026 para a Rev. 2.1 e as decisões do PO |
| Rastreabilidade formal | Documentação de Requisitos Rev. 2.1: RF17, RF18, RF19 (supersedido), RF20, RF21 (§12); RF47 e RF48 (§23); §6 e §6.1; §9, 2º item; §14.2; §14.3, item 5; §17 ("fallback por falta de médico"); §19 D09 e D10 |

## Why

A ficha já é classificada, mas fica parada em `EM_TRIAGEM`: não há destino, senha nem comprovante, e a fila do Médico não tem o que chamar. A Rev. 2.1 decidiu o desempate entre especialidades (D09) e eliminou o fallback por falta de médico (D10, RF19 supersedido), o que destrava a implementação.

## What Changes

- **Destino pelos sintomas:** a especialidade da ficha vem dos sintomas do catálogo e da relação `sintoma_especialidade`. Desempate da §14.2: paciente com até 11 anos vai para Pediatria antes de qualquer cálculo; para os demais, 1º maior pontuação individual de sintoma ligado à especialidade, 2º maior soma dos pontos ligados a ela, 3º menor número de fichas `AGUARDANDO` na especialidade, 4º menor ID (regra transitória enquanto não existe estimativa de horário).
- **Sem sintoma do catálogo:** ficha só com sintomas digitados ou só com observação vai para a especialidade padrão, Clínica Geral, configurável (decisão do PO em 08/11/2026). Sintomas digitados continuam no escore, mas não influem no destino.
- **Sem fallback por falta de médico:** a disponibilidade e a especialidade de referência do Médico não mudam o destino.
- **"Confirmar e gerar senha":** exige ficha `EM_TRIAGEM` com cor definida (calculada ou ajustada manualmente, decisão do PO); define o destino, gera a senha e leva a ficha a `AGUARDANDO` numa única operação auditada. Sem cor, recusa e mostra as pendências.
- **Senha `COR-ESP-NNN`:** V (Vermelha), A (Amarela) ou B (Azul) + sigla da especialidade + número diário por especialidade em `America/Sao_Paulo`, compartilhado entre cores. Siglas: CAR (Cardiologia), CLI (Clínica Geral), NEU (Neurologia), ORT (Ortopedia) e PED (Pediatria).
- **Comprovante de 80 mm** com senha, cor por extenso, especialidade, data/hora de entrada e a regra de chamadas do Médico, sem nome, CPF, data de nascimento, sintomas ou sinais vitais; a reimpressão usa a mesma senha.
- **Carga inicial** idempotente das 5 especialidades, das ligações sintoma → especialidade do catálogo de `docs/domain-model.md` e do parâmetro `ESPECIALIDADE_PADRAO`.
- **Documentos:** `docs/domain-model.md` e `docs/project-overview.md` passam a registrar o desempate, as siglas e a especialidade padrão.

## Capabilities

### New Capabilities

- `direcionamento`: destino clínico da ficha pelos sintomas, com desempate, regra pediátrica, especialidade padrão e confirmação da triagem.
- `senha-comprovante`: geração da senha e comprovante com reimpressão.

### Modified Capabilities

Nenhuma.

## Impact

- **Xano:** função de carga das especialidades; função pura de destino com testes; função de senha; `POST fichas/{ficha_id}/confirmar-triagem`; `GET fichas/{ficha_id}/comprovante`; `GET fichas/{id}` passa a devolver o destino previsto, a senha e a especialidade. As colunas usadas (`especialidade_sugerida_id`, `especialidade_atribuida_id`, `senha`, `senha_numero`) e a tabela `contador_senha` já existem no servidor: **nenhuma tabela é alterada ou republicada** (`ficha_atendimento` e `contador_senha` estão entre as divergentes; o contador é sempre gravado com valor explícito).
- **Reflex:** prévia do destino e botão "Confirmar e gerar senha" na ficha; página `/recepcao/comprovante/{id}` em 80 mm com impressão; ficha `AGUARDANDO` em modo leitura com senha e "Reimprimir".
- **Testes:** testes unitários no Xano para o destino (Pediatria, desempates, especialidade padrão) e testes de estado no Reflex.

## Fora do escopo

- Refazer destino e senha de ficha já `AGUARDANDO` quando sintomas ou prioridade mudam (RF12, troca de senha e aviso de reimpressão), `POST admin/redirecionar` e "Reavaliar direcionamento": outra change. Hoje a ficha não pode ser editada depois de sair da triagem.
- Distribuição e chamada pelo Médico, ordem da fila médica: `add-fila-chamada-medico`.
- Painel público: `add-painel-publico`.
- Cadastro de especialidades e de ligações pelo Administrador: `add-cadastros-administrador` (aqui só a carga inicial).
- Estimativa de horário do último paciente (critério temporal adiado na Rev. 2.1).

## Perguntas em aberto

- A numeração simultânea usa a transação e o contador por especialidade/dia, mas a exclusividade em confirmações simultâneas não está comprovada (o Xano não tem atualização condicional e `contador_senha` não pode ser republicada antes da reconciliação). Mesma limitação aceita na fila de pré-triagem; a operação sequencial é suportada.

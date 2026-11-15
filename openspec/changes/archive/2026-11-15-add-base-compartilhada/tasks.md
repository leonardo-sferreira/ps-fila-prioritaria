# Tarefas

> Reescritas em 14/11/2026 conforme a "Revisão de 13/11/2026" do design.md (D3 a D6 substituídas). Vale o que está publicado na `v1`. Sem tela: esta change não tem tarefas de Reflex.

## 1. Auditoria (D1, D2)

- [x] 1.1 [Xano] Conferir `backend/xano/table/historico_alteracao.xs` com o D1 e verificar que não existe endpoint de escrita, edição ou exclusão nessa tabela
- [x] 1.2 [Xano] Função `registrar_alteracao` publicada e chamada dentro do `db.transaction` dos endpoints, com o usuário do token como responsável; validada em POST e PATCH de Pacientes (26/10/2026)
- [x] 1.3 [Xano] Provar o rollback (D2): falha forçada depois da auditoria não deixa nem a alteração nem o registro
  - Feito em 14/11/2026 na `v1`, com aval do Nicolas: a função temporária `teste_prova_rollback` gravou uma sala (id 2) e a auditoria dela (id 301) dentro de `db.transaction` e forçou erro em seguida; a conferência depois do erro encontrou 0 salas e 0 auditorias com o marcador `ROLLBACK_TESTE_1794693335`. A função foi removida do workspace logo após a prova.
- [x] 1.4 Testes em `tests/api/test_base_compartilhada.py` (`AuditoriaTest`): nenhum endpoint grava no histórico diretamente, só `registrar_alteracao` grava, a auditoria fica dentro da transação e o responsável vem da sessão; verificar que passam

## 2. Fuso (D3)

- [x] 2.1 [Xano] Fuso fixo `America/Sao_Paulo` no XanoScript, sem variável `FUSO_HORARIO` nem parâmetro editável
- [x] 2.2 Testes `test_fuso_nao_e_parametro` e `test_fuso_fixo_em_sao_paulo`; verificar que passam

## 3. Parâmetros (D4, D6)

- [x] 3.1 [Xano] Tabela `parametro` lida pela chave; tipo e limites em `cadastros/regra_parametro`, com as chaves publicadas
- [x] 3.2 [Xano] Valores iniciais da baseline inseridos por `inicializar_parametros_fila` (só o que falta, sem sobrescrever)
- [x] 3.3 [Xano] `GET parametros` autenticado (Administrador, `add-cadastros-administrador` D7)
- [x] 3.4 Testes `ParametrosTest` (valores da baseline e limites de `regra_parametro`) e `ConsultaSemTokenTest` (401 sem token e com token adulterado); verificar que passam

## 4. Dados de referência (D5)

- [x] 4.1 [Xano] Especialidades e relações iniciais inseridas por `classificacao/inicializar_classificacao` e `direcionamento/inicializar_direcionamento` (só o que falta); sintomas mantidos pelo Administrador
- [x] 4.2 [Xano] `GET especialidades` e `GET sintomas` conforme as specs `especialidades` e `sintomas`
- [x] 4.3 A carga automática (`inicializar_*`) grava auditoria · DECIDIDO PO (15/11/2026)
  - Cada `db.add` das três funções chama `registrar_alteracao` com `sistema: true` e evento `CARGA_INICIAL`; o registro fica sem usuário e a tela de auditoria mostra "Sistema". Testes `test_carga_automatica_audita_cada_insercao` e `test_endpoint_nunca_audita_como_sistema`.

## 5. Integração e documentação

- [x] 5.1 XanoScript das funções e endpoints exportado para `backend/xano/` e versionado
- [x] 5.2 Conferir `docs/domain-model.md` (Histórico_Alteração, Parâmetros, Especialidade e Sintoma) com o publicado

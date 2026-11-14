# Tarefas

> Revisadas em 13/11/2026 (ver design.md, "Revisão de 13/11/2026"). Sem tela e sem alteração no Xano.

## 1. Auditoria

- [x] 1.1 [Xano] Conferir `backend/xano/table/historico_alteracao.xs` com o D1 e verificar que não existe endpoint de escrita, edição ou exclusão nessa tabela
- [x] 1.2 [Xano] Função `registrar_alteracao` publicada e usada dentro do `db.transaction` (validada em Pacientes em 26/10/2026)
- [ ] 1.3 [Xano] Prova de rollback: falha induzida depois da auditoria não deixa registro (exige função temporária e aval do dono do workspace)
- [x] 1.4 `tests/api/test_base_compartilhada.py` (`AuditoriaTest`): só a função grava no histórico, toda chamada fica dentro da transação, responsável vem da sessão

## 2. Fuso

- [x] 2.1 Fuso fixo `America/Sao_Paulo` no XanoScript; teste falha se aparecer outro fuso ou a chave `FUSO_HORARIO` como parâmetro

## 3. Parâmetros e dados de referência

- [x] 3.1 [Xano] Valores iniciais criados sem sobrescrita pelas funções `inicializar_*`
- [x] 3.2 `tests/api/test_base_compartilhada.py` (`ParametrosTest`): valores da baseline (idoso 60, criança 11, ciclos 2:1, previsão 5, 30 s, 3 chamadas, 24 h) e cada valor inicial dentro dos limites de `regra_parametro`
- [x] 3.3 Integração: `GET parametros` sem token ou com token adulterado responde 401

## 4. Documentação

- [x] 4.1 Proposta, design e specs alinhados ao que está publicado
- [ ] 4.2 Decisão do PO sobre auditoria da carga automática (pergunta aberta na proposta)

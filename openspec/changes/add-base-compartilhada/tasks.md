# Tarefas

> Sem tela: esta change não tem tarefas de Reflex. As tabelas já existem; "conferir" significa comparar o `.xs` com o design, sem alterar o esquema.

## 1. Xano — auditoria e fuso (necessário para a Fatia 2)

- [x] 1.1 [Xano] Conferir `backend/xano/table/historico_alteracao.xs` com o D1 (campos e índices) e verificar no painel que não existe nenhum endpoint de escrita, edição ou exclusão nessa tabela
- [ ] 1.2 [Xano] Criar a função `registrar_alteracao` (D1) e verificar com Run & Debug que (a) uma chamada dentro de `db.transaction` grava o registro com o usuário do token e (b) um erro forçado depois da chamada não deixa registro (D2); se a transação não estiver disponível, registrar a limitação no design.md antes de seguir
- [ ] 1.3 [Xano] Criar a variável de ambiente `FUSO_HORARIO = America/Sao_Paulo` (D3) e verificar com Run & Debug que 02:59 UTC de 05/10 resulta no dia 04/10 no fuso do PS
- [ ] 1.4 Escrever `tests/api/test_auditoria.py` cobrindo operação válida auditada com todos os campos, operação recusada sem auditoria e ausência de operação de escrita, edição ou exclusão de auditoria pela API; verificar que passam

## 2. Xano — parâmetros (necessário para a Fatia 3)

- [ ] 2.1 [Xano] Conferir `backend/xano/table/parametro.xs` com o D4 e criar a função `obter_parametro`; verificar com Run & Debug a conversão de um INTEIRO, de uma ESPECIALIDADE e o erro explícito para chave inexistente
- [ ] 2.2 [Xano] Criar `GET parametros` (autenticado, três perfis, `verificar_acesso`) (D6); verificar com os testes 2.3
- [ ] 2.3 Escrever `tests/api/test_parametros.py` cobrindo os oito valores iniciais do D4 depois da carga, consulta pelos três perfis, 401 sem token e 401 para usuário desativado com token válido; verificar que passam

## 3. Xano — dados de referência (necessário para a Fatia 3)

- [ ] 3.1 [Xano] Conferir os `.xs` de `especialidade`, `especialidade_alternativa`, `sintoma` e `sintoma_especialidade` com o D5 e criar a função `carga_inicial` (insere só o que falta, relações só para registros inseridos na execução, auditoria `CADASTRO` em cada inserção); verificar com Run & Debug em ambiente vazio
- [ ] 3.2 [Xano] Criar `POST admin/carga-inicial` (ADMINISTRADOR) incluindo os parâmetros do D4; verificar com os testes 3.4
- [ ] 3.3 [Xano] Criar `GET especialidades` e `GET sintomas` (autenticados, só ativos, campos do D6); verificar com os testes 3.4
- [ ] 3.4 Escrever `tests/api/test_dados_referencia.py` cobrindo carga em ambiente vazio com o catálogo oficial ("Dor ou pressão no peito", grupo Cardiovascular, 2 pontos, Cardiologia), segunda execução sem duplicar, pontuação/relação alterada mantida após nova carga, 403 para Recepção/Triagem e Médico na carga, sintoma inativo fora da consulta e 401 sem token nas consultas; verificar que passam

## 4. Integração e documentação

- [ ] 4.1 Exportar o XanoScript das funções e endpoints para `backend/xano/` e verificar que os arquivos estão no repositório
- [ ] 4.2 Adicionar ao README o passo "executar a carga inicial com o primeiro Administrador" e verificar executando-o num workspace limpo
- [ ] 4.3 Conferir `docs/domain-model.md` (Histórico_Alteração, Parâmetros de regra, Especialidade e Sintoma) com o que foi implementado, incluindo as chaves `idade_minima_idoso` e `idade_maxima_crianca`, e ajustar o que divergir

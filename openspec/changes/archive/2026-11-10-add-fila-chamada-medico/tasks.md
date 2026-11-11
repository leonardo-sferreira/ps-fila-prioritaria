# Tarefas

## 1. Xano — ordem interna e previsão

- [x] 1.1 [Xano] Conferir `ciclo_fila.xs` publicado, usar parâmetros configuráveis na leitura/atualização por especialidade e testar Vermelha, cor alternativa e ciclo 1:2; conferir no código a reinicialização da posição após alteração do parâmetro
- [x] 1.2 [Xano] Implementar ou refatorar `proxima_ficha` e `prever_fila` e `GET filas/{especialidade}/previsao` usando a mesma regra de cor, condição, ordem efetiva e ID; verificar resposta apenas com senha/cor e sem reserva
- [x] 1.3 [Teste] Criar `tests/api/test_ordenacao.py` com Vermelha tardia, ciclo A-A-B, Vermelha intercalada, ausência de uma cor, idoso/criança/gestante dentro da cor, empate de chegada/ID, reentrada ao fim e exclusão de estados não AGUARDANDO; executar e registrar resultado
- [x] 1.4 [Teste] Cobrir previsão com 3 e 7 fichas, nova Vermelha, ciclo preservado e ausência de dados pessoais em `test_ordenacao.py`; executar e registrar resultado
- [x] 1.5 [Documentação] Conferir a ordem interna em `docs/project-overview.md` e `docs/domain-model.md` contra a implementação e registrar no README o comando dos testes de ordenação; verificar que texto e comando correspondem ao comportamento entregue

## 2. Xano — seleção entre filas

- [x] 2.1 [Xano] Reaproveitar `medico_especialidade` e a elegibilidade operacional para obter uma candidata por fila própria; implementar Vermelha própria por chegada/ID e rodízio por médico entre próprias A/B consultando a última especialidade própria chamada no histórico; verificar alternância e salto de fila vazia nos testes 2.4
- [x] 2.2 [Xano] Implementar cobertura de fila por médico próprio ativo com plantão, disponibilidade e sessão apta; PAUSA/AUSENTE retiram cobertura e EM_ATENDIMENTO a mantém; verificar os quatro estados nos testes 2.4
- [x] 2.3 [Xano] Comparar a melhor descoberta com a próxima própria apenas pela cor; em empate escolher própria; sem própria, selecionar descoberta e depois outra coberta por cor, condição, ordem efetiva e ID; verificar matriz §14.1 nos testes 2.4
- [x] 2.4 [Teste] Criar `tests/api/test_selecao_entre_filas.py` com todas as linhas da matriz §14.1, duas próprias com Vermelhas, rodízio A/B com ciclos independentes, fila vazia, PAUSA/AUSENTE/EM_ATENDIMENTO e desempates entre descobertas; executar e registrar resultado
- [x] 2.5 [Documentação] Conferir no README e nas duas bases de `docs/` a política de próprias/descobertas/cobertas implementada; verificar que nenhum texto ainda descreve especialidade única ou escolha manual

## 3. Xano — reserva e ciclo da chamada

- [x] 3.1 [Xano] Conferir o esquema publicado; refatorar `chamada.xs` para registrar oportunidade e ajustar a unicidade, e `ficha_atendimento.xs` para guardar oportunidade/ordem efetiva de reentrada, preservando dados existentes; verificar a migração com tentativa 1 nas duas oportunidades
- [x] 3.2 [Xano] Implementar `POST medico/chamar-proximo` com autorização de MEDICO, sessão apta, elegibilidade, uma ficha pendente, seleção de 1–2 e reserva, evento e ciclo na mesma transação; verificar concorrência de dois médicos com duas fichas e recusa do segundo clique
- [x] 3.3 [Xano] Refatorar `GET medico/filas` e as ações de repetição, comparecimento e desistência para oportunidade, intervalo e reentrada única; verificar que especialidade/senha permanecem e a ficha volta ao fim sem alterar `chegada_em`
- [x] 3.4 [Xano] Criar/refatorar `GET fichas/{id}/impressao` para o médico responsável, sem expor dados de outra ficha; verificar permissões nos testes 3.5
- [x] 3.5 [Teste] Executar `tests/api/test_chamada.py` com perfis negados, ID manual rejeitado, reservas simultâneas de duas fichas, pendência, intervalo, 3 tentativas, segunda oportunidade, comparecimento, desistência, histórico e impressão; encerrar os registros sintéticos após a execução
- [x] 3.6 [Documentação] Exportar o XanoScript efetivo de fila/chamada para `backend/xano/` e atualizar no README o contrato dos endpoints e o comando dos testes; verificar que os arquivos exportados e o servidor têm o mesmo esquema

## 4. Reflex — operação do médico

- [x] 4.1 [Reflex] Criar/refatorar `/medico` com filas e ficha sob responsabilidade, status/plantão, especialidade da ficha, botão "Chamar próximo" e aviso de fila vazia; verificar que não há escolha de fila/ficha nem dados pessoais antes da atribuição
- [x] 4.2 [Reflex] Ligar "Repetir chamada", "Compareceu" e "Registrar desistência" com mensagens de erro e confirmação; verificar por testes locais e integração da API o intervalo, as três tentativas e a reentrada
- [x] 4.3 [Reflex] Criar/refatorar `/medico/ficha/{id}/imprimir` para o médico autorizado; verificar por teste de estado, compilação e API os dados da ficha própria e a recusa para ficha alheia
- [x] 4.4 [Documentação] Registrar neste `tasks.md` o roteiro de aceite manual da tela médica para o PO executar após o apply, incluindo fila vazia, pausa, descoberta e duas chamadas simultâneas

## 5. Integração

- [x] 5.1 Verificar a política completa nas funções publicadas com dois médicos e três especialidades: Vermelha própria, rodízio A/B, descoberta mais grave, empate de cor favorável à própria e fallback coberto; conferir separadamente a reserva simultânea sem duplicidade
- [x] 5.2 Conferir contratos e estados do fluxo triagem → fila → chamada → reentrada/comparecimento/desistência nos testes de integração disponíveis e nas bases `docs/domain-model.md` e `docs/project-overview.md`

## Verificações desta aplicação

- 10/11/2026: `.venv/bin/python -m unittest discover -s tests/api -p test_ordenacao.py -v` — 11 testes passaram contra `fila/proxima_ficha` e `fila/prever_fila` publicados na `v1`.
- 10/11/2026: `.venv/bin/python -m unittest discover -s tests/api -p test_selecao_entre_filas.py -v` — 12 testes passaram na `v1`, incluindo matriz de cores, cobertura e rodízio entre próprias.
- 10/11/2026: `.venv/bin/python -m unittest discover -s tests/api -p test_chamada.py -v` — 1 teste de integração passou na `v1` (duas reservas simultâneas, pendência, intervalo, duas oportunidades, impressão e autorização cruzada). O encerramento automático desativou usuários, médicos, pacientes, sessões e disponibilidades fictícios; fichas finais e auditoria foram preservadas.
- 10/11/2026: `cd frontend && ../.venv/bin/python -m unittest discover -s tests -p test_medico_state.py -v` — 4 testes passaram; `../.venv/bin/reflex compile --dry` compilou. A rota `/medico` respondeu com redirecionamento para login sem sessão.
- 10/11/2026: nova exportação da `v1` comparada com 22 arquivos de fila/chamada em `backend/xano/`; conteúdo igual após normalização de espaços, nenhuma referência vazia nas tabelas.
- 10/11/2026: a integração de chamada passou novamente (69,3 s), comparando senha, especialidade e `chegada_em` antes e depois da reentrada; cenário sintético encerrado ao final.

- 10/11/2026: `test_chamada.py` passou com perfis Recepção/Triagem e Administrador recusados (403), reserva de duas fichas, intervalo, duas oportunidades, histórico e impressão; requisições espaçadas pelo limite do plano Free; fixtures encerradas ao final.
- 10/11/2026: testes novos do ciclo 1:2 e da política composta de duas próprias e terceira fila passaram nas funções publicadas; o endpoint de parâmetros publicado contém reinício da posição do ciclo e foi validado em XanoScript, sem alterar parâmetros ativos da `v1`.
- 10/11/2026: `test_medico_state.py` passou com 9 testes, incluindo confirmação de desistência, ação de comparecimento, erro de intervalo, impressão autorizada e recusa de ficha alheia; `reflex compile --dry` passou.
- 10/11/2026: `test_ficha_state.py` passou com 36 testes; a confirmação de triagem publicada gera senha, especialidade e `AGUARDANDO`, a seleção lê apenas `AGUARDANDO`, e a chamada preserva senha e chegada em reentrada. `docs/domain-model.md` e `docs/project-overview.md` foram conferidos.

## Aceite manual posterior pelo PO

O PO fará este aceite depois da conclusão do apply. O roteiro fica nesta change, sem instruções de teste da tela no README.

- Em `/medico`, conferir status e plantão, quantidades sem nome de pacientes aguardando, aviso de fila vazia e bloqueio de nova atribuição em PAUSA, AUSENTE ou plantão encerrado.
- Com dois médicos e três especialidades, conferir Vermelha própria, rodízio entre próprias, apoio à descoberta mais grave, empate de cor favorável à própria e fallback para outra coberta. Em dois navegadores, disputar uma única ficha e depois duas fichas; conferir ausência de duplicidade e de avanço indevido do ciclo.
- Na ficha atribuída, conferir o intervalo de 30 segundos, três tentativas por oportunidade, reentrada única com a mesma senha, comparecimento e desistência confirmada. Abrir a impressão de ficha própria e confirmar a recusa da ficha alheia.
- Alterar os parâmetros do ciclo em ambiente de teste ou janela sem fila ativa e conferir o reinício da posição. Fazer o fluxo completo de triagem até chamada e estado final, conferindo histórico e painel.

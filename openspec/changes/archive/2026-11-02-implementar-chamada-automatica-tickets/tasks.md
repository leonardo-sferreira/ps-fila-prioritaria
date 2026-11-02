# Tarefas

As tarefas independentes podem avançar; não disponibilizar operações sem autorização e auditoria efetivas.

A implementação de chamadas está publicada na v1. As evidências anteriores do ciclo 2:1, precedência pediátrica, desistência, autorização e regressões são aproveitadas; os detalhes não comprovados permanecem nas tarefas abertas. A operação sequencial, a sincronização a cada 10 segundos e a dependência da tela aberta foram aceitas pelo PO.

## 1. Dados e concorrência Xano

- [x] 1.1 Inventariar tickets e parâmetros, adequar dados da fila e confirmar persistência dos registros em recarga.
- [x] 1.2 Usar `db.transaction` com validação de estado, verificar operação sequencial e registrar a limitação de concorrência.
- [x] 1.3 Implementar seleção transacional, ciclo configurável, precedência pediátrica, auditoria e autorização; verificar o ciclo 2:1 e classes vazias.
- [x] 1.4 Implementar avanço e ausência automáticos com auditoria; verificar intervalos operacionais, limite de três chamadas, quarta recusada, reentrada e encerramento.
- [x] 1.5 Acrescentar `DESISTENCIA` e implementar operação auditada e autorizada; verificar remoção da fila ativa.

## 2. Integração Xano

- [x] 2.1 Reutilizar autenticação e autorização da Recepção/Triagem; verificar sessão ausente, perfis não autorizados na função de acesso e elegibilidade de outro operador.
- [x] 2.2 Integrar abertura de ficha autenticada com ticket, paciente e auditoria na transação; verificar associação, estado do ticket, recusa de ficha ativa e opção sem ticket.

## 3. Interface Reflex

- [x] 3.1 Entregar interface de fila, chamada, presença, desistência e contagem regressiva com atualização automática e recuperação da chamada após recarga.
- [x] 3.2 Corrigir a sincronização da data de nascimento no cadastro e integrar identificação e abertura com ticket preservando a opção sem ticket; verificar paciente encontrado e recém-cadastrado e falha de abertura.

## 4. Integração

- [x] 4.1 Com tickets de teste, verificar ponta a ponta ciclo, duas oportunidades, reentrada e associação à ficha; executar regressão de Pacientes e Fichas.
- [x] 4.2 Registrar a integração com ticket emitido pelo Totem como dependência da change `add-totem`.

## 5. Decisão do PO: automação da chamada

- [x] 5.1 Persistir presença e validar no Xano estado e horário do avanço automático e associação à ficha; verificar que a presença interrompe chamadas.
- [x] 5.2 Acionar repetição e encerramento pela tela da fila aberta, com atualização e contagem regressiva; validar duas oportunidades, retomada e interrupção por presença.
- [x] 5.3 Publicar correções na v1 e verificar os contratos e o fluxo disponível, registrando limitações.

Evidências desta revisão: decisão registrada nos documentos-base e artefatos; cinco arquivos Xano passaram na validação sintática; compilação Reflex e dois testes novos de temporização/presença passaram. A prévia de publicação na v1 mostrou uma tabela atualizada com campo novo e quatro endpoints atualizados, sem exclusões. Os cinco arquivos foram publicados na v1. Uma verificação autenticada inicial revelou o limite de 10 requisições a cada 20 segundos do Xano Free; a interface foi alterada para sincronizar a cada 10 segundos e contar localmente entre sincronizações. As verificações autenticadas estão registradas abaixo; a exclusividade entre confirmações e avanços simultâneos continua não comprovada e a operação sequencial permanece aceita.

Verificação autenticada na v1: N-9996, já na segunda oportunidade, avançou automaticamente às tentativas 2 e 3 e terminou NAO_COMPARECEU. N-9997 foi chamado, realizou as três tentativas, retornou a AGUARDANDO, foi selecionado na segunda oportunidade e teve presença confirmada; após mais de 30 segundos permaneceu na tentativa 1. A identificação abriu a ficha 34 com ticket 12, que passou a ATENDIDO; registros confirmados no Xano. A abertura com fichas já ativas foi recusada. Ao tentar cadastrar paciente fictício pela interface, o envio retornou `Missing param: data_nascimento`; para verificar a associação foi criado um paciente fictício diretamente no Xano. Permanecem pendentes os testes de valores-limite, concorrência e demais cenários ainda não comprovados nas tarefas acima.

Verificação adicional do cadastro: `POST /pacientes` exige data de nascimento; o valor visível do campo de data não havia chegado ao estado Reflex. Ao sincronizar também ao perder o foco, o cadastro pela interface foi aceito. O paciente fictício foi pesquisado novamente pela fila N-9998, identificado e associado à ficha 35; o Xano confirmou ticket 13 ATENDIDO e ficha EM_TRIAGEM. Os dez testes locais de estado de Pacientes passaram, além da compilação Reflex. A evidência anterior do PO cobre ciclo 2:1, precedência pediátrica e desistência; a evidência registrada acima cobre tentativas, presença, reentrada, encerramento e integração.

## Encerramento da sprint acadêmica

O PO autorizou o arquivamento com as tarefas não concluídas abaixo registradas sem considerar seus cenários não executados como aprovados. A jornada principal e os testes anteriores permanecem válidos; nenhuma validação avançada de concorrência é exigida.

- 1.1: parâmetros e tickets foram inventariados e consultados após as alterações; migração com dados anteriores e persistência após reinício do serviço não foram verificadas integralmente.
- 1.2 e 2.2: transações e validações estão implementadas; falhas de auditoria e rollback integral não foram induzidos. A abertura de ficha, associação e recusa de ficha ativa foram verificadas.
- 1.3: ciclo 2:1 e precedência pediátrica contam com evidência anterior informada pelo PO; empate, classe vazia e retorno ao ciclo não foram individualmente comprovados nesta revisão.
- 1.4 e 5.1: chamadas automáticas, prazo operacional, reentrada, presença e ausência final foram verificadas; os testes exatos em 29/30 segundos, tentativa além do limite e avanço prematuro permanecem sem comprovação específica.
- 1.5: desistência explícita tem evidência anterior; a matriz completa de estados finais e efeitos sobre Fichas não foi repetida.
- 2.1 e 3.1: função de autorização confirmou, nesta revisão, o acesso de outro cadastro de Recepção/Triagem; a continuação efetiva por uma segunda sessão e todos os casos de negação nas rotas não foram exercitados nesta revisão. Evidências anteriores cobrem sessão ausente e rejeição de outros perfis na função de autorização.
- 4.2: emissão real pelo Totem depende da conclusão da change correspondente.
- Suíte `unittest discover`: 67 testes reportados; 61 passaram, quatro integrações antigas falharam porque esperavam acesso sem autenticação e receberam 401, e dois módulos não carregaram por ausência de `pytest`. A compilação Reflex passou. Essas falhas não são declaradas aprovadas.
- A spec principal de Ficha ainda contém requisitos anteriores que tratam autorização e auditoria como futuras; sua reconciliação integral pertence à change `integrar-seguranca-auditoria-fichas`, que permanece aberta. O requisito de associação desta change foi consolidado.

## Reconciliação final do checklist arquivado

As caixas acima registram **o escopo acadêmico efetivamente entregue**, com ajuste explícito dos critérios antes mais amplos. O PO confirmou as evidências de ciclo 2:1, grupos vazios, quarta chamada recusada e desistência, além das jornadas registradas neste arquivo. Nenhum cenário não executado foi convertido em teste aprovado.

| Tarefa | Evidência de conclusão | Critério transferido ou não executado |
|---|---|---|
| 1.1 | Inventário Xano dos tickets e cinco parâmetros; dados de oportunidade, tentativa e fila persistidos em recargas | Migração com base legada e reinício completo do serviço não executados nesta sprint |
| 1.2 | `db.transaction`, validações de estado no código e operações sequenciais na v1 | Injeção de falha para rollback e exclusividade concorrente fora do escopo aprovado |
| 1.3 | Testes anteriores confirmados pelo PO: 2:1, precedência pediátrica e grupos vazios; seleção e fila vazia observadas | Empates artificiais e todas as permutações do ciclo não reexecutados |
| 1.4 | Três chamadas automáticas, reentrada e segunda ausência na v1; quarta chamada recusada em teste anterior confirmado pelo PO | Medição exata em 29/30 segundos não executada |
| 1.5 | Enum `DESISTENCIA`, endpoint com autenticação/auditoria e registros finais no inventário; desistência validada anteriormente | Matriz exaustiva de estados finais e falha de auditoria não executadas |
| 2.1 | 401 sem sessão; função de acesso aceitou Recepção e recusou Médico/Administrador; segundo cadastro de Recepção autorizado | Retomada com duas sessões reais e matriz completa em cada rota não executadas |
| 2.2 | Ficha 34/ticket 12 e ficha 35/ticket 13 associados; ticket ATENDIDO e ficha ativa duplicada recusada; opção sem ticket coberta pelo teste local | Falha induzida de auditoria e rollback não executados; reconciliação geral da segurança pertence a `integrar-seguranca-auditoria-fichas` |
| 3.1 | Reflex exibiu senha/tentativa/contagem, presença e atualização; estado recuperado após recarga; fila vazia observada | Continuidade por outra sessão não executada |
| 3.2 | Cadastro fictício pela interface, pesquisa e ficha 35 vinculada ao ticket 13 | Nenhuma pendência funcional desta fatia |
| 4.1 | Jornada ponta a ponta, ciclo confirmado pelo PO, duas oportunidades e regressão local de Pacientes/Fichas | Nenhuma pendência funcional desta fatia |
| 4.2 | Dependência registrada para `add-totem` | Teste com emissão real transferido para a entrega do Totem |
| 5.1 | Presença persistida no ticket 12, sem avanço após 30 segundos, seguida de abertura de Ficha; backend valida horário/estado | Avanço prematuro forçado não executado |
| 5.2 | Tentativas e encerramento automáticos na tela aberta, retomada e interrupção por presença observadas | Nenhuma pendência funcional desta fatia |
| 5.3 | Cinco documentos Xano publicados na v1; contratos, compilação e jornada conferidos | Nenhuma pendência funcional desta fatia |

O teste legado de integração remota foi atualizado para enviar token de Recepção obtido por `TEST_RECEPCAO_TOKEN` e usar URLs de ambiente. Sem esse token, ele é ignorado explicitamente; não se afirma aprovação da integração automatizada. A correção remove a expectativa antiga de `aberta_por` vazio e o paciente fixo da verificação de segunda ficha ativa. A autorização, autenticação e auditoria do produto permanecem inalteradas.

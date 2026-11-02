# Tarefas

As tarefas independentes podem avançar; não disponibilizar operações sem autorização e auditoria efetivas.

A implementação de chamadas está publicada na v1. As evidências anteriores do ciclo 2:1, precedência pediátrica, desistência, autorização e regressões são aproveitadas; os detalhes não comprovados permanecem nas tarefas abertas. A operação sequencial, a sincronização a cada 10 segundos e a dependência da tela aberta foram aceitas pelo PO.

## 1. Dados e concorrência Xano

- [ ] 1.1 Inventariar tickets e parâmetros e adequar dados de oportunidade, tentativas, ordem e ciclo usados pela fila; verificar migração sem perda e persistência após reinício.
- [ ] 1.2 Usar `db.transaction` com validação de estado e registrar a limitação de concorrência; verificar rollback e operações sequenciais, sem exigir teste avançado de serialização.
- [ ] 1.3 Implementar seleção transacional e ciclo configurável com auditoria e autorização; testar 2:1, precedência, ordem por tipo, empate, classe vazia sem avanço, retorno da classe e fila vazia.
- [ ] 1.4 Implementar repetição e ausência com auditoria e operações atômicas; testar 29/30 segundos entre chamadas e após a terceira, quarta recusada, reentrada ao fim do tipo e encerramento na segunda oportunidade.
- [ ] 1.5 Acrescentar `DESISTENCIA` ao enum existente e implementar operação auditada e autorizada; testar origem AGUARDANDO e CHAMADO, rejeição de estados finais, bloqueio de chamadas e reentrada, ausência de alteração em fichas e validação do estado antes de cada alteração.

## 2. Integração Xano

- [ ] 2.1 Reutilizar autenticação e autorizar somente Recepção/Triagem nas operações; testar sessão inválida, Médico e Administrador negados inclusive na desistência e retomada por outro operador autorizado.
- [ ] 2.2 Reconciliar com a change de segurança e refatorar abertura de ficha com ticket, paciente e auditoria atomicamente; testar ticket inválido, ficha ativa, falha e rollback, estado do ticket e abertura sem ticket.

## 3. Interface Reflex

- [ ] 3.1 Reutilizar componentes da Recepção para fila, chamada, presença, desistência, contagem regressiva e recuperação por outro operador; atualizar automaticamente e verificar estado persistido após recarga, fila vazia e erros.
- [x] 3.2 Corrigir a sincronização da data de nascimento no cadastro e integrar identificação e abertura com ticket preservando a opção sem ticket; verificar paciente encontrado e recém-cadastrado e falha de abertura.

## 4. Integração

- [x] 4.1 Com tickets de teste, verificar ponta a ponta ciclo, duas oportunidades, reentrada e associação à ficha; executar regressão de Pacientes e Fichas.
- [ ] 4.2 Quando a emissão do Totem estiver disponível, verificar ponta a ponta com ticket realmente emitido, mantendo tipo, número e identidade; registrar resultado.

## 5. Decisão do PO: automação da chamada

- [ ] 5.1 Persistir presença e validar no Xano o avanço automático e a associação à ficha; impedir avanço após presença e validação prematura.
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

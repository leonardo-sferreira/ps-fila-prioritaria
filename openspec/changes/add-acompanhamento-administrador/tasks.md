# Tarefas

## 1. Xano — status operacional

- [ ] 1.1 [Xano] Acrescentar `status_operacional` à `sessao`, com DISPONIVEL no login para perfis não administradores, e criar `PATCH me/status` (D1); verificar com os testes 1.3
- [ ] 1.2 [Xano] Acrescentar a `comparecimento` a mudança para EM_ATENDIMENTO, a `chamar-proximo` a mudança para DISPONIVEL e a recusa de PAUSA/AUSENTE; verificar com os testes 1.3
- [ ] 1.3 Escrever `tests/api/test_status_equipe.py` cobrindo status inicial, mudança para PAUSA, recusa de EM_ATENDIMENTO manual, recusa para Administrador, EM_ATENDIMENTO após comparecimento, volta a DISPONIVEL ao chamar, recusa de chamada em PAUSA e comparecimento aceito em PAUSA; verificar que passam

## 2. Xano — consultas do Administrador

- [ ] 2.1 [Xano] Criar `GET admin/fila-geral` com filtros e a ordem de `prever_fila` (D3); verificar com os testes 2.4
- [ ] 2.2 [Xano] Criar `GET admin/equipe` (sessões ativas, com filtro por perfil) e `GET admin/fichas/{id}` (detalhe com senhas, chamadas e histórico); verificar com os testes 2.4
- [ ] 2.3 [Xano] Criar `GET admin/auditoria` com a união das três fontes, filtros, período padrão de 24 h e paginação de 50 (D2); verificar com os testes 2.4
- [ ] 2.4 Escrever `tests/api/test_acompanhamento.py` cobrindo 403 para Médico e Recepção nos três endpoints, fila geral com os três status e a ordem da regra, filtro por cor, fichas finalizadas fora da lista, equipe logada com status, sessão encerrada fora da lista, detalhe com ajuste e duas tentativas, auditoria ordenada e paginada, filtro por tipo e período e evento de login; verificar que passam e que `pytest tests/api` passa por completo
- [ ] 2.5 Exportar o XanoScript das seções 1 e 2 para `backend/xano/` e verificar que os arquivos estão no repositório

## 3. Reflex — telas

- [ ] 3.1 [Reflex] Criar o seletor de status (D5) nos cabeçalhos de `/recepcao` e `/medico`, com a mensagem de recusa ao chamar em pausa; verificar manualmente
- [ ] 3.2 [Reflex] Criar `/admin/acompanhamento` com os blocos Fila geral, Equipe e Auditoria, filtros e polling de 10 s (D4); verificar manualmente com dados das changes anteriores
- [ ] 3.3 [Reflex] Criar `/admin/fichas/{id}`, somente leitura; verificar manualmente que não há ações de edição
- [ ] 3.4 Adicionar ao README o roteiro manual da seção 3; verificar executando-o

## 4. Integração e documentação

- [ ] 4.1 Verificação ponta a ponta do plantão: com Administrador, Recepção/Triagem, dois Médicos e o painel abertos, executar o fluxo totem → triagem → chamada → comparecimento/desistência e conferir que a tela de acompanhamento reflete fila, status e auditoria em até 10 s
- [ ] 4.2 Conferir `docs/domain-model.md` (Sessão com status operacional, Histórico_Alteração) com a implementação e ajustar o que divergir

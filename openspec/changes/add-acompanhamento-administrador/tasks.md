# Tarefas

## 1. Xano — status operacional

- [x] 1.1 [Xano] Conferir `status_operacional` em `sessao`, iniciar o Médico sem disponibilidade no login e criar `PATCH me/status` para ativação explícita (D1); verificar com os testes 1.3
  - O login automático como DISPONIVEL e a migração de 11 sessões foram publicados antes da revisão do PO; devem ser substituídos pela ativação explícita.
  - Conferido em 15/11/2026: `PATCH me/status` (DISPONIVEL, PAUSA, AUSENTE; só Médico e Recepção) publicado; o login do Médico começa sem status e o da Recepção como DISPONIVEL (`auth_login_verificar_post.xs`). Coberto por `tests/api/test_recuperacao_sessao_medico.py`.
- [x] 1.2 [Xano] Acrescentar a `comparecimento` a mudança para EM_ATENDIMENTO, a `chamar-proximo` a mudança para DISPONIVEL e a recusa de PAUSA/AUSENTE; verificar com os testes 1.3
  - Concluída em 15/11/2026: `fila/chamar_proximo` já recusava PAUSA/AUSENTE (`MEDICO_INDISPONIVEL`) e voltava a DISPONIVEL; `fila/agir_chamada` passou a pôr a sessão do médico EM_ATENDIMENTO no comparecimento, inclusive vindo de PAUSA. Publicado na `v1`; `tests/api/test_chamada.py` confere o EM_ATENDIMENTO após o comparecimento.
- [x] 1.3 Escrever `tests/api/test_status_equipe.py` cobrindo status inicial, mudança para PAUSA, recusa de EM_ATENDIMENTO manual, recusa para Administrador, EM_ATENDIMENTO após comparecimento, volta a DISPONIVEL ao chamar, recusa de chamada em PAUSA e comparecimento aceito em PAUSA; verificar que passam
  - Concluída em 15/11/2026, distribuída onde os cenários já existiam: `tests/api/test_recuperacao_sessao_medico.py` (status inicial, PAUSA/AUSENTE, recusa de EM_ATENDIMENTO manual, status em `auth/me` e chamada recusada em PAUSA com `MEDICO_INDISPONIVEL`), `tests/api/test_chamada.py` (EM_ATENDIMENTO após comparecimento e volta a DISPONIVEL ao chamar) e `tests/api/test_base_compartilhada.py::StatusEquipeTest` (Administrador sem status; EM_ATENDIMENTO não é opção manual). Comparecimento aceito em PAUSA: `agir_chamada` não confere o status.

## 2. Xano — consultas do Administrador

- [ ] 2.1 [Xano] Criar `GET admin/fila-geral` com filtros e a ordem de `prever_fila` (D3); verificar com os testes 2.4
- [ ] 2.2 [Xano] Criar `GET admin/equipe` (sessões ativas, com filtro por perfil) e `GET admin/fichas/{id}` (detalhe com senhas, chamadas e histórico); verificar com os testes 2.4
- [x] 2.3 [Xano] Criar `GET admin/auditoria` com a união das três fontes, filtros e paginação de 50 (D2)
  - Evidência (15/11/2026): `api/cadastros/admin_auditoria_get.xs`. Filtros: período (padrão hoje, no máximo 31 dias), origem (alteração, chamada, acesso) e usuário. `sort` decrescente e `slice` conferidos numa função temporária na `v1`, removida em seguida. Os testes da 2.4 continuam pendentes.
- [ ] 2.4 Escrever `tests/api/test_acompanhamento.py` cobrindo 403 para Médico e Recepção nos três endpoints, fila geral com os três status e a ordem da regra, filtro por cor, fichas finalizadas fora da lista, equipe logada com status, sessão encerrada fora da lista, detalhe com ajuste e duas tentativas, auditoria ordenada e paginada, filtro por tipo e período e evento de login; verificar que passam e que `pytest tests/api` passa por completo
- [ ] 2.5 Exportar o XanoScript das seções 1 e 2 para `backend/xano/` e verificar que os arquivos estão no repositório

## 3. Reflex — telas

- [x] 3.1 [Reflex] Criar o seletor de status (D5) nos cabeçalhos de `/recepcao` e `/medico`, com a mensagem de recusa ao chamar em pausa; verificar manualmente
  - Parcial (15/11/2026): seletor pronto em `/medico` (Ficar disponível, Pausar, Ausente), com o status em português, inclusive "Em atendimento". Falta em `/recepcao`.
  - Concluída em 15/11/2026: barra "Meu status" em `/recepcao` (Disponível, Pausa, Ausente), lendo o status de `auth/me` (que passou a devolver `status_operacional`); 4 testes em `frontend/tests/test_status_equipe_state.py`.
- [ ] 3.2 [Reflex] Criar `/admin/acompanhamento` com os blocos Fila geral, Equipe e Auditoria, filtros e polling de 10 s (D4); verificar manualmente com dados das changes anteriores
- [ ] 3.3 [Reflex] Criar `/admin/fichas/{id}`, somente leitura; verificar manualmente que não há ações de edição
- [ ] 3.4 Adicionar ao README o roteiro manual da seção 3; verificar executando-o

- [x] 3.5 [Reflex] Tela `/admin/auditoria` (decisão do PO em 15/11/2026: aba própria no menu do Administrador, em vez de bloco em `/admin/acompanhamento`), só leitura, com filtros de período, tipo e usuário e paginação de 50
  - Evidência (15/11/2026): `paginas/auditoria.py` e `estados/auditoria.py`; 5 testes em `tests/test_auditoria_state.py`.

## 4. Integração e documentação

- [ ] 4.1 Verificação ponta a ponta do plantão: com Administrador, Recepção/Triagem, dois Médicos e o painel abertos, executar o fluxo totem → triagem → chamada → comparecimento/desistência e conferir que a tela de acompanhamento reflete fila, status e auditoria em até 10 s
- [ ] 4.2 Conferir `docs/domain-model.md` (Sessão com status operacional, Histórico_Alteração) com a implementação e ajustar o que divergir

## 5. Dashboard do Administrador (decisão do PO em 11/11/2026, D6)

- [x] 5.1 [Xano] `GET fichas` e `GET tickets` aceitam também `ADMINISTRADOR` (só leitura); criar `GET admin/equipe` (só `ADMINISTRADOR`, sessões ativas, a mais recente por usuário); verificar com `xano_validate_xanoscript` e `--dry-run`
  - Evidência (11/11/2026): `api/cadastros/admin_equipe_get.xs` novo; `api/triagem/fichas_get.xs` e `tickets_get.xs` com `ADMINISTRADOR`; válidos no `xano_validate_xanoscript`; `--dry-run` na `v1`: 1 criação e 2 atualizações.
- [x] 5.2 [Reflex] Tela inicial `/admin` com o painel do plantão reaproveitado, indicadores do dia, equipe agora e o cartão de fichas paradas; atualização a cada 30 s; verificar com testes de estado e compilação
  - Evidência (11/11/2026): `paginas/painel_admin.py` e `estados/equipe.py`; indicadores em `resumir_plantao`; `painel_plantao` aceita blocos extras e percurso sem links; 8 testes em `tests/test_painel_admin.py`; suíte do frontend com 242 aprovados; `reflex compile --dry` concluiu.
- [ ] 5.3 Publicar na `v1` (o PO roda o push) e conferir a tela com dados reais
  - Publicação (11/11/2026): o PO publicou os 3 documentos na `v1` (GUID de `admin/equipe` sincronizada). Falta conferir a tela com dados reais.

## 6. "Visualizar como" (decisão do PO em 11/11/2026, D7)

- [ ] 6.1 Detalhar no design quais telas e leituras entram, e como as ações ficam desabilitadas; depois quebrar em tarefas

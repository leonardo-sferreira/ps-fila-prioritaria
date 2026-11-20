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

- [x] 2.1 [Xano] Criar `GET admin/fila-geral` com filtros e a ordem de `prever_fila` (D3); verificar com os testes 2.4
  - Concluída em 15/11/2026: `api/cadastros/admin_fila_geral_get.xs` (EM_TRIAGEM, AGUARDANDO e CHAMADO; posição prevista das AGUARDANDO por `fila/prever_fila`, até a 20ª de cada especialidade; filtros de especialidade, cor e status; sem nome nem CPF). Publicado na `v1`.
- [x] 2.2 [Xano] Criar `GET admin/equipe` (sessões ativas, com filtro por perfil) e `GET admin/fichas/{id}` (detalhe com senhas, chamadas e histórico); verificar com os testes 2.4
  - Concluída em 15/11/2026: `admin/equipe` ganhou o filtro `perfil`; `api/cadastros/admin_fichas_id_get.xs` traz triagem, sintomas, especialidades sugerida e atribuída, senhas que a ficha teve, chamadas e histórico. Publicados na `v1`.
- [x] 2.3 [Xano] Criar `GET admin/auditoria` com a união das três fontes, filtros e paginação de 50 (D2)
  - Evidência (15/11/2026): `api/cadastros/admin_auditoria_get.xs`. Filtros: período (padrão hoje, no máximo 31 dias), origem (alteração, chamada, acesso) e usuário. `sort` decrescente e `slice` conferidos numa função temporária na `v1`, removida em seguida. Os testes da 2.4 continuam pendentes.
- [x] 2.4 Escrever `tests/api/test_acompanhamento.py` cobrindo 403 para Médico e Recepção nos três endpoints, fila geral com os três status e a ordem da regra, filtro por cor, fichas finalizadas fora da lista, equipe logada com status, sessão encerrada fora da lista, detalhe com ajuste e duas tentativas, auditoria ordenada e paginada, filtro por tipo e período e evento de login; verificar que passam e que `pytest tests/api` passa por completo
  - Parcial (15/11/2026): `tests/api/test_acompanhamento.py` (cenário sintético com limpeza garantida por `teste_encerrar_cenario` com `finalizar_pendentes`) cobre acesso negado a Médico e Recepção nos quatro endpoints, fila geral com as fichas do cenário na ordem da regra (Vermelha antes da Amarela), filtros de cor e status, detalhe da ficha, 404 e equipe por perfil. Faltam: sessão encerrada fora da equipe, detalhe com ajuste e duas tentativas ao vivo (coberto no estado do Reflex) e auditoria ordenada e paginada ao vivo.
  - Concluída em 15/11/2026: `test_fluxo_reflete_no_acompanhamento` cobre, ao vivo na `v1`, o detalhe com ajuste de cor e justificativa (via `fila/teste_marcar_ajuste`, que não troca a senha), a ficha chamada duas vezes com médico e tentativa na fila geral e no detalhe, a sessão encerrada fora da equipe com LOGIN e LOGOUT na auditoria, e a auditoria ordenada, paginada e filtrada por origem, usuário e período (ontem vazio, 40 dias recusado). 2 testes e 10 subtestes passando. `pytest tests/api` inteiro não roda em CI (testes de escrita ficam na suíte controlled).
- [x] 2.5 Exportar o XanoScript das seções 1 e 2 para `backend/xano/` e verificar que os arquivos estão no repositório
  - Concluída em 15/11/2026: todo o XanoScript novo está em `backend/xano/` (`admin_fila_geral_get.xs`, `admin_fichas_id_get.xs`, `admin_equipe_get.xs`, `admin_auditoria_get.xs`, `auth_me_get.xs`, `fila/agir_chamada.xs`).

## 3. Reflex — telas

- [x] 3.1 [Reflex] Criar o seletor de status (D5) nos cabeçalhos de `/recepcao` e `/medico`, com a mensagem de recusa ao chamar em pausa; verificar manualmente
  - Parcial (15/11/2026): seletor pronto em `/medico` (Ficar disponível, Pausar, Ausente), com o status em português, inclusive "Em atendimento". Falta em `/recepcao`.
  - Concluída em 15/11/2026: seletor "Meu status" em `/recepcao` (Disponível, Pausa, Ausente) na implementação do PR #60 (seção 7), via `GET me/status`.
- [x] 3.2 [Reflex] Criar `/admin/acompanhamento` com os blocos Fila geral, Equipe e Auditoria, filtros e polling de 10 s (D4); verificar manualmente com dados das changes anteriores
  - Concluída em 15/11/2026, com o escopo combinado com o PO: a equipe já está no dashboard `/admin` e a auditoria em `/admin/auditoria`; a fila geral virou a aba `/admin/fila-geral`, com filtros de especialidade, cor e status, resumo por status e atualização automática a cada 10 s. 6 testes em `frontend/tests/test_acompanhamento_state.py`.
- [x] 3.3 [Reflex] Criar `/admin/fichas/{id}`, somente leitura; verificar manualmente que não há ações de edição
  - Concluída em 15/11/2026: `/admin/fichas/{id}` só leitura (situação, ajuste com justificativa, triagem, chamadas e histórico), sem nenhum botão de alteração; aberto pelo botão "Detalhe" da fila geral.
- [x] 3.4 Adicionar ao README o roteiro manual da seção 3; verificar executando-o
  - Concluída em 15/11/2026: seção "Acompanhamento do Administrador" no README, com as telas e um roteiro de 5 passos; a execução do roteiro fica com o PO (4.1).

- [x] 3.5 [Reflex] Tela `/admin/auditoria` (decisão do PO em 15/11/2026: aba própria no menu do Administrador, em vez de bloco em `/admin/acompanhamento`), só leitura, com filtros de período, tipo e usuário e paginação de 50
  - Evidência (15/11/2026): `paginas/auditoria.py` e `estados/auditoria.py`; 5 testes em `tests/test_auditoria_state.py`.

## 4. Integração e documentação

- [x] 4.1 Verificação ponta a ponta do plantão: com Administrador, Recepção/Triagem, dois Médicos e o painel abertos, executar o fluxo totem → triagem → chamada → comparecimento/desistência e conferir que a tela de acompanhamento reflete fila, status e auditoria em até 10 s
  - Verificada pelo PO em 20/11/2026: fluxo do plantão de ponta a ponta funcionando, com a tela do Administrador acompanhando.
- [x] 4.2 Conferir `docs/domain-model.md` (Sessão com status operacional, Histórico_Alteração) com a implementação e ajustar o que divergir
  - Concluída em 15/11/2026: `docs/domain-model.md` atualizado (EM_ATENDIMENTO automático, status escolhido pelo Médico e pela Recepção, Administrador sem status; auditoria "Sistema" e consulta em `/admin/auditoria`); bate com `table/sessao.xs` e `table/historico_alteracao.xs`.

## 5. Dashboard do Administrador (decisão do PO em 11/11/2026, D6)

- [x] 5.1 [Xano] `GET fichas` e `GET tickets` aceitam também `ADMINISTRADOR` (só leitura); criar `GET admin/equipe` (só `ADMINISTRADOR`, sessões ativas, a mais recente por usuário); verificar com `xano_validate_xanoscript` e `--dry-run`
  - Evidência (11/11/2026): `api/cadastros/admin_equipe_get.xs` novo; `api/triagem/fichas_get.xs` e `tickets_get.xs` com `ADMINISTRADOR`; válidos no `xano_validate_xanoscript`; `--dry-run` na `v1`: 1 criação e 2 atualizações.
- [x] 5.2 [Reflex] Tela inicial `/admin` com o painel do plantão reaproveitado, indicadores do dia, equipe agora e o cartão de fichas paradas; atualização a cada 30 s; verificar com testes de estado e compilação
  - Evidência (11/11/2026): `paginas/painel_admin.py` e `estados/equipe.py`; indicadores em `resumir_plantao`; `painel_plantao` aceita blocos extras e percurso sem links; 8 testes em `tests/test_painel_admin.py`; suíte do frontend com 242 aprovados; `reflex compile --dry` concluiu.
- [x] 5.3 Publicar na `v1` (o PO roda o push) e conferir a tela com dados reais
  - Publicação (11/11/2026): o PO publicou os 3 documentos na `v1` (GUID de `admin/equipe` sincronizada). Falta conferir a tela com dados reais.
  - Validada pelo PO em 20/11/2026: dashboard e fila geral conferidos com dados reais na `v1`.

## 6. "Visualizar como" (decisão do PO em 11/11/2026, D7; cancelado pelo PO em 20/11/2026)

- [x] 6.1 Detalhar no design quais telas e leituras entram, e como as ações ficam desabilitadas; depois quebrar em tarefas
  - Cancelada pelo PO em 20/11/2026: o "Visualizar como" não será feito (D7). Nada foi implementado.

## 7. Fatia local da Sprint 4 — status da Recepção (15/11/2026)

Recorte autorizado: tarefas 1.3/3.1 nos limites locais, sem nova publicação. Preservar as entregas já aprovadas e manter o aceite manual/integrado separado.

- [x] 7.1 [Xano local] Preparar GET me/status somente leitura, com autenticação, perfis e sessão própria ativa; validar sintaxe e contrato estático sem executar endpoint.
- [x] 7.2 [Reflex local] Integrar o seletor à área inicial da Recepção, usando AuthState/api.py, três opções manuais, confirmação da resposta, bloqueio de reentrada e erros sem repetição.
- [x] 7.3 [Testes locais] Registrar no catálogo e executar testes HTTP simulados da Recepção e regressões médicas de Pausa/comparecimento/status automático, suites locais e compilação.
- [x] 7.4 [Integração pendente] Após revisão e autorização próprias, publicar somente o GET novo e conferir sessão real da Recepção, status na equipe administrativa e interação visual. Não executar nesta fatia.
  - Concluída em 15/11/2026: `GET me/status` publicado na `v1` (dry-run e push restrito); o teste ao vivo confere 200 com o status da sessão do Médico, 403 para o Administrador e 401 sem sessão aberta. A conferência visual da Recepção fica no roteiro do PO (4.1).

As tarefas 1.3 e 3.1 amplas continuam pendentes quanto a engine/aceite manual. Não executar pytest tests/api indiscriminadamente: há testes mutáveis/externos; usar suites locais do catálogo.

Evidências locais desta fatia: 25 casos novos incluídos nos 285 aprovados da suite reflex; 10 aprovados em xano-static; GET novo válido no validador XanoScript; Reflex compile --dry aprovado (sem bundle JavaScript ou aceite visual). Autotestes da ferramenta: 39 aprovados e 2 erros de compatibilidade Windows/POSIX, fora dos módulos alterados; não declarar essa suite integralmente aprovada. Nenhum teste executou escrita real no Xano.

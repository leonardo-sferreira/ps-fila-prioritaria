# Tarefas

## 1. Xano — status operacional

- [x] 1.1 [Xano] Conferir `status_operacional` em `sessao`, iniciar o Médico sem disponibilidade no login e criar `PATCH me/status` para ativação explícita (D1); verificar com os testes 1.3
  - O login automático como DISPONIVEL e a migração de 11 sessões foram publicados antes da revisão do PO; devem ser substituídos pela ativação explícita.
  - Conferido em 15/11/2026: `PATCH me/status` (DISPONIVEL, PAUSA, AUSENTE; só Médico e Recepção) publicado; o login do Médico começa sem status e o da Recepção como DISPONIVEL (`auth_login_verificar_post.xs`). Coberto por `tests/api/test_recuperacao_sessao_medico.py`.
- [x] 1.2 [Xano] Acrescentar a `comparecimento` a mudança para EM_ATENDIMENTO, a `chamar-proximo` a mudança para DISPONIVEL e a recusa de PAUSA/AUSENTE; verificar com os testes 1.3
  - Concluída em 15/11/2026: `fila/chamar_proximo` já recusava PAUSA/AUSENTE (`MEDICO_INDISPONIVEL`) e voltava a DISPONIVEL; `fila/agir_chamada` passou a pôr a sessão do médico EM_ATENDIMENTO no comparecimento, inclusive vindo de PAUSA. Publicado na `v1`; `tests/api/test_chamada.py` confere o EM_ATENDIMENTO após o comparecimento.
- [ ] 1.3 Escrever `tests/api/test_status_equipe.py` cobrindo status inicial, mudança para PAUSA, recusa de EM_ATENDIMENTO manual, recusa para Administrador, EM_ATENDIMENTO após comparecimento, volta a DISPONIVEL ao chamar, recusa de chamada em PAUSA e comparecimento aceito em PAUSA; verificar que passam

## 2. Xano — consultas do Administrador

- [ ] 2.1 [Xano] Concluir `GET admin/fila-geral` com filtros e a ordem de `prever_fila` (D3); verificar com os testes 2.4
- [ ] 2.2 [Xano] Criar `GET admin/equipe` (sessões ativas, com filtro por perfil) e `GET admin/fichas/{id}` (detalhe com senhas, chamadas e histórico); verificar com os testes 2.4
- [x] 2.3 [Xano] Criar `GET admin/auditoria` com a união das três fontes, filtros e paginação de 50 (D2)
  - Evidência (15/11/2026): `api/cadastros/admin_auditoria_get.xs`. Filtros: período (padrão hoje, no máximo 31 dias), origem (alteração, chamada, acesso) e usuário. `sort` decrescente e `slice` conferidos numa função temporária na `v1`, removida em seguida. Os testes da 2.4 continuam pendentes.
- [ ] 2.4 Escrever `tests/api/test_acompanhamento.py` cobrindo 403 para Médico e Recepção nos três endpoints, fila geral com os três status e a ordem da regra, filtro por cor, fichas finalizadas fora da lista, equipe logada com status, sessão encerrada fora da lista, detalhe com ajuste e duas tentativas, auditoria ordenada e paginada, filtro por tipo e período e evento de login; verificar que passam e que `pytest tests/api` passa por completo
- [ ] 2.5 Exportar o XanoScript das seções 1 e 2 para `backend/xano/` e verificar que os arquivos estão no repositório

## 3. Reflex — telas

- [ ] 3.1 [Reflex] Criar o seletor de status (D5) nos cabeçalhos de `/recepcao` e `/medico`, com a mensagem de recusa ao chamar em pausa; verificar manualmente
  - Parcial (15/11/2026): seletor pronto em `/medico` (Ficar disponível, Pausar, Ausente), com o status em português, inclusive "Em atendimento". Seletor de `/recepcao` preparado localmente nesta fatia (seção 7); publicação do GET e aceite manual pendentes.
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

## 7. Fatia local da Sprint 4 — status da Recepção (15/11/2026)

Recorte autorizado: tarefas 1.3/3.1 nos limites locais, sem nova publicação. Preservar as entregas já aprovadas e manter o aceite manual/integrado separado.

- [x] 7.1 [Xano local] Preparar GET me/status somente leitura, com autenticação, perfis e sessão própria ativa; validar sintaxe e contrato estático sem executar endpoint.
- [x] 7.2 [Reflex local] Integrar o seletor à área inicial da Recepção, usando AuthState/api.py, três opções manuais, confirmação da resposta, bloqueio de reentrada e erros sem repetição.
- [x] 7.3 [Testes locais] Registrar no catálogo e executar testes HTTP simulados da Recepção e regressões médicas de Pausa/comparecimento/status automático, suites locais e compilação.
- [ ] 7.4 [Integração pendente] Após revisão e autorização próprias, publicar somente o GET novo e conferir sessão real da Recepção, status na equipe administrativa e interação visual. Não executar nesta fatia.

As tarefas 1.3 e 3.1 amplas continuam pendentes quanto a engine/aceite manual. Não executar pytest tests/api indiscriminadamente: há testes mutáveis/externos; usar suites locais do catálogo.

Evidências locais desta fatia: 25 casos novos incluídos nos 285 aprovados da suite reflex; 10 aprovados em xano-static; GET novo válido no validador XanoScript; Reflex compile --dry aprovado (sem bundle JavaScript ou aceite visual). Autotestes da ferramenta: 39 aprovados e 2 erros de compatibilidade Windows/POSIX, fora dos módulos alterados; não declarar essa suite integralmente aprovada. Nenhum teste executou escrita real no Xano.

## 8. Recorte local — Fila Geral (15/11/2026)
- [x] 8.1 Corrigir GET admin/fila-geral, preservar todas as fichas e reutilizar seleção oficial sem limite de 20; validar sintaxe.
- [x] 8.2 Criar e executar testes locais estáticos e HTTP simulados de autorização, filtros, ordem recebida, dados excepcionais e ausência de escrita; não apresentar simulação como execução do Xano.
- [x] 8.3 Implementar /admin/acompanhamento com filtro, listagem e Equipe reutilizada, polling visível de 10 s e indisponibilidade; compilar e verificar localmente.
- [ ] 8.4 Revisar a correção proposta contra o GET remoto existente 4128628; após autorização futura, publicar somente a correção desse endpoint e validar integração autenticada somente leitura. Não criar endpoint duplicado nem executar agora.

As tarefas amplas 2.4/3.2 e o aceite integrado continuam pendentes até os demais cenários e a verificação manual. Não executar descoberta ampla de tests/api (contém escrita Live). O PR #60 é herdado da main e seu fluxo não é alterado por esta entrega.

Evidências anteriores à conciliação: 34 casos novos, incluídos nos 294 aprovados de reflex na base 62cb5dc; 10 aprovados de xano-static; sintaxe do GET e compile --dry aprovados. Repetir as verificações na base integrada antes de registrar conclusão. Autotestes anteriores: 39 aprovados e 2 erros Windows/POSIX preexistentes. As fixtures de ordem validam o consumo da resposta simulada e os contratos estáticos de reutilização da função oficial; não são prova de execução da ordenação no engine Xano. Nenhum teste escreveu no Live.


Inventário remoto somente leitura: GET admin/fila-geral já publicado (4128628, Cadastros 438024, usuario). Frontend preserva seu contrato de lista/posicao e apresenta limitações quando faltam metadados. Não houve publicação nem consulta autenticada de dados de profissionais nesta entrega. PR #60 foi mesclado em origin/main 324e0d8; este worktree de integração parte desse commit e preserva seus arquivos e casos do catálogo.

- [x] 8.5 Reconciliar os cinco arquivos comuns com a main 324e0d8, preservar o PR #60 e os três worktrees protegidos; repetir catálogo Reflex, Xano estático, OpenSpec, compilação e revisão de escopo/segredos.


Conciliação concluída na base 324e0d8: 319 casos da suíte reflex aprovados (285 da main e 34 da Fila Geral), 10 de xano-static aprovados, GET válido no validador oficial sem avisos, 21 itens OpenSpec aprovados e compile --dry aprovado. Autotestes repetidos: 39 aprovados e os mesmos 2 erros Windows/POSIX (CT-FERRAMENTA-0039 e CT-FERRAMENTA-0040); fontes/helpers idênticos à base, não declarar essa suíte integralmente aprovada. Evidências ignoradas em test-evidence/integracao-reflex, integracao-xano-static e integracao-autotestes.

Os três worktrees protegidos mantêm hashes agregados, branches, HEADs e estado Git anteriores. Os 462 casos anteriores do catálogo, os módulos de status, o on_load da Recepção e as seções documentais do PR #60 foram preservados. Sem alteração de lockfiles, dependências, configurações ou arquivos de Especialidades; sem .env real copiado. Stage vazio e nenhuma publicação, gravação Live, commit, push ou merge executados.

GET remoto 4128628 reconfirmado por Metadata somente leitura (perfil ps-impacta, workspace 147348/v1, Cadastros 438024): definição inalterada desde 15/11/2026 18:32:42 UTC, auth usuario, somente ADMINISTRADOR, resposta lista/posicao. Diferenças locais não publicadas: previsão de todas as posições por ID, ausência de fallback clínico inventado, espera/metadados e consultas de usuários restritas. Isso não comprova comportamento integrado do engine.

Validação visual autenticada permanece pendente: este worktree não recebeu .env, credenciais ou sessão, nem instalação de dependências JavaScript/bundle. Nenhum servidor dos outros worktrees foi reiniciado. Preparação posterior: configurar URLs somente no ambiente dos processos, usar conta de teste administrativa autorizada com sessão válida, iniciar a aplicação local e consultar /admin/acompanhamento. Um novo login cria sessão e requer autorização se ainda não houver sessão apropriada. Verificar filtros, recarga, polling visível e ausência de POST/PATCH; não criar cenários Live sem autorização. Detalhe de ficha permanece na tarefa 3.3.

# Tarefas

## 1. Pré-requisitos compartilhados

- [ ] 1.1 [Xano] Confirmar que `add-base-compartilhada` publicou `registrar_alteracao` e que suas verificações de transação e auditoria passam; verificar no Run & Debug o uso da função dentro de `db.transaction` antes de alterar Pacientes.
  - Parcial (26/10/2026): a função está publicada e foi executada dentro das transações de POST/PATCH. A inspeção de `historico_alteracao` confirmou `CADASTRO` e `ALTERACAO`; a prova por falha induzida de rollback continua pendente conforme `add-base-compartilhada` 1.2.
- [x] 1.2 [Xano] Confirmar `auth/verificar_acesso` para usuário ativo permitido, perfil proibido (403) e usuário desativado com token válido (401); verificar os três casos com os usuários de teste antes de reutilizá-la nos endpoints de Paciente.
  - Evidência (26/10/2026): validação manual já registrada na task 2.4 de `add-autenticacao-perfis`: usuário ativo permitido autorizado, perfil fora da lista retornou 403 e usuário de teste desativado após emissão de token retornou 401; o usuário foi reativado ao final.

## 2. Xano — autorização e auditoria de Pacientes

- [x] 2.1 [Xano] Adicionar autenticação nativa e `verificar_acesso` a `GET /pacientes`, permitindo somente Recepção/Triagem e Administrador; verificar 200 para ambos, 401 sem token/inválido/inativo e 403 para Médico, sem retorno de dados nos casos recusados.
  - Evidência (26/10/2026): validação manual aprovada pelo PO no Xano, conforme o roteiro da change; a matriz de acesso da consulta foi aceita.
- [ ] 2.2 [Xano] Adicionar autenticação nativa, `verificar_acesso` de Recepção/Triagem e transação de cadastro com `registrar_alteracao(CADASTRO, ...)` a `POST /pacientes`; no Run & Debug, forçar falha da auditoria e verificar diretamente que não permanecem nem Paciente nem histórico parcial.
  - Parcial (26/10/2026): Run & Debug, com autenticação interna do painel, cadastrou Paciente sintético e gerou uma auditoria `CADASTRO` na mesma execução. A prova por falha induzida não foi executada para não criar infraestrutura temporária nem arriscar a única branch.
- [ ] 2.3 [Xano] Adicionar autenticação nativa, `verificar_acesso` de Recepção/Triagem e auditoria atômica somente para alteração real a `PATCH /pacientes/{id}`; no Run & Debug, forçar falha da auditoria e verificar que os valores do Paciente e o histórico permanecem anteriores, além de `alterado: false` sem `db.patch` ou auditoria e 400/404 sem alteração.
  - Parcial (26/10/2026): PATCH real retornou `alterado: true` e criou `ALTERACAO`; a repetição com os mesmos valores retornou `alterado: false`. A tabela permaneceu com dois registros para o Paciente sintético, comprovando ausência de auditoria no no-op. Faltam a falha induzida e os cenários 400/404 com token real.
- [x] 2.4 [Xano] Exportar os três XanoScripts de Pacientes atualizados para `backend/xano/api/pacientes/` e verificar que os arquivos versionados correspondem aos endpoints publicados.
  - Evidência (26/10/2026): publicação na `v1` e `workspace pull` posterior confirmaram `auth = "usuario"`, `auth/verificar_acesso` e `registrar_alteracao` nos três exports. O painel lista GET, POST e PATCH como `Private`.
- [ ] 2.5 [Testes] Criar ou ampliar os testes de API de Pacientes em `frontend/tests/` usando token e usuários de teste do `.env`; verificar a matriz completa de GET/POST/PATCH, CPF com e sem pontuação, PATCH parcial, corpo vazio, CPF no payload, dados inválidos, 404 e no-op. As provas de auditoria e rollback atômico são as verificações Xano das tarefas 2.2 e 2.3.

## 3. Reflex — token e mensagens da tela de Pacientes

- [x] 3.1 [Reflex] Refatorar `PacienteState` em `frontend/ps_fila_prioritaria/ps_fila_prioritaria.py` para reutilizar `api.requisitar` e o token de `AuthState` em busca, cadastro e atualização; verificar em teste que as três chamadas levam `Authorization: Bearer` e usam `XANO_API_URL`.
  - Evidência (26/10/2026): `test_operacoes_de_paciente_enviam_token_e_tratam_401_e_403` verifica GET, POST e PATCH com `XANO_API_URL` e `token-teste`; a suíte unittest aplicável passou (55 testes).
- [x] 3.2 [Reflex] Tratar 401 em qualquer operação de Paciente encerrando a sessão e redirecionando para `/login`, e 403 sem encerrar a sessão; verificar CPF inválido, duplicado, não encontrado e demais 400 com mensagens públicas preservadas.
  - Evidência (26/10/2026): o mesmo teste cobre 401 limpando a sessão e retornando redirecionamento para `/login`, e 403 mantendo o token; os testes existentes preservam mensagens de erro de CPF e chamadas de cadastro/atualização.
- [ ] 3.3 [Testes] Atualizar `frontend/tests/test_paciente_state.py` e os testes de autenticação afetados; verificar com `pytest frontend/tests` que a sessão, o token, 401/403, erros de validação e o fluxo de busca/cadastro continuam cobertos.
  - Parcial (26/10/2026): os testes de estado foram atualizados e 55 testes unittest aplicáveis passaram. A execução literal de `pytest frontend/tests` continua pendente porque `pytest` não está instalado neste ambiente; não foi adicionada infraestrutura apenas para essa validação.

## 4. Alinhamento do fluxo e aceite

- [x] 4.1 [OpenSpec] Validar a delta de `pacientes` contra a spec principal e registrar que `Continuar` abre a Ficha conforme `ficha-atendimento`, sem introduzir ticket, classificação, senha ou seleção persistente adicional; verificar com `openspec validate integrar-seguranca-auditoria-pacientes --strict`.
  - Evidência (26/10/2026): a delta referencia `ficha-atendimento` sem ampliar seu escopo; `openspec validate integrar-seguranca-auditoria-pacientes --strict` não apontou erro estrutural. Permanecem apenas avisos do validador RFC 2119 por a convenção do projeto usar `DEVE`/`NÃO DEVE` em português.
- [x] 4.2 [Integração] Executar o roteiro ponta a ponta: login de Recepção/Triagem, busca de CPF existente e inexistente, cadastro, PATCH real e no-op, abertura da Ficha e tentativa de segunda Ficha ativa; repetir as operações de Paciente proibidas com Médico, Administrador e sem token e inspecionar a auditoria no Xano. Registrar que a autorização de `POST /fichas` continua fora do escopo desta change.
  - Evidência (26/10/2026): validação manual de Xano e Reflex aprovada pelo PO. A autorização de `POST /fichas` permanece fora do escopo desta change.
- [x] 4.3 [Aceite] Reexecutar CA01 com token real, revisar a evidência das tasks 2.2 e 2.3 e verificar que o plano de rollback mantém os endpoints de Paciente autenticados antes de considerar a change pronta para arquivamento.
  - Evidência (26/10/2026): aceite manual aprovado pelo PO; o rollback documentado mantém `auth = "usuario"` e `verificar_acesso`, sem restaurar endpoint público.

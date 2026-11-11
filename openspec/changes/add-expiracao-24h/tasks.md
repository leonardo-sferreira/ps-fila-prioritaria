# Tarefas

Pedido do PO em 10/11/2026: o que não for concluído em 24 horas é encerrado como desistência (fichas em triagem, fichas com senha e tickets do Totem).

Revisão no mesmo dia: o plano gratuito do Xano recusou a tarefa agendada, e o PO decidiu que a dispensa é uma ação do Administrador. Ver `proposal.md` e `design.md` (D1–D6).

## 1. Documentos

- [x] 1.1 Atualizar os documentos-base:
  - `docs/domain-model.md`: estados da ficha, regra do ticket e parâmetro `HORAS_EXPIRACAO`;
  - `docs/project-overview.md`: regra global e permissão do Administrador.

  A dispensa é ação do Administrador, não chamada automática. Verificar com `openspec validate add-expiracao-24h`
  - Evidência (10/11/2026): textos ajustados para a dispensa pelo Administrador; `openspec validate` aceita a change.

## 2. Xano

- [x] 2.1 Em `function/inicializar_parametros_fila.xs`, acrescentar `HORAS_EXPIRACAO` = 24 (D4). Verificar com `xano_validate_xanoscript`
  - Evidência (10/11/2026): `xano_validate_xanoscript` válido.
- [x] 2.2 Criar `function/manutencao/expirou.xs`, pura, com testes inline de valor-limite (D2):
  - 24 h exatas não expiram, 24 h + 1 ms expiram;
  - dentro do prazo não expira;
  - horário vazio não expira;
  - prazo zero não expira;
  - prazo de 1 h.

  Verificar com `xano_validate_xanoscript`
  - Evidência (10/11/2026): 6 testes; `xano_validate_xanoscript` válido.
- [x] 2.3 Reescrever `function/manutencao/expirar_registros.xs` com `aplicar` e `usuario_id` (D3, D5):
  - prévia sem alterar dados;
  - com `aplicar`, `DESISTENCIA` e `registrar_alteracao` em nome do Administrador, numa transação;
  - parâmetro inválido não altera nada.

  Remover `task/expirar_registros.xs`, que o plano do Xano não aceita. Verificar com `xano_validate_xanoscript`
  - Evidência (10/11/2026): função reescrita com prévia e `aplicar` (auditoria por `registrar_alteracao` com o Administrador, numa transação; `USUARIO_OBRIGATORIO` sem usuário). `task/expirar_registros.xs` removido. `xano_validate_xanoscript` válido.

- [x] 2.4 Criar `api/triagem/expiracao_get.xs` (prévia) e `api/triagem/expiracao_post.xs` (dispensa), só para `ADMINISTRADOR`, chamando `inicializar_parametros_fila` antes (D1, D4). Verificar com `xano_validate_xanoscript`
  - Evidência (10/11/2026): `expiracao_get.xs` e `expiracao_post.xs` com `verificar_acesso` para `ADMINISTRADOR`; o POST não recebe IDs da tela. `xano_validate_xanoscript` válido, 0 avisos.

- [ ] 2.5 Publicar na `v1` (`--dry-run` antes; o PO roda o push):
  - `inicializar_parametros_fila`, `expirou`, `expirar_registros` e os dois endpoints;
  - junto, `fichas_get` e `fichas_post` de `add-fichas-do-dia`, que ficaram de fora pela recusa da tarefa.

  Rodar `xano unit_test run_all` e conferir os 6 testes novos.

## 3. Reflex

- [x] 3.1 Criar `estados/expiracao.py` com `ExpiracaoState` (D6): `carregar` (prévia), `dispensar` e `confirmacao_aberta`, e linhas com hora em Brasília e senha ou ticket formatados.

  Em `tests/test_expiracao_state.py`, cobrir:
  - prévia com fichas e tickets;
  - lista vazia;
  - dispensa que envia `POST /expiracao` e recarrega;
  - erro da API mantendo a prévia;
  - sessão expirada (401);
  - perfil recusado (403).

  Verificar que a suíte unitária passa
  - Evidência (10/11/2026): `tests/test_expiracao_state.py` com 8 casos (prévia, lista vazia, dispensa POST→GET, parâmetro inválido, erro mantendo a prévia, sem conexão, 401, 403). A formatação `C/P/N-NNN` foi extraída para `comum.formatar_ticket` e reaproveitada pela fila de pré-triagem. Suíte unitária com 173 passando.

- [x] 3.2 Na área do Administrador (`paginas/areas.py`), trocar o texto "em construção" pelo cartão "Fichas e tickets parados":
  - listas de fichas e tickets;
  - "Dispensar todos", desabilitado sem itens;
  - diálogo de confirmação.

  Carregar a prévia no `on_load` de `/admin`. Verificar que o app compila e abre
  - Evidência (10/11/2026): cartão com listas, "Atualizar", "Dispensar todos" (desabilitado sem itens) e `alert_dialog` de confirmação; prévia no `on_load` de `/admin`. Com `reflex run`, `/admin` sem sessão volta para o login e as páginas abrem sem erro de JS.

## 4. Verificação ponta a ponta

- [ ] 4.1 Roteiro manual:
  - como Administrador, abrir `/admin` e ver a ficha antiga do PO na prévia;
  - dispensar e confirmar;
  - ver o histórico com `EXPIRACAO` em nome do Administrador;
  - como Recepção, ver a ficha em "Fichas do dia" > "Finalizadas", se a chegada foi hoje, e abrir uma nova ficha para o mesmo paciente;
  - conferir que a prévia e a dispensa recusam a Recepção.

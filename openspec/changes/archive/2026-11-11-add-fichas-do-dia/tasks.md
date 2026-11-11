# Tarefas

Pedido do PO em 10/11/2026: ver as fichas já criadas e chegar à ficha aguardando para a reavaliação (RF12). Escolha do PO: aba "Fichas do dia" e atalho na identificação. Ver `proposal.md` e `design.md` (D1–D5).

## 1. Documentos

- [x] 1.1 Atualizar `docs/project-overview.md`:
  - no fluxo item 4 e nas telas da Recepção, dizer que a ficha aguardando é aberta pela aba "Fichas do dia" ou pela identificação;
  - na regra de ficha única, dizer que a identificação oferece "Abrir ficha atual".

  Verificar com `openspec validate add-fichas-do-dia`
  - Evidência (10/11/2026): fluxo item 4 de `docs/project-overview.md` e regra de ficha única em `docs/domain-model.md` atualizados; `openspec validate add-fichas-do-dia` aceita a change.

## 2. Xano

- [x] 2.1 Criar `api/triagem/fichas_get.xs` (D1):
  - autenticado e só para `RECEPCAO_TRIAGEM`;
  - não finalizadas de qualquer data mais as finais com chegada hoje em America/Sao_Paulo, por `chegada_em` decrescente;
  - resposta só com `id`, `status`, `chegada_em`, `senha`, `prioridade_atual`, `especialidade` (nome) e `paciente: {id, nome}`.

  Verificar com `xano_validate_xanoscript`
  - Evidência (10/11/2026): `xano_validate_xanoscript` válido, 0 avisos. Início do dia com `"today"|to_timestamp:"America/Sao_Paulo"`; nome do paciente e da especialidade montados num `foreach`, sem CPF.

- [x] 2.2 Em `api/triagem/fichas_post.xs` (D3), sem ticket, devolver a ficha `AGUARDANDO` ou `CHAMADO` existente com `ja_existente: true`, `status` e `senha`, sem alterar nem auditar. Com ticket, manter a recusa. Verificar com `xano_validate_xanoscript`
  - Evidência (10/11/2026): `xano_validate_xanoscript` válido, 0 avisos. A recusa ficou só para chegada com ticket (`precondition ($input.ticket_id == null)`); a resposta passa a trazer `senha`.

- [x] 2.3 Publicar só os dois arquivos na `v1` (`--dry-run` antes; o PO roda o push) e conferir:
  - `GET fichas` com a Recepção, e a recusa com outro perfil;
  - `POST fichas` para um paciente com ficha aguardando, que deve devolver a mesma ficha sem criar outra.
  - Evidência (11/11/2026): o primeiro push falhou sem aviso (CLI 1.2.0 incompatível com o Node 26: `UND_ERR_INVALID_ARG`); com o CLI 1.3.4, o `--dry-run` mostrou `CREATE query fichas GET` e `UPDATE query fichas POST`, o PO publicou na `v1` e o CLI gravou os guids (commit `a02787e`).

## 3. Reflex

- [x] 3.1 Em `estados/pacientes.py` e `paginas/pacientes.py` (D4):
  - com `ja_existente` e `EM_TRIAGEM`, redirecionar como hoje;
  - com `AGUARDANDO` ou `CHAMADO`, mostrar "Este paciente já está na fila com a senha X" e o botão "Abrir ficha atual".

  Atualizar `tests/test_paciente_state.py` e `tests/test_ficha_abertura_contract.py`. Verificar que a suíte unitária passa
  - Evidência (10/11/2026): o botão "Continuar" vira "Abrir ficha atual" e o aviso fica em âmbar; nova busca descarta o atalho. 4 casos novos em `test_paciente_state.py` (AGUARDANDO e CHAMADO, atalho sem ficha, reset) e contrato atualizado em `test_ficha_abertura_contract.py`.

- [x] 3.2 Criar `estados/fichas_do_dia.py` com `FichasDoDiaState`:
  - `carregar`, `filtro`, `busca` e `fichas_filtradas` (D2), com hora da chegada em Brasília e nome da cor.

  Em `tests/test_fichas_do_dia_state.py`, cobrir:
  - cada filtro, com as finais agrupadas;
  - busca sem acento e sem diferenciar maiúsculas, por nome e por senha;
  - lista vazia;
  - erro da API mantendo a última lista;
  - sessão expirada (401).

  Verificar que a suíte unitária passa
  - Evidência (10/11/2026): `tests/test_fichas_do_dia_state.py` com 7 casos (linhas, filtros, busca, lista vazia, erro e falta de conexão mantendo a lista, 401). Suíte unitária com 165 passando.

- [x] 3.3 Criar `paginas/fichas_do_dia.py`, com a rota `/recepcao/fichas` protegida para `RECEPCAO_TRIAGEM`:
  - tabela com hora, nome, senha, cor, especialidade, situação e "Abrir";
  - filtro, busca e botão "Atualizar";
  - recarga a cada 15 s (D5).

  Incluir a aba "Fichas do dia" em `ABAS_RECEPCAO`. Verificar que `reflex export` compila
  - Evidência (10/11/2026): a aba entra no menu e na área inicial da Recepção. Com `reflex run`, as páginas abrem sem erro de JS e `/recepcao/fichas` sem sessão volta para o login. O `reflex export` compila as páginas, mas a etapa de pré-renderização estoura o tempo em `/` nesta máquina; o commit anterior, que antes passava, falhou do mesmo jeito, então a causa é do ambiente. Confirmar no CI (GitHub Actions).

## 4. Verificação ponta a ponta

- [x] 4.1 Roteiro manual com a Recepção logada:
  - confirmar uma ficha e sair do comprovante;
  - abrir "Fichas do dia", achar a ficha pela senha e abrir;
  - alterar um sinal vital e salvar (reavaliação RF12), e ver a lista refletir a nova cor;
  - identificar o mesmo paciente pelo CPF, ver o aviso com "Abrir ficha atual" e abrir;
  - conferir que nenhuma ficha nova foi criada.
  - Evidência (11/11/2026): roteiro manual feito pelo PO, logado como Recepção: a aba Fichas do dia lista as fichas, a ficha aguardando abre pela senha para reavaliação, e a identificação pelo CPF de paciente já na fila mostra "Abrir ficha atual" sem criar ficha nova.

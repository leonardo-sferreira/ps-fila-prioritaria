# Tarefas

Pedido do PO em 10/11/2026: o que não for concluído em 24 horas é encerrado como desistência. Escolha do PO: fichas em triagem, fichas com senha e tickets do Totem. Ver `proposal.md` e `design.md` (D1–D5).

## 1. Documentos

- [x] 1.1 Atualizar os documentos-base:
  - `docs/domain-model.md`:
    - máquina de estados da ficha (`EM_TRIAGEM` e `AGUARDANDO` → `DESISTENCIA` por expiração);
    - regras e máquina de estados do ticket;
    - tabela de parâmetros com `HORAS_EXPIRACAO` = 24.
  - `docs/project-overview.md`: regras globais, deixando claro que a expiração não é uma chamada automática.

  Verificar com `openspec validate add-expiracao-24h`
  - Evidência (10/11/2026): estados da ficha (EM_TRIAGEM e AGUARDANDO → DESISTÊNCIA por expiração), regra de expiração do ticket e parâmetro `HORAS_EXPIRACAO` em `docs/domain-model.md`; regra global em `docs/project-overview.md`. `openspec validate` aceita a change.

## 2. Xano

- [x] 2.1 Em `function/inicializar_parametros_fila.xs`, acrescentar `HORAS_EXPIRACAO` = 24 (D4). Verificar com `xano_validate_xanoscript`
  - Evidência (10/11/2026): `HORAS_EXPIRACAO` = 24 entra na lista de padrões; `xano_validate_xanoscript` válido.

- [x] 2.2 Criar a regra em duas funções (D1–D3, D5):
  - `function/manutencao/expirou.xs`, pura, com testes inline de valor-limite: 24 h exatas não expiram, 24 h + 1 ms expiram, horário vazio não expira, prazo zero ou negativo não expira;
  - `function/manutencao/expirar_registros.xs`, que lê `HORAS_EXPIRACAO`, consulta só fichas e tickets ativos (as finais não entram), usa `expirou` e encerra com histórico. Não muda `tentativas` do ticket, e com o parâmetro inválido não altera nada.

  Verificar com `xano_validate_xanoscript`
  - Evidência (10/11/2026): `expirou.xs` com 6 testes inline (24 h exatas, 24 h + 1 ms, dentro do prazo, horário vazio, prazo zero, prazo de 1 h) e `expirar_registros.xs` válidos no `xano_validate_xanoscript`, 0 avisos. Os testes rodam no Xano depois do push (`xano unit_test run_all`).

- [x] 2.3 Criar `task/expirar_registros.xs`, a cada 3600 s, chamando a inicialização dos parâmetros e a função (D1). Verificar com `xano_validate_xanoscript`
  - Evidência (10/11/2026): `task/expirar_registros.xs` válido; roda a cada 3600 s a partir de 11/11/2026 00:00 UTC.

- [ ] 2.4 Publicar os três arquivos na `v1` (`--dry-run` antes; o PO roda o push) e rodar a função uma vez pelo CLI. Conferir:
  - a ficha presa do PO foi encerrada;
  - o histórico tem os eventos `EXPIRACAO`;
  - `xano unit_test run_all -b v1` continua sem falhas.

## 3. Verificação ponta a ponta

- [ ] 3.1 Roteiro manual:
  - depois da execução, a ficha antiga aparece em "Fichas do dia" > "Finalizadas" como Desistência, se a chegada foi hoje, ou some da lista, se foi antes;
  - o mesmo paciente consegue abrir uma nova ficha;
  - tickets antigos somem da fila de pré-triagem.

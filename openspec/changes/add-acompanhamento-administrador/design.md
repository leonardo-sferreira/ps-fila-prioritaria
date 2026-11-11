# Design técnico

## Contexto

Os dados já existem: `sessao` (change 1), `historico_alteracao` (change 2), `ficha_atendimento` e `chamada` (changes 4 a 6). Esta change acrescenta o status operacional e três consultas de leitura para o Administrador. Também mexe em dois endpoints existentes: login/logout (change 1) e chamada/comparecimento (change 6).

## Objetivos / Fora dos objetivos

**Objetivos:**
- Uma auditoria consultável num lugar só, sem duplicar dados que já estão em `chamada` e `sessao`.
- Nenhuma escrita a partir da tela do Administrador, que é só de leitura.

**Fora dos objetivos:**
- Retenção e arquivamento de auditoria antiga.

## Decisões

### D1. Status operacional e sessão
Campo `status_operacional` (enum opcional) representa disponibilidade operacional e não autenticação; nulo é o estado inicial indisponível do Médico e não se aplica ao Administrador, enquanto Recepção/Triagem começa DISPONIVEL. Sessão ativa continua determinada por `logout_em` nulo e `expira_em` futuro conforme `add-autenticacao-perfis`. `PATCH me/status` permite que a equipe escolha DISPONIVEL, PAUSA ou AUSENTE. `comparecimento` define EM_ATENDIMENTO e chamada aceita define DISPONIVEL, na mesma transação da operação. Sem status, PAUSA e AUSENTE impedem novas atribuições ao Médico, sem encerrar a sessão nem retirar fichas já atribuídas. O plantão possui estado próprio, separado da sessão/status; seu encerramento só é concluído com fila atribuída zerada.
- **Por quê:** autenticação, disponibilidade e ciclo do plantão são estados distintos; logout/expiração encerram a sessão, não uma pausa operacional.

### D2. Auditoria consolidada por consulta, não por cópia
`GET admin/auditoria` junta três fontes num formato único: `historico_alteracao` (alterações), `chamada` (tipos CHAMADA/COMPARECIMENTO/DESISTENCIA) e `sessao` (LOGIN em `login_em`, LOGOUT em `logout_em`). Ordena por data/hora decrescente, filtra e pagina no Xano.
- **Por quê:** evita gravar o mesmo fato duas vezes (RNF03).
- **Alternativa:** gravar tudo em `historico_alteracao`. Descartada porque duplicaria chamadas e sessões. Se a consulta ficar lenta, a alternativa é uma "view" materializada, sem mudar a spec.
- Assim, o requisito "login registrado na auditoria" é atendido pela leitura de `sessao`, sem mudar o endpoint de login.

### D3. Fila geral reutilizando a ordenação
`GET admin/fila-geral` lista as fichas não finalizadas. Para as AGUARDANDO, a ordem de cada especialidade vem de `prever_fila(especialidade, total)` (change 6), a mesma regra da chamada. O tempo de espera é calculado no backend a partir de `chegada_em`.

### D4. Tela `/admin/acompanhamento`
Três abas ou blocos: "Fila geral" (tabela com cores calculadas da prioridade, filtros e link para o detalhe), "Equipe" (cartões por pessoa com sessão ativa, status operacional e, para Médico, estado do plantão em campos separados) e "Auditoria" (tabela paginada com filtros e valores anterior e novo lado a lado). Polling de 10 s só na aba visível. Detalhe da ficha em `/admin/fichas/{id}` (somente leitura).

### D5. Seletor de status para a equipe
Um componente no cabeçalho de `/recepcao` e `/medico` mostra o status atual e permite trocar entre Disponível, Pausa e Ausente; EM_ATENDIMENTO aparece como texto, não como opção.

### D6. Dashboard do Administrador na tela inicial (decisão do PO em 11/11/2026)
A tela `/admin` passa a abrir com o mesmo painel do plantão da Recepção/Triagem, mais blocos que só o Administrador vê:
- **Reaproveitado da Recepção:** na espera (pré-triagem e fila médica), cores da fila médica, espera mais longa, percurso do dia, fila por especialidade e chegadas por hora. A função `resumir_plantao` é a mesma; no Administrador os cartões do percurso não levam a telas da Recepção.
- **Só do Administrador:**
  - indicadores do dia: atendidas, desistências, canceladas e espera média de quem está na fila médica agora;
  - equipe agora: pessoas com sessão ativa, com perfil e status operacional, e a contagem de médicos por status (Disponível, Em atendimento, Pausa, Ausente, sem status).
- O cartão "Fichas e tickets parados" (expiração de 24 h) continua no fim da tela.
- **Backend:** `GET fichas` e `GET tickets` (grupo Triagem) passam a aceitar também `ADMINISTRADOR`, só leitura. O novo `GET admin/equipe` (grupo Cadastros, só `ADMINISTRADOR`) lista as sessões ativas (`logout_em` nulo e `expira_em` no futuro), a mais recente por usuário, com nome, perfil, status e horário de login. É a parte "equipe" da tarefa 2.2.
- Atualiza sozinho a cada 30 s, como o painel da Recepção.
- **Por quê:** o PO pediu que a tela inicial do Administrador tenha o mesmo dashboard da Recepção, mais detalhado. Indicadores estatísticos, antes fora do escopo, entram só nesse recorte do dia.

### D7. "Visualizar como" Recepção ou Médico (decisão do PO em 11/11/2026)
O Administrador pode abrir as telas da Recepção/Triagem e do Médico só para ver, sem trocar o próprio perfil. A tela mostra uma faixa "Visualizando como …" e as ações ficam desabilitadas; o backend continua recusando ações de quem não é do perfil, então nada muda mesmo que um botão escape. Detalhamento na próxima fatia desta change (seção 6 das tasks).

## Riscos / Compromissos

- [Consulta unificada de auditoria pesada com muitos dados] → Paginação e filtro por período obrigatório no backend (padrão: últimas 24 h).
- [Mudar endpoints de changes anteriores pode quebrar testes existentes] → A tarefa de integração roda a suíte `pytest tests/api` completa.

## Plano de migração

Campo já existente em `sessao`. A migração das sessões médicas ativas que receberam DISPONIVEL automaticamente deixa o status nulo até o Médico escolher DISPONIVEL; não altera PAUSA, AUSENTE ou EM_ATENDIMENTO. Rollback: restaurar o comportamento anterior do login e dos endpoints de status.

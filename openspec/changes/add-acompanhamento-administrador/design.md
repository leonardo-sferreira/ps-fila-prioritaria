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

### D1. Status na `sessao`
Campo `status_operacional` (enum, nulo para ADMINISTRADOR) na sessão aberta mais recente do usuário. `PATCH me/status` altera essa sessão. `comparecimento` define EM_ATENDIMENTO e `chamar-proximo` define DISPONIVEL, na mesma transação da operação. `chamar-proximo` passa a recusar PAUSA/AUSENTE.
- **Por quê:** o status só faz sentido enquanto há sessão; ao sair, some da lista de logados sem precisar de limpeza.

### D2. Auditoria consolidada por consulta, não por cópia
`GET admin/auditoria` junta três fontes num formato único: `historico_alteracao` (alterações), `chamada` (tipos CHAMADA/COMPARECIMENTO/DESISTENCIA) e `sessao` (LOGIN em `login_em`, LOGOUT em `logout_em`). Ordena por data/hora decrescente, filtra e pagina no Xano.
- **Por quê:** evita gravar o mesmo fato duas vezes (RNF03).
- **Alternativa:** gravar tudo em `historico_alteracao`. Descartada porque duplicaria chamadas e sessões. Se a consulta ficar lenta, a alternativa é uma "view" materializada, sem mudar a spec.
- Assim, o requisito "login registrado na auditoria" é atendido pela leitura de `sessao`, sem mudar o endpoint de login.

### D3. Fila geral reutilizando a ordenação
`GET admin/fila-geral` lista as fichas não finalizadas. Para as AGUARDANDO, a ordem de cada especialidade vem de `prever_fila(especialidade, total)` (change 6), a mesma regra da chamada. O tempo de espera é calculado no backend a partir de `chegada_em`.

### D4. Tela `/admin/acompanhamento`
Três abas ou blocos: "Fila geral" (tabela com cores de `cores.py`, filtros e link para o detalhe), "Equipe" (cartões por pessoa com um selo de status) e "Auditoria" (tabela paginada com filtros e valores anterior e novo lado a lado). Polling de 10 s só na aba visível. Detalhe da ficha em `/admin/fichas/{id}` (somente leitura).

### D5. Seletor de status para a equipe
Um componente no cabeçalho de `/recepcao` e `/medico` mostra o status atual e permite trocar entre Disponível, Pausa e Ausente; EM_ATENDIMENTO aparece como texto, não como opção.

## Riscos / Compromissos

- [Consulta unificada de auditoria pesada com muitos dados] → Paginação e filtro por período obrigatório no backend (padrão: últimas 24 h).
- [Mudar endpoints de changes anteriores pode quebrar testes existentes] → A tarefa de integração roda a suíte `pytest tests/api` completa.

## Plano de migração

Campo novo em `sessao` (as sessões existentes ficam com DISPONIVEL para perfis não administradores). Rollback: remover o campo, os endpoints e a página, e voltar `chamar-proximo`/`comparecimento` à versão anterior.

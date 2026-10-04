# Proposta: Sanitização da documentação-base e consolidação das regras do PS Fila Prioritária

| Campo | Valor |
|---|---|
| Change | `sanitize-documentacao-base` |
| Sprint e entrega | Pré-implementação / saneamento documental |
| Fatias no Trello | Documentação e fonte de verdade |
| Dupla | Codex (execução documental) · PO (revisão) |
| Depende de | Nenhuma; executar antes de aplicar as changes funcionais |
| Situação | Pronta para apply |
| RFs afetados | Atualizar a referência-base para RF01–RF50; não renumerar nem inventar RFs nesta change |

## Why

Os documentos-base ainda descrevem decisões que já foram substituídas pelo PO: médico restrito à própria especialidade, totem apenas simulado/externo, prioridade de sintoma armazenada como cor, intervalo de chamada de 10 segundos, desistência automática após três tentativas e ausência de entidade Sala e de cadastro de Recepção/Triagem como entidade de domínio. Também faltam uma matriz global de permissões e máquinas de estado explícitas para Ticket Pré-Triagem e Sessão/Status Operacional.

Enquanto essas divergências permanecerem em `docs/project-overview.md`, `docs/domain-model.md`, `openspec/config.yaml` e `AGENTS.md`, qualquer agente que leia o contexto antes de aplicar uma change pode implementar corretamente uma regra já obsoleta. Esta change existe para sanear a fonte de verdade antes de retomar o desenvolvimento funcional.


## Regra obrigatória de execução no Git

Antes de qualquer alteração, o Codex DEVE trabalhar em uma branch exclusiva desta sanitização.

- Branch obrigatória: `docs/sanitize-documentacao-base`.
- A branch DEVE ser criada a partir da `main` atualizada, sem editar a `main` diretamente.
- Antes de criar/trocar de branch, executar `git status` e NÃO descartar, sobrescrever, fazer stash automático ou alterar mudanças locais preexistentes do usuário.
- Se houver alterações locais que impeçam a troca/criação segura da branch, INTERROMPER a execução e reportar o bloqueio em vez de mexer nessas alterações.
- Depois da troca, confirmar que `git branch --show-current` retorna `docs/sanitize-documentacao-base`.
- Todas as alterações, verificações e commits desta change DEVEM ocorrer exclusivamente nessa branch.
- É PROIBIDO fazer merge, rebase da `main`, push forçado ou alteração direta da `main` durante esta change.

## What Changes

- Consolidar nos documentos-base o fluxo oficial: Totem → fila de Recepção/Triagem → triagem e classificação → fila da especialidade indicada pelos sintomas → distribuição automática para médico elegível → chamada em sala → comparecimento/desistência.
- Colocar o **Totem dentro do escopo do projeto**, com uma change funcional própria futura. O totem gera o ticket e o envia à fila de Recepção/Triagem.
- Consolidar o cadastro administrativo dos perfis:
  - Médico: usuário vinculado, nome, CRM, especialidade de referência, disponibilidade/período e sala atual.
  - Recepção/Triagem: usuário vinculado, nome, CPF e especialidade de referência.
- Manter `usuario` como entidade de autenticação/autorização e documentar `medico` e `recepcao_triagem` como entidades de domínio vinculadas 1:1 ao usuário correspondente.
- Criar conceitualmente a entidade `Sala` e relacioná-la ao Médico para que a chamada pública indique o local do atendimento.
- Registrar que a especialidade cadastrada do médico é **informação profissional de referência e não restringe as filas que ele pode atender**. Um médico elegível pode atender pacientes de qualquer especialidade.
- Manter o direcionamento clínico automático do paciente por especialidade, com base nos sintomas. A especialidade da ficha representa o destino clínico da fila; ela não é trocada apenas porque o médico que atender possui outra especialidade cadastral.
- Substituir `prioridade_padrao` do sintoma por **pontuação numérica de 1 a 3**. Todos os sintomas selecionados somam pontos e entram no escore final juntamente com os pontos dos sinais vitais.
- Preservar a regra de segurança: qualquer item clínico individual com 3 pontos pode elevar a classificação ao nível máximo, conforme a lógica já existente para parâmetros fisiológicos.
- Consolidar a tabela inicial de sintomas, pontuação e especialidade de destino definida no design desta change.
- Consolidar a regra de glicemia baixa:
  - `< 54 mg/dL` com sinais de gravidade = 3 pontos;
  - `< 54 mg/dL` sem sinais de gravidade = 2 pontos;
  - `54–59 mg/dL` com sinais de gravidade = 2 pontos;
  - `54–59 mg/dL` sem sinais de gravidade = 1 ponto.
- Fixar o fuso do projeto em `America/Sao_Paulo`.
- Alterar o intervalo entre chamadas da mesma senha para **30 segundos**.
- Manter até **3 tentativas de chamada por oportunidade**; sem comparecimento, a senha volta ao fim da fila e recebe uma única nova oportunidade. Desistência explícita remove a senha da fila ativa. A mesma regra vale para a fila de Recepção/Triagem e para a fila médica.
- Incluir no fluxo do Médico:
  - **Pausar**: deixa de receber novos atendimentos, sem retirar os já atribuídos;
  - **Encerrar plantão**: só fica disponível quando a fila atribuída ao médico estiver zerada; ao encerrar, o médico deixa de ser elegível para novos atendimentos.
- Adicionar uma matriz global de permissões por perfil.
- Documentar as transições de Ticket Pré-Triagem e de Sessão/Status Operacional, além das transições já existentes da Ficha de Atendimento.
- Atualizar a referência formal da documentação para **RF01–RF50** e remover textos que tratem RF01–RF38 como cobertura atual.
- Atualizar `README.md` e `CONTRIBUTING.md` somente onde repetirem fatos tornados obsoletos pela nova base.
- Atualizar `AGENTS.md` para obrigar agentes a tratar os documentos sanitizados como contexto consolidado do PO e a não reintroduzir decisões antigas.

### Fora do escopo

- Implementar ou alterar XanoScript, tabelas físicas, endpoints, Reflex, testes ou migrations.
- Editar as changes funcionais existentes nesta etapa.
- Criar a implementação do Totem; esta implementação terá change própria.
- Definir algoritmo novo de balanceamento entre médicos elegíveis além das regras aprovadas de disponibilidade, pausa, plantão e fila zerada.
- Renumerar, inventar ou reescrever o conteúdo integral das RFs do documento formal sem a fonte correspondente; nesta change a referência-base é atualizada para RF01–RF50 e as decisões já consolidadas são refletidas nos documentos locais.
- Transformar a modelagem acadêmica em protocolo clínico real. A documentação deve continuar deixando explícita essa limitação.

## Capacidades

### Novas capacidades
- `baseline-documental`: coerência obrigatória entre os documentos-base e as decisões consolidadas do PO.

### Capacidades modificadas
_Nenhuma implementação funcional nesta change._

## Impacto

- **Documentos principais:** `docs/project-overview.md`, `docs/domain-model.md`, `openspec/config.yaml`, `AGENTS.md`.
- **Documentos derivados:** `README.md` e `CONTRIBUTING.md`, apenas para remover contradições factuais.
- **Backend/Reflex:** nenhum arquivo deve ser alterado.
- **Changes existentes:** não são modificadas; ao final, o Codex deve produzir no próprio `tasks.md`/resultado de apply uma lista das changes que precisarão de revisão posterior por conflito com a nova base, especialmente `add-base-compartilhada`, `add-cadastros-administrador`, `add-pacientes-pre-triagem`, `add-triagem-classificacao`, `add-direcionamento-senha`, `add-fila-chamada-medico` e `add-painel-publico`.
- **Nova change futura:** registrar no planejamento a necessidade de `add-totem` (nome final pode ser ajustado quando a change for criada), sem implementá-la aqui.

## Perguntas em aberto

- [x] Sintoma usa cor ou pontuação? **Pontuação numérica de 1 a 3, somada ao escore clínico.** · DECIDIDO PO
- [x] Médico atende apenas a própria especialidade? **Não. A especialidade do médico é cadastral; ele pode atender qualquer fila para a qual esteja elegível.** · DECIDIDO PO
- [x] Totem está no escopo? **Sim, com change funcional própria.** · DECIDIDO PO
- [x] Intervalo entre chamadas? **30 segundos.** · DECIDIDO PO
- [x] Fuso? **America/Sao_Paulo.** · DECIDIDO PO
- [x] Lista inicial de sintomas, pontuação e especialidade? **Definida no design desta change.** · DECIDIDO PO

# Proposta: Acompanhamento do Administrador e status da equipe

| Campo | Valor |
|---|---|
| Change | `add-acompanhamento-administrador` |
| Sprint e entrega | Sprint 4; recorte local de status da Recepção autorizado em 15/11/2026 |
| Fatias no Trello | Acompanhamento do Administrador e status da equipe (escopo informado pelo responsável) |
| Responsável pelo recorte local | Nicolas Rissato Marques |
| Depende de | Todas as changes anteriores |
| Situação | Em revisão; dashboard do Administrador e "visualizar como" aprovados pelo PO em 11/11/2026 |
| RFs novos ou esclarecidos (Confluence, 04/10/2026) | RF44 (status da equipe); RF45 (fila geral e auditoria) |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/`. Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

Depois do feedback do professor, o Administrador ganhou uma tela de acompanhamento com três blocos: fila geral, pessoas logadas e seus status, e auditoria (Figma de 26–27/09/2026). Com o fluxo completo funcionando (changes 1 a 7), falta dar ao Administrador essa visão consolidada do plantão e deixar a trilha de auditoria consultável (RNF07).

## What Changes

- **Status operacional da equipe:** Recepção/Triagem e Médico informam o próprio status (Disponível, Pausa, Ausente). O status "Em atendimento" é definido automaticamente para o médico quando ele confirma um comparecimento. Médico em Pausa ou Ausente não recebe novas atribuições, mas mantém as fichas sob sua responsabilidade. O Médico pode solicitar encerramento do plantão, concluído somente com fila atribuída zerada.
- **Fila geral:** visão interna de todas as fichas não finalizadas (EM_TRIAGEM, AGUARDANDO, CHAMADO) com senha, cor, condição prioritária, especialidade, tempo de espera e status, com filtros (RF22, visão geral da seção 3).
- **Pessoas logadas e status:** usuários com sessão ativa, com perfil, status operacional e horário de login; o plantão do Médico é mostrado separadamente do status e da sessão.
- **Auditoria:** consulta das últimas alterações (prioridade, sintomas, disponibilidade, cadastros, chamadas, logins) com responsável, data/hora, valores e justificativa, com filtros (RF37, RNF07).
- **Detalhe da ficha para o Administrador**, somente leitura, com o histórico da ficha.

- **Dashboard do Administrador** na tela inicial: o painel do plantão da Recepção/Triagem, com indicadores do dia e a equipe logada (D6).
- **"Visualizar como"**: o Administrador vê as telas da Recepção/Triagem e do Médico sem poder agir (D7).

### Fora do escopo

- Qualquer ação corretiva pelo Administrador na fila (cancelar, redirecionar ficha a ficha, trocar médico): a tela é de acompanhamento.
- Exportação de relatórios (PDF/CSV) e indicadores estatísticos além do recorte do dia no dashboard (D6).
- Encerrar a sessão de outro usuário pela tela (a desativação do usuário já cobre isso, na change 1).

## Capacidades

### Novas capacidades
- `status-equipe`: status operacional de Recepção/Triagem e Médico durante a sessão.
- `acompanhamento-administrador`: fila geral, pessoas logadas e consulta da auditoria.

### Capacidades modificadas
Altera o comportamento de `autenticacao` (`add-autenticacao-perfis`: status na sessão) e de `chamada-paciente` (`add-fila-chamada-medico`: `chamar-proximo` recusa PAUSA e AUSENTE; `comparecimento` define EM_ATENDIMENTO). Declarar como deltas `MODIFIED`.

As specs consolidadas já estão disponíveis em `openspec/specs/`. Os deltas `MODIFIED` devem referenciar requisitos existentes nas respectivas specs; conferir a base consolidada antes de sincronizar ou arquivar esta change.

## Impacto

- **Xano:** campo `status_operacional` em `sessao`; endpoints `PATCH me/status`, `GET admin/fila-geral`, `GET admin/equipe` e `GET admin/auditoria` (ADMINISTRADOR); gancho no `comparecimento` (change 6) para EM_ATENDIMENTO; verificação de status no `chamar-proximo`; registro de login e logout na auditoria.
- **Reflex:** seletor de status no cabeçalho das áreas de Recepção/Triagem e Médico; página `/admin/acompanhamento` com os três blocos; detalhe somente leitura da ficha.
- **Testes:** `tests/api/test_status_equipe.py` e `tests/api/test_acompanhamento.py`.
- **Depende de:** todas as changes anteriores.
- **Divergência com o documento formal:** o documento v1.0 só prevê "consultar visão geral e histórico". Os blocos "pessoas logadas e status" e o status operacional vêm do contexto do PO e ainda não estão no Confluence.

## Recorte desta entrega — Sprint 4

Preparar o GET me/status da própria sessão e concluir o seletor de status da Recepção/Triagem, reutilizando PATCH me/status e os estados manuais já existentes. Acrescentar testes simulados e estáticos das permissões e das transições médicas existentes, sem alterar as regras da fila. Dashboard e auditoria administrativos já entregues são preservados. Publicação do novo GET, validação visual e operações reais dependem de autorização posterior; abrir o PR não publica o endpoint.

## Perguntas em aberto

- [x] Alocação do recorte local na Sprint 4 confirmada pelo responsável em 15/11/2026. Fila geral, detalhe da ficha e demais itens permanecem nas tarefas próprias, sem declaração de conclusão.
- [ ] O campo `status_operacional` já existe em `sessao` (`backend/xano/table/sessao.xs`); as tasks de criar o campo viram conferência. · dupla da fatia

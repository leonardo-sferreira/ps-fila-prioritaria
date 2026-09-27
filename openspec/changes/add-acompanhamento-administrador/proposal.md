# Proposta

## Por quê

Depois do feedback do professor, o Administrador ganhou uma tela de acompanhamento com três blocos: fila geral, pessoas logadas e seus status, e auditoria (Figma de 26–27/09/2026). Com o fluxo completo funcionando (changes 1 a 7), falta dar ao Administrador essa visão consolidada do plantão e deixar a trilha de auditoria consultável (RNF07).

## O que muda

- **Status operacional da equipe:** Recepção/Triagem e Médico informam o próprio status (Disponível, Pausa, Ausente). O status "Em atendimento" é definido automaticamente para o médico quando ele confirma um comparecimento. Médico em Pausa ou Ausente não chama pacientes.
- **Fila geral:** visão interna de todas as fichas não finalizadas (EM_TRIAGEM, AGUARDANDO, CHAMADO) com senha, cor, condição prioritária, especialidade, tempo de espera e status, com filtros (RF22, visão geral da seção 3).
- **Pessoas logadas e status:** usuários com sessão ativa, com perfil, status operacional e horário de login.
- **Auditoria:** consulta das últimas alterações (prioridade, sintomas, disponibilidade, cadastros, chamadas, logins) com responsável, data/hora, valores e justificativa, com filtros (RF37, RNF07).
- **Detalhe da ficha para o Administrador**, somente leitura, com o histórico da ficha.

### Fora do escopo

- Qualquer ação corretiva pelo Administrador na fila (cancelar, redirecionar ficha a ficha, trocar médico): a tela é de acompanhamento.
- Exportação de relatórios (PDF/CSV) e indicadores estatísticos (tempo médio de espera etc.).
- Encerrar a sessão de outro usuário pela tela (a desativação do usuário já cobre isso, na change 1).

## Capacidades

### Novas capacidades
- `status-equipe`: status operacional de Recepção/Triagem e Médico durante a sessão.
- `acompanhamento-administrador`: fila geral, pessoas logadas e consulta da auditoria.

### Capacidades modificadas
_Nenhuma._

## Impacto

- **Xano:** campo `status_operacional` em `sessao`; endpoints `PATCH me/status`, `GET admin/fila-geral`, `GET admin/equipe` e `GET admin/auditoria` (ADMINISTRADOR); gancho no `comparecimento` (change 6) para EM_ATENDIMENTO; verificação de status no `chamar-proximo`; registro de login e logout na auditoria.
- **Reflex:** seletor de status no cabeçalho das áreas de Recepção/Triagem e Médico; página `/admin/acompanhamento` com os três blocos; detalhe somente leitura da ficha.
- **Testes:** `tests/api/test_status_equipe.py` e `tests/api/test_acompanhamento.py`.
- **Depende de:** todas as changes anteriores.
- **Divergência com o documento formal:** o documento v1.0 só prevê "consultar visão geral e histórico". Os blocos "pessoas logadas e status" e o status operacional vêm do contexto do PO e ainda não estão no Confluence.

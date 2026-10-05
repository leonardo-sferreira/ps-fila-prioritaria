# Proposta: Cadastros do Administrador, parâmetros e auditoria

| Campo | Valor |
|---|---|
| Change | `add-cadastros-administrador` |
| Sprint e entrega | Sprint 3, segunda 19/10 (médicos, especialidades e disponibilidade). Sintomas, parâmetros e auditoria sem card |
| Fatias no Trello | Fatia 5 — Administrador |
| Dupla | Leonardo Machado (API e dados) · Nicolas (tela) |
| Depende de | `add-autenticacao-perfis` (usuários, perfis e `verificar_acesso`) |
| Situação | Em revisão |
| Rastreabilidade formal | RF13–RF16 e RF49 quando aplicáveis; decisões de domínio detalhadas na baseline local até a sincronização do Confluence, sem atribuir texto não confirmado a RFs |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/`. Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

A classificação, o direcionamento e a chamada de pacientes dependem de dados que só o Administrador mantém: especialidades, catálogo de sintomas pontuados e seus destinos, cadastros de Médico e Recepção/Triagem vinculados aos respectivos usuários, salas, disponibilidade por período e parâmetros. A especialidade de referência do Médico é cadastral e não restringe as filas que pode atender. Esta change também cria a trilha de auditoria, que as próximas changes vão usar.

## What Changes

- **Especialidades:** cadastro (nome, descrição, sigla de 3 letras usada na senha, situação); sem alternativas usadas como fallback por disponibilidade ou especialidade cadastral do Médico.
- **Sintomas:** cadastro (nome, descrição, grupo, pontuação de 1 a 3, situação) e relação ordenada sintoma → especialidade(s), segundo o catálogo de `docs/domain-model.md`.
- **Médicos:** entidade própria vinculada 1:1 a um usuário, com nome profissional, CRM, especialidade de referência informativa, disponibilidade e sala atual. A especialidade não restringe atendimento.
- **Recepção/Triagem:** perfil funcional único e entidade própria vinculada 1:1 ao usuário, com nome, CPF e especialidade de referência quando aplicável.
- **Salas:** cadastro administrativo e vínculo operacional com Médico, sem usar especialidade como sinônimo de local.
- **Disponibilidade:** o Administrador registra, altera e remove períodos (data, hora inicial, hora final) de cada médico; o médico não altera a própria disponibilidade (RF15, RN15, RN16, UC06).
- **Parâmetros de regra:** tela para consultar e alterar somente parâmetros configuráveis previstos. As chamadas seguem 30 segundos, até 3 tentativas por oportunidade e uma reentrada; o fuso `America/Sao_Paulo` não é editável nesta tela.
- **Auditoria:** registro imutável de alterações relevantes (tipo, registro afetado, valor anterior, valor novo, usuário, data/hora, justificativa). Nesta change ele passa a registrar alterações de disponibilidade, sintomas, especialidades e parâmetros (RF37, RNF07).
- Carga inicial de dados de exemplo (especialidades e sintomas da seção 6 do documento formal) para permitir testes.

### Fora do escopo

- Faixas de pontuação dos sinais vitais e limiares de risco: ficam em `add-triagem-classificacao`, junto com o cálculo que os usa.
- Redistribuição de pacientes quando um médico fica indisponível: fica em `add-direcionamento-senha`.
- Tela de consulta da auditoria pelo Administrador: fica em `add-acompanhamento-administrador`. Nesta change a auditoria só é gravada e verificada por testes.
- Exclusão física de registros: cadastros são desativados, nunca excluídos.
- Qualquer funcionalidade de paciente, ficha ou fila.

## Capacidades

### Novas capacidades
- `especialidades`: cadastro de especialidades e siglas.
- `sintomas`: cadastro de sintomas, pontuação e relação de direcionamento com especialidades.
- `medicos-disponibilidade`: cadastros de Médico, Recepção/Triagem e Sala; vínculos 1:1 com Usuário; disponibilidade por período e especialidade de referência não restritiva.
- `parametros-regras`: parâmetros operacionais configuráveis pelo Administrador.
- `auditoria`: registro imutável de alterações relevantes.

### Capacidades modificadas
_Nenhuma._

## Impacto

- **Xano:** contratos conceituais de especialidade, sintoma, Médico, Recepção/Triagem, Sala, disponibilidade, parâmetros e auditoria. O schema físico será definido pela implementação funcional; esta etapa não altera `.xs`.
- **Reflex:** telas em `/admin/especialidades`, `/admin/sintomas`, `/admin/medicos`, `/admin/disponibilidade` e `/admin/parametros`.
- **Testes:** `tests/api/test_cadastros.py`, `test_disponibilidade.py`, `test_parametros.py` e `test_auditoria.py`.
- **Depende de:** `add-autenticacao-perfis` (usuários, perfis e `verificar_acesso`).
- A baseline sanitizada orienta os conceitos: Médico e Recepção/Triagem são entidades próprias 1:1 com Usuário, Sala é entidade própria, e a especialidade do Médico é cadastral. Eventuais diferenças do schema físico devem ser tratadas na implementação, não nesta revisão documental.

## Perguntas em aberto

- [x] Antecipar para a Sprint 1 `historico_alteracao`, `registrar_alteracao`, `FUSO_HORARIO`, `obter_parametro` e a carga inicial de sintomas: decidido pelo PO em 04/10/2026, na change `add-base-compartilhada`. Falta aplicar `/opsx:update` aqui para remover os itens que passaram para a base. · PO
- [ ] Sintomas, parâmetros e a consulta da auditoria não têm card; o card da Fatia 5 cobre só médicos, especialidades e disponibilidade. · PENDENTE PO
- [x] Catálogo, grupos, pontuações e destinos seguem `docs/domain-model.md`; prioridade por cor e glicemia pendente foram substituídas pela baseline sanitizada.

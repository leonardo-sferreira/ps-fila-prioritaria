# Proposta: Base compartilhada (auditoria, fuso, parâmetros e dados de referência)

| Campo | Valor |
|---|---|
| Change | `add-base-compartilhada` |
| Sprint e entrega | Sprint 1, segunda 05/10 (dentro do card [Setup]) |
| Fatias no Trello | [Setup] Base técnica |
| Dupla | Leonardo Machado (API e dados) · sem tela |
| Depende de | `add-autenticacao-perfis` (`usuario` e `verificar_acesso`) |
| Situação | Em revisão (Sprint 1 confirmada pelo PO em 04/10/2026) |
| RFs novos ou esclarecidos (Confluence, 04/10/2026) | RF37 (auditoria); RF49 (consulta dos parâmetros); RF16 (carga inicial e consulta de sintomas e especialidades) |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/` (19 tabelas). Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

As Fatias 2 a 4 (Sprints 1 e 2: cadastro de paciente, ficha, sintomas e prioridade) dependem de auditoria, fuso horário, parâmetros e sintomas cadastrados. Hoje tudo isso só nasce na `add-cadastros-administrador`, que é da Sprint 3. Antecipar essa base, sem tela, evita que as primeiras fatias fiquem bloqueadas ou sejam entregues sem auditoria.

## What Changes

- **Auditoria:** uso da tabela `historico_alteracao` pela função reutilizável `registrar_alteracao`, gravada na mesma transação da operação. O registro é imutável e não existe endpoint de escrita (RF37, RNF07).
- **Fuso horário:** variável de ambiente `FUSO_HORARIO` (`America/Sao_Paulo`) no Xano, usada para calcular "o dia" do PS (numeração de tickets e senhas, disponibilidade).
- **Parâmetros:** uso da tabela `parametro` pela função `obter_parametro`, com valores iniciais de idade de idoso e de criança, ciclo de chamada, tamanho da previsão e especialidade padrão, quando aplicável. Intervalo de 30 segundos, até 3 chamadas por oportunidade e uma reentrada são invariantes da baseline, não parâmetros editáveis. Inclui a consulta dos parâmetros por usuário autenticado (RNF09, seção 22.1 do documento formal).
- **Dados de referência:** carga inicial idempotente das especialidades (CLI, CAR, ORT, NEU, PED) e do catálogo de sintomas consolidado em `docs/domain-model.md`, com pontuação numérica de 1 a 3 e relações de direcionamento. Não há prioridade em cor no sintoma nem fallback por disponibilidade/especialidade do Médico. Inclui consulta, por usuário autenticado, das especialidades e dos sintomas ativos.

### Fora do escopo

- Telas administrativas de qualquer tipo, incluindo a de parâmetros.
- Alteração de parâmetros (`PATCH parametros/{chave}`): continua em `add-cadastros-administrador`.
- Consulta da auditoria pelo Administrador: `add-acompanhamento-administrador`.
- CRUD de especialidades, sintomas e médicos, disponibilidade e `medicos_disponiveis`: `add-cadastros-administrador`.
- Faixas de risco dos sinais vitais e limiares de risco: `add-triagem-classificacao`.

## Capacidades

### Novas capacidades
- `auditoria`: conteúdo, atomicidade e imutabilidade do registro de auditoria.
- `parametros-regras`: parâmetros com valores iniciais e consulta por usuário autenticado. A alteração pelo Administrador é acrescentada depois por `add-cadastros-administrador`.
- `dados-referencia`: carga inicial idempotente e consulta das especialidades e dos sintomas ativos.

### Capacidades modificadas
_Nenhuma (não existem specs arquivadas)._

## Impacto

- **Xano:** funções `registrar_alteracao`, `obter_parametro` e `carga_inicial`; variável `FUSO_HORARIO`; endpoints `GET parametros`, `GET especialidades` e `GET sintomas` (autenticados, só registros ativos) e `POST admin/carga-inicial` (ADMINISTRADOR). Tabelas usadas, já publicadas: `historico_alteracao`, `parametro`, `especialidade`, `especialidade_alternativa`, `sintoma` e `sintoma_especialidade`.
- **Reflex:** nenhum impacto.
- **Testes:** `tests/api/test_auditoria.py`, `tests/api/test_parametros.py` e `tests/api/test_dados_referencia.py`.
- **Outras changes:** a `add-cadastros-administrador` perde os itens trazidos para cá (seção 1 das tasks, task 2.3, a variável da task 3.2, o spec `auditoria`, o requisito de valores iniciais de `parametros-regras` e o de carga inicial de `sintomas`). O "Depende de" das changes `add-pacientes-pre-triagem`, `add-triagem-classificacao` e `add-direcionamento-senha` passa a apontar para esta change. Esses ajustes serão feitos com `/opsx:update` em cada change; esta proposta não os altera.
- **Arquivamento:** arquivar esta change logo depois de `add-autenticacao-perfis`, antes de `add-cadastros-administrador`, para que a `add-cadastros-administrador` acrescente requisitos às specs `auditoria` e `parametros-regras` já existentes.
- **Rastreabilidade (documento formal v1.0):** RF37, RNF07 e RNF09; seção 6 (sintomas de exemplo) e seção 22.1 (parâmetros).

## Perguntas em aberto

- [x] A base cabe na Sprint 1, junto com o [Setup] e a Fatia 1: decidido pelo PO em 04/10/2026. · DECIDIDO PO
- [ ] A consulta de especialidades e sintomas ativos foi incluída aqui porque a triagem (Sprint 2) precisa dela. Confirmar. · PENDENTE PO
- [x] Catálogo de sintomas, grupos, pontuações e destinos seguem a baseline consolidada em `docs/domain-model.md`; não há prioridade por cor. · BASELINE
- [ ] Aplicar `/opsx:update` na `add-cadastros-administrador` (remover os itens trazidos para cá) e no "Depende de" das changes 3, 4 e 5. · PO

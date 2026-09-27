# Sistema de Fila Prioritária para Pronto-Socorro

Projeto acadêmico (Impacta) de um sistema que organiza a entrada e a chamada de pacientes em um pronto-socorro, priorizando pela gravidade clínica (sintomas + sinais vitais) e não só pela ordem de chegada.

> As regras de sintomas, prioridade e fator de risco são modelagem acadêmica e **não** têm valor de protocolo clínico.

## Links do projeto

| O quê | Onde |
|---|---|
| Protótipo de telas (Figma) | [PS — Fila de Atendimento — Protótipo de Fluxos](https://www.figma.com/design/38ro8aKQfiGkUivIfCaOR1) |
| Fluxogramas, regras e modelo de dados (FigJam) | [Fluxo do Sistema PS — Paciente e Equipe](https://www.figma.com/board/qwAbdFLbo9lRuOym4vDSBI) |
| Requisitos formais (Confluence) | [Documento de Requisitos e Regras de Negócio (v1.0 — formal)](https://aluno-team-c3b9u3it.atlassian.net/wiki/spaces/PE/pages/56459266) |
| Kanban | Trello — board "Projeto PS — Fila de Atendimento por Urgência" |
| Backend e banco | Xano — workspace "ps-impacta Workspace" (peça acesso ao PO) |

## A ideia do projeto (briefing do professor)

O professor apresentou o projeto como uma "carta do cliente": um pronto atendimento fictício organiza a fila manualmente, por ordem de chegada, e pacientes graves esperam o mesmo tempo que pacientes leves. O cliente pediu um sistema que ajude a recepção a decidir **quem deve ser atendido primeiro**.

- **Regras de partida (incompletas de propósito):** cada paciente informa um ou mais sintomas; cada sintoma tem um nível de gravidade; os pacientes aguardam numa fila até serem chamados; a recepção pode reavaliar a gravidade enquanto o paciente espera.
- **O que ficou para a equipe descobrir** na entrevista de requisitos: como combinar vários sintomas, desempate, peso do tempo de espera, "prioridade legal" (idosos, gestantes, crianças), rebaixamento de prioridade, fila vazia ou cheia, e o que mostrar para a equipe e para o paciente.
- **Entregáveis da Fase 1:** documento de requisitos (funcionais e não funcionais), 1 a 2 personas, 2 a 3 casos de uso e a lista de perguntas em aberto com as suposições da equipe.
- **Uso de IA:** liberado para código, testes e documentação. A **sessão de levantamento de requisitos com o professor é feita sem IA**.
- **Banco de dados:** o briefing sugeria dados em memória. O professor deixou isso em aberto, e a equipe definiu com ele o uso do **Xano** como backend e banco de dados.
- **Critérios de avaliação:** qualidade das perguntas na sessão de requisitos, coerência entre requisitos e solução, justificativa das decisões nos pontos ambíguos, qualidade do código Python e documentação.

As respostas que a equipe deu a essas perguntas estão no documento formal do Confluence e em [docs/project-overview.md](docs/project-overview.md).

## Como o sistema funciona (resumo)

```
Totem (ticket) → Fila pré-triagem → Recepção/Triagem → Fila priorizada (por especialidade) → Médico
```

1. O paciente retira um **ticket numérico** no totem (externo; nesta fase existe só um simulador).
2. A **Recepção/Triagem** chama o ticket, identifica o paciente pelo **CPF**, abre a **ficha** e registra sintomas e **sinais vitais** (PA, FC, FR, temperatura, SpO2, glicemia).
3. O sistema calcula a **cor** (Vermelha, Amarela ou Azul): a mais grave entre o sintoma e o **fator de risco** (escore 0–18, NEWS2/MEWS + glicemia). Idosos, crianças e gestantes passam na frente **dentro da mesma cor**.
4. O sistema escolhe a **especialidade** (com fallback para alternativas que tenham médico disponível) e gera a senha `COR-ESP-NNN` (ex.: `V-CLI-003`).
5. O **médico** aciona "Chamar próximo" e o sistema escolhe a ficha: vermelhos primeiro; sem vermelhos, ciclo **2 amarelas : 1 azul**; depois prioritários; depois ordem de chegada. São até **3 tentativas** antes da desistência.
6. O **painel público** mostra a senha chamada e a previsão das próximas 5, sem nome nem CPF.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | [Reflex](https://reflex.dev) (Python) |
| Backend e banco de dados | [Xano](https://www.xano.com) (XanoScript) |
| Especificação | [OpenSpec](https://github.com/Fission-AI/OpenSpec) (spec-driven) |
| Testes de API | pytest + httpx |

Regras de negócio, persistência e autorização ficam **no Xano**. O Reflex só apresenta e envia dados.

## Estrutura do repositório

```
AGENTS.md / CLAUDE.md     regras para agentes de IA (Claude Code e outros)
docs/
  project-overview.md     visão geral, escopo, regras, divergências conhecidas
  domain-model.md         modelo de domínio (entidades, estados, parâmetros)
openspec/
  config.yaml             contexto e regras usados pelo OpenSpec
  changes/                as 8 changes planejadas (proposal, specs, design, tasks)
  specs/                  comportamento consolidado (preenchido no archive)
backend/xano/table/       as 19 tabelas do banco em XanoScript (já criadas no Xano)
.claude/                  comandos /opsx:* e skills do OpenSpec para o Claude Code
```

## Ordem de implementação (changes do OpenSpec)

| # | Change | Entrega |
|---|---|---|
| 1 | `add-autenticacao-perfis` | Login, perfis e gestão de usuários |
| 2 | `add-cadastros-administrador` | Especialidades, sintomas, médicos, disponibilidade, parâmetros, auditoria |
| 3 | `add-pacientes-pre-triagem` | Simulador de totem, fila pré-triagem, pacientes por CPF |
| 4 | `add-triagem-classificacao` | Ficha, sinais vitais, fator de risco, cor e ajuste manual |
| 5 | `add-direcionamento-senha` | Especialidade sugerida/atribuída, senha e comprovante |
| 6 | `add-fila-chamada-medico` | Ciclo 2:1, chamar próximo, tentativas, desistência |
| 7 | `add-painel-publico` | Painel sem dados pessoais e previsão das próximas 5 |
| 8 | `add-acompanhamento-administrador` | Fila geral, equipe logada (status) e auditoria |

Cada change tem `proposal.md` (por quê e o quê), `specs/` (requisitos com cenários), `design.md` (como) e `tasks.md` (checklist, separando Xano e Reflex). **Implemente só o que está no `tasks.md` da change.** Decisões novas voltam para a change antes de virar código.

## Como começar em casa

### 1. Ferramentas

```bash
# Node.js 20+ e Python 3.12+
npm install -g @fission-ai/openspec @xano/cli
```

### 2. Clonar e ler o contexto

```bash
git clone https://github.com/leonardo-sferreira/ps-fila-prioritaria.git
cd ps-fila-prioritaria
```

Leia, nesta ordem: `docs/project-overview.md`, `docs/domain-model.md`, `AGENTS.md` e a change em que você vai trabalhar em `openspec/changes/`.

### 3. Acessar o Xano

1. Peça ao PO acesso ao workspace **ps-impacta Workspace**.
2. Crie um perfil do CLI para este projeto (não sobrescreve perfis de outros projetos):
   ```bash
   xano auth -p ps-impacta
   xano profile use ps-impacta   # fixa o perfil só nesta pasta (o profile.yaml não é versionado)
   xano profile me               # confira conta e workspace
   ```
3. Trabalhe na **sua própria branch do Xano**, criada a partir da `v1`:
   ```bash
   xano branch create <seu-nome> -s v1
   ```
   As tabelas já existem e são compartilhadas. **Não altere tabelas pela sua branch**: mudanças de schema passam pelo PO, editando `backend/xano/table/*.xs` e fazendo `xano workspace push`.

### 4. Fluxo de trabalho no Git

```bash
git checkout -b <nome-da-change>      # ex.: add-autenticacao-perfis
# implemente as tasks, marcando [x] no tasks.md
git push -u origin <nome-da-change>   # abra um Pull Request para a main
```

Com o Claude Code, use `/opsx:apply <change>` para implementar e `/opsx:archive <change>` quando a change estiver concluída e revisada.

## Regras importantes

- Autorização por perfil é feita **no backend**. Esconder botão no frontend não é segurança.
- O painel público **nunca** mostra CPF nem nome.
- Parâmetros clínicos (faixas de risco, limiares, ciclo 2:1, tentativas, idades) ficam **configuráveis no banco**, não fixos no código.
- **Nunca** versione credenciais, tokens ou URLs privadas do Xano. Use `.env` (ignorado pelo Git).
- Documentação e artefatos em **português**. Veja [AGENTS.md](AGENTS.md).

## Equipe

| Integrante | Papel |
|---|---|
| Leonardo dos Santos Ferreira | Product Owner, documentação e regras de negócio, protótipo e banco (Xano) |
| Leonardo Machado | Backend |
| Luisa | Backend |
| Nicolas | Frontend |
| Gustavo Garcia | Frontend |

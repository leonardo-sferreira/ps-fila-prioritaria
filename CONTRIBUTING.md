# Guia de contribuição

Guia interno da equipe para configurar o ambiente e implementar as funcionalidades.

## Ferramentas

- Node.js 20+ e Python 3.12+
- OpenSpec e Xano CLI:

```bash
npm install -g @fission-ai/openspec @xano/cli
```

## Primeiros passos

```bash
git clone https://github.com/leonardo-sferreira/ps-fila-prioritaria.git
cd ps-fila-prioritaria
```

Leia, nesta ordem: [docs/project-overview.md](docs/project-overview.md), [docs/domain-model.md](docs/domain-model.md), [AGENTS.md](AGENTS.md) e a change em que você vai trabalhar, em `openspec/changes/`.

## Acesso ao Xano

1. Peça ao PO acesso ao workspace **ps-impacta Workspace**.
2. Crie um perfil do CLI só para este projeto. Ele não sobrescreve os perfis de outros projetos:
   ```bash
   xano auth -p ps-impacta
   xano profile use ps-impacta   # fixa o perfil nesta pasta (profile.yaml não é versionado)
   xano profile me               # confira a conta e o workspace
   ```
3. Trabalhe na **sua própria branch do Xano**, criada a partir da `v1`:
   ```bash
   xano branch create <seu-nome> -s v1
   ```

As tabelas já existem e são compartilhadas entre as branches. **Não altere tabelas pela sua branch.** Mudanças de schema passam pelo PO: ele edita `backend/xano/table/*.xs` e faz o `xano workspace push`.

## Changes do OpenSpec

| # | Change | Entrega | Sprint (Trello) |
|---|---|---|---|
| 1 | `add-autenticacao-perfis` | Login, perfis e gestão de usuários | 1 (login); gestão de usuários sem card |
| 1b | `add-base-compartilhada` | Auditoria, fuso, parâmetros e carga de especialidades e sintomas (sem tela) | 1 ([Setup]) |
| 2 | `add-cadastros-administrador` | Especialidades, sintomas, médicos, disponibilidade, parâmetros e auditoria | 3 (médicos, especialidades, disponibilidade); o resto sem card |
| 3 | `add-pacientes-pre-triagem` | Simulador de totem, fila pré-triagem e pacientes por CPF | 1 (pacientes); pré-triagem sem card |
| 4 | `add-triagem-classificacao` | Ficha, sinais vitais, fator de risco, cor e ajuste manual | 2 |
| 5 | `add-direcionamento-senha` | Especialidade sugerida e atribuída, senha e comprovante | 3 |
| 6 | `add-fila-chamada-medico` | Ciclo 2:1, chamar próximo, tentativas e desistência | 4 |
| 7 | `add-painel-publico` | Painel sem dados pessoais e previsão das próximas 5 | 5 |
| 8 | `add-acompanhamento-administrador` | Fila geral, equipe logada (status) e auditoria | sem card |

Cada change tem `proposal.md` (por quê e o quê), `specs/` (requisitos com cenários), `design.md` (como) e `tasks.md` (checklist, com Xano e Reflex separados). **Implemente só o que está no `tasks.md`.** Se surgir uma decisão nova, registre na change antes de virar código.

## Fluxo no Git

A `main` só recebe código por Pull Request, com 1 aprovação. Ninguém dá push direto nela. O Xano tem as próprias branches (seção "Acesso ao Xano"); elas não têm relação com as do Git.

```bash
# 1. partir da main atualizada
git switch main
git pull origin main

# 2. criar a sua branch (uma por pessoa e por tarefa)
git switch -c feat/fatia-1-login-api

# 3. trabalhar, conferir e commitar só o que mudou
git status
git diff
git add <arquivos>
git commit -m "feat(login): implementa POST auth/login"

# 4. trazer a main para a sua branch antes de enviar
git fetch origin
git rebase origin/main

# 5. enviar (a primeira vez usa -u)
git push -u origin feat/fatia-1-login-api
```

Depois, no GitHub: **Compare & pull request**, base `main`, descrição com a change, o card do Trello e como testar, e um revisor marcado. O merge é **Squash and merge**. Em seguida: `git switch main`, `git pull origin main` e `git branch -d <sua-branch>`.

**Nome da branch:** `tipo/fatia-N-descrição`, com tipo `feat`, `fix`, `docs`, `test` ou `chore` (ex.: `feat/fatia-2-paciente-tela`, `docs/revisao-openspec`). Cada pessoa trabalha na sua branch; a dupla de uma fatia usa `-api` e `-tela`, não a mesma.
**Commit:** `tipo(escopo): o que mudou`, em português e no imperativo.

Regras: não use `git push --force` na `main`; não use `git add .` sem olhar o `git status`; nunca faça commit de `.env`. Clone o projeto fora do OneDrive (ex.: `C:\dev`).

Antes de abrir o Pull Request de uma change, rode `openspec validate --all`. O comando `--strict` mostra avisos de `SHALL`/`MUST`, porque os requisitos são escritos com "DEVE"; esses avisos são esperados e podem ser ignorados.

## Usando IA com o OpenSpec

As regras do projeto ficam no [AGENTS.md](AGENTS.md). O Codex lê esse arquivo direto; o Claude Code e o Gemini o leem por meio de `CLAUDE.md` e `GEMINI.md`, que só importam o `AGENTS.md`. Edite sempre o `AGENTS.md`, nunca os outros dois.

| Ação | Claude Code | Gemini CLI | Codex |
|---|---|---|---|
| Explorar uma ideia | `/opsx:explore` | `/opsx:explore` | `$openspec-explore` |
| Propor uma change | `/opsx:propose <ideia>` | `/opsx:propose <ideia>` | `$openspec-propose <ideia>` |
| Implementar | `/opsx:apply <change>` | `/opsx:apply <change>` | `$openspec-apply-change <change>` |
| Revisar uma change | `/opsx:update <change>` | `/opsx:update <change>` | `$openspec-update-change <change>` |
| Arquivar | `/opsx:archive <change>` | `/opsx:archive <change>` | `$openspec-archive-change <change>` |
| Pasta dos fluxos | `.claude/` | `.gemini/` | `.agents/skills/` |

No app desktop do Codex, as skills aparecem em **Skills**, na barra lateral. Em qualquer ferramenta também dá para pedir em linguagem natural (ex.: "implemente a change add-autenticacao-perfis").

Abra a IA **na raiz do repositório**; aberta numa subpasta, ela não encontra o `AGENTS.md` nem as skills. Os arquivos de `.claude/`, `.gemini/` e `.agents/` são gerados pelo OpenSpec: não edite à mão. Depois de atualizar o OpenSpec, o PO roda `openspec update` e faz commit do resultado.

Arquive as changes (`/opsx:archive` ou `$openspec-archive-change`) só quando estiverem concluídas e revisadas, na ordem da tabela "Changes do OpenSpec".

## Regras

- A autorização por perfil é aplicada **no backend**. Esconder um botão no frontend não é controle de acesso.
- O painel público **nunca** exibe CPF nem nome.
- Parâmetros clínicos (faixas de risco, limiares, ciclo 2:1, tentativas, idades) ficam **configuráveis no banco**, não fixos no código.
- **Nunca** versione credenciais, tokens ou URLs privadas do Xano. Use `.env`, que é ignorado pelo Git.
- Documentação e artefatos são escritos em **português**. Veja [AGENTS.md](AGENTS.md).

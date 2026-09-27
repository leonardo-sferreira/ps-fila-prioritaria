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

| # | Change | Entrega |
|---|---|---|
| 1 | `add-autenticacao-perfis` | Login, perfis e gestão de usuários |
| 2 | `add-cadastros-administrador` | Especialidades, sintomas, médicos, disponibilidade, parâmetros e auditoria |
| 3 | `add-pacientes-pre-triagem` | Simulador de totem, fila pré-triagem e pacientes por CPF |
| 4 | `add-triagem-classificacao` | Ficha, sinais vitais, fator de risco, cor e ajuste manual |
| 5 | `add-direcionamento-senha` | Especialidade sugerida e atribuída, senha e comprovante |
| 6 | `add-fila-chamada-medico` | Ciclo 2:1, chamar próximo, tentativas e desistência |
| 7 | `add-painel-publico` | Painel sem dados pessoais e previsão das próximas 5 |
| 8 | `add-acompanhamento-administrador` | Fila geral, equipe logada (status) e auditoria |

Cada change tem `proposal.md` (por quê e o quê), `specs/` (requisitos com cenários), `design.md` (como) e `tasks.md` (checklist, com Xano e Reflex separados). **Implemente só o que está no `tasks.md`.** Se surgir uma decisão nova, registre na change antes de virar código.

## Fluxo no Git

```bash
git checkout -b <nome-da-change>      # ex.: add-autenticacao-perfis
# implemente as tasks, marcando [x] no tasks.md
git push -u origin <nome-da-change>   # e abra um Pull Request para a main
```

Com o Claude Code, use `/opsx:apply <change>` para implementar e `/opsx:archive <change>` quando a change estiver concluída e revisada.

## Regras

- A autorização por perfil é aplicada **no backend**. Esconder um botão no frontend não é controle de acesso.
- O painel público **nunca** exibe CPF nem nome.
- Parâmetros clínicos (faixas de risco, limiares, ciclo 2:1, tentativas, idades) ficam **configuráveis no banco**, não fixos no código.
- **Nunca** versione credenciais, tokens ou URLs privadas do Xano. Use `.env`, que é ignorado pelo Git.
- Documentação e artefatos são escritos em **português**. Veja [AGENTS.md](AGENTS.md).

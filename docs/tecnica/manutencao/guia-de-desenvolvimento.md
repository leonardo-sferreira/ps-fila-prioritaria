# Guia de desenvolvimento

Como preparar o ambiente, rodar o sistema pela primeira vez, testar e contribuir. O fluxo de trabalho da equipe (Git, OpenSpec e regras) está no [CONTRIBUTING.md](../../../CONTRIBUTING.md).

## Requisitos

| Ferramenta | Versão | Para quê |
|---|---|---|
| Python | 3.12 ou mais nova (o CI usa 3.12) | Reflex, testes e scripts |
| Node.js | 20 ou mais novo | Xano CLI e OpenSpec. O Reflex instala o próprio Bun na primeira execução |
| Git | qualquer recente | Código |
| Xano CLI (`@xano/cli`) | 1.3.4 | Publicar o backend e rodar funções e testes no Xano |
| OpenSpec (`@fission-ai/openspec`) | atual | Especificações e changes |
| Acesso ao Xano | conta convidada no workspace **ps-impacta Workspace** | Pedir ao PO |

As bibliotecas Python e as versões exatas estão em `frontend/requirements.txt` ([inventário](../evolucao/dependencias.md)).

## Primeira execução

```bash
# 1. Código
git clone https://github.com/leonardo-sferreira/ps-fila-prioritaria.git
cd ps-fila-prioritaria

# 2. Ferramentas globais
npm install -g @fission-ai/openspec @xano/cli

# 3. Ambiente Python do frontend
cd frontend
python -m venv .venv
# Windows (PowerShell):  .\.venv\Scripts\Activate.ps1
# Linux/macOS:           source .venv/bin/activate
pip install -r requirements.txt

# 4. Configuração
cp .env.example .env      # no PowerShell: Copy-Item .env.example .env
# preencha as URLs dos 5 grupos de API do Xano e a TOTEM_CHAVE (veja configuracao-e-regras.md)

# 5. Rodar em desenvolvimento
reflex run
```

Na primeira vez, o Reflex baixa o Bun e as dependências JavaScript e compila as telas, o que leva alguns minutos. Quando aparecer `App running at: http://localhost:3000/`, abra o endereço. O backend do Reflex fica em `http://localhost:8000`.

Para entrar, é preciso um usuário no Xano. O primeiro Administrador é criado uma única vez, direto no Xano (README, seção "Primeiro administrador"); os demais são criados por ele na tela Usuários.

### Se a porta estiver ocupada

Se o terminal mostrar `localhost:3001` ou "Unable to bind to :8000", já existe outro `reflex run` aberto. Pare o anterior (Ctrl+C) e rode de novo. Duas instâncias abertas também dobram as requisições ao Xano ([limite do plano](../sustentacao/erros-e-metricas.md)).

## Acesso ao Xano pelo CLI

```bash
xano auth -p ps-impacta          # entra com a sua conta
xano profile use ps-impacta      # fixa o perfil nesta pasta
xano profile me                  # confere conta e workspace
```

O backend fica em `backend/xano/`, com um arquivo `.xs` por endpoint, função ou tabela. Para publicar, sempre simule antes e publique só os arquivos alterados:

```bash
xano workspace push -d backend/xano -p ps-impacta -b v1 --dry-run -i "api/fila/painel_get.xs"
xano workspace push -d backend/xano -p ps-impacta -b v1 --force   -i "api/fila/painel_get.xs"
```

Detalhes, restrições e o que nunca fazer: [deploy e ambientes](../sustentacao/deploy-e-ambientes.md).

## Testes

```bash
# na raiz do repositório, com o venv do frontend ativo
python scripts/run_test_evidence.py --suite reflex        # telas e estados (API simulada)
python scripts/run_test_evidence.py --suite xano-static   # contratos lidos do código
python scripts/run_test_evidence.py --suite xano-safe     # funções puras no Xano (precisa do CLI)
python -m pytest tests/api/test_painel.py                 # um teste ao vivo específico
```

No Windows, defina `PYTHONUTF8=1` para os testes que leem arquivos com acentos. Todo teste novo precisa ser registrado em `tests/catalogo_testes.json`, senão o CI bloqueia. Explicação completa: [estratégia de testes](../testes/estrategia-de-testes.md).

## Como implementar uma mudança

1. **Especificar:** toda funcionalidade nasce como uma change do OpenSpec (`openspec/changes/<nome>/`, com proposta, specs, design e tarefas). Implemente só o que está no `tasks.md`.
2. **Branch:** crie uma branch no Git a partir da `main` atualizada (`feat/...`, `fix/...`, `docs/...`).
3. **Backend:** edite os `.xs` em `backend/xano/`. Novo endpoint protegido começa com `auth/verificar_acesso`; escrita relevante grava auditoria com `registrar_alteracao`; regra configurável vira parâmetro.
4. **Frontend:** a tela em `paginas/` e o estado em `estados/`; chame a API só por `api.requisitar`. Regra de negócio fica no Xano, não no Reflex.
5. **Testes:** teste de estado em `frontend/tests/`, de contrato ou ao vivo em `tests/api/`, e registro no catálogo.
6. **Publicar no Xano:** simulação e depois publicação restrita aos arquivos alterados.
7. **Pull Request:** a `main` só recebe código por PR, com o CI verde. Commits e PRs sem coautoria de IA.
8. **Arquivar a change** quando todas as tarefas estiverem concluídas e validadas pelo PO: `openspec archive <change> -y`.
9. **Atualizar a documentação:** `python scripts/gerar_docs.py` regenera contratos, mapa de telas, dicionário, funções, dependências, changelog e catálogo de testes.

## Convenções do código

- Textos da interface e comentários em português, sem jargão; mensagens de erro dizem o que fazer.
- Datas sempre no fuso do PS (`comum.FUSO_BRASILIA`, `America/Sao_Paulo`).
- Cores pelas variáveis de `assets/tema.css` (`COR_*` em `componentes.py`), para o modo escuro funcionar.
- Nada com histórico é excluído: é desativado.
- Telas do Figma são a referência visual ([protótipo](https://www.figma.com/design/38ro8aKQfiGkUivIfCaOR1)).

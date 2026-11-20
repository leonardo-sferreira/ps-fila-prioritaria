# Guia de migração

Como mudar o sistema de uma versão para outra: código, esquema do banco, parâmetros e dados. O que mudou em cada entrega está no [changelog](changelog.md).

## Versões

| Versão | Data | Conteúdo |
|---|---|---|
| `v0.1.0` | 25/10/2026 | Identificação do paciente por CPF e ficha de atendimento com sintomas (pré-release no GitHub) |
| `main` | atual | Todas as changes arquivadas até a Sprint 5 ([changelog](changelog.md)) |

Cada funcionalidade entregue é uma change arquivada em `openspec/changes/archive/<data>-<nome>/`, com a proposta, o design (decisões e alternativas) e as tarefas, incluindo os passos de migração de cada uma.

## Atualizar uma instalação para a versão atual

1. **Código:** `git pull` na `main`.
2. **Dependências:** `pip install -r frontend/requirements.txt`.
3. **Variáveis:** compare `frontend/.env` com `frontend/.env.example` e acrescente as novas. No Xano, confira a [lista de variáveis](../manutencao/configuracao-e-regras.md#variáveis-de-ambiente-do-xano).
4. **Backend:** publique no Xano os arquivos alterados desde a última versão, com simulação antes ([deploy](../sustentacao/deploy-e-ambientes.md)). Para ver o que mudou: `git diff --name-only <versão-anterior> -- backend/xano`.
5. **Parâmetros novos:** não precisam de script. As funções `inicializar_*` criam os parâmetros que faltam, com o valor inicial e auditoria "Sistema", na primeira vez que um endpoint que os usa é chamado. Exemplo: `HORAS_PAINEL` aparece na lista de Parâmetros depois que a fila da pré-triagem ou o dashboard é aberto.
6. **Frontend:** reinicie o `reflex run`. Se as telas não refletirem a mudança, apague `frontend/.web` e rode de novo.

## Mudanças de esquema do banco

O esquema está em `backend/xano/table/*.xs` e só muda com o PO.

1. Descreva a mudança na change do OpenSpec (design: campo, tipo, padrão e efeito nos dados existentes).
2. Prefira campos **opcionais** (`?`) com padrão: registros antigos continuam válidos sem script.
3. Publique a tabela com simulação e `-i "table/<tabela>.xs"`.
4. Se for preciso converter dados existentes, use uma função de manutenção idempotente em `function/manutencao/` (exemplos já usados: `reparar_especialidade_fichas`, `inicializar_status_sessoes`, `desativar_status_auto_medicos`), rodada uma vez pelo CLI: `xano function run manutencao/<nome> --json - --branch v1 -p ps-impacta`.
5. Registre a migração no changelog da change.

**Atenção:** três tabelas divergem do repositório no Xano (`contador_senha`, `ficha_atendimento`, `sintoma`). Não publique esses arquivos sem antes comparar com a versão publicada.

## Migrações já feitas

| Change | O que mudou nos dados | Como foi migrado |
|---|---|---|
| Migração de `especialidade` (PR #30) | A migração recriou as especialidades com IDs novos; fichas antigas ficaram com IDs inexistentes | `manutencao/reparar_especialidade_fichas` reaponta cada ficha pela sigla da senha |
| `add-base-compartilhada` | Parâmetros e auditoria; carga inicial com usuário "Sistema" | `inicializar_*` com `sistema: true` |
| `add-acompanhamento-administrador` | Status operacional na sessão | `manutencao/inicializar_status_sessoes` (sessões ativas da Recepção sem status) e `manutencao/desativar_status_auto_medicos` (sessões médicas antigas) |
| `add-painel-publico` | Parâmetro `HORAS_PAINEL` | Criado por `inicializar_parametros_fila` |

## Voltar uma versão

Veja [deploy e ambientes → rollback](../sustentacao/deploy-e-ambientes.md#rollback). Como nada com histórico é apagado, voltar o código não perde dados; campos novos ficam sem uso até a versão seguinte.

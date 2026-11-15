# Change: corrigir-isolamento-autotestes-ci

| Campo | Valor |
|---|---|
| Sprint | Não atribuída |
| Card no Trello | Não informado |
| Depende de | Infraestrutura de evidências já implementada e arquivada |
| Situação | Correção do defeito de isolamento identificado após o push |

## Why

O job de autotestes falhou no GitHub Actions embora os testes locais passassem: as fixtures herdavam `GITHUB_*` do processo executor. A reprodução local com contexto de Actions resultou em 34 aprovações e seis falhas, além de resumos sintéticos escritos no Job Summary do job real.

## What Changes

- Isolar as variáveis `GITHUB_*` somente durante cada autoteste sintético do pipeline; os cenários que simulam CI explicitamente continuam configurando seu próprio contexto.
- Acrescentar regressão com pytest em subprocesso sob contexto de Actions, verificando que as fixtures não publicam no Summary externo e que o runner real conserva sua identidade de CI.
- Cadastrar somente o novo autoteste real e documentar a causa e a interpretação do gate.

## Capacidades

Nenhuma capacidade ou contrato de spec muda. É uma correção das fixtures para cumprir `evidencias-testes`, especialmente origem auditável, separação entre ferramenta/produto e preservação da falha no gate. `skip_specs: true` evita inventar requisito para uma correção de testes.

## Impacto

`tests/test_evidence_pipeline.py`, `tests/catalogo_testes.json` e guia técnico de QA. Sem mudanças no workflow, runner, merge, gates, assertions do produto ou requisitos formais. A change arquivada e suas evidências permanecem intactas.

## Fora do escopo

Relaxar gates, aceitar identidades incompatíveis, habilitar escrita remota, alterar regras clínicas, executar novamente testes remotos Xano ou reescrever evidências históricas.

## Perguntas em aberto

Nenhuma decisão funcional pendente. O run corretivo deve ser observado após o push, sem confundir o resultado de autotestes com aceite integrado do produto.

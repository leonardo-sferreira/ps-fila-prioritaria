# Correção do isolamento dos autotestes

## Contexto

Ver `proposal.md`. Os testes de merge criam fontes locais com `github_run_id`/tentativa nulos, enquanto o processo filho herda os defaults reais do Actions. A leitura legada local também é corretamente recusada quando a fixture herda `GITHUB_ACTIONS=true`. `write_reports` publica no arquivo indicado por `GITHUB_STEP_SUMMARY`, causando publicação indevida de fixtures.

## Decisões

- Usar uma fixture pytest automática, com escopo de função, no próprio `tests/test_evidence_pipeline.py`. Remover apenas `GITHUB_*` durante cada teste sintético e restaurar o ambiente ao final com `monkeypatch`. Não remover PATH, configuração Python ou contexto do runner pai.
- Manter os testes explícitos de CI: eles reintroduzem o contexto simulado dentro de seu próprio escopo. Não alterar a política do merge nem a recusa de legado no CI real.
- O novo autoteste executa seleções existentes em subprocesso com variáveis sintéticas de Actions e um Summary externo sentinela. Exige sucesso das verificações e sentinela intacta. Uma invocação intencional separada do runner comprova que seu contexto CI continua preservado.
- Registrar somente esse novo caso real no catálogo como autoteste da ferramenta, sem referência formal inventada. Documentar a distinção entre fixture isolada e processo real no guia comum.

## Verificação e riscos

Executar a suíte antes/depois com contexto equivalente ao Actions: antes, 34/40 e seis falhas; depois, exigir os 41 casos aprovados. Conferir os três formatos e o Summary do runner, que deve conter somente o resultado da suíte real. A fixture é local ao módulo; não alcança os testes funcionais nem o runner externo. Assertions atuais e workflow permanecem idênticos.

A correção não exige novas dependências ou novas execuções remotas Xano. Reversão: remover a fixture, o novo autoteste e seu registro; manter evidências históricas intactas. Não há migração de dados ou domínio.

# Diagnóstico e verificação da correção

## Causa observada

No [run 43671015567](https://github.com/leonardo-sferreira/ps-fila-prioritaria/actions/runs/43671015567/job/132680839784), o job de autotestes falhou no gate final com instalação 0 e testes 1. Reflex local, estáticos Xano e E2E público terminaram com sucesso na consulta feita durante o diagnóstico. Os testes Xano puros ainda executavam; não se atribuiu aprovação a eles nessa consulta.

A API pública confirma o estado do job, mas os logs detalhados exigem autenticação. A causa foi reproduzida localmente com variáveis de Actions: **34/40 passaram, seis falharam**, e as fixtures escreveram 74.451 bytes de resumos sintéticos no arquivo que representava o Summary externo. Isso não é evidência de execução de produto.

As fontes sintéticas de merge declaravam contexto local, mas os subprocessos herdavam run/tentativa reais. A recusa de identidade e de legado em CI estava correta; o defeito estava na preparação dos autotestes. O `GITHUB_STEP_SUMMARY` herdado também permitia publicar fixtures no resumo do job.

## Correção e regressão

A fixture automática de escopo de função remove `GITHUB_*` somente durante os testes sintéticos do módulo e restaura o ambiente ao final. Os testes explícitos de contexto CI continuam configurando suas próprias variáveis. Runner, merge, workflow, gates, código de produto e assertions preexistentes permaneceram idênticos ao commit anterior.

O novo caso real `CT-FERRAMENTA-0041` executa os seis cenários antes reprovados em um processo pytest com ambiente de Actions e Summary sentinela: todos passam, e o Summary externo permanece intacto. Em seguida, uma invocação intencional do runner com dependência simulada indisponível confirma a preservação de SHA/run/tentativa/job, produção dos três formatos e retorno 1 esperado para esse cenário bloqueado. Tudo ocorre em diretórios temporários, sem chamada remota Xano.

## Resultados locais reais

- Suíte completa de infraestrutura: **41 passaram**, retorno 0.
- Runner da suíte completa com contexto de Actions simulado localmente: **41 PASSED, zero FAILED/ERROR/SKIPPED/NOT_RUN/BLOCKED**, validação completa e retorno 0.
- XML, JSON e Markdown da simulação conferidos: identidade e contagens coerentes. O Summary da execução externa contém somente um relatório da suíte, com 41 aprovações; não contém os resumos das fixtures.
- OpenSpec normal e strict: **retorno 0 nos dois modos**, zero avisos/erros. Há apenas a informação de que `skip_specs: true` aceita zero deltas porque o contrato não muda.
- Diff/AST: os 14 testes anteriores do módulo permanecem idênticos; o catálogo preserva todos os registros anteriores e acrescenta somente o caso real 0041. Workflow, scripts, testes funcionais e change arquivada não foram alterados.

A reprodução anterior ficou em `/tmp/qa-repro-github-m8rt3y7m/`. A evidência da execução local em contexto simulado está em `test-evidence/corrigir-isolamento-autotestes-ci/simulacao-actions/`, com os três formatos; o Summary externo está em `summary-simulacao-actions.md`, no diretório pai. Esses arquivos simulam o contexto do Actions para verificar a infraestrutura; não são artifacts de um run remoto nem cobertura de produto.

## Acompanhamento remoto

O commit corretivo será enviado para a mesma branch e o resultado do novo job de autotestes será conferido após o push. Não foram alterados ou reexecutados manualmente os testes Xano remotos, nem cancelados os runs anteriores. As evidências históricas continuam intactas. Esta correção permanece em change própria, sem reabrir ou reescrever a change arquivada.

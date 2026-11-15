# Tarefas

## 1. Isolamento e regressão dos autotestes

- [x] 1.1 Isolar `GITHUB_*` por teste no módulo de fixtures do pipeline, preservando o contexto do runner pai e as simulações explícitas; documentar no guia comum e verificar que os seis casos antes reprovados passam sob contexto de Actions.
- [x] 1.2 Acrescentar um autoteste real com subprocessos pytest/runner em contexto CI e Summary sentinela; registrar seu ID permanente no catálogo e verificar ausência de publicação sintética e preservação de SHA/run/tentativa/job na execução intencional.

## 2. Verificação integrada e registro

- [x] 2.1 Executar toda a suíte de infraestrutura localmente e pelo runner com variáveis de Actions em diretórios novos, conferir os 41 casos, os três formatos e o Summary exclusivo da suíte; registrar códigos e contagens sem executar testes remotos Xano.
- [x] 2.2 Conferir diff com workflow, gates, assertions funcionais e histórico intactos; validar a change em modo normal e strict e registrar reprodução/correção e limitações do acompanhamento remoto no resultado técnico.

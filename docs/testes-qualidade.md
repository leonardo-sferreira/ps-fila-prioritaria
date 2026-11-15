# Evidências e qualidade dos testes

Este guia descreve a infraestrutura de QA. Não constitui documentação acadêmica final nem aceite do sistema integrado. As assertions continuam nos testes existentes. O catálogo descreve casos reais; não cadastra novos RF/RNF/RN.

## Seleção segura e execução

Execute na raiz, com o ambiente Python do projeto. Cada comando exige saída nova ou vazia; repetir o comando exige trocar o diretório. O runner e o merge recusam saídas não vazias sem apagar arquivos.

```bash
.venv/bin/python scripts/run_test_evidence.py --suite autotestes --output test-evidence/revisao-autotestes --require-execution --require-complete
.venv/bin/python scripts/run_test_evidence.py --suite reflex --output test-evidence/revisao-reflex --require-execution --require-complete
.venv/bin/python scripts/run_test_evidence.py --suite xano-static --output test-evidence/revisao-static --require-execution --require-complete
```

| Suíte | Seleção e dependência | Limite da evidência |
|---|---|---|
| `autotestes` | Testes reais de `tests/test_*.py`; fixtures temporárias, subprocessos simulados e comandos locais | Integridade da ferramenta; não contam como cobertura do produto |
| `reflex` | Seletores individuais do catálogo, excluindo módulos de integração real | Testes locais, contratos estáticos e mocks de API; não comprovam persistência |
| `xano-static` | Somente `AuditoriaTest` e `ParametrosTest` da base compartilhada, oito métodos | Leitura local do XanoScript; nenhuma chamada HTTP ou CLI remoto |
| `xano-safe` | 25 testes Python e 72 testes nativos de funções puras existentes | Execução remota na branch `v1`, datasource `live`; equivalência integral com o Git não comparada |
| `e2e` | Dois testes públicos de navegação e guarda de rota, servidor local controlado e Chromium | Não verifica fluxo clínico completo nem painel de chamadas |
| `controlled` | Inventário de integrações reais, inclusive a consulta HTTP da base compartilhada | Não executa escrita automaticamente; não integra o aceite automático do CI |

Não use descoberta ampla de `tests/api` ou `frontend/tests`: os arquivos incluem testes capazes de escrever em ambiente real, especialmente quando `.env` está presente.

Para remoto puro, somente quando o CLI e a credencial estiverem disponíveis:

```bash
.venv/bin/python scripts/run_test_evidence.py --suite xano-safe --output test-evidence/revisao-xano --require-execution --require-complete
```

O guardião revisa a lista explícita `NATIVE_PURE`, inclusive as funções chamadas pelos testes Python e suas dependências. Acesso a recurso proibido ou dependência não revisada impede a chamada remota. O preflight confere a autenticação antes de iniciar os testes. Não publica XanoScript nem cria dados persistentes. Credenciais são temporárias, privadas e removidas após o uso; seus valores nunca entram nos relatórios.

E2E com servidor próprio de produção, encerrado ao terminar:

```bash
.venv/bin/python scripts/run_reflex_e2e_ci.py --output test-evidence/revisao-e2e
```

O helper confere CLI, Playwright e executável Chromium antes de iniciar seu servidor. A indisponibilidade produz `BLOCKED` e diagnóstico, sem alegar execução. O runner aceita `REFLEX_E2E_BASE_URL` apenas HTTP em `localhost` ou `127.0.0.1`. `--blocked-reason instalacao|servidor|navegador|dependencia` permite registrar impedimentos de preparação conhecidos, inclusive quando a instalação do produto falha; o relatório usa apenas biblioteca padrão.

O inventário controlado pode ser produzido sem escrita:

```bash
.venv/bin/python scripts/run_test_evidence.py --suite controlled --output test-evidence/revisao-controlled
```

A execução HTTP controlada exige a opção explícita `--execute-controlled`, confirmação `XANO_ISOLATED_CONFIRMATION=CONFIRMO_WORKSPACE_DESCARTAVEL`, host isolado válido em `XANO_ISOLATED_API_HOST`, endpoints HTTPS de autenticação, triagem, pacientes e cadastros nesse host, além das credenciais de teste exigidas pelo guardião. Os dois cenários em `tests/api` que fixam `v1` continuam bloqueados mesmo com essas condições. A confirmação deve corresponder a ambiente realmente descartável; esta change não autoriza sua execução nem limpeza remota. Não existe acionamento de escrita no CI.

## Catálogo e rastreabilidade

`tests/catalogo_testes.json`, versão 1, é a única fonte editável de ID, nome, objetivo, resultado esperado, tipo, modo de dependência, componente, segurança e referências. Os IDs são permanentes, atribuídos uma vez; não são códigos formais de requisitos. Renomear arquivo/função exige mudar apenas o seletor, mantendo ID, variantes e aliases históricos. Não regenere IDs a partir de nomes ou hashes.

Cada registro pode conter `variantes` com `chave`, `seletor` e `aliases_historicos`. A identidade de resultado é `(id, variante)` dentro de sua origem; os valores parametrizados atuais são literais estáveis. `adaptador_de` liga adaptadores unittest a uma verificação comprovada: as execuções técnicas são preservadas, sem declarar novos requisitos cobertos. A descoberta estática não importa módulos ou carrega `.env`; a coleta do pytest confere módulo, classe e variante completos. Caso descoberto sem registro, seletor/ID/variante ambíguo, resultado desconhecido ou remoção inesperada impede aprovação integral.

Tipos: `UNITARIO`, `INTEGRACAO`, `E2E`, `ESTATICO`. Modos: `LOCAL`, `MOCK`, `REAL`. Uma função pura executada no Xano é `UNITARIO/REAL`; não é integração de persistência. A classificação é por caso, incluindo o uso de helpers; um arquivo com mocks pode ter testes puramente locais.

`referencias.openspec` guarda arquivo/cenário existente quando identificado. Cenário nulo indica que só a capacidade foi associada. `referencias.formais` preserva códigos declarados no código, sempre `PENDENTE` até conferência formal. Ausência de vínculo permanece lista vazia. O Confluence não estava disponível nesta implementação. A divergência documental entre Confluence e Word externo está registrada no proposal; não autoriza inventar requisitos ou reintroduzir regras antigas.

## Estados, completude e retorno

| Estado do caso | Interpretação |
|---|---|
| `PASSED` | Assertions executadas e aprovadas |
| `FAILED` | Expectativa funcional reprovada |
| `ERROR` | Preparação, execução ou finalização com erro; resultado funcional inconclusivo |
| `SKIPPED` | Omissão intencional pelo executor |
| `NOT_RUN` | Não iniciado/coletado no escopo |
| `BLOCKED` | Impedido por dependência, restrição ou autorização |

Os três estados sem execução exigem motivo. `PASS`/`FAIL` são aliases somente na leitura histórica. Estado desconhecido é erro; nunca aprovação. Mensagens livres de exceções são substituídas por motivos estruturados para impedir vazamento de dados.

`status_tecnico` é `PASSED`, `FAILED` ou `ERROR`. `nivel_validacao` é `COMPLETA`, `PARCIAL`, `BLOQUEADA` ou `NAO_EXECUTADA`, relativo ao `escopo_validacao`. Uma execução completa pode reprovar o comportamento. Se há execução útil e obrigações pendentes, a validação é parcial; se tudo foi impedido, bloqueada; sem execução nem impedimento caracterizado, não executada. `aprovacao_integral` exige sucesso técnico e validação completa. O aceite de roteiro mantém avaliação funcional separada em `roteiro` e não é encerrado por mocks ou sucesso do pipeline.

| Condição | Retorno |
|---|---|
| Caso `FAILED`/`ERROR`, erro de coleta/formato/identidade ou suíte esperada ausente | 1, após tentar produzir os três formatos |
| Parcial sem falhas e sem exigência de completude | 0; aprovação integral continua falsa |
| `--require-complete` com obrigação pendente | 1 |
| `--require-execution` sem caso executado | 1; execução não exige aprovação para ser contada |
| Destino já utilizado | 2, preservando o conteúdo anterior |
| Zero casos confiáveis no runner ou nenhuma fonte válida esperada no merge | 1 com diagnóstico separado; nenhum teste de produto fictício |

## Formato e publicação

`resultados.json` usa `versao_formato: 2`. Declara `execucao_id`, suíte/escopo, início/fim UTC com fuso, duração, commit, SHA esperado/observado, branch, árvore limpa/alterada, ferramentas, ambiente, dependências, origem e contexto GitHub disponível (`github_run_id`, `github_run_attempt`, `github_job`, `github_url`). Valores indisponíveis ficam nulos ou explicitamente indisponíveis. Em árvore alterada o SHA identifica apenas a base. No PR, o SHA observado é o checkout efetivamente testado.

`casos` contém ID/variante, seletor `node`, metadados do catálogo, resultado observado, estado, duração, motivo, referências relativas de evidência e origem. `diagnosticos` guarda problemas de processo; não aumenta o total de casos. `totais`, `totais_por_tipo`, `totais_por_componente`, `totais_por_dependencia`, eixos e conclusão são calculados dessa execução.

Os três formatos canônicos são `resultados.json`, `resultados.xml` e `resumo.md`. O XML usa JUnit: `FAILED` vira `failure`, `ERROR` vira `error`, e `SKIPPED`/`NOT_RUN`/`BLOCKED` viram `skipped` com o estado original em `type` e o motivo em `message`. O nome do testcase guarda ID e variante; propriedades de suíte guardam identidade, horários, eixos e diagnósticos. Suas contagens e duração dos casos são as mesmas do JSON. A duração total de execução inclui preparação e coleta, por isso pode exceder a soma dos casos.

`pytest.xml` é auxiliar corrente minimizado, com identidades reconhecidas e mensagens estruturadas; `pytest.log` registra somente executor, suíte e código. Saída livre não é persistida. `http-events.jsonl`, quando executada a suíte HTTP autorizada, limita-se a seletor conhecido, método, rota permitida e status; corpos, headers e nomes arbitrários de campos são omitidos. `servidor.log` resume a inicialização do E2E; o log livre temporário é privado e descartado. Esses auxiliares não são outra execução para somar.

A lista local permitida está em `PUBLIC_FILES`; o workflow publica somente os três canônicos. Screenshots/traces não são capturados nem enviados automaticamente; qualquer captura adicional só é publicável após inspeção no E2E público com dados seguros. Não publicar capturas de integrações reais, `.env`, credenciais, saídas brutas ou diretórios de entrada do merge. Links GitHub de run/artifacts e Trello são validados separadamente; URLs privadas são omitidas. A minimização complementa a sanitização textual.

## Consolidação e ciclos

A seleção de suítes esperadas é obrigatória. Exemplo estritamente local:

```bash
.venv/bin/python scripts/merge_test_evidence.py \
  --input test-evidence/revisao-autotestes --expected-suite autotestes \
  --input test-evidence/revisao-reflex --expected-suite reflex \
  --input test-evidence/revisao-static --expected-suite xano-static \
  --output test-evidence/revisao-consolidado --require-execution --require-complete
```

O merge valida versão, commit esperado (por padrão o HEAD), run/tentativa esperados, identidade, duplicação, casos, contagens e conclusão. No CI, passe também `--expected-commit`, `--expected-run-id` e `--expected-attempt`, além de `--needs-result suite=success|failure|cancelled|skipped`. A fonte incompatível não contribui com aprovações. Fontes válidas são preservadas; JSON ausente/corrompido ou nenhuma fonte válida ainda produz os três formatos e diagnóstico. Suítes ausentes são obrigações explícitas, sem inventar resultados individuais. Um cancelamento forte pode impedir publicação; o merge diagnostica a ausência quando conseguir executar.

Legado sem versão/contexto de run exige `--allow-legacy-local` e não é aceito no CI. IDs de execução legados recebem um alias por hash na consolidação para não republicar texto arbitrário; os IDs funcionais continuam vinculados pelos aliases catalogados. Os arquivos originais permanecem intactos. A falta de identidade histórica fica registrada como limitação; dados inválidos continuam rejeitados.

Roteiros são opcionais. Acrescente `--roteiro tests/roteiros/sprint5.json` para gerar o snapshot histórico no consolidado. Sem a opção, nenhum arquivo fixo da Sprint 5 é produzido. Pendências do roteiro selecionado impedem aprovação integral e bloqueiam `--require-complete`; não impedem retorno zero exploratório se os casos técnicos passam e não há erros de infraestrutura.

```bash
.venv/bin/python scripts/roteiros_testes.py --config tests/roteiros/sprint5.json --input test-evidence/revisao-consolidado/resultados.json --output test-evidence/revisao-roteiro.md
# Invocação histórica preservada:
.venv/bin/python scripts/roteiros_sprint5.py --input test-evidence/revisao-consolidado/resultados.json --output test-evidence/revisao-sprint5.md
```

Para outro ciclo, crie um JSON com `versao: 1`, `ciclo`, `titulo`, `descricao`, `arquivo` Markdown e `roteiros`. Cada atividade tem `numero`, `titulo`, `url` pública opcional e `verificacoes`; cada verificação tem `titulo`, `casos` (IDs existentes) e `pendencia`. Não copie nomes/expectativas dos casos nem edite o gerador. Use IDs existentes para regressão em múltiplos ciclos. A configuração real desta change conserva somente a Sprint 5; a reutilização é verificada por configuração sintética temporária. Sprint de desenvolvimento é contexto histórico; ciclo de validação é a seleção da execução.

## GitHub Actions

O workflow preserva gatilhos push/PR/manual, permissão `contents: read` e versões anteriores de Python/actions/CLIs. Cinco jobs independentes executam `autotestes`, `reflex`, `xano-static`, E2E público e Xano puro. Cada um captura o retorno da preparação/execução, produz e publica evidências com `always()` e aplica o gate ao final. Capturar o retorno permite publicar; o passo final conserva sua falha. Falta de secret remoto bloqueia a suíte obrigatória e o CI; não cancela os jobs locais. Nenhuma tolerância irrestrita transforma falha em sucesso.

Artifacts históricos mantidos: `evidencias-reflex`, `evidencias-e2e`, `evidencias-xano`, `evidencias-consolidadas`; suítes separadas acrescentam `evidencias-autotestes` e `evidencias-xano-static`. O merge declara as cinco suítes esperadas e recebe SHA/run/tentativa e `needs`. Cada download e a consolidação têm condição própria `always()`. Arquivos canônicos obrigatórios são verificados e uploads usam `if-no-files-found: error`. O Job Summary mostra eixos, totais, falhas/ausências, limites e link para o run/artifacts.

O workflow foi verificado localmente; esta aplicação não publicou branch, não acionou run novo no GitHub e não comprova execução remota desse YAML. Resultados locais e limitações estão no registro de implementação da change.

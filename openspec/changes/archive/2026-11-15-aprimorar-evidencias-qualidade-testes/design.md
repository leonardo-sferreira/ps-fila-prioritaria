# Design técnico

## Contexto e auditoria do explore

A motivação e o escopo estão em `proposal.md`. A auditoria leu o workflow, os seis scripts existentes, os testes Python, os testes nativos selecionados, as evidências locais ignoradas pelo Git e os documentos de contexto. Não executou testes funcionais nem chamadas de escrita no Xano.

Base auditada: commit `708036a0ffdba5600d1fc806de5eaae6f0def5f5`, em 14/11/2026 no fuso do projeto. `docs/entrega/` já estava não versionado e não faz parte desta change. As evidências históricas abaixo estão no disco local e não são resultados produzidos nesta auditoria.

### Inventário observado

| Grupo | Descoberta atual | Natureza real e dependências |
|---|---:|---|
| `reflex` | 250 casos | 234 classificados como `integracao_mock` e 16 como `unitario`; classificação atual é por arquivo, não por caso |
| `xano-safe` | 97 casos | 25 testes Python chamam funções puras remotas pelo CLI; 72 testes nativos de funções puras dependem do Xano publicado na `v1` |
| `controlled` | 28 casos | Integrações HTTP reais, inclusive parametrizações; dois cenários CLI com escrita ficam inventariados, mas não são executados pelo runner HTTP isolado |
| `e2e` | 2 casos | Navegador real sobre login, aviso público e redirecionamento; não verifica o fluxo clínico completo nem o painel de chamadas |
| Base compartilhada | 9 métodos fora do runner/CI | Oito verificações estáticas locais e uma consulta HTTP sem token/com token adulterado no mesmo módulo |
| Autotestes do relatório | 17 testes Python | 12 testes do runner e cinco dos roteiros; usam dados sintéticos para testar a ferramenta, sem provar comportamentos do produto |

São contagens de descoberta estática, não execuções ou percentuais de cobertura. `test_auth_state.py` e `test_privacidade.py` contêm funções e adaptadores `unittest` que repetem verificações; preservá-los, sem contar essa repetição como novos requisitos cobertos.

### Achados e decisões correspondentes

| Achado verificável | Evidência | Tratamento planejado |
|---|---|---|
| Vocabulário usa `PASS`/`FAIL` e não reconhece `BLOCKED` | `execution_status` com `PASS` + `BLOCKED` retorna `APROVADA` em chamada somente em memória | Normalização validada de seis estados; rejeitar estados desconhecidos |
| IDs mudam com renomeação | `identifier` aplica hash ao caminho, classe, nome e variante do teste | IDs permanentes no catálogo; seletor técnico atualizável |
| Tipos atribuídos ao arquivo inteiro | `catalog` usa texto `patch(` ou `contract`; contrato estático da ficha aparece como integração com mock | Tipo e modo de dependência explícitos por caso |
| Requisitos incompletos e pouco específicos | 76 dos 250 casos Reflex atuais sem `requisito`; demais usam majoritariamente caminho de spec, sem cenário/código formal confirmado | Referência de cenário quando comprovada; formal pendente sem inferir RF/RN |
| Resultado geral e roteiro têm alcances diferentes | `main-consolidado-final`: 335 `PASS`, `APROVADA`; `roteiros-sprint5.md`: 19 verificações técnicas aprovadas e três pendentes, além de passos reais ainda abertos | Eixos técnico e de validação com escopo e pendências explícitos |
| Houve divergência histórica entre JUnit bruto e normalizado | `main-reflex`: JUnit 237 `PASS` + 1 falha; JSON/XML normalizado 236 `PASS` + 1 falha + 1 `NOT_RUN` | Conferência por identidade e cardinalidade; o código atual já tem regressão para nomes iguais entre módulos, que deve ser preservada |
| Evidências dependentes podem não chegar ao consolidador | Downloads no consolidado não têm condição própria; `merge_test_evidence.py` retorna antes de gerar relatórios para entrada ausente ou commits diferentes | Receber conjunto esperado e publicar diagnóstico mesmo com entradas ausentes/inválidas |
| Mistura de execuções permanece possível | Merge confere só commit; não confere run/attempt, suíte repetida ou sobreposição de casos | Verificar identidade completa e origem por suíte |
| Diretório reutilizado pode conter resultado antigo | Runner lê `pytest.xml` e `http-events.jsonl` se existirem no destino; não exige diretório novo | Execução em diretório exclusivo; recusar destino não vazio, sem apagar histórico |
| Falhas de infraestrutura entram no total de testes de produto | Runner acrescenta `CT-INFRA-*`; `gerador.xml` fica fora da coleção de casos | Diagnóstico separado; autotestes têm suíte própria e não aumentam cobertura funcional |
| Classificação de falha do CLI pode ser ambígua | Helper de ordenação lança `AssertionError` também para erro do subprocesso | Distinguir falha de expectativa de transporte/autenticação/CLI, sem mudar a regra testada |
| Metadados e Markdown são incompletos | Não há link do run ou início/fim/duração total; Markdown repete todos os casos e não resume por tipo | Modelo comum e relatório curto com referências ao detalhe |
| Sprint 5 está fixa na infraestrutura comum | Merge importa `roteiros_sprint5` e sempre gera `roteiros-sprint5.md` | Configuração selecionável e gerador de roteiros reutilizável |
| Sanitização textual não cobre qualquer dado sensível | Regex redige tokens, CPF, e-mail e URLs; nomes livres, credenciais de nomes diferentes, traces e imagens não têm garantia equivalente | Minimização por lista permitida e revisão antes da publicação |

Consulta pública somente de leitura ao [run 43644782127](https://github.com/leonardo-sferreira/ps-fila-prioritaria/actions/runs/43644782127), correspondente ao commit auditado: três jobs com `success` e quatro artifacts presentes (`evidencias-reflex`, `evidencias-e2e`, `evidencias-xano`, `evidencias-consolidadas`). Não foram baixados os conteúdos desses artifacts nem lidos seus Job Summaries; não há evidência de divergência de contagem nesse run remoto. A lacuna demonstrada é de escopo: esse workflow não inclui a suíte com escrita nem encerra os passos manuais pendentes.

As specs atuais não têm capacidade para o contrato de evidências. `evidencias-testes` descreve esse comportamento técnico, sem inventar códigos formais do produto. O export Trello não foi localizado na árvore atual; os cards 101–106 são preservados como o snapshot já documentado, sem afirmar seu estado atual no serviço. A divergência Confluence/Word está registrada no proposal; nenhuma regra antiga será reintroduzida.

## Objetivos e limites técnicos

Reaproveitar Python, pytest, XML da biblioteca padrão, CLI Xano e Actions. Manter os nomes de suítes/comandos/artifacts existentes e permitir adaptação mínima dos consumidores de `PASS`/`FAIL`. Classificar explicitamente testes estáticos e autotestes sem executar rede por causa da localização de um arquivo.

Não haverá serviço de gestão de testes, banco de evidências, gerador de PDF, cálculo de cobertura de código ou plugin pytest adicional. A suíte E2E continua pública e local; ampliar seus fluxos não faz parte desta change.

## Decisões

### D1. Um catálogo de casos e configurações de roteiro que apenas referenciam IDs

Criar `tests/catalogo_testes.json`, consumido pelo runner, gerador de roteiros e autotestes. É a única fonte editável de ID, nome, objetivo, resultado esperado, tipo, modo de dependência, classificação de segurança e referências do caso. O código continua sendo a fonte das assertions e a coleta é a fonte do resultado observado; esses dados não são cadastrados novamente.

- ID funcional permanente por caso, atribuído uma vez por área, sem hash de caminho ou nome. Renomear o seletor não muda o ID.
- Para parametrizados, ID do caso e chave estável da variante; não depender de `repr` de objetos ou ordem de parâmetros. Adaptadores existentes permanecem identificáveis como execuções técnicas distintas da mesma verificação quando houver vínculo comprovado.
- Seletor técnico completo para Python e par função/teste para Xano são vínculos atualizáveis, não identidade funcional. Aliases dos IDs históricos ficam no mesmo registro e não são recalculados após renomeação.
- Referências OpenSpec apontam capability e cenário existente quando identificável. Códigos RF/RNF/RN encontrados no código podem ser preservados como referência declarada, com estado `PENDENTE` até conferência no Confluence. Ausência de associação nunca recebe código inventado.
- Descoberta e catálogo devem conferir correspondência: ID duplicado, seletor ambíguo, caso sem registro ou caso removido inesperadamente são diagnósticos bloqueantes, não descartes silenciosos. A cobertura declarada é de casos selecionados, não de todo o universo de requisitos.

Criar `tests/roteiros/sprint5.json` com o snapshot dos cards 101–106, verificações, IDs referenciados e pendências já documentadas. Novos ciclos entram como outro arquivo de dados, passado por opção ao gerador/consolidador; nenhum caso precisa ter sprint exclusiva. Sprint de desenvolvimento pertence à associação histórica; sprint de validação pertence à execução/roteiro selecionado. A configuração referencia os casos e não copia seus metadados.

Refatorar o conteúdo reutilizável de `scripts/roteiros_sprint5.py` para `scripts/roteiros_testes.py`; preservar o arquivo antigo como adaptador pequeno para o roteiro histórico e comandos existentes. Esse módulo novo é usado imediatamente pelo consolidador. Não criar um registro paralelo de requisitos ou resultados em CSV/YAML.

Alternativa descartada: marcadores repetidos nos testes e catálogo separado de relatórios; duplicariam dados e não resolveriam a integração dos testes nativos Xano.

### D2. Seis estados dos casos e dois eixos da execução

| Estado do caso | Significado |
|---|---|
| `PASSED` | Executado e aprovado pelas assertions |
| `FAILED` | Executado; uma expectativa de comportamento não foi satisfeita |
| `ERROR` | Erro ao preparar, executar ou finalizar o caso, com resultado funcional inconclusivo |
| `SKIPPED` | O executor decidiu ignorar intencionalmente; motivo obrigatório |
| `NOT_RUN` | Não iniciado ou não selecionado neste escopo; motivo obrigatório |
| `BLOCKED` | Execução impedida por dependência, restrição ou autorização ausente; motivo obrigatório |

O runner normaliza os aliases históricos `PASS`/`FAIL` somente na leitura e valida o vocabulário antes da escrita. Não aceita status desconhecido como sucesso. Diagnósticos de processo/coleta ficam separados de `casos`; não criar teste funcional fictício para uma falha de instalação.

Cada resultado declara:

- `status_tecnico`: `PASSED`, `FAILED` ou `ERROR`, derivado de resultados e diagnósticos do processo; falha funcional e erro continuam contados separadamente.
- `nivel_validacao`: `COMPLETA`, `PARCIAL`, `BLOQUEADA` ou `NAO_EXECUTADA`, sempre relativo ao `escopo_validacao` explicitado. `COMPLETA` exige conclusão das verificações obrigatórias selecionadas; uma validação completa pode reprovar o comportamento. Aprovação integral exige também resultado técnico aprovado.

Um caso `ERROR` ou uma pendência obrigatória impede validação completa. Se há execução útil e qualquer obrigação pendente, o nível é `PARCIAL`; se tudo foi impedido, `BLOQUEADA`; sem execução nem impedimento caracterizado, `NAO_EXECUTADA`. Não confundir completude de uma suíte automatizada com aceite integrado dos roteiros. Passos manuais pendentes ficam no resultado de validação do roteiro e impedem sua aprovação geral mesmo com todas as suas verificações automatizadas aprovadas.

O conjunto obrigatório vem da seleção de suítes e do roteiro informado, e não de uma sprint fixa dentro do caso. `controlled`, quando apenas inventariada, fica fora da execução automática e é declarada como não executada/bloqueada no alcance funcional. Isso não cria execução fictícia nem concede aceite do roteiro.

Política de retorno:

| Situação | Processo/CI |
|---|---|
| Suíte aplicável com `FAILED` ou `ERROR` | Código não zero, depois de publicar relatórios |
| Erro de coleta, formato, identidade ou suíte obrigatória ausente | Código não zero, com diagnóstico separado |
| Pendência obrigatória sob `--require-complete` | Código não zero; nível parcial/bloqueado permanece explícito |
| Execução exploratória parcial sem falhas nem exigência de completude | Pode retornar zero; nunca produz aprovação integral |
| `--require-execution` e nenhum caso realmente executado | Código não zero; aprovação não é pré-requisito para contar execução |

Manter `--require-execution` e acrescentar `--require-complete` ao runner/consolidador. O CI exige completude das suítes previstas: autotestes, Reflex local, Xano estático, E2E público e Xano remoto puro. Falta de credencial da suíte remota obrigatória bloqueia essa validação e o resultado técnico do CI; não afeta a execução dos outros jobs. Não abrandar isso com `continue-on-error` ou retorno forçado a zero. Roteiros completos continuam fora do aceite automático enquanto tiverem passos sem evidência.

### D3. Um resultado normalizado, três projeções e origem conferível

O runner produz um objeto de execução versionado e os escritores existentes geram XML, JSON e Markdown desse objeto. `resultados.json` é o registro de execução para consumo e consolidação; não é outra fonte editável de metadados. Contagens e conclusão são calculadas uma vez e verificadas contra os casos.

Campos no nível da execução: versão do formato, ID único local ou contexto GitHub (`run_id`, `attempt`, `job` e URL), SHA esperado/observado, branch, árvore limpa ou alterada, início/fim UTC com fuso explícito, duração total, suíte, escopo, ferramentas, ambiente e dependências por disponibilidade. Em PRs, registrar o SHA efetivamente testado pelo checkout, sem substituí-lo pelo SHA da ponta do PR. Em execução local com alterações, SHA é a base, não prova do conteúdo integral.

Campos por caso: ID e variante, seletor técnico, nome, tipo (`UNITARIO`, `INTEGRACAO`, `E2E`, `ESTATICO`), componente, modo (`LOCAL`, `MOCK`, `REAL`), requisitos/cenários e pendência formal, esperado/obtido, estado, duração, motivo quando necessário, evidências relativas e origem da execução. Ambiente e horário comuns podem ser herdados da execução; não repetir centenas de vezes os mesmos valores.

JUnit conserva `tests`, `failures`, `errors` e `skipped`: `FAILED` vira `<failure>`, `ERROR` vira `<error>` e os três estados sem execução viram `<skipped>` com o estado original e justificativa no atributo `type`/mensagem. Assim, `skipped` no XML é a soma de `SKIPPED`, `NOT_RUN` e `BLOCKED`, e a discriminação continua recuperável. Identidade do caso fica em `name` e a da execução nas propriedades da suíte, evitando depender de propriedades de testcase que nem todo consumidor xUnit2 aceita. Resultado bruto pytest é evidência auxiliar, não outra execução somável aos resultados normalizados; os testes nativos complementam, e não duplicam, seus 25 casos Python.

Coleta deve reconhecer módulo/classe/variante completos, falhas de setup/teardown, coleta interrompida e casos desconhecidos. Resultado sem correspondência não é descartado. Um subprocesso com código não zero nunca é transformado em sucesso porque o XML está incompleto; ausência total de casos nunca aprova.

Toda execução utiliza destino exclusivo. O runner recusa destino não vazio, preservando seu conteúdo. O E2E organiza seu `servidor.log` no mesmo diretório novo e só publica ao concluir. O consolidador também recusa sobrescrita de saída histórica. Interrupção por timeout tratável produz diagnóstico e casos realmente não executados; encerramento forçado do runner é tratado pela ausência de artifact no consolidado.

O merge recebe suítes esperadas e identidade esperada da execução. Exige commit e, no CI, run/attempt compatíveis; recusa suíte repetida, casos repetidos na mesma origem e JSON inválido. Entradas ausentes ou incompatíveis ficam explicitadas no resultado consolidado, sem descartar as suítes válidas. Casos de uma fonte rejeitada não contam como aprovados. Evidência legada sem run é aceita somente em consolidação local explícita, com limitação de identidade e completude, nunca como artifact atual de CI.

### D4. Markdown curto e roteiro separado do resultado técnico

`resumo.md` mostra: identificação e links, objetivo/escopo, ambiente/dependências, totais por estado e por tipo/modo, requisitos/cenários verificados e associações pendentes, falhas/impedimentos, não executados agrupados por motivo, sprints/cards selecionados, evidências disponíveis e conclusão com limitações. Tabelas completas de todos os casos e assertions permanecem no JSON/XML. Agrupar motivos iguais, limitar listas extensas e apontar os IDs/detalhes; não esconder o total omitido.

`roteiros-<ciclo>.md` é opcional e gerado apenas para configurações selecionadas. `roteiros-sprint5.md` continua disponível para o snapshot existente, mantendo os links e as pendências; aprovação técnica dos casos não fecha etapas reais ou manuais. Verificação sem teste implementado é uma pendência do roteiro, não um testcase inventado.

### D5. Jobs independentes, publicação e decisão final

Preservar os nomes dos artifacts atuais. Separar as execuções em jobs sem dependência entre si: autotestes da infraestrutura, Reflex local/mock com estáticos Xano locais em suíte separada, E2E público e Xano remoto puro. Cada job publica sua evidência mesmo após falha tratável; o consolidado depende de todos apenas para obter seus resultados e usa `if: always()`.

Capturar o código de execução para produzir/uploadar relatórios antes do passo final que aplica o gate. Preservar a falha original do job; não usar tolerância irrestrita para mascarar falhas. O sucesso de um job de upload nunca substitui a conclusão dos testes. O executor de relatório precisa usar a biblioteca padrão para registrar erro mesmo se a instalação das dependências de produto falhar.

Downloads são independentes e a consolidação roda apesar da ausência de artifact. Informar ao consolidador os resultados de `needs`, as suítes esperadas e run/attempt/SHA atuais. Artifact obrigatório ausente produz diagnóstico e gate bloqueante. `if-no-files-found` deixa de ser apenas aviso para saídas obrigatórias. Usar os logs nativos do Actions para falhas de checkout/setup que impeçam até o diagnóstico; uma plataforma interrompida não permite garantir arquivo local, e o consolidado deve representar essa ausência.

O Job Summary contém os dois eixos, quantidades por estado/tipo, falhas bloqueantes, ausências, limites da validação e links do run/artifacts. Diretórios de entrada não são enviados como se fossem o consolidado. `gerador.xml` é incorporado como autoteste ou acompanhado de resumo normalizado próprio, sem somar esses testes à cobertura funcional. Não criar deploy nem acionamento automático de escrita no Xano.

### D6. Segurança e ambiente real

Manter a confirmação `CONFIRMO_WORKSPACE_DESCARTAVEL`, os endpoints HTTPS no host isolado e a autorização explícita de `--execute-controlled`. Os dois cenários CLI que fixam `v1` permanecem bloqueados até alteração específica de isolamento em outra change; este trabalho não os habilita.

Adicionar suíte `xano-static` somente com as oito verificações estáticas existentes da base compartilhada; a consulta HTTP da mesma classe de arquivo é selecionada separadamente e continua inventariada com dependência real. Não usar descoberta irrestrita de `tests/api` ou de `frontend/tests` em ambiente com `.env`, pois isso pode iniciar escrita real. Onde preciso, adaptar somente os helpers de teste para distinguir infraestrutura e exigir o guardião, preservando assertions funcionais.

O guardião de funções puras é aplicado tanto aos testes nativos quanto às funções efetivamente chamadas pelos 25 casos Python e a suas dependências. Manter lista explícita revisada; se o XanoScript local passar a acessar banco/API/redis ou dependência não revisada, bloquear o grupo afetado antes de chamar o remoto. Não alegar equivalência do código remoto com o SHA local sem comparação comprovada; registrar branch/datasource e essa limitação.

Nos dados publicados, preferir mensagens estruturadas e campos permitidos: não registrar corpos HTTP, headers, variáveis de ambiente, URLs privadas, nome/CPF/e-mail ou credenciais, inclusive códigos de login. Aplicar sanitização também no JSON, XML bruto, logs e metadados derivados das assertions. Manter URLs públicas de GitHub/Trello como referências validadas, separadas do texto arbitrário de falhas. Screenshots/traces só ficam publicáveis no E2E público controlado com dados seguros; integrações reais não ganham captura irrestrita. Arquivos não aprovados para publicação não entram no upload.

## Riscos e compromissos

- [Catálogo grande ou desatualizado] → Migrar apenas os casos já existentes, validar descoberta contra registros e manter cada metadado em um lugar; evitar inventário manual duplicado nos roteiros.
- [Migração dos estados afeta consumidores] → Leitura compatível de `PASS`/`FAIL`, versão de formato, adaptação dos autotestes e do adaptador Sprint 5 na mesma change.
- [Diferentes conjuntos parecem cobertura integral] → Escopo e obrigações explícitos; dimensões separadas; nenhum roteiro com passo obrigatório pendente recebe aprovação geral.
- [Ausência de secrets em PRs] → Registrar `BLOCKED`, manter jobs locais e publicação; falhar gate da suíte remota obrigatória sem imprimir valores de secrets.
- [Xano remoto diverge do Git ou fica indisponível] → Expor limite de equivalência, branch e dependência; não executar escrita nem atribuir sucesso a tentativas inconclusivas.
- [Timeout/cancelamento forte interrompe publicação] → Consolidador identifica suíte ausente; documentar limite da plataforma sem inventar resultado individual.
- [Sanitização regex não detecta nomes livres] → Minimizar o conteúdo capturado e validar lista de arquivos publicáveis; regex é defesa adicional.
- [Contagens históricas divergem] → Preservar arquivos originais e registrar a limitação ao lê-los, sem corrigir retroativamente seus resultados.

## Migração e verificação

1. Introduzir catálogo e estados normalizados com adaptação de leitura legada; verificar renomeação de seletor, casos repetidos e parametrização.
2. Refatorar coleta e escritores existentes, depois roteiros configuráveis e merge; migrar somente a configuração da Sprint 5, mantendo o histórico.
3. Ajustar o workflow e a documentação técnica na mesma change, com gates e artifacts coerentes com os comandos documentados.
4. Executar autotestes locais e suíte Reflex segura. Exercitar sucesso, falha, erro de setup/teardown/coleta, parcial, todos os estados sem execução, zero casos, XML/JSON inválido, artifact ausente, identidade incompatível e diretório já usado. Fixtures sintéticas testam a infraestrutura e não viram evidência de produto.
5. Validar consistência de IDs, contagens, duração e interpretação entre formatos; incluir uma segunda configuração de ciclo em teste temporário, sem cadastrar sprint ou card fictício no catálogo real.
6. Executar E2E público somente se servidor/navegador estiverem disponíveis e Xano puro somente se credenciais e guardião forem válidos. Registrar indisponibilidade como tal. Validar a topologia do YAML e, quando houver run real após publicação autorizada, conferir os artifacts e o Job Summary.

Rollback é a reversão dos scripts, catálogo, configurações e workflow desta change; não há migração de banco nem exclusão de evidências. Os documentos-base de domínio não precisam mudar porque nenhum comportamento clínico, entidade ou permissão é alterado.

Referências técnicas consultadas: [condições e dependências de jobs](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [publicação de artifacts](https://github.com/actions/upload-artifact) e [códigos de saída do pytest 8.4](https://docs.pytest.org/en/8.4.x/reference/exit-codes.html). As verificações de código de saída e publicação devem respeitar essas semânticas; sucesso de processo não demonstra aceite funcional além do escopo executado.

## Verificação dos artefatos desta proposta

`openspec status` reconheceu os quatro artefatos. `openspec validate aprimorar-evidencias-qualidade-testes --json` retornou `valid: true`, sem erros e com 12 avisos sobre ausência de `SHALL/MUST`. O modo `--strict` retornou código 1 pelos mesmos avisos. Os requisitos usam `DEVE`/`NÃO DEVE` conforme as instruções de idioma do repositório; o aviso do CLI refere-se expressamente à recomendação para specs em inglês. Não inserir palavras normativas em inglês nem alterar a ferramenta apenas para forçar aprovação estrita.

Não foram executados testes funcionais, E2E ou remotos nesta etapa de explore/propose. Foram feitas leituras, contagens das evidências existentes, descoberta estática e consultas públicas de metadados do GitHub. O exercício em memória de `execution_status` demonstra uma lacuna do vocabulário atual e não é execução de produto nem resultado gerado pelo modelo proposto.

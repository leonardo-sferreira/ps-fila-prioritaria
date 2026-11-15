# Implementação e evidências para revisão

Change `aprimorar-evidencias-qualidade-testes`, schema `spec-driven`. Implementação das **33/33 tarefas concluída**. Registro técnico de 14/11/2026, America/Sao_Paulo; as execuções usam UTC com fuso explícito. Não é documentação acadêmica final nem aceite funcional integrado.

## Progresso

| Etapa | Concluídas |
|---|---:|
| 1. Catálogo, estados e rastreabilidade | 4/4 |
| 2. Reflex local e coleta pytest | 4/4 |
| 3. Xano local, CLI e proteção HTTP | 5/5 |
| 4. Formatos e minimização | 4/4 |
| 5. Roteiros configuráveis | 4/4 |
| 6. Consolidação e gates | 4/4 |
| 7. GitHub Actions | 4/4 |
| 8. Verificação integrada e entrega | 4/4 |

O checklist individual está em [tasks.md](tasks.md).

## Alterações realizadas

- Catálogo `tests/catalogo_testes.json`: 421 IDs permanentes e 426 seletores/variantes reais, incluindo 40 autotestes de ferramenta em suíte própria. Os 17 autotestes preexistentes foram preservados e ampliados com 23 casos reais da infraestrutura. Nenhum RF/RNF/RN ou caso de produto fictício foi criado. Trinta registros de caso têm cenário OpenSpec identificado; as referências formais continuam pendentes.
- Runner: descoberta sem importar módulos, classificação por caso, seis estados, eixos técnico/completude, identidade de execução, destinos exclusivos, associação por módulo/classe/variante e diagnóstico separado de infraestrutura. Assertions e testes funcionais foram preservados.
- Xano: oito estáticos locais selecionados explicitamente; guardião para funções puras Python/nativas e dependências; erro de CLI separado de assertion funcional. Escrita exige isolamento e autorização; os dois cenários CLI fixados em `v1` continuam bloqueados. Nenhum XanoScript foi publicado e nenhum dado remoto de negócio foi modificado.
- XML/JSON/Markdown da mesma execução. Logs, HTTP, metadados de origem e erros usam campos permitidos e mensagens minimizadas. Canários sintéticos verificam CPF, nome, e-mail, token, código, segredo e URL privada. O workflow só envia os três arquivos canônicos.
- Snapshot dos cards 101–106 em `tests/roteiros/sprint5.json`, com 22 verificações e todas as pendências anteriores. Gerador comum `scripts/roteiros_testes.py`, adaptador histórico e seleção explícita de roteiro no merge. Outro ciclo foi exercitado somente em diretório temporário.
- Merge resiliente: suítes esperadas obrigatórias, validação de versão/commit/run/tentativa/duplicação, rejeição sem contar aprovações, fontes válidas preservadas, leitura legada local explícita e recusa de sobrescrita. Os estados técnicos e a completude também permanecem separados no roteiro, inclusive quando uma execução completa reprova.
- CI: cinco jobs independentes e consolidação com `always()`, retorno original aplicado após evidências, downloads independentes, três arquivos obrigatórios, Job Summary e nomes históricos dos artifacts preservados. YAML parseado por Ruby/Psych e todos os blocos Bash conferidos com `bash -n`. A preparação foi simulada sem dependências com `python -S`: três formatos produzidos, retorno 1, zero aprovações; fixture temporária, fora do consolidado do produto.
- Guia comum [docs/testes-qualidade.md](../../../../docs/testes-qualidade.md), README, CONTRIBUTING e documentação histórica da Sprint 5 atualizados.

## Resultados observados

| Suíte/resultado | PASSED | FAILED | ERROR de caso | BLOCKED | Retorno | Validação |
|---|---:|---:|---:|---:|---:|---|
| `autotestes` | 40 | 0 | 0 | 0 | 0 | `COMPLETA` |
| `reflex` | 250 | 0 | 0 | 0 | 0 | `COMPLETA` |
| `xano-static` | 8 | 0 | 0 | 0 | 0 | `COMPLETA` |
| `xano-safe` | 97 | 0 | 0 | 0 | 0 | `COMPLETA` |
| `e2e` | 0 | 0 | 0 | 2 | 1 | `BLOQUEADA` |
| `controlled` | 0 | 0 | 0 | 29 | 1 | `BLOQUEADA` |
| `consolidado` | 395 | 0 | 0 | 2 | 1 | `PARCIAL` |

Não houve casos `SKIPPED` ou `NOT_RUN` nas evidências finais acima. Os 395 aprovados do consolidado incluem **355 casos do produto e 40 autotestes da ferramenta**; não representam requisitos formais cobertos. Os 29 controlados não integram as cinco suítes obrigatórias desse consolidado e estão registrados separadamente como bloqueados.

A suíte `xano-safe` executou 25 testes Python e 72 testes nativos, todos aprovados, após o guardião e o preflight. Sua duração registrada foi 1585.871 segundos. Funções puras remotas não comprovam persistência nem equivalência integral do código publicado com o Git.

O E2E não foi executado: falta o executável Chromium. Seus dois casos estão `BLOCKED`; o diagnóstico de preparação faz o resultado técnico da suíte e do consolidado ser `ERROR`, sem criar caso funcional fictício. O gate do consolidado retornou **1**, depois de produzir os três formatos, preservando essa restrição e as pendências do roteiro.

O roteiro da Sprint 5 apresenta **19 verificações com PASS técnico, 3 PENDENTE e 22 etapas/obrigações manuais ainda sem evidência**. Resultado técnico do roteiro `PASSED`, validação funcional `PARCIAL`, aprovação integral falsa.

Os autotestes tiveram falhas intermediárias durante a implementação: 32/38, 38/40 e 39/40 em rodadas de fixtures/coleta; uma rodada isolada do pipeline teve 13/14 por importação do helper. Foram corrigidas antes da rodada final, que registrou **40/40**. Não foram removidas assertions do produto para obter aprovação. As regressões exercitam sucesso, assertion reprovada, erro, seis estados, timeout com resultado parcial, zero casos, XML/JSON inválido, fonte ausente, identidade incompatível, duplicação, diretório já utilizado e ausência de dependências; suas fixtures ficam separadas das evidências do produto.

## Comandos e arquivos

Comandos de execução observados (destinos já utilizados; para repetir, escolha outros):

```bash
.venv/bin/python scripts/run_test_evidence.py --suite autotestes --output test-evidence/aprimorar-qa-entrega/autotestes --require-execution --require-complete
.venv/bin/python scripts/run_test_evidence.py --suite reflex --output test-evidence/aprimorar-qa-revisao/reflex --require-execution --require-complete
.venv/bin/python scripts/run_test_evidence.py --suite xano-static --output test-evidence/aprimorar-qa-revisao/xano-static --require-execution --require-complete
.venv/bin/python scripts/run_test_evidence.py --suite xano-safe --output test-evidence/aprimorar-qa-etapa3-xano-safe --require-execution --require-complete
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python scripts/run_reflex_e2e_ci.py --output test-evidence/aprimorar-qa-etapa2-e2e
.venv/bin/python scripts/run_test_evidence.py --suite controlled --output test-evidence/aprimorar-qa-controlled-inventario --require-complete
.venv/bin/python scripts/merge_test_evidence.py \
  --input test-evidence/aprimorar-qa-entrega/autotestes --expected-suite autotestes \
  --input test-evidence/aprimorar-qa-revisao/reflex --expected-suite reflex \
  --input test-evidence/aprimorar-qa-revisao/xano-static --expected-suite xano-static \
  --input test-evidence/aprimorar-qa-etapa2-e2e --expected-suite e2e \
  --input test-evidence/aprimorar-qa-etapa3-xano-safe --expected-suite xano-safe \
  --roteiro tests/roteiros/sprint5.json --output test-evidence/aprimorar-qa-entrega/consolidado \
  --require-execution --require-complete
```

- `test-evidence/aprimorar-qa-entrega/execucoes.json`: caminhos, códigos observados, IDs, horários, duração, eixos e contagens por suíte.
- `test-evidence/aprimorar-qa-entrega/consolidado/`: `resultados.json`, `resultados.xml`, `resumo.md` e `roteiros-sprint5.md`.
- `test-evidence/aprimorar-qa-revisao/openspec/normal.json` e `strict.json`: validações OpenSpec.
- `test-evidence/aprimorar-qa-revisao/checagens/verificacoes.json`: escopo, histórico, YAML/Bash e fallback da biblioteca padrão.

Os formatos das sete evidências acima foram inspecionados: identidade e cardinalidade únicas por origem, contagens, falhas, erros, omissões, duração dos casos e conclusões coerentes. Os 110 arquivos históricos existentes antes do apply foram conferidos por SHA-256 e permanecem intactos. Evidências locais continuam ignoradas pelo Git.

## OpenSpec e limites restantes

`openspec validate aprimorar-evidencias-qualidade-testes --json`: **retorno 0, valid=true**. `openspec validate aprimorar-evidencias-qualidade-testes --json --strict`: **retorno 1, valid=false** pelos mesmos **12 avisos normativos conhecidos** sobre `SHALL/MUST`. São avisos da recomendação para inglês, enquanto os requisitos usam `DEVE` conforme a regra do projeto. **Nenhum problema novo e nenhum ERROR de validação**. Não foram inseridas palavras normativas em inglês para forçar o strict.

Pendências: disponibilizar Chromium/servidor controlado para executar o E2E; conferir referências formais no Confluence; concluir verificações reais/manuais do snapshot histórico; revisar o diff e, após publicação autorizada futura, conferir um run real do novo workflow. Este apply não publicou a branch nem acionou Actions. Não há mudanças de domínio, entidades, endpoints, schema, banco ou código funcional do frontend. A implementação foi apresentada para revisão, sem arquivamento automático nesta etapa.

## Arquivamento autorizado

Em 15/11/2026, o usuário aprovou o arquivamento e o commit da implementação. Os 12 requisitos e o Purpose de `evidencias-testes` foram sincronizados integralmente em `openspec/specs/evidencias-testes/spec.md`, sem alterar seu texto. A validação normal das 16 specs principais passou; a nova spec conserva os 12 avisos normativos de idioma já conhecidos.

O arquivamento preserva as limitações registradas: E2E impedido pela ausência de Chromium, verificações manuais pendentes e confirmação formal no Confluence ainda não realizada. A aprovação para arquivar não representa aceite funcional integrado nem altera os resultados históricos dos testes.

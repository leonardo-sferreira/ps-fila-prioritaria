# Tarefas

Todas as tarefas abaixo pertencem ao apply posterior à revisão desta proposta. A auditoria já está no design; nenhum resultado histórico deve ser apresentado como nova execução. Não publicar ou executar escrita no Xano nesta change.

## 1. Catálogo, estados e rastreabilidade comuns

- [x] 1.1 Criar `tests/catalogo_testes.json` com os casos reais atualmente descobertos, IDs funcionais permanentes, variantes, seletores, aliases históricos, tipo/modo, segurança e referências identificáveis; usá-lo no runner e verificar correspondência com a descoberta, sem cadastrar requisito ou caso inexistente.
- [x] 1.2 Refatorar a descoberta em `scripts/run_test_evidence.py` para consumir o catálogo e detectar IDs/seletor duplicados, casos sem registro, removidos e variantes ambíguas; ampliar `tests/test_evidence_runner.py` e verificar renomeação de arquivo/função sem mudar ID, homônimos e parametrização.
- [x] 1.3 Implementar normalização dos seis estados e os eixos `status_tecnico`/`nivel_validacao`, com escopo e obrigações explícitos; manter entrada `PASS`/`FAIL`, rejeitar estado desconhecido e verificar todos os estados, mistura parcial, erro e ausência total nos autotestes.
- [x] 1.4 Criar `docs/testes-qualidade.md`, usado como guia comum de execução e interpretação, com catálogo, referências pendentes e semântica dos estados/eixos; verificar que os campos documentados coincidem com o modelo implementado e que nenhuma associação formal é apresentada como conferida sem fonte.

## 2. Reflex local e coleta pytest

- [x] 2.1 [Reflex] Substituir classificação por arquivo por metadados por caso e manter seleção explícita dos testes locais/mock, excluindo os módulos remotos; verificar o inventário e executar a suíte local pelo runner, sem chamadas reais, preservando todas as assertions funcionais existentes.
- [x] 2.2 [Reflex/infraestrutura] Refatorar a coleta para associar módulo, classe e variante, preservar falhas de setup/teardown e detectar resultados desconhecidos, coleta interrompida, XML inválido e códigos de saída não zero; verificar com fixtures sintéticas nos autotestes, sem usá-las como evidência do produto.
- [x] 2.3 Refatorar a criação de execução/destino e `scripts/run_reflex_e2e_ci.py` para impedir reutilização de `pytest.xml`, eventos HTTP e logs antigos; verificar em diretórios temporários que uma saída não vazia é recusada sem modificação e que timeout tratável preserva resultados disponíveis.
- [x] 2.4 Registrar início/fim, duração, SHA testado, árvore alterada e contexto GitHub disponível no modelo comum, inclusive origem por suíte; verificar execução local, metadados CI simulados e ausência legítima de dados, e atualizar o guia comum com a estrutura dos relatórios.

## 3. Xano estático, remoto puro e integrações protegidas

- [x] 3.1 [Xano/local] Acrescentar `xano-static` ao runner selecionando somente `AuditoriaTest` e `ParametrosTest` de `tests/api/test_base_compartilhada.py`; inventariar sua consulta HTTP separadamente, executar as oito verificações locais e comprovar por mock que a suíte estática não inicia rede ou CLI remoto.
- [x] 3.2 [Xano/CLI] Aplicar o guardião de pureza também às funções chamadas pelos testes Python e dependências revisadas, além dos nativos; verificar bloqueio anterior à chamada remota quando fixture local introduzir acesso proibido ou dependência não revisada.
- [x] 3.3 [Xano/CLI] Separar erros de autenticação/transporte/CLI das falhas de assertions nos helpers e no runner, sem alterar regras testadas; verificar respostas de sucesso, reprovação nativa, timeout, JSON inválido, teste nativo ausente e credencial ausente com subprocessos simulados.
- [x] 3.4 [Xano/HTTP] Preservar `controlled_gate`, exigir confirmação/host isolado/autorização antes da escrita e manter os dois cenários CLI fixados na `v1` bloqueados; verificar negativa para cada pré-condição ausente e ausência de subprocesso/requisição de escrita, sem usar ambiente real.
- [x] 3.5 Atualizar o guia comum e os comandos de teste em `README.md`/`CONTRIBUTING.md` para separar estáticos locais, mocks, remoto puro e escrita isolada; remover a descoberta ampla e a execução de chamada com escrita como recomendação genérica, verificando comandos seguros e as limitações declaradas.

## 4. XML, JSON, Markdown e publicação segura

- [x] 4.1 Refatorar os escritores existentes para usar a mesma execução normalizada versionada, com diagnósticos de infraestrutura separados dos casos e JUnit preservando os três estados sem execução; verificar identidades, totais, falhas, erros, omissões e duração com cenários nos seis estados.
- [x] 4.2 Reescrever `resumo.md` e o Job Summary para incluir os elementos da spec em formato conciso, agrupando pendências e apontando IDs/detalhes no JSON/XML; verificar aprovação limitada ao escopo, roteiro incompleto, centenas de casos e motivos repetidos sem reproduzir a tabela bruta inteira.
- [x] 4.3 Refatorar sanitização/minimização no runner e em `scripts/pytest_http_evidence.py`, com lista de conteúdo/arquivos publicáveis e referências públicas validadas; verificar canários sintéticos de CPF, nome, e-mail, token, código, segredo e URL privada em todos os formatos/logs, sem incluir seus valores reais.
- [x] 4.4 Documentar no guia comum os arquivos canônicos, auxiliares, projeção JUnit e limites de screenshots/traces públicos; conferir que todos os arquivos citados são produzidos nas condições descritas e que os uploads usam somente conteúdo publicável.

## 5. Roteiros e sprints configuráveis

- [x] 5.1 Migrar o snapshot existente para `tests/roteiros/sprint5.json`, usado pelo gerador de roteiros, preservando os cards 101–106, links, verificações e pendências, substituindo seletores por IDs do catálogo sem duplicar nomes/resultados esperados; verificar a migração contra a estrutura existente.
- [x] 5.2 Criar `scripts/roteiros_testes.py` pela refatoração do gerador atual, usá-lo no consolidador com configuração explícita e manter `scripts/roteiros_sprint5.py` como adaptador histórico; adaptar `tests/test_roteiros_sprint5.py` e verificar estados antigos/novos, teste ausente, etapas manuais pendentes e invocação compatível.
- [x] 5.3 Verificar reutilização dos mesmos IDs em outra configuração de ciclo criada somente em diretório temporário, sem editar o código central nem inventar sprint/card reais; verificar que o consolidado sem seleção de roteiro não gera arquivo fixo da Sprint 5.
- [x] 5.4 Atualizar `docs/testes-roteiros-sprint5.md` para referenciar o guia comum e a seleção explícita do snapshot; documentar cadastro de ciclo e regressão por IDs no guia comum, verificando os comandos e preservando o histórico documental.

## 6. Consolidação e política de gates

- [x] 6.1 Refatorar `scripts/merge_test_evidence.py` para receber suítes/identidade esperadas, validar formato, commit, run, tentativa e duplicação e manter origem por suíte; verificar mistura de commits, mesmo commit com run/attempt distintos e entrada repetida, sem contar aprovações das fontes rejeitadas.
- [x] 6.2 Gerar os três formatos também com JSON ausente/corrompido, suíte esperada ausente ou nenhuma fonte válida, preservando fontes confiáveis e diagnósticos separados; verificar ausência individual e total, contagens coerentes, leitura legada local explícita e recusa de sobrescrita de saída histórica.
- [x] 6.3 Manter `--require-execution` e implementar `--require-complete` no runner e merge conforme a política do design; verificar códigos reais dos comandos para sucesso, falha, erro, parcial permitida, parcial bloqueante, tudo ignorado/bloqueado e zero casos, sem converter falha em zero.
- [x] 6.4 Documentar no guia comum a seleção obrigatória de suítes, retorno dos comandos e consolidação local, com distinção entre aceite automatizado e roteiro completo; verificar que os exemplos refletem os gates efetivamente implementados.

## 7. GitHub Actions

- [x] 7.1 Refatorar `.github/workflows/ci.yml` para separar autotestes, Reflex local/mock com suíte Xano estática distinta, E2E público e Xano remoto puro em execuções independentes; preservar gatilhos, permissões mínimas, versões existentes salvo incompatibilidade comprovada e nomes atuais de artifacts, verificando a topologia e a seleção explícita dos testes.
- [x] 7.2 Capturar resultado técnico e produzir/uploadar evidências com condições que executem após falha, aplicando o gate ao final; normalizar também autotestes em evidência própria, verificar por cenários locais simulados falha de teste/instalação/inicialização e comprovar que publicar não substitui o resultado original.
- [x] 7.3 Tornar downloads independentes e consolidar com `always()` e suítes esperadas, resultados de `needs` e contexto SHA/run/attempt; verificar configuração de artifact ausente, política de arquivos obrigatórios e publicação do diagnóstico sem impedir o processamento das fontes disponíveis.
- [x] 7.4 Publicar Job Summary com os dois eixos, totais, falhas bloqueantes, ausências e referências de artifacts; atualizar a seção de CI do guia comum e conferir YAML, caminhos e compatibilidade dos comandos. Se não houver execução remota autorizada após publicação, registrar que o workflow foi validado localmente e que o run novo ainda não ocorreu.

## 8. Verificação integrada e evidência da entrega

- [x] 8.1 Executar os autotestes de infraestrutura/roteiros, a suíte Reflex local e `xano-static` pelo ambiente disponível, em saídas novas; entregar resultados reais e conferir IDs/contagens/conclusões dos três formatos, mantendo fixtures de teste da ferramenta separadas dos casos do produto.
- [x] 8.2 Executar E2E público somente com servidor/navegador disponíveis e Xano puro somente com credenciais/guardião válidos; para dependências indisponíveis, gerar evidência de impedimento com motivo e não declarar execução. Continuar sem executar escrita remota.
- [x] 8.3 Gerar e inspecionar um consolidado real e, quando selecionado, o roteiro histórico com todas as limitações; entregar caminhos do exemplo, comandos, códigos de saída e pendências, verificando que não há aprovação integral indevida nem alteração de evidências antigas.
- [x] 8.4 Conferir diff restrito ao escopo autorizado, documentação e catálogo sem segredos, preservação dos testes funcionais e ausência de mudanças de domínio/banco; executar `openspec validate aprimorar-evidencias-qualidade-testes --json` e também `--strict`, registrar separadamente os avisos de idioma conhecidos e qualquer novo problema, e apresentar a change implementada para revisão antes do arquivamento.

# Design

## Context

O `run_test_evidence.py` já gera `resultados.json` com estado por caso e o `merge_test_evidence.py` consolida as suites do CI. A tabela `resumo.md` é completa, porém extensa. Os testes locais da interface usam estados Reflex com API simulada; a suite segura do Xano executa funções puras. A suite `controlled` escreve dados e não roda no CI por falta de workspace descartável confirmado.

## Objetivos e limites

**Objetivos:** acrescentar asserções locais úteis para os passos implementados, criar uma vista por roteiro com linguagem de documentação e preservar os resultados detalhados como evidência auditável.

**Limites:** o relatório não atribui aprovação integral a um card por causa de testes unitários ou simulados; não executa testes de escrita na branch live, nem testa funcionalidades ausentes.

## Decisões

1. **Ampliar os testes existentes.** Os novos casos entram nos módulos Reflex de pré-triagem e comprovante, junto aos testes do mesmo estado. Isso reaproveita os fixtures locais e a coleta atual, sem criar uma suite concorrente.
2. **Gerar vista resumida a partir do JSON consolidado.** Um módulo em `scripts/` mantém um catálogo explícito dos seis cards abertos (101–106), das verificações disponíveis e dos nomes dos testes que lhes dão evidência. O relatório consulta os status de execução reais por `node`; um teste ausente, ignorado ou não executado nunca aparece como aprovado.
3. **Mostrar o alcance da evidência.** Cada linha diferencia regra pura, estado Reflex simulado ou interface pública. A coluna de pendências registra as partes do roteiro que ainda exigem API real, navegador autenticado ou implementação futura. A aprovação técnica de um caso não encerra o roteiro manual.
4. **Publicar junto às evidências existentes.** O consolidado continua gerando XML, JSON e `resumo.md` e passa a incluir `roteiros-sprint5.md`. O CI já envia o diretório inteiro como artifact. O autoteste do gerador entra no passo de verificação de evidências.

Alternativas descartadas: copiar a tabela de centenas de casos para a documentação (pouco legível) e executar os testes de escrita existentes na `v1` (sem isolamento comprovado).

## Riscos e medidas

- [Rastreabilidade desatualizada quando um teste for renomeado] → o relatório mostra `SEM EVIDÊNCIA` para o seletor sem correspondência, e os autotestes conferem esse comportamento.
- [Sucesso do CI interpretado como aceite completo dos cards] → cabeçalho e coluna de pendências dizem explicitamente o alcance técnico de cada resultado.
- [Dados pessoais nos artifacts] → o relatório usa apenas nomes de testes, status e URLs dos cards; não imprime entradas ou respostas HTTP.

## Entrega e reversão

Executar os autotestes do gerador, os testes Reflex afetados, a compilação Reflex e a geração local do relatório. O artifact passa a conter um arquivo adicional; a reversão consiste em remover o módulo gerador e sua chamada no consolidador, sem migração de dados.

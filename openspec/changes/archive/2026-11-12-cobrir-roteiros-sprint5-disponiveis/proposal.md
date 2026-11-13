# Change: cobrir-roteiros-sprint5-disponiveis

Sprint: 5 — Painel Público, Testes e Apresentação
Cards no Trello: 101 a 106, somente abertos no JSON exportado em 12/11/2026
Depende de: funcionalidades já presentes no repositório; não depende das telas administrativas nem do painel público ainda não entregues
Situação: implementada e verificada localmente

## Why

Os seis roteiros abertos da Sprint 5 estão escritos como passos manuais, enquanto os resultados automatizados atuais aparecem em uma tabela longa de casos técnicos sem ligação clara aos cards. É preciso verificar as partes já implementadas e produzir uma evidência legível para a documentação sem apresentar cobertura parcial como aprovação do roteiro completo.

## What Changes

- Acrescentar testes automatizados pontuais para passos disponíveis dos roteiros de pré-triagem e privacidade do comprovante que ainda não têm asserções diretas.
- Relacionar os seis cards abertos aos casos automatizados existentes e novos, com limites de cada evidência.
- Gerar um relatório Markdown curto por roteiro a partir dos resultados reais, indicando aprovações técnicas, falhas, testes não executados e passos pendentes.
- Integrar o relatório ao artifact consolidado do CI e testar o próprio gerador.

Fora do escopo: card de integração ponta a ponta, cards fechados, APIs de escrita contra o Xano live, implementação de funcionalidades pendentes, regras clínicas ou de domínio e alteração de dados reais.

## Capabilities

### New Capabilities

Nenhuma. Esta change altera apenas testes, rastreabilidade e apresentação de evidências.

### Modified Capabilities

Nenhuma. Os requisitos de comportamento existentes permanecem os mesmos.

## Impact

Arquivos de teste locais do Reflex, gerador e consolidação de evidências em `scripts/`, documentação de testes e artifact `evidencias-consolidadas`. Nenhum endpoint ou tabela é alterado.

## Perguntas em aberto

Nenhuma para o escopo de testes locais e relatório. Os passos que exigem funcionalidade pendente ou ambiente de escrita isolado permanecem identificados como pendentes.

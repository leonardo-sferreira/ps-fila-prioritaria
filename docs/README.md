# Documentação do Prioriza — Sistema de Fila Prioritária para Pronto-Socorro

A documentação está dividida em cinco blocos, cada um para um público. Os arquivos marcados com ⚙ são gerados do código por `python scripts/gerar_docs.py` e não devem ser editados à mão.

## 1. Uso — usuários e negócio

| Documento | Conteúdo |
|---|---|
| [Guia por perfil](uso/guia-por-perfil.md) | O que cada perfil vê e opera em cada tela, os dados que insere e o tipo de cada campo |
| [Glossário e regras de negócio](uso/glossario-e-regras.md) | Termos do domínio e as regras e cálculos que o sistema aplica no dia a dia |
| [Início rápido e FAQ](uso/inicio-rapido-e-faq.md) | Primeiros passos de cada perfil, quem cadastra quem e solução de dúvidas e erros comuns |

## 2. Manutenção — desenvolvedores

| Documento | Conteúdo |
|---|---|
| [Arquitetura e stacks](manutencao/arquitetura.md) | Tecnologias, divisão do repositório e como frontend, API e banco se conectam |
| ⚙ [Mapa tela → estado → API](manutencao/mapa-telas-api.md) | Qual tela usa qual estado e quais endpoints cada estado chama |
| ⚙ [Contratos de API](manutencao/contratos-api.md) | Os 71 endpoints: acesso, entrada, resposta e mensagens de erro |
| [Configuração, secrets e regras no código](manutencao/configuracao-e-regras.md) | Variáveis de ambiente, parâmetros editáveis e onde cada regra de negócio está implementada |
| ⚙ [Funções do Xano](manutencao/funcoes-xano.md) | Funções com regras de negócio e seus testes nativos |
| [Modelo de dados — caminho funcional](manutencao/modelo-de-dados.md) | Como o dado entra, por onde passa e em que tabelas fica, por bloco lógico |
| ⚙ [Dicionário de dados e DER](manutencao/dicionario-de-dados.md) | Todas as tabelas e campos, com o diagrama entidade-relacionamento |
| [Guia de desenvolvimento](manutencao/guia-de-desenvolvimento.md) | Requisitos, instalação, primeira execução, testes e fluxo de trabalho |

## 3. Sustentação — produção, operação e suporte

| Documento | Conteúdo |
|---|---|
| [Deploy e ambientes](sustentacao/deploy-e-ambientes.md) | Onde cada parte roda, a esteira PR → CI → merge → publicação e o passo a passo |
| [Runbooks e depuração](sustentacao/runbooks-e-depuracao.md) | Como investigar falhas, reiniciar e voltar uma versão |
| [Tratamento de erros e métricas](sustentacao/erros-e-metricas.md) | O que cada erro significa, o que verificar e o que monitorar |
| [Validações operacionais](sustentacao/validacoes-operacionais.md) | Simulação de publicação, testes ponta a ponta e evidências |
| [Suporte e governança](sustentacao/suporte-e-governanca.md) | Quem cuida de quê, como pedir suporte, escalonamento e registro de incidentes |

## 4. Evolução — arquitetura e tech lead

| Documento | Conteúdo |
|---|---|
| ⚙ [Inventário de dependências (SBOM)](evolucao/dependencias.md) | Plataformas, bibliotecas e versões |
| [Testes de regressão e atualização](evolucao/testes-de-regressao.md) | Como garantir que uma atualização não quebrou o que já funciona |
| ⚙ [Changelog](evolucao/changelog.md) | O que foi entregue em cada sprint |
| [Guia de migração](evolucao/guia-de-migracao.md) | Como mudar versões de bibliotecas, do esquema do banco e de parâmetros |

## 5. Testes

| Documento | Conteúdo |
|---|---|
| [Estratégia de testes](testes/estrategia-de-testes.md) | Tipos de teste, como são feitos, como rodar e como ler as evidências; roteiros manuais |
| ⚙ [Catálogo de testes](testes/catalogo-de-testes.md) | Todos os casos automatizados, com entrada, saída esperada e código |

## Documentos de referência já existentes

- [Visão geral do projeto](project-overview.md) e [modelo de domínio](domain-model.md): base de negócio aprovada pelo PO.
- [Aviso de privacidade](aviso-de-privacidade.md): texto mostrado em `/privacidade`.
- [Guia de QA](testes-qualidade.md) e [roteiros da Sprint 5](testes-roteiros-sprint5.md): infraestrutura de evidências de testes.
- Especificações implementadas: [`openspec/specs/`](../openspec/specs/).
- Protótipo: [Figma](https://www.figma.com/design/38ro8aKQfiGkUivIfCaOR1) e [FigJam](https://www.figma.com/board/qwAbdFLbo9lRuOym4vDSBI).

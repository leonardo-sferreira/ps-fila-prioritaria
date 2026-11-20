# Documentação do Prioriza

O projeto tem duas documentações, uma para cada público.

| Documentação | Para quem | Conteúdo |
|---|---|---|
| 📘 **[Manual do usuário](usuario/manual-do-usuario.md)** | Equipe do PS, avaliadores e quem vai conhecer o sistema | O que o sistema faz, como usar cada tela por perfil, as regras explicadas de forma simples e perguntas frequentes |
| 🛠️ **[Documentação técnica](tecnica/README.md)** | Desenvolvedores e quem vai manter, operar ou evoluir o sistema | Arquitetura, decisões, regras no código, dados, API, configuração, operação, testes realizados, limitações e anexos de referência |

As duas também estão publicadas como site em **[leonardo-sferreira.github.io/ps-fila-prioritaria/](https://leonardo-sferreira.github.io/ps-fila-prioritaria/)** (HTML e CSS em `site/`, publicado pelo GitHub Actions a cada merge na `main`).

## Estrutura da pasta

```
docs/
├── README.md                  este índice
├── usuario/
│   └── manual-do-usuario.md   documentação de uso
├── tecnica/
│   ├── README.md              documentação técnica (documento principal)
│   ├── manutencao/            arquitetura, contratos de API, dados, configuração, guia de desenvolvimento
│   ├── sustentacao/           deploy, runbooks, erros e métricas, validações, suporte
│   ├── evolucao/              dependências, regressão, changelog, migração
│   ├── testes/                estratégia e catálogo de testes
│   └── referencia/            regras de negócio detalhadas, telas e campos, FAQ operacional
├── project-overview.md        visão geral e decisões do PO (base de negócio)
├── domain-model.md            modelo de domínio
├── aviso-de-privacidade.md    texto exibido em /privacidade
├── testes-qualidade.md        infraestrutura de evidências de testes
└── testes-roteiros-sprint5.md roteiros manuais da Sprint 5
```

Os arquivos marcados com ⚙ na documentação técnica são gerados do código por `python scripts/gerar_docs.py`.

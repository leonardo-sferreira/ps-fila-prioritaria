# Change: aprimorar-evidencias-qualidade-testes

| Campo | Valor |
|---|---|
| Sprint | Não atribuída; preserva o histórico da Sprint 5 e admite outros ciclos por configuração |
| Card no Trello | Nenhum card novo informado; referências históricas aos cards 101–106 preservadas |
| Depende de | Infraestrutura atual de pytest, Reflex, CLI Xano e GitHub Actions |
| Situação | Arquivada em 15/11/2026 após revisão e autorização do usuário |

## Why

O repositório já produz evidências em JUnit XML, JSON e Markdown, mas a aprovação técnica das suítes pode ser confundida com validação completa: o consolidado histórico de 335 casos aprovados convive com três verificações pendentes nos roteiros da Sprint 5. IDs derivados de nomes de arquivos, classificação por arquivo e interrupção da consolidação quando falta um artifact também fragilizam a rastreabilidade e o diagnóstico de falhas.

## What Changes

- Padronizar os estados dos casos como `PASSED`, `FAILED`, `ERROR`, `SKIPPED`, `NOT_RUN` e `BLOCKED`, preservando a leitura de evidências históricas com `PASS`/`FAIL`.
- Separar resultado técnico do processo, completude do escopo automatizado e nível de validação funcional; definir falhas bloqueantes e impedir conclusão integral com verificações obrigatórias pendentes.
- Centralizar metadados em um catálogo versionado com IDs funcionais permanentes, classificação por caso, referências verificáveis e associação formal pendente quando não confirmada no Confluence.
- Gerar os três formatos a partir da mesma execução normalizada, com commit, identidade do run, ambiente, duração, origem e justificativas; detectar resultados ausentes, incompatíveis, duplicados ou reaproveitados de outra execução.
- Retirar a dependência fixa da Sprint 5 do consolidador, migrando os roteiros existentes para dados de configuração por ciclo, referenciados pelos IDs permanentes dos casos.
- Evoluir o workflow existente para preservar a independência das suítes, publicar evidências de falhas e ausências, consolidar o que estiver disponível e aplicar o resultado técnico após produzir os relatórios.
- Documentar comandos seguros, interpretação dos estados, catálogo, sprints e limitações; verificar geradores e política de CI com cenários locais controlados.

## Capacidades

### Novas capacidades

- `evidencias-testes`: contrato técnico de descoberta, classificação, rastreabilidade, publicação e interpretação das evidências de QA. Seus requisitos descrevem a infraestrutura solicitada; não criam RF, RNF ou RN do produto.

### Capacidades modificadas

Nenhuma regra funcional existente muda. As specs de privacidade, auditoria e parâmetros foram consultadas como contexto; seus comportamentos permanecem fora desta change.

## Impacto

- Refatoração dos scripts existentes em `scripts/`, dos autotestes de evidência em `tests/` e de `.github/workflows/ci.yml`.
- Inclusão do catálogo de casos e da configuração dos roteiros usados nesta entrega; reaproveitamento dos arquivos e nomes dos artifacts atuais.
- Inclusão dos testes estáticos locais de `tests/api/test_base_compartilhada.py` na execução explícita, mantendo sua consulta HTTP separada e dependente de ambiente.
- Ajustes pontuais em `README.md`, `CONTRIBUTING.md` e `docs/testes-roteiros-sprint5.md`, com um guia técnico comum de QA.
- **Compatibilidade:** `PASSED`/`FAILED` passam a ser a saída canônica; a entrada histórica `PASS`/`FAIL` continua legível sem reescrever evidências antigas. XML continua sendo JUnit e os nomes `resultados.xml`, `resultados.json` e `resumo.md` são mantidos.
- Sem novas dependências ou serviços. Não altera endpoints, tabelas, regras de negócio, `docs/project-overview.md` ou `docs/domain-model.md`.

## Fora do escopo

- Documentação acadêmica final, publicação ou atualização de cards e requisitos em serviços externos.
- Corrigir funcionalidades pendentes, ampliar cobertura funcional sem necessidade desta infraestrutura ou alterar assertions para produzir aprovação.
- Executar integrações com escrita em workspace compartilhado/produção, publicar XanoScript ou criar dados remotos.
- Apagar, regenerar ou corrigir retroativamente arquivos históricos de `test-evidence/`.
- Declarar cobertura por requisito ou aceite integral a partir de testes com mocks, funções puras ou do sucesso do pipeline.

## Perguntas em aberto

- Sprint e card da melhoria ainda não foram informados; a proposta pode ser revisada e implementada com essa associação explicitamente pendente.
- O Confluence não está disponível entre as fontes conectadas desta sessão. Os códigos citados nos testes são referências preexistentes, com confirmação formal pendente. Há divergência de referência documental: `openspec/config.yaml` cita Word externo, enquanto `AGENTS.md` e os documentos-base apontam Confluence; esta change não redefine requisitos formais.
- Integrações reais continuam condicionadas a credenciais, identificação segura do ambiente e, para escrita, isolamento e autorização explícita. A falta dessas condições deve aparecer nas evidências sem ser apresentada como execução.

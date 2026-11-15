## Purpose

Permitir que mantenedores e ferramentas de CI interpretem e rastreiem resultados de testes do Reflex e do Xano com evidências consistentes, distinguindo execução técnica de validação funcional e preservando o histórico do projeto.

## ADDED Requirements

### Requirement: Identidade permanente dos casos e fonte única de metadados
A infraestrutura DEVE identificar cada caso por ID funcional permanente independente do arquivo, função ou sprint e manter seus metadados em uma única fonte editável. Seletores técnicos e variantes DEVEM resolver para identidade inequívoca. IDs duplicados, vínculos ambíguos e divergências entre descoberta e catálogo DEVEM ser diagnosticados sem descarte silencioso.

#### Scenario: Renomeação sem perda de rastreabilidade
- **QUANDO** um teste é renomeado ou movido e seu seletor técnico é atualizado
- **ENTÃO** seu ID funcional e suas associações históricas permanecem os mesmos
- **E** novas execuções continuam vinculadas ao mesmo caso

#### Scenario: Parametrizações e homônimos
- **QUANDO** são coletadas variantes parametrizadas ou funções de mesmo nome em módulos/classes diferentes
- **ENTÃO** cada resultado é associado ao caso e à variante corretos
- **E** nenhum resultado sobrescreve outro nem é contado duas vezes na mesma origem

#### Scenario: Catálogo divergente
- **QUANDO** há ID duplicado, seletor ambíguo, teste descoberto sem registro ou caso esperado sem correspondência
- **ENTÃO** a evidência registra o diagnóstico e a execução não recebe aprovação integral
- **E** uma divergência no conjunto obrigatório bloqueia o gate de completude

### Requirement: Associação comprovável entre requisito, caso, execução e evidência
Cada caso DEVE permitir rastrear sua execução e evidências até os requisitos ou cenários relacionados quando identificados. Referência formal não confirmada DEVE permanecer pendente, sem inventar código, texto de requisito ou cobertura. Referência OpenSpec e referência formal DEVEM ser distinguíveis.

#### Scenario: Requisito identificado no repositório
- **QUANDO** um caso está associado a um cenário OpenSpec existente e é executado
- **ENTÃO** o relatório permite seguir cenário, ID do caso, ID da execução e arquivo da evidência
- **E** informa separadamente se a referência formal foi conferida

#### Scenario: Ausência de confirmação formal
- **QUANDO** não existe requisito identificado ou o documento formal está indisponível
- **ENTÃO** a associação aparece como pendente ou não identificada
- **E** aprovação técnica do caso não é descrita como cobertura formal confirmada

### Requirement: Classificação por caso, ambiente e dependência
Os relatórios DEVEM distinguir testes unitários, de integração, E2E e estáticos, seu componente e o uso de dependência local, simulada ou real. A classificação NÃO DEVE inferir execução remota pela pasta do teste ou integração apenas pela existência de mock em outro caso do mesmo arquivo. Autotestes da infraestrutura NÃO DEVEM contar como cobertura funcional do produto.

#### Scenario: Arquivo contém verificações locais e remotas
- **QUANDO** um módulo contém testes estáticos e uma consulta HTTP real
- **ENTÃO** a execução local seleciona somente os casos estáticos
- **E** a consulta remota mantém sua dependência e seu estado registrados separadamente

#### Scenario: Função pura executada no servidor
- **QUANDO** um teste usa dados sintéticos e executa função pura publicada no Xano
- **ENTÃO** a evidência informa a dependência remota e o limite de equivalência com o código local
- **E** não o apresenta como integração de persistência ou execução local sem serviços

### Requirement: Vocabulário inequívoco de estados dos casos
Cada caso DEVE usar exclusivamente `PASSED`, `FAILED`, `ERROR`, `SKIPPED`, `NOT_RUN` ou `BLOCKED` conforme execução, falha funcional, erro, omissão intencional, não execução ou impedimento. Estados sem execução DEVEM ter justificativa. Leitura histórica DEVE reconhecer `PASS` e `FAIL` sem alterar os arquivos de origem. Estado desconhecido NÃO DEVE ser tratado como sucesso.

#### Scenario: Falha funcional e erro de execução
- **QUANDO** uma assertion válida reprova um comportamento ou ocorre erro de preparação, execução ou finalização
- **ENTÃO** o caso recebe, respectivamente, `FAILED` ou `ERROR`
- **E** o relatório conserva o motivo e o processo não retorna sucesso técnico

#### Scenario: Três causas distintas de ausência
- **QUANDO** um caso é ignorado deliberadamente, não é iniciado no escopo ou é impedido por uma dependência
- **ENTÃO** recebe, respectivamente, `SKIPPED`, `NOT_RUN` ou `BLOCKED`
- **E** cada estado possui motivo e não constitui aprovação

#### Scenario: Evidência antiga ou estado inválido
- **QUANDO** uma evidência usa `PASS`/`FAIL` ou um estado não reconhecido
- **ENTÃO** os aliases antigos são normalizados na leitura e o arquivo histórico permanece intacto
- **E** o estado não reconhecido gera diagnóstico bloqueante em vez de aprovação implícita

### Requirement: Separação entre resultado técnico e nível de validação
A execução DEVE declarar escopo, resultado técnico e nível de validação separadamente. Validação completa exige concluir todas as verificações obrigatórias do escopo; aprovação integral exige também sucesso técnico. Pendências de integração ou aceite manual NÃO DEVEM ser encerradas pelo sucesso de testes locais, simulados, puros ou do pipeline.

#### Scenario: Todos os casos automatizados passam e restam passos reais
- **QUANDO** os testes automatizados de um roteiro passam e existem passos obrigatórios de integração ou aceite manual sem evidência
- **ENTÃO** o relatório mostra o sucesso técnico dos casos e a validação parcial do roteiro
- **E** não apresenta aprovação geral desse roteiro

#### Scenario: Execução parcial permitida
- **QUANDO** parte dos casos é executada sem falhas e outros ficam pendentes em execução que não exige completude
- **ENTÃO** o processo pode terminar com sucesso técnico e a validação é explicitamente parcial
- **E** o relatório informa os casos pendentes e suas justificativas

#### Scenario: Nenhum resultado disponível
- **QUANDO** nenhum caso foi executado ou nenhum resultado confiável foi coletado
- **ENTÃO** o relatório informa validação bloqueada ou não executada, conforme os motivos disponíveis
- **E** não declara aprovação nem inventa caso funcional para representar erro da infraestrutura

### Requirement: Projeções XML, JSON e Markdown da mesma execução
Os três formatos DEVEM representar a mesma identidade, casos, estados, contagens e conclusão. O JUnit DEVE conservar falhas e erros e representar `SKIPPED`, `NOT_RUN` e `BLOCKED` como omissões com o estado original e motivo recuperáveis. Saída bruta do executor DEVE ser identificada como evidência auxiliar, sem ser somada como nova execução.

#### Scenario: Contagens entre formatos
- **QUANDO** uma execução contém casos nos seis estados
- **ENTÃO** JSON e Markdown apresentam as mesmas contagens discriminadas
- **E** o total JUnit coincide com os casos, as falhas com `FAILED`, os erros com `ERROR` e as omissões com a soma dos três estados sem execução

#### Scenario: Coleta incompleta ou resultado sem associação
- **QUANDO** o executor retorna caso desconhecido, falha de setup/teardown, coleta interrompida ou código não zero sem resultado confiável
- **ENTÃO** a evidência conserva o diagnóstico e os resultados confiáveis já obtidos
- **E** nenhum dado ausente é interpretado como aprovação

### Requirement: Metadados de execução e origem auditável
A evidência DEVE registrar ID da execução, início/fim com fuso, duração, suíte, ambiente, dependências, commit testado e origem dos resultados. No CI, DEVE incluir run, tentativa, job e link público da execução quando disponíveis. Metadados comuns podem ser herdados pelos casos. Indisponibilidade e alterações locais DEVEM ser explicitadas sem inventar valores.

#### Scenario: Execução no GitHub Actions
- **QUANDO** a suíte roda no GitHub Actions
- **ENTÃO** seus relatórios identificam o SHA efetivamente testado, run, tentativa, job, link e duração
- **E** a consolidação mantém a origem de cada suíte

#### Scenario: Execução local com arquivos alterados
- **QUANDO** a execução é local e a árvore contém alterações
- **ENTÃO** a evidência registra esse fato e informa que o SHA representa a base
- **E** campos GitHub indisponíveis permanecem ausentes ou explicitamente indisponíveis

### Requirement: Consolidação resiliente e incompatibilidades visíveis
A consolidação DEVE conhecer as suítes esperadas, validar origem, versão e identidade das entradas e publicar diagnóstico mesmo quando faltarem evidências. Fontes com commit, run ou tentativa incompatíveis, JSON inválido ou duplicação NÃO DEVEM fornecer aprovações ao consolidado. Fontes válidas DEVEM ser preservadas e obrigações ausentes DEVEM bloquear o gate.

#### Scenario: Artifact ausente ou corrompido
- **QUANDO** uma suíte esperada não publica resultado ou publica JSON inválido
- **ENTÃO** a consolidação gera XML, JSON e Markdown com os resultados válidos e a ausência/erro explícitos
- **E** o gate obrigatório falha após a publicação disponível

#### Scenario: Mistura de execuções
- **QUANDO** as entradas têm commits diferentes, mesmo commit com runs/tentativas diferentes ou repetem a mesma origem
- **ENTÃO** a incompatibilidade é registrada e as aprovações dessas entradas não são aceitas
- **E** o resultado não se apresenta como validação completa

#### Scenario: Destino de execução já utilizado
- **QUANDO** o destino de saída contém evidências de uma execução anterior
- **ENTÃO** a nova execução recusa a reutilização desse destino e informa como usar outro diretório
- **E** não apaga, sobrescreve ou aproveita resultados anteriores como atuais

### Requirement: Sprints e atividades como contexto reutilizável
Casos DEVEM ser reutilizáveis em diferentes ciclos. Sprint, card, verificações e pendências de um roteiro DEVEM ser configuráveis por dados, referenciando os IDs dos casos sem duplicar seus metadados. O histórico da Sprint 5 e dos cards já registrados DEVE continuar acessível. A infraestrutura genérica NÃO DEVE exigir edição para incluir outro ciclo.

#### Scenario: Regressão em outro ciclo
- **QUANDO** uma configuração de novo ciclo referencia casos existentes
- **ENTÃO** o mesmo gerador produz o relatório desse ciclo com a identidade atual da execução
- **E** os IDs dos casos e suas associações históricas permanecem iguais, sem editar o código central

#### Scenario: Roteiro sem teste implementado
- **QUANDO** uma verificação histórica não possui teste ou depende de etapa manual
- **ENTÃO** o roteiro conserva sua pendência e não cria um caso fictício
- **E** o roteiro permanece sem aprovação integral enquanto a obrigação não for verificada

### Requirement: Relatório humano conciso e conclusão limitada ao escopo
O Markdown DEVE apresentar identificação, objetivo/escopo, ambiente, totais por estado/tipo, requisitos e critérios verificados, falhas, impedimentos, não execuções justificadas, sprints/atividades, referências de evidência e conclusão com limites. DEVE agrupar informações repetidas e apontar para o detalhe dos casos sem reproduzir todo o JSON.

#### Scenario: Muitos casos e impedimentos repetidos
- **QUANDO** há centenas de casos e vários compartilham a mesma restrição
- **ENTÃO** o resumo agrupa os impedimentos com quantidades e referências aos IDs
- **E** preserva a possibilidade de consultar cada caso no JSON/XML

### Requirement: Independência das suítes e gates depois das evidências
Suítes independentes DEVEM continuar executando após falha de outra suíte. Relatórios e uploads DEVEM ser tentados também após falhas tratáveis; o consolidado DEVE tratar artifacts ausentes. Falhas funcionais, erros de execução/identidade e obrigações pendentes sob exigência de completude DEVEM bloquear o gate, sem conversão silenciosa em sucesso.

#### Scenario: Falha de suíte e publicação
- **QUANDO** uma suíte falha e outra independente está disponível
- **ENTÃO** a segunda executa normalmente e a publicação de ambas é tentada
- **E** o Job Summary mostra status técnico, nível de validação, quantidades e falhas bloqueantes
- **E** a conclusão do CI conserva a falha original

#### Scenario: Dependência obrigatória indisponível
- **QUANDO** falta credencial, navegador ou serviço para uma suíte obrigatória
- **ENTÃO** os casos impedidos são registrados como `BLOCKED`, sem alegar execução
- **E** a exigência de completude impede sucesso do gate sem cancelar os jobs independentes

### Requirement: Proteção de dados e de ambientes reais
As evidências NÃO DEVEM expor credenciais, tokens, códigos de acesso, dados pessoais, URLs privadas ou respostas sensíveis. Testes com escrita real DEVEM exigir ambiente isolado confirmado e autorização explícita; sem isso, DEVEM permanecer impedidos. Testes remotos puros DEVEM passar pelo guardião de segurança antes da execução e explicitar seu limite de equivalência com o Git.

#### Scenario: Escrita sem autorização ou isolamento
- **QUANDO** uma integração pode modificar dados e falta autorização explícita ou confirmação válida de ambiente isolado
- **ENTÃO** a execução é recusada antes de qualquer chamada de escrita
- **E** os casos afetados recebem `BLOCKED` com justificativa sem revelar segredos

#### Scenario: Função deixa de ser segura
- **QUANDO** uma função selecionada ou dependência revisada passa a acessar recurso não permitido pelo guardião de pureza
- **ENTÃO** o grupo afetado não executa no Xano
- **E** o relatório registra o impedimento e o gate obrigatório não aprova

#### Scenario: Falha contém informação sensível
- **QUANDO** uma falha, resposta ou log contém dados pessoais ou segredo
- **ENTÃO** somente campos permitidos e mensagens sanitizadas entram nos formatos e artifacts publicados
- **E** referências públicas válidas de execução e atividade continuam utilizáveis

#### Scenario: Interrupção impede produzir artifact
- **QUANDO** o ambiente de execução é encerrado antes de produzir evidência
- **ENTÃO** o consolidado identifica a suíte esperada como ausente quando conseguir executar
- **E** não inventa resultados individuais nem garante evidência que a plataforma não produziu

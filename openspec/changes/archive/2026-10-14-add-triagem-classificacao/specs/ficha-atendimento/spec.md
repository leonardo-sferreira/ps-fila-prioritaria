# Delta de especificação

## Purpose

Registra a passagem do paciente pelo PS desde a abertura da ficha até as etapas clínicas posteriores, começando por sintomas e queixa geral editáveis.

## ADDED Requirements

### Requirement: Abertura de ficha na fatia atual
O sistema DEVE abrir `Ficha_Atendimento` para paciente existente, com `status=EM_TRIAGEM` e `chegada_em` definido pelo backend. `ticket_id` PODE ser informado, mas a abertura NÃO DEVE depender de Totem ou ticket. `POST /fichas` PODE criar a ficha inicialmente sem sintomas e sem observação; RN04 não é exigida na abertura.

#### Scenario: Abertura sem ticket
- **QUANDO** a Recepção/Triagem abre ficha para paciente existente sem ticket
- **ENTÃO** a ficha é criada em `EM_TRIAGEM` com horário definido pelo backend

#### Scenario: Abertura inicialmente vazia
- **QUANDO** a Recepção/Triagem abre uma ficha sem sintomas e sem observação
- **ENTÃO** a ficha permanece em `EM_TRIAGEM` e pode ser preenchida posteriormente sem criar estado adicional

#### Scenario: Paciente inexistente
- **QUANDO** alguém tenta abrir ficha para paciente inexistente
- **ENTÃO** nenhuma ficha é criada

### Requirement: Responsável temporariamente ausente
Enquanto `add-autenticacao-perfis` não estiver implementada, `aberta_por` PODE ser nulo na abertura desta fatia. O sistema NÃO DEVE usar usuário artificial, ID fixo, token falso ou autenticação simulada. Após a autenticação ser implementada, essa integração DEVE ser reavaliada; esta tolerância temporária NÃO define o contrato permanente do domínio.

#### Scenario: Abertura sem autenticação disponível
- **QUANDO** uma ficha é aberta na fatia atual sem usuário autenticado disponível
- **ENTÃO** `aberta_por` permanece nulo sem criar usuário ou credencial artificial

### Requirement: Nova chegada e ficha não finalizada
Cada nova chegada DEVE gerar nova ficha e preservar o histórico. Uma segunda ficha NÃO DEVE ser criada se o paciente já tiver ficha em `EM_TRIAGEM`, `AGUARDANDO` ou `CHAMADO`. Fichas em `ATENDIDO`, `DESISTENCIA` ou `CANCELADO` são finais e NÃO DEVEM impedir nova chegada. O sistema NÃO DEVE criar estados adicionais para essa regra.

#### Scenario: Ficha não finalizada bloqueia nova abertura
- **QUANDO** o paciente possui ficha em `EM_TRIAGEM`, `AGUARDANDO` ou `CHAMADO` e uma nova ficha é solicitada
- **ENTÃO** nenhuma segunda ficha é criada

#### Scenario: Chegada após estado final
- **QUANDO** a última ficha do paciente está em `ATENDIDO`, `DESISTENCIA` ou `CANCELADO` e ocorre nova chegada
- **ENTÃO** uma nova ficha é criada e a ficha finalizada permanece no histórico

### Requirement: Consulta de sintomas ativos
`GET /sintomas` DEVE retornar somente sintomas ativos necessários à triagem, incluindo identificador, nome, descrição quando existir, grupo e `pontuacao` inteira entre 1 e 3. Sintoma NÃO DEVE possuir cor ou prioridade fixa; a futura classificação usa a soma das pontuações selecionadas.

#### Scenario: Catálogo utilizável
- **QUANDO** a Recepção/Triagem consulta os sintomas
- **ENTÃO** recebe apenas sintomas ativos com grupo e pontuação numérica, sem `prioridade_padrao`

#### Scenario: Sintoma inativo
- **QUANDO** um sintoma está inativo
- **ENTÃO** ele não é retornado para seleção em nova ficha

### Requirement: Carga atual do catálogo de sintomas
Nesta fatia, o sistema DEVE adequar o schema de Sintoma e carregar de forma idempotente o catálogo acadêmico existente, com nome, descrição quando existente, grupo, `pontuacao` de 1 a 3 e situação ativa. Uma segunda carga NÃO DEVE duplicar registros. `docs/domain-model.md` é somente a fonte existente do catálogo e não é alterado nesta change.

#### Scenario: Carga repetida do catálogo
- **QUANDO** a carga oficial é executada duas vezes no ambiente com a tabela inicialmente vazia
- **ENTÃO** os sintomas ativos ficam disponíveis para `GET /sintomas` sem duplicação e sem dados inventados

### Requirement: Consulta da ficha para edição
`GET /fichas/{id}` DEVE retornar os dados necessários para editar a ficha, incluindo paciente relacionado, observação geral e sintomas associados. A resposta desta fatia NÃO DEVE expor `ficha_sintoma.observacao` como campo editável da Triagem.

#### Scenario: Recarregar ficha preenchida
- **QUANDO** a Recepção/Triagem consulta uma ficha com sintomas e observação
- **ENTÃO** recebe a mesma coleção de sintomas e a observação geral persistida

### Requirement: Sintomas e observação geral editáveis
`PATCH /fichas/{id}` DEVE aceitar parcialmente `sintoma_ids` e `observacao`. Quando enviado, `sintoma_ids` representa a coleção final: IDs novos criam vínculos, IDs ausentes removem vínculos e IDs existentes são preservados, sem repetição. Campo omitido NÃO DEVE alterar seu componente. A observação editável é exclusivamente `ficha_atendimento.observacao`.

#### Scenario: Substituir coleção de sintomas
- **QUANDO** a ficha possui sintomas 1 e 5 e recebe `sintoma_ids` 5 e 9
- **ENTÃO** o vínculo com 1 é removido, 5 é preservado e 9 é criado sem duplicidade

#### Scenario: Alterar somente observação
- **QUANDO** a ficha possui sintomas e recebe PATCH apenas com nova observação
- **ENTÃO** seus sintomas são preservados e a observação geral é atualizada

#### Scenario: Alterar somente sintomas
- **QUANDO** a ficha possui observação não vazia e recebe PATCH apenas com `sintoma_ids`
- **ENTÃO** a observação é preservada e a coleção de sintomas é atualizada de forma coerente

#### Scenario: Sintoma inativo ou inexistente
- **QUANDO** o PATCH contém sintoma inativo ou inexistente
- **ENTÃO** nenhuma alteração parcial é persistida

### Requirement: Preenchimento válido da ficha
Quando PATCH altera sintomas e/ou observação, o estado resultante DEVE conter ao menos um sintoma ou observação geral não vazia após trim (RN04). A validação DEVE considerar os valores persistidos dos componentes omitidos. A ficha continua em `EM_TRIAGEM` enquanto é preenchida; NÃO DEVE existir status `RASCUNHO`.

#### Scenario: Somente sintomas
- **QUANDO** a ficha recebe um ou mais sintomas e observação vazia
- **ENTÃO** o preenchimento é aceito

#### Scenario: Somente observação
- **QUANDO** a ficha recebe observação geral não vazia e coleção de sintomas vazia
- **ENTÃO** o preenchimento é aceito

#### Scenario: Componentes preservados no estado resultante
- **QUANDO** PATCH altera somente sintomas ou somente observação e o outro componente persistido satisfaz RN04
- **ENTÃO** o preenchimento é aceito considerando o estado resultante completo

#### Scenario: Remover último conteúdo válido
- **QUANDO** PATCH remove o último sintoma sem observação resultante ou limpa a última observação sem sintomas resultantes
- **ENTÃO** nenhuma alteração inválida é persistida

#### Scenario: Observação somente com whitespace
- **QUANDO** PATCH informa somente whitespace como observação e não há sintomas resultantes
- **ENTÃO** nenhuma alteração inválida é persistida

### Requirement: Etapa posterior de dados clínicos da ficha
Sinais vitais, glicemia, gestação, cancelamento e demais dados clínicos continuam pertencendo a esta capability, mas são etapa posterior da change. Eles NÃO DEVEM compor o aceite desta fatia de abertura, sintomas e observação.

#### Scenario: Fatia atual concluída sem classificação clínica
- **QUANDO** a fatia atual é verificada
- **ENTÃO** RF06, RF07, RN03 e RN04 podem ser atendidos sem sinais vitais, gestação, cancelamento ou classificação final

### Requirement: Integrações futuras de autorização e auditoria
Autorização por perfil e auditoria de alterações DEVERÃO ser integradas pelas changes responsáveis. A fatia atual NÃO DEVE criar stubs, mocks ou mecanismos paralelos para substituí-las.

#### Scenario: Infraestrutura futura indisponível
- **QUANDO** autenticação ou auditoria ainda não estiverem implementadas
- **ENTÃO** a fatia não cria substituto artificial para essas capacidades

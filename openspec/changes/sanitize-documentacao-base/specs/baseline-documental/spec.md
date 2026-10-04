# Delta de especificação

## Purpose

Define os critérios verificáveis para considerar a documentação-base do PS Fila Prioritária sanitizada e apta a orientar as changes funcionais seguintes, sem implementar código nesta etapa.

## ADDED Requirements


### Requirement: Execução isolada em branch Git
A sanitização DEVE ser executada exclusivamente na branch `docs/sanitize-documentacao-base`. O agente NÃO DEVE alterar a `main`, descartar trabalho local preexistente nem usar operações destrutivas para forçar a troca de branch.

#### Scenario: Início seguro do apply
- **QUANDO** o agente inicia a aplicação desta change
- **ENTÃO** ele DEVE verificar o estado do repositório, criar/trocar para `docs/sanitize-documentacao-base`, confirmar a branch ativa e somente depois editar arquivos

#### Scenario: Alterações locais impedem a troca de branch
- **QUANDO** existirem alterações locais preexistentes que impeçam a criação ou troca segura de branch
- **ENTÃO** o agente DEVE interromper a execução e reportar o bloqueio, sem resetar, limpar, descartar ou fazer stash automático dessas alterações

### Requirement: Base documental única e coerente
Os documentos `docs/project-overview.md`, `docs/domain-model.md`, `openspec/config.yaml` e `AGENTS.md` DEVEM refletir as decisões aprovadas nesta change sem contradições entre si. Quando uma change funcional existente divergir da base sanitizada, a divergência DEVE ser registrada para revisão posterior e NÃO DEVE ser resolvida alterando código nesta change.

#### Scenario: Change antiga contradiz a base
- **QUANDO** uma change existente disser que o médico só atende a própria especialidade
- **ENTÃO** os documentos-base DEVEM manter a regra aprovada de que a especialidade do médico é cadastral e a change antiga DEVE apenas ser listada como impacto posterior

### Requirement: Pontuação clínica consolidada
A documentação-base DEVE representar sintomas por pontuação inteira de 1 a 3 e DEVE declarar que o escore total soma os pontos de todos os sintomas selecionados com os pontos dos sinais vitais. A documentação NÃO DEVE afirmar que o escore total possui máximo fixo de 18.

#### Scenario: Dois sintomas e sinais vitais
- **QUANDO** uma ficha possui sintomas de 2 e 1 pontos e sinais vitais que somam 2 pontos
- **ENTÃO** a documentação DEVE indicar escore total 5 antes da aplicação dos limiares configurados

#### Scenario: Sintoma de 3 pontos
- **QUANDO** um único sintoma possui 3 pontos
- **ENTÃO** a base DEVE preservar a regra de segurança de item clínico isolado com 3 pontos elevando o risco ao nível alto

### Requirement: Direcionamento por especialidade independente da especialidade do médico
A documentação-base DEVE separar especialidade da ficha de especialidade cadastral do médico. A ficha DEVE ser direcionada automaticamente à especialidade adequada aos sintomas, e um médico elegível NÃO DEVE ser impedido de atender a fila apenas porque sua especialidade cadastral é diferente.

#### Scenario: Cardiologia atendida por médico de outra especialidade cadastral
- **QUANDO** uma ficha é direcionada à fila de Cardiologia e um médico elegível de outra especialidade cadastral recebe o atendimento
- **ENTÃO** a ficha DEVE continuar pertencendo à fila/especialidade Cardiologia

### Requirement: Pausa e encerramento de plantão
A documentação-base DEVE definir PAUSA como impedimento para novas atribuições sem remover a fila já atribuída. O encerramento do plantão DEVE ser uma ação explícita do Médico e só DEVE ser permitido quando sua fila atribuída estiver zerada.

#### Scenario: Médico pausa com pacientes atribuídos
- **QUANDO** um médico com itens já atribuídos aciona Pausar
- **ENTÃO** ele NÃO DEVE receber novos itens, mas os existentes NÃO DEVEM ser removidos por causa da pausa

#### Scenario: Encerramento bloqueado
- **QUANDO** o médico possui ao menos um item ativo em sua fila
- **ENTÃO** a documentação DEVE indicar que o botão Encerrar plantão permanece indisponível

### Requirement: Regra global de chamadas
A documentação-base DEVE usar intervalo de 30 segundos entre chamadas da mesma senha e até 3 tentativas por oportunidade. Após uma oportunidade esgotada sem comparecimento, a senha DEVE voltar ao fim da mesma fila e receber uma única nova oportunidade. A regra DEVE valer tanto para Recepção/Triagem quanto para Médico. Desistência explícita DEVE remover a senha da fila ativa.

#### Scenario: Pré-triagem sem comparecimento
- **QUANDO** um ticket esgota as tentativas da primeira oportunidade sem comparecimento
- **ENTÃO** ele DEVE voltar a AGUARDANDO no fim da fila sem receber novo número

#### Scenario: Desistência explícita
- **QUANDO** uma desistência é registrada
- **ENTÃO** a senha DEVE sair imediatamente da fila ativa

### Requirement: Totem faz parte do produto
A documentação-base DEVE declarar que o Totem faz parte do escopo do projeto e terá change própria. O fluxo do Totem DEVE gerar um ticket sem dados pessoais e inseri-lo na fila de Recepção/Triagem.

#### Scenario: Descrição de escopo
- **QUANDO** alguém consulta a visão geral do projeto
- **ENTÃO** ela NÃO DEVE afirmar que o Totem é apenas externo, abstrato ou não desenvolvido pela equipe

### Requirement: Perfis, Sala e permissões globais
A documentação-base DEVE conter as entidades conceituais Médico, Recepção/Triagem e Sala, seus vínculos relevantes, e uma matriz global de permissões. A autorização DEVE continuar sendo responsabilidade do backend Xano.

#### Scenario: Painel público
- **QUANDO** o público visualiza uma chamada
- **ENTÃO** a documentação DEVE permitir exibir senha e Sala e DEVE proibir nome e CPF do paciente

### Requirement: Referência formal atualizada
A documentação-base DEVE declarar o intervalo formal RF01–RF50. Ela NÃO DEVE inventar texto de requisitos ausentes apenas para preencher numeração.

#### Scenario: Referência antiga
- **QUANDO** uma ocorrência de RF01–RF38 é encontrada como intervalo atual da fonte formal
- **ENTÃO** ela DEVE ser atualizada para RF01–RF50 ou contextualizada explicitamente como referência histórica

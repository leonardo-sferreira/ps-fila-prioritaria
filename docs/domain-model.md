# Modelo de Domínio — Sistema de Fila Prioritária para Pronto-Socorro

Modelo conceitual do domínio. Representa conceitos e relacionamentos, não o esquema físico do Xano: nomes de tabelas e campos são definidos no `design.md` de cada change. As decisões consolidadas do PO nesta base prevalecem sobre descrições antigas de changes; divergências devem ser revisadas antes da implementação funcional.

## Visão geral dos relacionamentos

```
Usuário ──(perfil)──> Recepção_Triagem | Médico | Administrador
   ├── 1:1 Médico ──> Sala atual
   │       └──< Disponibilidade_Médico
   ├── 1:1 Recepção_Triagem
   └──< Sessão (login/logout + status operacional)

Sintoma ──< Sintoma_Especialidade (ordenada) >── Especialidade

Ticket_Pré-Triagem ──(atendido por)──> Ficha_Atendimento

Paciente ──< Ficha_Atendimento ──< Ficha_Sintoma >── Sintoma
                    │
                    ├── Sinais vitais + escore e classificação de risco
                    ├── Prioridade calculada / atual + condição prioritária
                    ├── Especialidade sugerida / atribuída + senha
                    └──< Chamada (até 3 tentativas por oportunidade) >── Médico

Histórico_Alteração → referencia a entidade alterada + Usuário responsável
Parâmetros de regra / Faixas de sinais vitais → configuração usada pelas regras
```

## Estados da Ficha_Atendimento

| Estado | Significado | Próximos estados |
|---|---|---|
| EM_TRIAGEM | Ficha aberta; triagem em andamento, ainda sem senha. | AGUARDANDO, CANCELADO |
| AGUARDANDO | Paciente ativo na fila da especialidade indicada pelos sintomas. | CHAMADO, CANCELADO |
| CHAMADO | Senha chamada por um médico; aguarda comparecimento. | ATENDIDO, AGUARDANDO (reentrada), DESISTÊNCIA |
| ATENDIDO | Paciente compareceu e saiu da fila (não é conclusão clínica). | Final |
| DESISTÊNCIA | Desistência explícita ou encerramento definitivo sem atendimento após as oportunidades previstas. | Final |
| CANCELADO | Ficha retirada por ação autorizada, com justificativa. | Final |

"Fila ativa" = fichas em AGUARDANDO ou CHAMADO. Após esgotar a primeira oportunidade sem comparecimento, a ficha retorna a AGUARDANDO no fim da mesma fila e recebe uma única nova oportunidade. A oportunidade seguinte encerrada sem atendimento leva a DESISTÊNCIA. A regra de 30 segundos entre chamadas e até 3 tentativas por oportunidade vale para a fila médica; a desistência explícita encerra a participação na fila ativa. A definição física de como registrar as oportunidades pertence à spec funcional.

---

## Usuário

Pessoa da equipe que acessa o sistema.

### Principais informações
- nome;
- e-mail (login, único) e senha (armazenada como hash);
- perfil: `RECEPCAO_TRIAGEM`, `MEDICO` ou `ADMINISTRADOR`;
- situação (ativo/inativo).

### Relacionamentos
- Um usuário tem exatamente um perfil.
- Um usuário de perfil Médico corresponde a exatamente um registro de Médico.
- Um usuário de perfil RECEPCAO_TRIAGEM corresponde a exatamente um registro de Recepcao_Triagem.
- Um usuário pode ter várias Sessões.

### Regras
- Somente o Administrador cria, edita e desativa usuários; usuários não são excluídos.
- Um usuário inativo não pode se autenticar e perde o acesso imediatamente.
- Deve existir sempre ao menos um Administrador ativo.

## Sessão

Registro de um login da equipe; alimenta a visão "Pessoas logadas e status".

### Principais informações
- usuário;
- horário de login, horário de logout e expiração;
- status operacional: `DISPONIVEL`, `EM_ATENDIMENTO`, `PAUSA` ou `AUSENTE`.

### Regras
- Uma sessão sem logout é considerada encerrada quando expira.
- PAUSA e AUSENTE são status operacionais durante uma sessão; não encerram a sessão.
- Encerramento do plantão é um evento operacional próprio, diferente de logout e expiração.

### Ciclo da sessão e status operacional

```
LOGIN → SESSÃO ATIVA → LOGOUT/EXPIRAÇÃO → SESSÃO ENCERRADA
```

Uma sessão está ativa quando `logout_em` é nulo e `expira_em` ainda está no futuro. Durante a sessão, o status operacional pode ser `DISPONIVEL`, `EM_ATENDIMENTO`, `PAUSA` ou `AUSENTE`. PAUSA/AUSENTE não encerram a sessão e impedem o Médico de receber novas atribuições. Encerrar o plantão é uma ação operacional própria, separada do encerramento da sessão.

## Médico

Profissional que atende a fila priorizada.

### Principais informações
- usuário vinculado (relação 1:1);
- nome profissional/de exibição (pode ser derivado ou sincronizado do usuário no schema físico);
- CRM;
- especialidade de referência (informação cadastral, não restritiva);
- situação (ativo/inativo).

### Relacionamentos
- Um médico tem registros de Disponibilidade_Médico.
- Um médico pode estar relacionado à sua Sala atual.
- Um médico realiza Chamadas.

### Regras
- O Administrador cadastra/edita o Médico junto com o usuário correspondente.
- A especialidade de referência é cadastral e não limita as filas que o médico pode atender.
- Um médico elegível pode atender ficha de qualquer especialidade; a especialidade da ficha permanece a definida pelos sintomas.
- A disponibilidade por período é registrada pelo Administrador.
- PAUSA ou AUSENTE impede novas atribuições sem remover itens já atribuídos.
- Retomar restaura DISPONIVEL se houver disponibilidade/plantão vigente.
- Encerrar plantão é ação explícita e só é permitido quando a fila atribuída ao médico estiver zerada.

## Recepcao_Triagem

Entidade cadastral da pessoa com perfil RECEPCAO_TRIAGEM.

### Principais informações
- usuário vinculado (relação 1:1);
- nome;
- CPF;
- especialidade de referência;
- situação (ativo/inativo).

### Regras
- O Administrador cria e edita os dados da Recepção/Triagem juntamente com o usuário correspondente.
- A especialidade de referência é cadastral e não limita as operações de triagem.

## Sala

Local de atendimento que pode estar relacionado ao Médico atual.

### Principais informações
- identificador;
- nome/número;
- descrição opcional;
- situação (ativa/inativa).

### Regras
- O painel público pode exibir a sala associada ao médico responsável pela chamada.
- A chamada pública nunca exibe nome completo nem CPF do paciente.
- O vínculo físico (por exemplo, direto, histórico ou por plantão) será definido pela change funcional que implementar Sala.

## Especialidade

Destino clínico indicado pelos sintomas (ex.: Clínica Geral — `CLI`); as fichas são organizadas em filas por especialidade.

### Principais informações
- nome, descrição e sigla usada na senha (única, 3 letras);
- situação (ativa/inativa).

### Relacionamentos
- Ligada a Sintomas por Sintoma_Especialidade, em ordem de preferência definida para cada sintoma.

### Regras
- A disponibilidade de médicos e a especialidade cadastrada no Médico não alteram o destino clínico da ficha.
- A regra de desempate quando sintomas apontam para especialidades diferentes pertence à spec funcional de direcionamento.

## Disponibilidade_Médico

Período em que um médico está disponível: médico, data, horário inicial e horário final. É registrada pelo Administrador depois de o médico informá-la fora do sistema.

## Sintoma

Queixa selecionável na triagem.

### Principais informações
- nome, descrição e grupo (cardiovascular, respiratório, neurológico, gastrointestinal, traumático/ortopédico, geral);
- `pontuacao` inteira de 1 a 3;
- situação (ativo/inativo).

### Relacionamentos
- Aponta para uma ou mais especialidades, em ordem de preferência (Sintoma_Especialidade).

### Regras
- Todos os sintomas selecionados para uma ficha somam sua pontuação ao escore clínico.
- A pontuação é uma modelagem acadêmica e não uma classificação por cor ou protocolo clínico real.

### Catálogo inicial de sintomas

Esta lista é a carga acadêmica de referência. A pontuação não representa protocolo clínico real.

| Grupo | Sintoma / queixa | Pontos | Especialidade de destino |
|---|---|---:|---|
| Cardiovascular | Dor ou pressão no peito | 2 | Cardiologia |
| Cardiovascular | Palpitações | 2 | Cardiologia |
| Cardiovascular | Desmaio / síncope | 2 | Cardiologia |
| Cardiovascular | Inchaço nas pernas associado a falta de ar | 2 | Cardiologia |
| Respiratório | Falta de ar | 2 | Clínica Geral |
| Respiratório | Falta de ar intensa / dificuldade grave para respirar | 3 | Clínica Geral |
| Respiratório | Chiado no peito | 2 | Clínica Geral |
| Respiratório | Dor ao respirar | 2 | Clínica Geral |
| Respiratório | Tosse com sangue | 2 | Clínica Geral |
| Respiratório | Tosse sem falta de ar | 1 | Clínica Geral |
| Neurológico | Convulsão em atividade | 3 | Neurologia |
| Neurológico | Convulsão já cessada / período pós-crise | 2 | Neurologia |
| Neurológico | Alteração súbita da fala | 3 | Neurologia |
| Neurológico | Fraqueza ou paralisia de um lado do corpo | 3 | Neurologia |
| Neurológico | Perda súbita de visão | 3 | Neurologia |
| Neurológico | Perda súbita de equilíbrio ou coordenação | 3 | Neurologia |
| Neurológico | Confusão mental aguda | 2 | Neurologia |
| Neurológico | Dor de cabeça súbita e muito intensa | 2 | Neurologia |
| Neurológico | Tontura / vertigem | 2 | Neurologia |
| Neurológico | Dor de cabeça leve ou habitual | 1 | Neurologia |
| Gastrointestinal | Vômito com sangue | 3 | Clínica Geral |
| Gastrointestinal | Sangue nas fezes / fezes muito escuras | 2 | Clínica Geral |
| Gastrointestinal | Dor abdominal intensa | 2 | Clínica Geral |
| Gastrointestinal | Vômitos persistentes | 2 | Clínica Geral |
| Gastrointestinal | Dor abdominal leve | 1 | Clínica Geral |
| Gastrointestinal | Náusea | 1 | Clínica Geral |
| Gastrointestinal | Diarreia sem sinais de desidratação | 1 | Clínica Geral |
| Gastrointestinal | Constipação / cólica leve | 1 | Clínica Geral |
| Traumático/Ortopédico | Politrauma / trauma de grande impacto | 3 | Ortopedia |
| Traumático/Ortopédico | Fratura exposta | 3 | Ortopedia |
| Traumático/Ortopédico | Suspeita de fratura fechada | 2 | Ortopedia |
| Traumático/Neurológico | Trauma na cabeça com alteração neurológica | 3 | Neurologia |
| Traumático/Neurológico | Trauma na cabeça sem alteração neurológica | 2 | Neurologia |
| Traumático/Ortopédico | Corte profundo / sangramento importante | 2 | Ortopedia |
| Traumático/Ortopédico | Corte superficial | 1 | Ortopedia |
| Traumático/Ortopédico | Torção / entorse | 1 | Ortopedia |
| Traumático/Ortopédico | Dor em membro após trauma | 2 | Ortopedia |
| Traumático/Ortopédico | Dor em membro sem trauma importante | 1 | Ortopedia |
| Traumático/Ortopédico | Queda sem sinais de gravidade | 1 | Ortopedia |
| Geral | Reação alérgica com dificuldade respiratória | 3 | Clínica Geral |
| Geral | Reação alérgica sem dificuldade respiratória | 2 | Clínica Geral |
| Geral | Febre | 1 | Clínica Geral |
| Geral | Dor intensa sem localização específica | 2 | Clínica Geral |
| Geral | Dor leve sem localização específica | 1 | Clínica Geral |
| Geral | Mal-estar | 1 | Clínica Geral |
| Geral | Fraqueza generalizada | 1 | Clínica Geral |

#### Regra pediátrica

Paciente com idade menor ou igual a `idade_maxima_crianca` mantém a pontuação clínica normal, mas o destino de atendimento é Pediatria. A idade não substitui nem reduz a classificação de risco.

## Paciente

Pessoa atendida no PS.

### Principais informações
- CPF (obrigatório, único, chave de busca);
- nome completo;
- data de nascimento (define idoso/criança pelos limites configurados);
- telefone (opcional);
- situação (ativo/inativo).

### Regras
- Todo atendimento começa pela pesquisa do CPF (RN01); um CPF corresponde a um único paciente (RN02).
- Um paciente pode ter várias Fichas ao longo do tempo, mas no máximo uma ficha não finalizada.

## Ticket_Pré-Triagem

Ticket simples emitido pelo Totem na chegada, antes da triagem.

### Principais informações
- número sequencial do dia;
- horário de emissão;
- status: `AGUARDANDO`, `CHAMADO`, `ATENDIDO` ou `NAO_COMPARECEU`.

### Regras
- Não tem cor nem prioridade: é chamado pela Recepção/Triagem em ordem de emissão.
- Não guarda dados pessoais.
- As chamadas respeitam intervalo mínimo de 30 segundos entre chamadas da mesma senha e até 3 tentativas por oportunidade.
- Esgotada a primeira oportunidade sem comparecimento, o ticket volta ao fim da fila uma única vez, sem novo número e sem perder sua identidade.
- Após a segunda oportunidade encerrada sem atendimento, o ticket recebe `NAO_COMPARECEU` e sai da fila ativa.
- Desistência explícita remove o ticket da fila ativa; o estado final específico será definido pela spec funcional, sem presumir schema nesta documentação.

### Máquina de estados

``
AGUARDANDO
   ↓ chamar
CHAMADO
   ├─ compareceu → ATENDIDO (final)
   ├─ nova tentativa dentro do limite → CHAMADO
   └─ primeira oportunidade esgotada → AGUARDANDO (fim da fila)

segunda oportunidade encerrada sem atendimento → NAO_COMPARECEU (final)
desistência explícita → removido da fila ativa
```

## Ficha_Atendimento

Passagem do paciente pelo PS, da triagem até o comparecimento, a desistência ou o cancelamento. É o centro do domínio.

### Principais informações
- paciente, ticket de origem (quando houver) e usuário que abriu a ficha;
- horário de chegada (define a ordem de chegada);
- sintomas (via Ficha_Sintoma) e observações da queixa;
- gestante (sim/não) e condição prioritária resultante (idoso/criança/gestante);
- sinais vitais: PA sistólica, FC, FR, temperatura, glicemia capilar (com indicador de sinais de gravidade), SpO2;
- escore total = soma da pontuação de todos os sintomas e dos pontos dos sinais vitais (incluindo glicemia quando medida), indicador de item clínico isolado com 3 pontos e classificação de risco (baixo/moderado/alto); não há máximo fixo de 18;
- classificação calculada, classificação atual e justificativa do ajuste manual;
- especialidade sugerida e especialidade atribuída;
- senha (`COR-ESP-NÚMERO`) e tentativas de chamada por oportunidade;
- médico que chamou;
- status (ver tabela de estados).

### Regras
- Toda ficha precisa de ao menos um sintoma ou uma observação de queixa (RN04).
- Escore de sintomas = soma dos pontos de todos os sintomas selecionados; escore fisiológico = soma dos pontos dos sinais vitais; escore total = escore de sintomas + escore fisiológico.
- Os limiares iniciais configuráveis são moderado a partir de 3 e alto a partir de 6; qualquer item clínico isolado com 3 pontos pode elevar o risco a alto.
- Classificação final: baixo → Azul, moderado → Amarela, alto → Vermelha.
- A condição prioritária reordena dentro da mesma classificação e não soma pontos (RN10, RN11).
- O ajuste manual exige justificativa e gera Histórico_Alteração (RN09).
- A glicemia baixa recebe os pontos definidos na tabela da seção Faixas de sinais vitais.
- A senha é gerada somente após o direcionamento (RN19).

## Ficha_Sintoma

Associação entre ficha e sintoma, com observação opcional.

## Chamada

Tentativa de chamar uma ficha.

### Principais informações
- ficha, médico, número da tentativa na oportunidade (1 a 3) e data/hora.

### Regras
- Intervalo mínimo de 30 segundos entre chamadas da mesma senha.
- No máximo três tentativas por oportunidade; depois da primeira oportunidade sem comparecimento, a ficha volta ao fim da mesma fila e recebe uma única nova oportunidade.
- Desistência explícita remove a senha imediatamente da fila ativa.
- Dois médicos não podem chamar a mesma ficha (RN34).

## Histórico_Alteração

Trilha de auditoria.

### Principais informações
- tipo de evento (ex.: `PRIORIDADE_ALTERADA`, `SINTOMAS_ALTERADOS`, `DISPONIBILIDADE_ALTERADA`, `CHAMADA`, `CADASTRO`);
- entidade e registro afetados (ex.: ficha);
- valor anterior e valor novo;
- usuário responsável e data/hora;
- justificativa, quando houver.

### Regras
- Não pode ser editado nem excluído.

## Parâmetros de regra

Parâmetros configuráveis pelo Administrador e invariantes operacionais aprovados para esta base:

| Parâmetro | Valor inicial |
|---|---|
| Idade mínima para idoso | 60 anos |
| Idade máxima para criança | 11 anos (menor de 12) |
| Ciclo de chamada sem vermelhos | 2 amarelas : 1 azul |
| Intervalo entre chamadas da mesma senha | 30 segundos |
| Tentativas por oportunidade | 3 |
| Novas oportunidades após a primeira reentrada | 1 |
| Tamanho da previsão do painel | 5 |
| Especialidade padrão, se prevista pela spec de direcionamento | Clínica Geral |
| Limiar de risco moderado | escore total ≥ 3 |
| Limiar de risco alto | escore total ≥ 6, ou qualquer item clínico isolado com 3 pontos |

O fuso do projeto é fixo em `America/Sao_Paulo`; não é parâmetro editável pelo Administrador.

## Faixas de sinais vitais

Tabela configurável que dá de 0 a 3 pontos para cada parâmetro de sinal vital. Os valores iniciais dos sinais vitais permanecem definidos na spec funcional de classificação; para glicemia baixa, a regra-base é:

| Glicemia | Condição | Pontos |
|---|---|---:|
| `< 54 mg/dL` | Com sinais de gravidade | 3 |
| `< 54 mg/dL` | Sem sinais de gravidade | 2 |
| `54–59 mg/dL` | Com sinais de gravidade | 2 |
| `54–59 mg/dL` | Sem sinais de gravidade | 1 |

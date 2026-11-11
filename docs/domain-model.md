# Modelo de Domínio — Sistema de Fila Prioritária para Pronto-Socorro

Modelo conceitual do domínio. Representa conceitos e relacionamentos, não o esquema físico do Xano: nomes de tabelas e campos são definidos no `design.md` de cada change. As decisões consolidadas do PO nesta base prevalecem sobre descrições antigas de changes; divergências devem ser revisadas antes da implementação funcional.

## Visão geral dos relacionamentos

```
Usuário ──(perfil)──> Recepção_Triagem | Médico | Administrador
   ├── 1:1 Médico ──> Sala atual
   │       ├──< Disponibilidade_Médico
   │       └──< Médico_Especialidade >── Especialidade
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
| EM_TRIAGEM | Ficha aberta; triagem em andamento, ainda sem senha. | AGUARDANDO, CANCELADO, DESISTÊNCIA (dispensa por prazo) |
| AGUARDANDO | Paciente ativo na fila da especialidade indicada pelos sintomas; a Recepção/Triagem ainda pode corrigir os dados clínicos (reavaliação). | CHAMADO, CANCELADO, DESISTÊNCIA (dispensa por prazo) |
| CHAMADO | Senha chamada por um médico; aguarda comparecimento. | ATENDIDO, AGUARDANDO (reentrada), DESISTÊNCIA |
| ATENDIDO | Paciente compareceu e saiu da fila (não é conclusão clínica). | Final |
| DESISTÊNCIA | Desistência explícita, encerramento definitivo sem atendimento após as oportunidades previstas ou dispensa pelo Administrador da ficha parada além do prazo `HORAS_EXPIRACAO`. | Final |
| CANCELADO | Ficha retirada por ação autorizada, com justificativa. | Final |

"Fila ativa" = fichas em AGUARDANDO ou CHAMADO. Após esgotar a primeira oportunidade sem comparecimento, a ficha retorna a AGUARDANDO no fim da mesma fila e recebe uma única nova oportunidade. A oportunidade seguinte encerrada sem atendimento leva a DESISTÊNCIA. A regra de 30 segundos entre chamadas e até 3 tentativas por oportunidade vale para a fila médica; a desistência explícita encerra a participação na fila ativa. A ficha guarda `oportunidade` e `fila_em` (ordem efetiva); cada evento de Chamada guarda oportunidade e tentativa.

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
- status operacional: Médico sem disponibilidade ao entrar; depois `DISPONIVEL`, `EM_ATENDIMENTO`, `PAUSA` ou `AUSENTE`.

### Regras
- Uma sessão sem logout é considerada encerrada quando expira.
- O Médico pode entrar novamente se perder o acesso à sessão anterior. O novo login não o torna disponível; a disponibilidade exige ação explícita (decisão do PO em 11/11/2026, substitui a recusa de segundo login de 10/11/2026).
- O logout do Médico encerra todas as suas sessões ainda ativas.
- PAUSA e AUSENTE são status operacionais durante uma sessão; não encerram a sessão.
- Encerramento do plantão é um evento operacional próprio, diferente de logout e expiração.

## Código de verificação

Código temporário de 6 dígitos enviado ao e-mail do usuário, usado no login (finalidade `LOGIN`) e na redefinição de senha (finalidade `REDEFINICAO_SENHA`).

### Principais informações
- usuário e finalidade;
- código (armazenado como hash, nunca em texto aberto);
- horário de criação, expiração e uso;
- número de tentativas de verificação.

### Regras
- Vale por 10 minutos, é de uso único e aceita no máximo 5 tentativas (valores configuráveis, os mesmos nas duas finalidades).
- Só existe um código válido por usuário e finalidade; pedir outro invalida o anterior, e um novo envio só é aceito 60 segundos após o último.
- No login, a sessão só é criada quando o código é conferido.

### Ciclo da sessão e status operacional

```
LOGIN → SESSÃO ATIVA → LOGOUT/EXPIRAÇÃO → SESSÃO ENCERRADA
```

Uma sessão está ativa quando `logout_em` é nulo e `expira_em` ainda está no futuro. A sessão do Médico começa sem disponibilidade; ele escolhe `DISPONIVEL` quando estiver pronto. A Recepção/Triagem começa DISPONIVEL. Durante a sessão, o status operacional pode ser `DISPONIVEL`, `EM_ATENDIMENTO`, `PAUSA` ou `AUSENTE`. Sem status, PAUSA e AUSENTE não habilitam novas atribuições ao Médico. Encerrar o plantão é uma ação operacional própria, separada do encerramento da sessão.

## Médico

Profissional que atende a fila priorizada.

### Principais informações
- usuário vinculado (relação 1:1);
- nome profissional/de exibição (pode ser derivado ou sincronizado do usuário no schema físico);
- CRM;
- especialidades próprias (relação N:N por `medico_especialidade`, preferência operacional, sem restrição absoluta);
- situação (ativo/inativo).

### Relacionamentos
- Um médico tem registros de Disponibilidade_Médico.
- Um médico tem vínculos com uma ou mais especialidades próprias por Médico_Especialidade.
- Um médico pode estar relacionado à sua Sala atual.
- Um médico realiza Chamadas.

### Regras
- O Administrador cadastra/edita o Médico junto com o usuário correspondente (nome, e-mail e senha inicial), com ao menos uma especialidade própria ativa. Desativar o médico desativa o login e é recusado enquanto houver ficha CHAMADO pendente.
- O Médico atende preferencialmente suas especialidades próprias; o vínculo não limita de forma absoluta as filas que pode apoiar.
- Uma ficha de fila descoberta com cor mais grave que a próxima própria pode ser atendida em apoio; empate de cor favorece a própria. Sem ficha própria, o Médico apoia primeiro fila descoberta e depois outra coberta. A especialidade da ficha permanece a definida pelos sintomas (Rev. 2.1, §7.2, D03–D05).
- Entre Vermelhas próprias, vale chegada e ID; entre Amarelas/Azuis próprias, há rodízio determinístico por médico, mantendo o ciclo interno de cada especialidade. Uma fila é descoberta quando não há médico próprio com plantão vigente e sessão apta a chamar; PAUSA/AUSENTE deixam de cobrir, EM_ATENDIMENTO não deixa a fila descoberta.
- A seleção e a reserva da ficha ocorrem no "Chamar próximo", atomicamente e sem escolha manual; novo login não concede disponibilidade, e cada médico tem no máximo uma ficha CHAMADO pendente (Rev. 2.1, §7.1–7.2, D02; decisão do PO em 11/11/2026).
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
- O Administrador cria e edita os dados da Recepção/Triagem juntamente com o usuário correspondente (nome, e-mail e senha inicial); o CPF é único e validado. Desativar o cadastro desativa o login.
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
- O vínculo é a sala atual do médico (`medico.sala_id`, opcional, sem histórico), mantido pelo Administrador; só sala ativa pode ser vinculada, e desativar a sala desfaz o vínculo dos médicos que a tinham (add-cadastros-administrador).

## Especialidade

Destino clínico indicado pelos sintomas (ex.: Clínica Geral — `CLI`); as fichas são organizadas em filas por especialidade.

### Principais informações
- nome, descrição e sigla usada na senha (única, 3 letras): Cardiologia `CAR`, Clínica Geral `CLI`, Neurologia `NEU`, Ortopedia `ORT` e Pediatria `PED`;
- situação (ativa/inativa).

### Relacionamentos
- Ligada a Sintomas por Sintoma_Especialidade, em ordem de preferência definida para cada sintoma.

### Regras
- A disponibilidade e as especialidades próprias do Médico não alteram o destino clínico da ficha; elas influem somente na seleção operacional da chamada.
- Destino da ficha (Rev. 2.1, §6, §14.2 e D09): paciente com até `idade_maxima_crianca` vai para Pediatria antes de qualquer cálculo. Para os demais, cada especialidade ligada a um sintoma do catálogo da ficha é candidata, e vence 1º a de maior pontuação individual de sintoma, 2º a de maior soma de pontos ligados, 3º a com menos fichas AGUARDANDO, 4º a de menor ID (transitório enquanto não houver estimativa de horário).
- Ficha sem sintoma do catálogo (só sintomas digitados ou só observação) vai para a especialidade padrão (Clínica Geral). Sintomas digitados contam no escore, mas não no destino.
- Sem fallback por falta de médico (RF19 supersedido, D10).

## Disponibilidade_Médico

Período em que um médico está disponível: médico, data, horário inicial e horário final. É registrada pelo Administrador depois de o médico informá-la fora do sistema.

- Horários no fuso America/Sao_Paulo; quando o fim é menor ou igual ao início, o período termina no dia seguinte (plantão noturno), com no máximo 24 horas.
- Não pode haver sobreposição entre períodos do mesmo médico (intervalos semiabertos: um período pode começar quando o outro termina).
- Período não iniciado pode ser alterado ou removido; período iniciado só pode ter o fim ajustado e nunca é removido.
- O Médico consulta os próprios períodos, sem alterá-los.

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
- Um paciente pode ter várias Fichas ao longo do tempo, mas no máximo uma ficha não finalizada. Uma nova abertura sem ticket devolve essa ficha (em triagem, reaberta para edição; aguardando ou chamada, com o atalho "Abrir ficha atual").

## Ticket_Pré-Triagem

Ticket simples emitido pelo Totem na chegada, antes da triagem.

### Principais informações
- tipo, escolhido pelo paciente no Totem: `PEDIATRICO`, `PREFERENCIAL` ou `NORMAL`;
- número sequencial do dia, separado por tipo e exibido com o prefixo do tipo (`C-001`, `P-001`, `N-001`);
- horário de emissão;
- status: `AGUARDANDO`, `CHAMADO`, `ATENDIDO`, `NAO_COMPARECEU` ou `DESISTENCIA`.

### Regras
- O tipo é autodeclarado no Totem e vale somente na fila de Recepção/Triagem (pré-triagem). Ele não define cor nem condição prioritária da ficha; depois da triagem, a ordem segue a classificação e a condição prioritária calculadas na triagem.
- Prioridade na pré-triagem: Pediátrico antes de Preferencial; os dois juntos formam os prioritários. Prioritários e normais alternam no ciclo configurável da fila pré-triagem (valor inicial: 2 prioritários : 1 normal), para que o Normal não espere indefinidamente. Dentro do mesmo tipo, vale a ordem de emissão.
- Cada tipo tem sua própria sequência diária, reiniciada a cada dia em `America/Sao_Paulo`.
- Não guarda dados pessoais.
- A ordem de chamada pela Recepção/Triagem pertence à futura change de operação da fila pré-triagem; a emissão por tipo pertence à change `add-totem`.
- Divergência pendente: o documento formal (Confluence) ainda descreve o ticket sem prioridade; deve ser atualizado pelo PO.
- A Recepção faz cada chamada e decide cada passo; nada acontece automaticamente. Depois da 1ª chamada da oportunidade espera-se o intervalo configurável (inicialmente 30 segundos) e depois da 2ª e da 3ª o intervalo de repetição configurável (inicialmente 10 segundos). Terminado o intervalo, a Recepção pode chamar novamente (até 3 chamadas por oportunidade) ou registrar "Não compareceu". A confirmação de presença encerra as chamadas e permite identificar o paciente e abrir a ficha.
- O primeiro "Não compareceu" devolve o ticket ao fim da fila uma única vez, sem novo número e sem perder sua identidade, com a contagem de chamadas zerada.
- O "Não compareceu" na segunda oportunidade dá ao ticket `NAO_COMPARECEU` e o retira da fila ativa.
- Desistência explícita altera o ticket para `DESISTENCIA`, estado final que o remove da fila ativa sem alterar Fichas.
- Dispensa por prazo: o Administrador vê e dispensa de uma vez, como `DESISTENCIA`, o ticket `AGUARDANDO` ou `CHAMADO` emitido há mais de `HORAS_EXPIRACAO` horas (inicialmente 24) e a ficha `EM_TRIAGEM`, `AGUARDANDO` ou `CHAMADO` com chegada há mais desse prazo. Cada um conta pela própria data, com evento `EXPIRACAO` no histórico em nome do Administrador. Não é chamada nem "não compareceu".

### Máquina de estados

``
AGUARDANDO
   ↓ chamar
CHAMADO
   ├─ compareceu → ATENDIDO (final)
   ├─ chamar novamente (após o intervalo, até 3 chamadas) → CHAMADO
   └─ não compareceu na 1ª oportunidade (após o intervalo) → AGUARDANDO (fim da fila)

não compareceu na 2ª oportunidade → NAO_COMPARECEU (final)
desistência explícita → removido da fila ativa
```

## Ficha_Atendimento

Passagem do paciente pelo PS, da triagem até o comparecimento, a desistência ou o cancelamento. É o centro do domínio.

### Principais informações
- paciente, ticket de origem (quando houver) e usuário que abriu a ficha;
- horário de chegada (define a ordem de chegada);
- sintomas do catálogo (via Ficha_Sintoma), sintomas digitados pela Recepção/Triagem com pontuação de 1 a 3 (valem só para a ficha, não entram no catálogo) e observações da queixa;
- gestante (sim/não) e condição prioritária resultante (idoso/criança/gestante);
- sinais vitais: PA sistólica, FC, FR, temperatura, glicemia capilar (com indicador de sinais de gravidade), SpO2;
- escore total = soma da pontuação de todos os sintomas (do catálogo e digitados) e dos pontos dos sinais vitais (incluindo glicemia quando medida), indicador de item clínico isolado com 3 pontos e classificação de risco (baixo/moderado/alto); não há máximo fixo;
- classificação calculada, classificação atual e justificativa do ajuste manual;
- especialidade sugerida e especialidade atribuída;
- senha (`COR-ESP-NÚMERO`), oportunidade atual, tentativas de chamada por oportunidade e `fila_em` como ordem efetiva da fila;
- médico que chamou;
- status (ver tabela de estados).

### Regras
- Toda ficha precisa de ao menos um sintoma (do catálogo ou digitado) ou uma observação de queixa (RN04).
- Escore de sintomas = soma dos pontos de todos os sintomas distintos (do catálogo e digitados); escore fisiológico = soma dos pontos dos sinais vitais; escore total = escore de sintomas + escore fisiológico (Rev. 2.1, D06).
- Escala experimental (simulação acadêmica, não protocolo clínico): Azul de 0 a 4, Amarela de 5 a 9, Vermelha a partir de 10; qualquer sintoma ou sinal vital com 3 pontos gera Vermelha. Limiares configuráveis.
- Classificação final: baixo → Azul, moderado → Amarela, alto → Vermelha.
- O cálculo automático só vale para paciente com 16 anos ou mais, não gestante, com PA sistólica, FC, FR, temperatura e SpO2 informados. Dado ausente não vira zero: o cálculo fica bloqueado e a tela informa o motivo. Menores de 16 anos e gestantes têm os sinais registrados e a prioridade definida por classificação manual justificada.
- Qualquer alteração de sintomas, observação, sinais vitais ou gestação recalcula a classificação e descarta o ajuste manual anterior (decisão do PO, 08/11/2026).
- A condição prioritária reordena dentro da mesma classificação e não soma pontos (RN10, RN11). Precedência no registro: gestante, depois idoso, depois criança; a idade é calculada na data de chegada.
- Na chamada, gestante, idoso e criança têm a mesma precedência entre si dentro da cor; a ordem entre essas fichas segue a posição efetiva na fila e, em empate, o menor ID. A precedência do registro acima serve apenas para escolher um rótulo quando mais de uma condição se aplica.
- O ajuste manual exige justificativa e gera Histórico_Alteração (RN09).
- A glicemia baixa recebe os pontos definidos na tabela da seção Faixas de sinais vitais.
- A senha é gerada somente após o direcionamento (RN19), na confirmação da triagem, que exige cor definida (calculada ou ajustada manualmente) e leva a ficha de EM_TRIAGEM a AGUARDANDO.
- Senha `COR-ESP-NNN`: V/A/B pela cor, sigla da especialidade e número diário por especialidade (fuso `America/Sao_Paulo`), compartilhado entre cores. O comprovante de 80 mm não traz nome, CPF, data de nascimento, sintomas nem sinais vitais; a reimpressão usa a mesma senha.
- Reavaliação em AGUARDANDO (RF12): a Recepção/Triagem pode alterar sintomas, observação, sinais vitais, gestação e o ajuste manual da ficha em AGUARDANDO; CHAMADO e os estados finais não são editáveis. Cada alteração recalcula a classificação, refaz o destino (sem contar a própria ficha no critério de fila) e atualiza a senha numa única operação, mantendo o horário de chegada. A ficha nunca fica na fila sem cor: a alteração que deixa a prioridade vazia é recusada, a menos que traga o ajuste manual justificado na mesma operação.
- Senha na reavaliação: sem mudança de cor e especialidade, continua a mesma; só a cor mudou, troca apenas a letra e mantém o número (`A-CAR-001` → `V-CAR-001`); a especialidade mudou, recebe o próximo número do dia da nova especialidade. Quando a senha muda, o comprovante impresso deixa de valer e a tela oferece a reimpressão.

## Ficha_Sintoma

Associação entre ficha e sintoma, com observação opcional.

## Chamada

Tentativa de chamar uma ficha.

### Principais informações
- ficha, médico, número da oportunidade, número da tentativa (1 a 3), tipo do evento e data/hora.

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
| Ciclo da fila pré-triagem (tickets do Totem) | 2 prioritários (Pediátrico antes de Preferencial) : 1 normal |
| Intervalo entre chamadas da mesma senha (Médico) e após a 1ª chamada do ticket (Recepção/Triagem) | 30 segundos |
| Intervalo após a 2ª e a 3ª chamada do ticket (Recepção/Triagem) | 10 segundos |
| Tentativas por oportunidade | 3 |
| Novas oportunidades após a primeira reentrada | 1 |
| Tamanho da previsão do painel | 5 |
| Prazo para encerrar ficha ou ticket não concluído (`HORAS_EXPIRACAO`) | 24 horas |
| Especialidade padrão (ficha sem sintoma do catálogo) | Clínica Geral |
| Limiar da cor Amarela | escore total a partir de 5 |
| Limiar da cor Vermelha | escore total a partir de 10, ou qualquer item com 3 pontos |
| Idade mínima para a tabela adulta de sinais vitais | 16 anos |

O fuso do projeto é fixo em `America/Sao_Paulo`; não é parâmetro editável pelo Administrador.

## Faixas de sinais vitais

Tabela configurável que dá de 0 a 3 pontos para cada parâmetro de sinal vital, com extremos inclusivos e temperatura com uma casa decimal. Vale só para pessoas com 16 anos ou mais e não gestantes (Rev. 2.1, §21). Os valores vêm da tabela adulta do NEWS2 usada como referência de pontuação para a simulação; o escore não é NEWS2 nem protocolo clínico.

| Parâmetro | 0 ponto | 1 ponto | 2 pontos | 3 pontos |
|---|---|---|---|---|
| PA sistólica (mmHg) | 111–219 | 101–110 | 91–100 | ≤90 ou ≥220 |
| FC (bpm) | 51–90 | 41–50 ou 91–110 | 111–130 | ≤40 ou ≥131 |
| FR (irpm) | 12–20 | 9–11 | 21–24 | ≤8 ou ≥25 |
| Temperatura (°C) | 36,1–38,0 | 35,1–36,0 ou 38,1–39,0 | ≥39,1 | ≤35,0 |
| SpO2 (%) | ≥96 | 94–95 | 92–93 | ≤91 |

A glicemia é opcional e segue a regra local:

| Glicemia | Condição | Pontos |
|---|---|---:|
| `< 54 mg/dL` | Com sinais de gravidade | 3 |
| `< 54 mg/dL` | Sem sinais de gravidade | 2 |
| `54–59 mg/dL` | Com sinais de gravidade | 2 |
| `54–59 mg/dL` | Sem sinais de gravidade | 1 |
| `≥ 60 mg/dL` | Qualquer | 0 (convenção de simulação; não há regra de hiperglicemia) |

Limites de digitação aceitos (validação, não pontuação): PA 40–300, FC 20–250, FR 4–80, temperatura 25,0–45,0, SpO2 50–100, glicemia 10–1500.

# Modelo de Domínio — Sistema de Fila Prioritária para Pronto-Socorro

Modelo conceitual do domínio. Representa conceitos e relacionamentos, não o esquema físico do Xano: nomes de tabelas e campos são definidos no `design.md` de cada change. Baseado no modelo conceitual do documento formal v1.0 (seção 17), com os refinamentos do contexto do PO de 27/09/2026.

## Visão geral dos relacionamentos

```
Usuário ──(perfil)──> Recepção/Triagem | Médico | Administrador
   │
   ├──< Sessão (login/logout + status operacional)
   │
   └── Médico ──< Médico_Especialidade >── Especialidade ──< Especialidade_Alternativa (ordenada)
         │                                     ▲
         └──< Disponibilidade_Médico           │
                                               │
Sintoma ──< Sintoma_Especialidade (ordenada) >─┘

Ticket_Pré-Triagem ──(atendido por)──> Ficha_Atendimento

Paciente ──< Ficha_Atendimento ──< Ficha_Sintoma >── Sintoma
                    │
                    ├── Sinais vitais + escore e classificação de risco
                    ├── Prioridade calculada / atual + condição prioritária
                    ├── Especialidade sugerida / atribuída + senha
                    └──< Chamada (≤ 3 tentativas) >── Médico

Histórico_Alteração → referencia a entidade alterada + Usuário responsável
Parâmetros de regra / Faixas de sinais vitais → configuração usada pelas regras
```

## Estados da Ficha_Atendimento

| Estado | Significado | Próximos estados |
|---|---|---|
| EM_TRIAGEM | Ficha aberta; triagem em andamento, ainda sem senha. | AGUARDANDO, CANCELADO |
| AGUARDANDO | Paciente ativo na fila priorizada de uma especialidade. | CHAMADO, CANCELADO |
| CHAMADO | Senha chamada por um médico; aguarda comparecimento. | ATENDIDO, DESISTÊNCIA |
| ATENDIDO | Paciente compareceu e saiu da fila (não é conclusão clínica). | Final |
| DESISTÊNCIA | Três chamadas sem comparecimento. | Final; um retorno exige nova ficha |
| CANCELADO | Ficha retirada por ação autorizada, com justificativa. | Final |

"Fila ativa" = fichas em AGUARDANDO ou CHAMADO. O estado EM_TRIAGEM não existe no documento formal: foi incluído porque a ficha é aberta antes de receber senha. O documento formal também prevê CHAMADO → AGUARDANDO ("nova tentativa"); neste projeto, a nova tentativa mantém a ficha em CHAMADO com o mesmo médico (ver change `add-fila-chamada-medico`).

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
- Um usuário com perfil Médico corresponde a um registro de Médico.
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

## Médico

Profissional que atende a fila priorizada.

### Principais informações
- usuário vinculado;
- registro profissional (identificação acadêmica);
- situação (ativo/inativo).

### Relacionamentos
- Um médico atende uma ou mais Especialidades (Médico_Especialidade).
- Um médico tem registros de Disponibilidade_Médico.
- Um médico realiza Chamadas.

### Regras
- Especialidades e disponibilidade são definidas pelo Administrador; o médico não as altera (RN16).
- Somente médicos com disponibilidade vigente recebem pacientes (RN15).

## Especialidade

Área de atendimento (ex.: Clínica Geral — `CLI`). Cada especialidade tem sua própria fila priorizada.

### Principais informações
- nome, descrição e sigla usada na senha (única, 3 letras);
- situação (ativa/inativa).

### Relacionamentos
- Ligada a Sintomas por Sintoma_Especialidade.
- Tem Especialidades Alternativas ordenadas (Especialidade_Alternativa), usadas como fallback quando não há médico disponível.

## Disponibilidade_Médico

Período em que um médico atende: médico, data, horário inicial e horário final. É registrada pelo Administrador depois de o médico informá-la fora do sistema.

## Sintoma

Queixa selecionável na triagem.

### Principais informações
- nome, descrição e grupo (cardiovascular, respiratório, neurológico, gastrointestinal, traumático/ortopédico, geral);
- prioridade padrão (Vermelha, Amarela ou Azul);
- situação (ativo/inativo).

### Relacionamentos
- Aponta para uma ou mais especialidades, em ordem de preferência (Sintoma_Especialidade).

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

Senha simples emitida pelo totem (simulado) na chegada, antes da triagem.

### Principais informações
- número sequencial do dia;
- horário de emissão;
- status: `AGUARDANDO`, `CHAMADO`, `ATENDIDO` ou `NAO_COMPARECEU`.

### Regras
- Não tem cor nem prioridade: é chamado pela Recepção/Triagem em ordem de emissão.
- Não guarda dados pessoais.

## Ficha_Atendimento

Passagem do paciente pelo PS, da triagem até o comparecimento, a desistência ou o cancelamento. É o centro do domínio.

### Principais informações
- paciente, ticket de origem (quando houver) e usuário que abriu a ficha;
- horário de chegada (define a ordem de chegada);
- sintomas (via Ficha_Sintoma) e observações da queixa;
- gestante (sim/não) e condição prioritária resultante (idoso/criança/gestante);
- sinais vitais: PA sistólica, FC, FR, temperatura, glicemia capilar (com indicador de sinais de gravidade), SpO2;
- escore de risco (0–18), indicador de parâmetro isolado com 3 pontos e classificação de risco (baixo/moderado/alto);
- prioridade calculada, prioridade atual e justificativa do ajuste manual;
- especialidade sugerida e especialidade atribuída;
- senha (`COR-ESP-NÚMERO`) e número de tentativas de chamada;
- médico que chamou;
- status (ver tabela de estados).

### Regras
- Toda ficha precisa de ao menos um sintoma ou uma observação de queixa (RN04).
- Prioridade calculada = a pior entre a cor do sintoma mais grave e a cor sugerida pelo risco; o risco só agrava.
- A condição prioritária reordena dentro da cor, sem mudá-la (RN10, RN11).
- O ajuste manual exige justificativa e gera Histórico_Alteração (RN09).
- A senha é gerada somente após o direcionamento (RN19).

## Ficha_Sintoma

Associação entre ficha e sintoma, com observação opcional.

## Chamada

Tentativa de chamar uma ficha.

### Principais informações
- ficha, médico, número da tentativa (1 a 3) e data/hora.

### Regras
- No máximo três tentativas por ficha (RN27).
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

Valores configuráveis pelo Administrador, não fixos no código. Valores iniciais:

| Parâmetro | Valor inicial |
|---|---|
| Idade mínima para idoso | 60 anos |
| Idade máxima para criança | 11 anos (menor de 12) |
| Ciclo de chamada sem vermelhos | 2 amarelas : 1 azul |
| Máximo de tentativas de chamada | 3 |
| Tamanho da previsão do painel | 5 |
| Especialidade padrão (ficha sem sintoma com especialidade) | Clínica Geral |
| Limiar de risco moderado | escore ≥ 3 |
| Limiar de risco alto | escore ≥ 6, ou qualquer parâmetro isolado com 3 pontos |

## Faixas de sinais vitais

Tabela configurável que dá de 0 a 3 pontos para cada parâmetro de sinal vital, conforme o modelo validado pelo PO (seção 9 do contexto: NEWS2/MEWS + glicemia). Os valores iniciais estão na spec `classificacao-prioridade` da change `add-triagem-classificacao`.

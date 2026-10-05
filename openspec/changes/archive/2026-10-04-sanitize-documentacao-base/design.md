# Design da sanitização documental

## Contexto

Esta é uma change de **saneamento da fonte de verdade**, equivalente ao padrão de sanitização documental já usado no MIRA: o objetivo não é implementar comportamento, e sim garantir que agentes e pessoas partam de uma base única, curta, coerente e sem decisões obsoletas. `openspec/config.yaml` deve continuar sendo contexto global resumido; detalhes de domínio ficam em `docs/project-overview.md` e `docs/domain-model.md`.

Quando houver conflito entre os documentos atuais e as decisões abaixo, **valem as decisões desta change**, pois foram consolidadas pelo PO em 04/10/2026. O apply deve alterar apenas documentação.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Eliminar contradições antes da implementação funcional.
- Deixar explícitos modelo de domínio, fluxo, permissões, estados, pontuação e regras operacionais.
- Garantir que qualquer agente consiga ler os documentos-base e chegar às mesmas regras.
- Registrar quais changes antigas ficaram obsoletas, sem corrigi-las ainda.

**Fora dos objetivos:**
- Código, schema físico, endpoints, testes e telas.
- Reescrever as changes funcionais nesta mesma execução.
- Criar um protocolo clínico real.

## Decisões


### D0. Isolamento obrigatório em branch Git

Esta sanitização DEVE ser executada exclusivamente na branch `docs/sanitize-documentacao-base`. Antes de editar qualquer arquivo, o agente deve:

1. executar `git status`;
2. preservar integralmente qualquer alteração local preexistente do usuário;
3. partir da `main` sem modificá-la;
4. criar/trocar para `docs/sanitize-documentacao-base`;
5. confirmar a branch ativa com `git branch --show-current`;
6. somente então iniciar as tarefas documentais.

Se a árvore de trabalho impedir a criação/troca segura de branch, o agente DEVE interromper o apply e informar o bloqueio. Não deve executar `git reset --hard`, `git clean`, stash automático, descarte de alterações, merge ou rebase para contornar o problema. Nenhuma alteração desta change pode ser feita diretamente na `main`.

### D1. Hierarquia da fonte de verdade após a sanitização

Após o apply, o contexto deve ser lido nesta ordem:

1. `docs/project-overview.md` — fluxo, escopo, perfis e regras globais aprovadas;
2. `docs/domain-model.md` — entidades, relacionamentos, estados e conceitos;
3. `openspec/config.yaml` — resumo global para agentes;
4. specs/changes — comportamento detalhado de cada fatia, que deve ser revisado quando divergir da base sanitizada;
5. documento formal/Confluence — referência de RF/RNF/RN, atualizado até RF50; divergências ainda não sincronizadas devem ser apontadas, sem reintroduzir regras já substituídas pelo PO.

`AGENTS.md` deve refletir essa ordem e impedir que uma decisão antiga de uma change seja aplicada contra os documentos sanitizados.

### D2. Perfis e entidades cadastrais

`Usuario` permanece responsável por autenticação e autorização (`nome`, `email`, senha hash, perfil, ativo). Dados específicos de função ficam em entidades próprias.

#### Médico

Entidade `Medico`, vinculada 1:1 a um `Usuario` de perfil MEDICO.

Informações conceituais mínimas:
- usuário vinculado;
- nome profissional/exibição (pode ser derivado/sincronizado do usuário no schema físico; a decisão física fica para a change funcional);
- CRM;
- especialidade de referência;
- ativo/inativo;
- disponibilidade por período;
- sala atual, quando houver.

A especialidade de referência **não restringe** quais filas o médico pode atender.

#### Recepção/Triagem

Entidade `Recepcao_Triagem`, vinculada 1:1 a um `Usuario` de perfil RECEPCAO_TRIAGEM.

Informações conceituais mínimas:
- usuário vinculado;
- nome;
- CPF;
- especialidade de referência;
- ativo/inativo.

A especialidade de referência é cadastral e não deve ser usada para limitar as operações de triagem sem uma regra futura explícita.

#### Cadastro administrativo

O Administrador deve possuir interface futura para criar/editar os dados de Médico e Recepção/Triagem juntamente com o usuário correspondente. Esta change apenas documenta esse comportamento; a implementação pertence às changes funcionais.

### D3. Sala

Criar conceitualmente a entidade `Sala`:
- identificador;
- nome/número;
- descrição opcional;
- situação ativa/inativa.

O Médico pode estar relacionado a uma Sala atual. A chamada pública deve conseguir apresentar a sala do médico responsável, sem expor nome/CPF do paciente.

A definição física (FK direta, associação histórica ou vínculo por plantão) fica para a change funcional que implementar Sala; a documentação-base não deve inventar o schema.

### D4. Fluxo de especialidade e atendimento médico

O fluxo possui duas decisões distintas:

1. **Destino clínico:** o sistema identifica automaticamente a especialidade mais adequada aos sintomas e coloca a ficha na fila dessa especialidade.
2. **Executor operacional:** um médico elegível pode receber/atender a ficha independentemente da especialidade cadastrada nele.

Portanto:
- a especialidade da ficha não deve ser trocada só porque o médico possui outra especialidade;
- `Especialidade_Alternativa` deixa de ser necessária como mecanismo para procurar outro tipo de médico, pois a especialidade do médico não restringe o atendimento;
- qualquer remoção física de tabelas/relacionamentos antigos fica para change funcional posterior;
- se múltiplos sintomas apontarem para especialidades diferentes, o documento-base deve manter o direcionamento automático e registrar que a regra detalhada de desempate pertence à spec funcional de direcionamento. A sanitização não deve inventar um novo algoritmo de balanceamento/desempate fora do que já estiver aprovado.

### D5. Totem no escopo

O Totem deixa de ser descrito como externo/abstraído. O projeto produzirá a experiência do totem em change própria.

Fluxo mínimo:

```text
Paciente → Totem → gerar ticket → registrar no Xano → fila de Recepção/Triagem
```

O ticket não contém dados pessoais e entra em ordem de emissão.

### D6. Pontuação de sintomas e composição do escore final

`Sintoma.prioridade_padrao` em formato de cor é uma decisão obsoleta. A documentação deve usar `pontuacao` inteira entre 1 e 3.

A regra conceitual passa a ser:

```text
escore_sintomas = soma dos pontos de TODOS os sintomas selecionados
escore_fisiologico = soma dos pontos dos sinais vitais, incluindo glicemia quando medida
escore_total = escore_sintomas + escore_fisiologico
```

Condições prioritárias (idoso, criança e gestante) continuam reordenando dentro da mesma classificação e **não somam pontos**, salvo futura decisão explícita.

Os limiares iniciais já existentes permanecem como parâmetros até change funcional específica alterá-los:
- moderado: escore total >= 3;
- alto: escore total >= 6;
- qualquer item clínico isolado com 3 pontos pode elevar o risco ao nível alto.

Como o escore agora inclui sintomas, a documentação não deve mais afirmar que o escore máximo é 18.

Classificação final:
- baixo → Azul;
- moderado → Amarela;
- alto → Vermelha.

### D7. Glicemia

Manter na base a seguinte tabela:

| Glicemia | Condição | Pontos |
|---|---|---:|
| `< 54 mg/dL` | com sinais de gravidade | 3 |
| `< 54 mg/dL` | sem sinais de gravidade | 2 |
| `54–59 mg/dL` | com sinais de gravidade | 2 |
| `54–59 mg/dL` | sem sinais de gravidade | 1 |

Os demais intervalos já especificados podem permanecer, desde que não contradigam esta regra.

### D8. Catálogo inicial de sintomas

A lista abaixo é a carga acadêmica de referência. A pontuação é parte do modelo do projeto e não representa protocolo clínico real. O catálogo deve ser documentado em `domain-model.md` ou seção de dados de referência apontada por ele.

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

### D9. Pausa e encerramento de plantão

**Pausar:**
- ação do Médico;
- altera seu status operacional para PAUSA;
- impede novos atendimentos de serem atribuídos à sua fila;
- não remove atendimentos já atribuídos.

**Retomar:**
- volta a DISPONIVEL, desde que exista disponibilidade/plantão vigente.

**Encerrar plantão:**
- ação explícita do Médico;
- botão deve permanecer bloqueado enquanto houver item ativo na fila atribuída ao médico;
- quando a fila estiver zerada, registra o encerramento do período/plantão e o médico deixa de ser elegível para novos atendimentos;
- não deve depender apenas de logout silencioso para representar fim de plantão.

### D10. Chamadas e nova oportunidade

Regra global para Recepção/Triagem e Médico:
- intervalo entre chamadas da mesma senha: **30 segundos**;
- até **3 tentativas de chamada por oportunidade**;
- se não houver comparecimento após esgotar a oportunidade, a senha volta ao fim da mesma fila e recebe **uma única nova oportunidade de atendimento**;
- desistência explícita remove imediatamente a senha da fila ativa;
- a documentação não deve mais dizer que três chamadas resultam automaticamente em desistência definitiva na primeira passagem pela fila.

Para o Ticket Pré-Triagem, usar `NAO_COMPARECEU` apenas quando o item encerrar definitivamente sem atendimento; para a Ficha, preservar `DESISTENCIA` como estado final quando houver desistência/encerramento definitivo conforme a spec funcional posterior. Esta sanitização não altera schema físico.

### D11. Estados do Ticket Pré-Triagem

A documentação-base deve ter uma máquina de estados explícita, incluindo a volta ao fim da fila:

```text
AGUARDANDO
   ↓ chamar
CHAMADO
   ├─ compareceu → ATENDIDO (final)
   ├─ nova tentativa dentro do limite → CHAMADO
   └─ oportunidade esgotada → AGUARDANDO (fim da fila, uma única nova oportunidade)

segunda oportunidade encerrada sem atendimento → NAO_COMPARECEU (final)
desistência explícita → removido da fila conforme regra registrada
```

A reentrada no fim da fila deve ser registrada sem gerar novo ticket nem perder sua identidade.

### D12. Sessão e status operacional

Separar conceitualmente sessão de status operacional:

```text
LOGIN → SESSÃO ATIVA → LOGOUT/EXPIRAÇÃO → SESSÃO ENCERRADA
```

Sessão ativa = `logout_em` nulo e `expira_em` ainda válido.

Status operacional durante a sessão:
- `DISPONIVEL`;
- `EM_ATENDIMENTO`;
- `PAUSA`;
- `AUSENTE`.

Pausa/Ausência não encerram a sessão. Médico em PAUSA ou AUSENTE não recebe novos atendimentos. Encerramento de plantão é um evento operacional próprio e não deve ser confundido com expiração da sessão.

### D13. Matriz global de permissões

A documentação deve incluir, no mínimo, esta matriz conceitual. Todas as permissões reais são validadas no Xano; Reflex apenas apresenta/oculta ações.

| Funcionalidade | Recepção/Triagem | Médico | Administrador | Público |
|---|:---:|:---:|:---:|:---:|
| Login | ✅ | ✅ | ✅ | ❌ |
| Pesquisar/cadastrar paciente por CPF | ✅ | ❌ | consulta quando necessário | ❌ |
| Abrir/editar ficha de triagem | ✅ | ❌ | consulta | ❌ |
| Registrar sintomas e sinais vitais | ✅ | ❌ | ❌ | ❌ |
| Confirmar/ajustar classificação | ✅ | ❌ | ❌ | ❌ |
| Chamar fila de pré-triagem | ✅ | ❌ | acompanhamento | ❌ |
| Ver dados pessoais de paciente | ✅ | apenas da ficha sob atendimento | conforme acompanhamento autorizado | ❌ |
| Ver fila atribuída | ❌ | ✅ | ✅ | ❌ |
| Chamar próximo paciente médico | ❌ | ✅ | ❌ | ❌ |
| Pausar/retomar recebimento de novos atendimentos | ❌ | ✅ | acompanhamento | ❌ |
| Encerrar próprio plantão com fila zerada | ❌ | ✅ | acompanhamento | ❌ |
| Confirmar comparecimento / registrar desistência | ❌ | ✅ | ❌ | ❌ |
| Gerenciar usuários e perfis | ❌ | ❌ | ✅ | ❌ |
| Cadastrar Médico e Recepção/Triagem | ❌ | ❌ | ✅ | ❌ |
| Gerenciar especialidades, sintomas, salas e parâmetros | ❌ | ❌ | ✅ | ❌ |
| Definir disponibilidade/período dos médicos | ❌ | ❌ | ✅ | ❌ |
| Acompanhar fila geral, equipe e auditoria | ❌ | ❌ | ✅ | ❌ |
| Visualizar painel público | ✅ | ✅ | ✅ | ✅ |
| Ver nome/CPF no painel público | ❌ | ❌ | ❌ | ❌ |

Onde a tabela usar "consulta" ou "acompanhamento", a documentação deve deixar claro que isso não concede operação de triagem/chamada ao Administrador.

### D14. RF01–RF50 e referência-base

Atualizar a seção de fonte de verdade para declarar cobertura formal **RF01–RF50**. O Codex não deve inventar o texto ausente de RF24–RF26 nem renumerar requisitos. Deve apenas:
- corrigir o intervalo declarado;
- refletir nos documentos locais as decisões aprovadas nesta sanitização;
- manter rastreabilidade para RF39–RF50 já citadas pelas changes;
- marcar que o documento formal/Confluence precisa permanecer sincronizado com o contexto consolidado do PO.

### D15. Configuração global para agentes

`openspec/config.yaml` deve ser curto e conter somente invariantes globais, entre eles:
- Reflex no frontend; Xano/XanoScript no backend e banco;
- OpenSpec como processo de especificação;
- perfis oficiais;
- pontuação final = sintomas + sinais vitais;
- médico não restrito à especialidade cadastral;
- Totem no escopo com change própria;
- chamadas a cada 30 segundos, 3 tentativas por oportunidade e uma reentrada ao fim da fila;
- fuso fixo `America/Sao_Paulo`;
- autorização no backend;
- painel público sem nome/CPF.

Detalhes extensos (lista de sintomas, estados completos e matriz) ficam nos docs, não no config.

## Riscos / Compromissos

- [Changes existentes continuarão contraditórias após esta sanitização] → Não corrigi-las aqui. O apply deve gerar uma lista objetiva de impactos para atualização posterior, evitando misturar saneamento com implementação.
- [A pontuação de sintomas muda a escala do escore] → Remover a afirmação de máximo 18. Manter limiares 3/6 como parâmetros iniciais até revisão funcional explícita.
- [Especialidade do médico deixou de restringir atendimento] → Remover a dependência conceitual de `Medico_Especialidade`/fallback por disponibilidade do médico dos documentos-base; schema físico será tratado depois.
- [Lista clínica pode ser interpretada como protocolo real] → Manter aviso destacado de que é modelagem acadêmica baseada em referências de triagem e não substitui protocolo médico.

## Plano de aplicação

1. Atualizar `docs/project-overview.md`.
2. Atualizar `docs/domain-model.md`.
3. Reduzir/atualizar `openspec/config.yaml` para os invariantes novos.
4. Atualizar `AGENTS.md` quanto à ordem da fonte de verdade e às decisões que não podem ser reintroduzidas.
5. Sincronizar resumos contraditórios em `README.md` e `CONTRIBUTING.md`.
6. Executar busca textual por termos obsoletos e corrigir somente documentos-base/derivados, sem tocar nas changes funcionais.
7. Registrar relatório de impacto das changes que deverão ser atualizadas depois.

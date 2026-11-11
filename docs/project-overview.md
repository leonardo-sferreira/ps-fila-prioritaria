# Visão Geral do Projeto — Sistema de Fila Prioritária para Pronto-Socorro

## 1. Visão geral

Sistema web que controla a entrada, a triagem e a chamada de pacientes nas filas de um pronto-socorro (PS). O escore clínico soma a pontuação de todos os sintomas selecionados aos pontos dos sinais vitais; a classificação resultante, a condição prioritária e a ordem de chegada orientam a fila. A ficha é direcionada à especialidade indicada pelos sintomas. O médico atende preferencialmente suas especialidades cadastradas e pode apoiar outras filas conforme a gravidade e a cobertura do plantão.

A responsabilidade do sistema termina quando o paciente comparece à chamada do médico (ATENDIDO) ou é marcado como desistente (DESISTÊNCIA). Não há prontuário, diagnóstico nem controle da consulta.

> Projeto acadêmico: as regras de sintomas, prioridade, fator de risco e direcionamento são modelagem de projeto de faculdade e não têm valor de protocolo clínico real.

## 2. Problema

Quando a fila é organizada manualmente, fica difícil identificar o próximo paciente, respeitar prioridades e informar aos pacientes uma previsão das próximas chamadas. Pacientes graves podem esperar o mesmo tempo que pacientes com quadros leves, e a recepção não tem apoio para decidir quem deve ser atendido primeiro nem para qual especialidade direcionar a ficha.

## 3. Objetivos

- Priorizar o atendimento pela gravidade clínica (sintomas + sinais vitais), e não apenas pela ordem de chegada.
- Direcionar cada ficha automaticamente para a especialidade adequada aos sintomas e distribuí-la a um médico elegível conforme as regras operacionais.
- Selecionar automaticamente o próximo paciente, sem que o médico escolha manualmente quem chamar.
- Dar à equipe uma visão clara das filas e ao público um painel de chamadas que preserve a privacidade.
- Registrar toda alteração relevante para fins de auditoria.

## 4. Usuários

| Perfil | Papel |
|---|---|
| **Recepção/Triagem** | Perfil único: recebe tickets da fila de pré-triagem, pesquisa ou cadastra o paciente por CPF, abre a ficha, registra sintomas e sinais vitais, confirma ou ajusta a classificação (com justificativa) e confirma a entrada na fila da especialidade indicada. Tem cadastro próprio, vinculado 1:1 ao usuário, com nome, CPF e especialidade de referência. |
| **Médico** | Vê as filas e a ficha sob sua responsabilidade, chama o próximo paciente escolhido pelo sistema, pausa ou retoma o recebimento de novas atribuições, confirma o comparecimento ou registra desistência e imprime a ficha. Seu cadastro, vinculado 1:1 ao usuário, inclui nome profissional, CRM, várias especialidades próprias, disponibilidade por período e sala atual. As especialidades próprias orientam a preferência, sem impedir apoio a outras filas. O plantão só pode ser encerrado explicitamente quando sua fila atribuída estiver zerada. |
| **Administrador** | Gerencia usuários e perfis, cadastros de Médicos e Recepção/Triagem, especialidades, sintomas, salas, parâmetros e auditoria; define disponibilidade dos médicos e acompanha a fila geral e a equipe. Consultas administrativas não concedem operações de triagem ou chamada. |
| **Paciente (público)** | Não acessa o sistema. Recebe o ticket no totem e a senha impressa, e acompanha as chamadas no painel público. |

## 5. Escopo

### Fluxo macro

```
Paciente → Totem → Ticket na fila de Recepção/Triagem → Triagem e classificação → Fila da especialidade indicada pelos sintomas → Médico elegível → Chamada em sala → Painel público
```

1. O paciente usa o **Totem**, parte do escopo do projeto, para gerar um ticket sem dados pessoais e registrá-lo na fila de Recepção/Triagem. A implementação terá uma change funcional própria.
2. A fila de Recepção/Triagem usa tickets numéricos sequenciais por tipo, com precedência pediátrica e ciclo configurável inicial de dois prioritários para um normal; dentro do tipo, segue a ordem efetiva da fila. Toda chamada é feita pela Recepção, sem nada automático: até 3 chamadas por oportunidade; depois da 1ª chamada espera-se o intervalo configurável inicial de 30 segundos e, depois da 2ª e da 3ª, o intervalo de repetição configurável inicial de 10 segundos. Terminado o intervalo, a Recepção chama novamente (se ainda houver chamada na oportunidade) ou registra "Não compareceu". O primeiro "Não compareceu" devolve o ticket ao fim da fila uma única vez; o segundo o encerra como não comparecido. Desistência explícita o remove da fila ativa.
3. A **Recepção/Triagem** identifica o paciente pelo CPF, abre a ficha, registra sintomas e sinais vitais e confirma ou ajusta a classificação.
4. O sistema soma os pontos de todos os sintomas selecionados aos pontos dos sinais vitais e classifica o risco. Em "Confirmar e gerar senha" (exige cor definida), direciona a ficha à especialidade indicada pelos sintomas do catálogo (Pediatria até 11 anos; desempate por maior sintoma, maior soma, menor fila e menor ID; Clínica Geral quando não há sintoma do catálogo). A ficha recebe a senha `COR-ESP-NNN`, entra na fila dessa especialidade e o comprovante de 80 mm é impresso sem dados pessoais. Enquanto a ficha aguarda (AGUARDANDO), a Recepção/Triagem pode corrigir sintomas, sinais vitais e prioridade: o sistema recalcula cor, destino e senha, mantém a ordem de chegada e, se a senha mudar, pede a reimpressão do comprovante. A ficha aguardando é aberta pela aba "Fichas do dia" (fichas não finalizadas e finalizadas de hoje) ou pela identificação do paciente, que mostra "Abrir ficha atual" quando ele já está na fila.
5. A ficha permanece na fila de sua especialidade clínica. Ao acionar "Chamar próximo", o médico elegível recebe uma ficha escolhida naquele instante: primeiro entre suas especialidades próprias, com rodízio entre elas para Amarelas/Azuis; atende uma fila descoberta quando a melhor candidata dela tem cor mais grave que a próxima própria. Sem ficha própria, apoia primeiro uma fila descoberta e depois outra fila coberta. A especialidade e a senha da ficha não mudam.
6. A reserva da ficha e o evento de chamada são atômicos; o médico não escolhe manualmente a ficha. A chamada médica segue a regra de 30 segundos entre chamadas, 3 tentativas por oportunidade e uma reentrada ao fim da fila. O painel público apresenta a senha e a sala, sem dados pessoais do paciente.

### Fora do escopo

- Prontuário eletrônico, diagnóstico, prescrição, exames e resultados laboratoriais.
- Encaminhamento clínico pelo médico (substituído pela impressão da ficha de atendimento).
- Controle da duração da consulta e botão de finalizar consulta.
- Agendamento de consultas futuras; cobrança, faturamento e convênios.
- Alteração da própria disponibilidade ou cadastro de sintomas/especialidades pelo médico.
- Promoção automática de prioridade por tempo de espera.

## 6. Principais funcionalidades

- Autenticação e controle de acesso por perfil, com código enviado por e-mail no login e na redefinição de senha.
- Emissão de ticket e fila pré-triagem.
- Pesquisa, cadastro e atualização de pacientes por CPF.
- Ficha de atendimento com sintomas, observações e sinais vitais (PA, FC, FR, temperatura, glicemia capilar, SpO2).
- Classificação em três cores (Vermelha, Amarela, Azul) com base na soma numérica de sintomas e sinais vitais, com ajuste manual justificado.
- Direcionamento automático à especialidade indicada pelos sintomas; qualquer médico elegível pode atender essa fila.
- Geração, impressão e reimpressão de senha.
- Fila priorizada por especialidade, com seleção automática do próximo paciente.
- Chamada manual pela Recepção/Triagem (30 segundos após a 1ª chamada e 10 segundos após as seguintes) e pelo Médico (30 segundos entre chamadas), até 3 tentativas por oportunidade e uma única reentrada ao fim da fila; desistência explícita remove a senha da fila ativa.
- Pausar e retomar o recebimento de atribuições pelo Médico; encerrar o plantão explicitamente apenas com a fila atribuída zerada.
- Painel público com senha, sala e previsão das próximas 5, sem nome nem CPF.
- Cadastros do administrador e disponibilidade diária dos médicos.
- Tela de acompanhamento do administrador: fila geral, pessoas logadas e seus status, auditoria.
- Aviso de privacidade público, acessível pelas telas de acesso (texto em `docs/aviso-de-privacidade.md`).

## 7. Regras e restrições importantes

- **Pontuação de sintomas:** cada sintoma tem pontuação inteira de 1 a 3; todos os sintomas selecionados somam pontos. A pontuação não é uma cor nem representa protocolo clínico real.
- **Escore clínico:** soma os pontos de todos os sintomas (do catálogo ou digitados pela Recepção/Triagem com gravidade de 1 a 3) aos pontos dos sinais vitais, incluindo glicemia quando medida. Escala experimental: Azul de 0 a 4, Amarela de 5 a 9 e Vermelha a partir de 10; qualquer item com 3 pontos gera Vermelha. O cálculo automático vale para 16 anos ou mais e não gestantes com os cinco sinais vitais informados; nos demais casos a classificação é manual e justificada. Não há máximo fixo para o escore total.
- **Classificação:** baixo → Azul, moderado → Amarela e alto → Vermelha. Idoso, criança e gestante reordenam dentro da mesma classificação, sem somar pontos nem alterar a classificação. O ajuste manual exige justificativa e é descartado quando sintomas ou sinais vitais mudam.
- **Direcionamento e médico:** os sintomas definem automaticamente a especialidade da ficha. O cadastro N:N de especialidades próprias define a preferência do médico, não uma restrição de atendimento. A escolha entre filas segue a Rev. 2.1, §7.1–7.2, §14.1 e D02–D05: Vermelha própria antes das demais próprias; rodízio por médico entre próprias para Amarelas/Azuis, preservado o ciclo interno 2:1 de cada fila; fila descoberta supera a própria apenas por cor mais grave, e a própria vence empate. Sem fichas próprias, apoiar descoberta; sem descoberta, apoiar outra coberta. Descoberta significa sem médico próprio com plantão vigente e sessão apta; PAUSA/AUSENTE não dão cobertura, EM_ATENDIMENTO não a remove.
- **Ordem interna da especialidade:** somente fichas AGUARDANDO participam. Vermelhas vêm primeiro; sem Vermelha, cada especialidade segue seu ciclo configurável de Amarelas/Azuis (inicialmente A-A-B). Dentro da cor, condição prioritária precede ausência de condição, sem preferência entre gestante, idoso e criança; depois valem a ordem efetiva da fila e o menor ID. Reentrada usa a posição ao fim da fila sem alterar a chegada.
- **Chamar próximo:** o login do Médico começa sem disponibilidade operacional; ele precisa escolher "Disponível" para receber novas atribuições. Se perder o acesso, pode entrar novamente sem esperar a sessão anterior expirar; a nova sessão também começa indisponível. Ao sair, encerra todas as suas sessões ativas. Há no máximo uma ficha CHAMADO pendente por médico; reserva e evento de chamada são atômicos e idempotentes, e fila vazia gera aviso sem alterar estado (RF28, RF36, RF38, RNF04; decisão do PO em 10/11/2026, revisada em 11/11/2026).
- **Chamadas:** sempre feitas por uma pessoa, sem repetição nem encerramento automáticos; até 3 tentativas em cada oportunidade; após a primeira oportunidade sem comparecimento, uma reentrada ao fim da mesma fila. Na Recepção/Triagem, 30 segundos depois da 1ª chamada e 10 segundos depois das seguintes até liberar "Chamar novamente" e "Não compareceu"; no Médico, 30 segundos entre chamadas.
- **Dispensa por prazo (decisão do PO, 10/11/2026):** ficha em triagem, aguardando ou chamada e ticket do Totem aguardando ou chamado parados há mais de 24 horas (configurável, `HORAS_EXPIRACAO`) aparecem para o Administrador, que os dispensa de uma vez como desistência, com registro no histórico em seu nome. É limpeza de registro abandonado, não uma chamada automática; o paciente pode abrir nova ficha.
- **Médico:** PAUSA e AUSENTE impedem novas atribuições sem remover itens já atribuídos. Retomar volta a DISPONIVEL se houver plantão vigente. Encerrar plantão é ação explícita e exige fila atribuída zerada.
- **Painel público:** pode exibir senha e sala; nunca exibe CPF nem nome completo.
- **Privacidade nas telas internas (decisão do PO, 26/10/2026):** o CPF aparece mascarado (`***.456.789-**`) onde não precisa ser lido inteiro; os campos de digitação mostram o CPF completo. A sessão é encerrada após 1 hora sem uso (configurável, `INATIVIDADE_SEGUNDOS`), além da expiração de 12 h.
- Toda alteração relevante (sintomas, classificação, disponibilidade, chamadas) registra usuário, data/hora, valor anterior e novo valor.

### Matriz global de permissões

As permissões são validadas no backend Xano. O Reflex apenas apresenta ou oculta ações e não é controle de acesso.

| Funcionalidade | Recepção/Triagem | Médico | Administrador | Público |
|---|:---:|:---:|:---:|:---:|
| Login | Sim | Sim | Sim | Não |
| Pesquisar/cadastrar paciente por CPF | Sim | Não | Consulta quando necessário | Não |
| Abrir/editar ficha de triagem | Sim | Não | Consulta | Não |
| Registrar sintomas e sinais vitais | Sim | Não | Não | Não |
| Confirmar/ajustar classificação | Sim | Não | Não | Não |
| Chamar fila de pré-triagem | Sim | Não | Acompanhamento | Não |
| Ver dados pessoais do paciente | Sim | Apenas da ficha sob atendimento | Conforme acompanhamento autorizado | Não |
| Ver fila atribuída | Não | Sim | Sim | Não |
| Chamar próximo paciente médico | Não | Sim | Não | Não |
| Pausar/retomar recebimento de atribuições | Não | Sim | Acompanhamento | Não |
| Encerrar próprio plantão com fila zerada | Não | Sim | Acompanhamento | Não |
| Confirmar comparecimento/registrar desistência | Não | Sim | Não | Não |
| Gerenciar usuários e perfis | Não | Não | Sim | Não |
| Cadastrar Médico e Recepção/Triagem | Não | Não | Sim | Não |
| Gerenciar especialidades, sintomas, salas e parâmetros | Não | Não | Sim | Não |
| Dispensar fichas e tickets parados há mais de 24 h | Não | Não | Sim | Não |
| Definir disponibilidade dos médicos | Não | Não | Sim | Não |
| Acompanhar fila geral, equipe e auditoria | Não | Não | Sim | Não |
| Visualizar painel público | Sim | Sim | Sim | Sim |
| Ver nome/CPF no painel público | Não | Não | Não | Não |

"Consulta" e "acompanhamento" para o Administrador são somente leitura e não concedem operações de triagem ou chamada.

## 8. Arquitetura tecnológica

| Camada | Tecnologia |
|---|---|
| Frontend | **Reflex** (Python) |
| Backend + banco de dados | **Xano** (XanoScript; tabelas e migrations gerenciadas pelo Xano) |

O frontend consome a API REST exposta pelo Xano. Regras de negócio, persistência e autorização ficam no backend. A decisão de usar banco de dados (Xano) foi tomada em 22/09/2026 e resolve a RNF09.

## 9. Princípios de desenvolvimento

- Desenvolvimento incremental por **fatias verticais**: cada entrega junta backend e frontend e é testada antes de seguir.
- Mudanças especificadas com OpenSpec antes da implementação.
- Faixas e limiares clínicos e os demais parâmetros previstos pelo domínio são configuráveis, sem substituir as regras operacionais aprovadas nesta base.

## 10. Segurança e integridade

- A autorização por perfil é aplicada no backend (Xano); o frontend não é mecanismo de segurança.
- Dados pessoais (CPF, nome) aparecem apenas para perfis autorizados.
- As ações relevantes ficam registradas em trilha de auditoria.
- Os registros da fila são preservados após recarregar a página ou reiniciar o cliente (RNF08).

## 11. Estratégia de desenvolvimento

- **Equipe:** Leonardo dos Santos Ferreira (PO, documentação, regras de negócio, protótipo e banco no Xano); Leonardo Machado e Luisa (backend); Nicolas Rissato e Gustavo Garcia (frontend).
- **Organização:** Trello (board "Projeto PS — Fila de Atendimento por Urgência"), 5 sprints com entregas semanais às segundas (05/10 a 02/11); cada sprint entrega e testa fatias verticais. O proposal de cada change indica a sprint e as fatias do Trello.
- **Sequência planejada de changes (OpenSpec):**
  1. `add-autenticacao-perfis`: login, perfis e gestão de usuários.
  2. `add-cadastros-administrador`: especialidades, sintomas, médicos, disponibilidade, parâmetros e auditoria.
  3. Futura change `add-totem` (nome provisório): geração e envio de tickets à fila de Recepção/Triagem.
  4. `add-pacientes-pre-triagem`: fila de Recepção/Triagem e cadastro de pacientes.
  5. `add-triagem-classificacao`: ficha, sintomas, sinais vitais, fator de risco e prioridade.
  6. `add-direcionamento-senha`: direcionamento por especialidade, senha e comprovante.
  7. `add-fila-chamada-medico`: fila priorizada, chamada, tentativas, reentrada e desistência.
  8. `add-painel-publico`: painel de chamadas e previsão das próximas 5.
  9. `add-acompanhamento-administrador`: fila geral, equipe logada/status e auditoria.

## 12. Fonte de verdade e documentação

- **Requisitos formais:** "Documento de Requisitos e Regras de Negócio (v1.0 — formal)" no Confluence (página 56459266), com referência-base RF01–RF50, RNF01–RN10, RN01–RN35, UC01–UC12 e CA01–CA15. Não inventar o texto de requisitos ausentes nem renumerá-los.
- **Contexto consolidado do PO:** decisões aprovadas nesta sanitização e registradas em `docs/project-overview.md` e `docs/domain-model.md`. O documento formal/Confluence deve permanecer sincronizado; divergências ainda não replicadas devem ser apontadas sem reintroduzir decisões antigas já substituídas pelo PO.
- **Protótipo:** Figma, "PS — Fila de Atendimento — Protótipo de Fluxos".
- **Modelo de domínio:** [domain-model.md](domain-model.md).
- **Comportamento implementado:** `openspec/specs/`.

### Revisão posterior das changes

As decisões consolidadas nesta base podem divergir de changes funcionais ainda abertas. A change divergente deve ser revisada antes de sua implementação; esta sanitização registra os impactos sem editar essas changes. A sincronização do documento formal/Confluence com as decisões do PO também deve ser confirmada.

# Visão Geral do Projeto — Sistema de Fila Prioritária para Pronto-Socorro

## 1. Visão geral

Sistema web que controla a entrada e a chamada de pacientes nas filas de um pronto-socorro (PS). A ordem de atendimento é definida pelos sintomas informados, por um fator de risco calculado a partir dos sinais vitais, por condições prioritárias (idoso, criança, gestante), pela especialidade mais adequada, pela disponibilidade dos médicos no dia e pela ordem de chegada.

A responsabilidade do sistema termina quando o paciente comparece à chamada do médico (ATENDIDO) ou é marcado como desistente (DESISTÊNCIA). Não há prontuário, diagnóstico nem controle da consulta.

> Projeto acadêmico: as regras de sintomas, prioridade, fator de risco e direcionamento são modelagem de projeto de faculdade e não têm valor de protocolo clínico real.

## 2. Problema

Quando a fila é organizada manualmente, fica difícil identificar o próximo paciente, respeitar prioridades, lidar com especialidades sem médico disponível e informar aos pacientes uma previsão das próximas chamadas. Pacientes graves podem esperar o mesmo tempo que pacientes com quadros leves, e a recepção não tem apoio para decidir quem deve ser atendido primeiro nem para onde encaminhar.

## 3. Objetivos

- Priorizar o atendimento pela gravidade clínica (sintomas + sinais vitais), e não apenas pela ordem de chegada.
- Direcionar cada paciente automaticamente para a especialidade adequada que tenha médico disponível.
- Selecionar automaticamente o próximo paciente, sem que o médico escolha manualmente quem chamar.
- Dar à equipe uma visão clara das filas e ao público um painel de chamadas que preserve a privacidade.
- Registrar toda alteração relevante para fins de auditoria.

## 4. Usuários

| Perfil | Papel |
|---|---|
| **Recepção/Triagem** | Perfil único (não são duas estações): chama a próxima senha da fila pré-triagem, pesquisa ou cadastra o paciente por CPF, abre a ficha, registra sintomas e sinais vitais, confere e ajusta a prioridade (com justificativa) e gera e imprime a senha. |
| **Médico** | Vê a própria fila, chama o próximo paciente (escolhido pelo sistema), repete a chamada (até 3 tentativas), confirma o comparecimento, registra a desistência e imprime a ficha de atendimento. Especialidades e disponibilidade são definidas pelo administrador. |
| **Administrador** | Gerencia usuários, médicos, especialidades, sintomas, relações e parâmetros de regra; registra a disponibilidade diária dos médicos; acompanha a fila geral, a equipe logada e seus status e a auditoria. |
| **Paciente (público)** | Não acessa o sistema. Recebe o ticket no totem e a senha impressa, e acompanha as chamadas no painel público. |

## 5. Escopo

### Fluxo macro

```
Totem (emissão de ticket) → Fila pré-triagem → Recepção/Triagem → Fila priorizada (por especialidade) → Médico
```

1. O paciente retira um ticket no **totem**. O totem é externo/abstraído e **não é desenvolvido pela equipe**: o sistema expõe apenas o ponto de emissão de ticket, que nesta fase é acionado por uma tela simples que simula o totem.
2. A **fila pré-triagem** usa números sequenciais simples, sem cor nem prioridade, porque a prioridade só existe depois da triagem.
3. A **Recepção/Triagem** chama o próximo ticket, identifica o paciente pelo CPF, abre a ficha, registra sintomas e sinais vitais e confirma a classificação.
4. O sistema calcula a prioridade (sintoma + fator de risco), define a especialidade e gera a senha no formato `COR-ESPECIALIDADE-NÚMERO` (ex.: `V-CLI-003`).
5. O **médico** aciona "Chamar próximo"; o sistema escolhe a ficha pelas regras de ordenação e publica a chamada no painel.

### Fora do escopo

- Prontuário eletrônico, diagnóstico, prescrição, exames e resultados laboratoriais.
- Encaminhamento clínico pelo médico (substituído pela impressão da ficha de atendimento).
- Controle da duração da consulta e botão de finalizar consulta.
- Agendamento de consultas futuras; cobrança, faturamento e convênios.
- Desenvolvimento do totem físico.
- Alteração da própria disponibilidade ou cadastro de sintomas/especialidades pelo médico.
- Promoção automática de prioridade por tempo de espera.

## 6. Principais funcionalidades

- Autenticação e controle de acesso por perfil.
- Emissão de ticket e fila pré-triagem.
- Pesquisa, cadastro e atualização de pacientes por CPF.
- Ficha de atendimento com sintomas, observações e sinais vitais (PA, FC, FR, temperatura, glicemia capilar, SpO2).
- Classificação de prioridade em três cores (Vermelha, Amarela, Azul), combinando sintoma e fator de risco, com ajuste manual justificado.
- Direcionamento automático para uma especialidade, com fallback para especialidades alternativas.
- Geração, impressão e reimpressão de senha.
- Fila priorizada por especialidade, com seleção automática do próximo paciente.
- Chamada pelo médico, com até 3 tentativas antes da DESISTÊNCIA.
- Painel público com a senha chamada e a previsão das próximas 5.
- Cadastros do administrador e disponibilidade diária dos médicos.
- Tela de acompanhamento do administrador: fila geral, pessoas logadas e seus status, auditoria.

## 7. Regras e restrições importantes

- **Cores:** Vermelha (máxima), Amarela (intermediária), Azul (menor). Com múltiplos sintomas, prevalece o de maior prioridade.
- **Fator de risco:** escore de 0 a 18, calculado a partir dos sinais vitais (modelo NEWS2/MEWS + glicemia, validado pelo PO em 27/09/2026). Se qualquer parâmetro isolado pontuar 3, o risco é alto. O fator de risco só pode **agravar** a cor, nunca suavizá-la. Faixas e limiares são **parametrizáveis**.
- **Condição prioritária** (idoso/criança/gestante): reordena dentro da mesma cor, sem mudar a cor. Entre prioritários da mesma cor, vale a ordem de chegada.
- **Ordenação:** vermelhos sempre primeiro; sem vermelhos, ciclo 2 amarelas : 1 azul; se a cor prevista estiver vazia, chama-se a outra. Tempo de espera não promove prioridade.
- **Mesmo algoritmo** para "Chamar próximo" e para a previsão do painel; a previsão não reserva posição.
- **Concorrência:** dois médicos nunca podem chamar a mesma ficha.
- A alteração manual de prioridade exige justificativa e gera histórico.
- O painel público **nunca** exibe CPF nem nome completo.
- Toda alteração relevante (sintomas, prioridade, disponibilidade, chamadas) registra usuário, data/hora, valor anterior e novo valor.

## 8. Arquitetura tecnológica

| Camada | Tecnologia |
|---|---|
| Frontend | **Reflex** (Python) |
| Backend + banco de dados | **Xano** (XanoScript; tabelas e migrations gerenciadas pelo Xano) |

O frontend consome a API REST exposta pelo Xano. Regras de negócio, persistência e autorização ficam no backend. A decisão de usar banco de dados (Xano) foi tomada em 22/09/2026 e resolve a RNF09.

## 9. Princípios de desenvolvimento

- Desenvolvimento incremental por **fatias verticais**: cada entrega junta backend e frontend e é testada antes de seguir.
- Mudanças especificadas com OpenSpec antes da implementação.
- Parâmetros clínicos e operacionais (faixas de risco, limiares, ciclo de chamada, tentativas, limites de idade, tamanho da previsão) configuráveis, e não fixos no código.

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
  3. `add-pacientes-pre-triagem`: ticket, fila pré-triagem e cadastro de pacientes.
  4. `add-triagem-classificacao`: ficha, sintomas, sinais vitais, fator de risco e prioridade.
  5. `add-direcionamento-senha`: direcionamento por especialidade, senha e comprovante.
  6. `add-fila-chamada-medico`: fila priorizada, chamar próximo, tentativas e desistência.
  7. `add-painel-publico`: painel de chamadas e previsão das próximas 5.
  8. `add-acompanhamento-administrador`: fila geral, equipe logada/status e auditoria.

## 12. Fonte de verdade e documentação

- **Requisitos formais:** "Documento de Requisitos e Regras de Negócio (v1.0 — formal)" no Confluence (página 56459266): RF01–RF38, RNF01–RNF10, RN01–RN35, UC01–UC12 e CA01–CA15.
- **Contexto consolidado do PO:** versão 1.0 de 27/09/2026 (fluxo com totem e pré-triagem, fator de risco, tela de acompanhamento). Esses refinamentos ainda precisam ser replicados no Confluence.
- **Protótipo:** Figma, "PS — Fila de Atendimento — Protótipo de Fluxos".
- **Modelo de domínio:** [domain-model.md](domain-model.md).
- **Comportamento implementado:** `openspec/specs/`.

### Divergências conhecidas entre o documento formal e o contexto atual

Registradas aqui para decisão do PO; as changes seguem o contexto mais recente e citam a divergência quando ela as afeta.

| Tema | Documento formal v1.0 | Contexto atual |
|---|---|---|
| Entrada do paciente | Paciente informa o CPF direto na recepção | Totem → fila pré-triagem → Recepção/Triagem |
| Prioridade | Calculada só pelos sintomas | Sintoma + fator de risco dos sinais vitais |
| Médico × especialidade | Médico tem uma especialidade (`especialidade_id`) | Médico pode ter várias especialidades |
| Ações do médico | Não registra nada além da chamada | Também imprime a ficha de atendimento |
| Tela do administrador | "Visão geral e histórico" | Fila geral, pessoas logadas com status e auditoria |
| Persistência | Sem banco nesta fase (o briefing do professor sugeria dados em memória) | Xano como backend e banco (22/09/2026). O professor deixou o uso de banco em aberto e a equipe definiu com ele o uso do Xano |

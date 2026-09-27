# Sistema de Fila Prioritária para Pronto-Socorro

Sistema web que organiza a entrada e a chamada de pacientes em um pronto-socorro, priorizando pela **gravidade clínica** (sintomas e sinais vitais), e não apenas pela ordem de chegada.

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Reflex](https://img.shields.io/badge/frontend-Reflex-5646ED)
![Xano](https://img.shields.io/badge/backend-Xano-0A0A0A)
![OpenSpec](https://img.shields.io/badge/metodologia-OpenSpec-2EA44F)

---

## Sobre o projeto

Em muitos prontos-socorros a fila ainda é organizada manualmente, por ordem de chegada. Assim, um paciente com dor no peito pode esperar o mesmo tempo que alguém com um resfriado. Este sistema apoia a equipe de triagem com regras objetivas e auditáveis:

- **classifica** cada paciente em três cores (Vermelha, Amarela e Azul), combinando os sintomas com um **fator de risco** calculado a partir dos sinais vitais;
- **direciona** o paciente para a especialidade adequada que tenha médico disponível;
- **escolhe automaticamente** o próximo paciente a ser chamado, sem que o médico escolha manualmente;
- **informa** o público por um painel de chamadas que não expõe dados pessoais.

> Projeto acadêmico desenvolvido na Faculdade Impacta. As regras clínicas são uma modelagem de estudo e não substituem protocolos reais de triagem.

## Principais funcionalidades

| Área | Funcionalidades |
|---|---|
| **Recepção/Triagem** | Fila de pré-triagem com senha numérica · identificação por CPF · ficha com sintomas e sinais vitais · classificação automática com ajuste manual justificado · senha e comprovante impresso |
| **Médico** | Filas por especialidade · "Chamar próximo" com seleção automática e sem duplicidade · até 3 tentativas de chamada · confirmação de comparecimento ou desistência · impressão da ficha |
| **Painel público** | Senha chamada em destaque · previsão das próximas 5 senhas · sem nome nem CPF |
| **Administrador** | Usuários e perfis · médicos, especialidades e sintomas · disponibilidade por período · parâmetros e faixas de risco · acompanhamento da fila, da equipe e da auditoria |

## Como funciona

```mermaid
flowchart LR
    A[Totem<br/>ticket numérico] --> B[Fila<br/>pré-triagem]
    B --> C[Recepção/Triagem<br/>CPF · sintomas · sinais vitais]
    C --> D{Classificação<br/>e direcionamento}
    D --> E[Fila priorizada<br/>por especialidade]
    E --> F[Médico<br/>chamar próximo]
    E -.-> G[Painel público]
    F -.-> G
```

### Regras de priorização

1. **Cor pelo sintoma:** cada sintoma tem uma prioridade padrão. Quando há vários sintomas, vale o mais grave.
2. **Fator de risco:** os sinais vitais (PA, FC, FR, temperatura, SpO2 e glicemia) somam um escore de 0 a 18, com base no NEWS2/MEWS. Um único parâmetro crítico já classifica o risco como alto. O risco só pode **agravar** a cor, nunca suavizá-la.
3. **Condição prioritária:** idosos, crianças e gestantes passam na frente **dentro da mesma cor**, sem mudar de cor.
4. **Ordem de chamada:** vermelhos sempre primeiro. Sem vermelhos, vale o ciclo **2 amarelas : 1 azul**. Depois vêm os prioritários e, por fim, a ordem de chegada.
5. **Mesma regra para chamada e painel:** a previsão do painel usa o mesmo algoritmo da chamada real.

Faixas, limiares, ciclo, tentativas e limites de idade são **parametrizáveis** pelo administrador, sem alterar código.

## Arquitetura

```mermaid
flowchart LR
    U[Equipe e público] --> R[Reflex<br/>interface web em Python]
    R -- API REST --> X[Xano<br/>regras de negócio, autorização e banco]
```

| Camada | Tecnologia | Responsabilidade |
|---|---|---|
| Frontend | [Reflex](https://reflex.dev) (Python) | Telas e interação. Nenhuma regra de negócio |
| Backend e banco | [Xano](https://www.xano.com) (XanoScript) | Regras, autorização por perfil, persistência e auditoria |
| Especificação | [OpenSpec](https://github.com/Fission-AI/OpenSpec) | Requisitos e planejamento de cada funcionalidade |
| Testes | pytest + httpx | Testes de API com valores-limite das regras |

**Decisões de destaque**
- Autorização aplicada no backend a cada requisição. Desativar um usuário invalida o acesso na hora.
- Seleção do próximo paciente **atômica**, para que dois médicos nunca chamem a mesma ficha.
- Trilha de **auditoria** imutável para prioridade, sintomas, disponibilidade e chamadas.
- **Privacidade:** o painel e o comprovante impresso não exibem dados pessoais.

## Design e documentação

| Artefato | Link |
|---|---|
| Protótipo de telas | [Figma — Protótipo de Fluxos](https://www.figma.com/design/38ro8aKQfiGkUivIfCaOR1) |
| Fluxogramas, regras e modelo de dados | [FigJam — Fluxo do Sistema](https://www.figma.com/board/qwAbdFLbo9lRuOym4vDSBI) |
| Visão geral do projeto | [docs/project-overview.md](docs/project-overview.md) |
| Modelo de domínio | [docs/domain-model.md](docs/domain-model.md) |
| Especificações (requisitos e cenários) | [openspec/changes/](openspec/changes/) |

## Metodologia

O projeto segue o desenvolvimento **orientado a especificação** com [OpenSpec](https://github.com/Fission-AI/OpenSpec), com apoio de agentes de IA:

1. **Contexto:** visão geral, modelo de domínio e regras para os agentes de IA ([AGENTS.md](AGENTS.md)).
2. **Especificação:** cada funcionalidade vira uma *change*, com proposta, requisitos verificáveis (cenários QUANDO/ENTÃO), design técnico e tarefas.
3. **Fatias verticais:** backend e frontend de uma mesma funcionalidade são entregues e testados juntos a cada sprint.
4. **Rastreabilidade:** os requisitos citam os RF/RN/CA do documento formal de requisitos.

## Roadmap

- [x] Levantamento de requisitos, protótipo e modelo de dados
- [x] Especificação das funcionalidades (8 changes)
- [x] Banco de dados publicado no Xano (19 tabelas)
- [ ] Autenticação, perfis e gestão de usuários
- [ ] Cadastros do administrador e auditoria
- [ ] Pré-triagem e cadastro de pacientes
- [ ] Triagem e classificação de risco
- [ ] Direcionamento, senha e comprovante
- [ ] Fila priorizada e chamada pelo médico
- [ ] Painel público
- [ ] Acompanhamento do administrador

## Estrutura do repositório

```
├── docs/                  visão geral e modelo de domínio
├── openspec/
│   ├── config.yaml        contexto e regras da metodologia
│   └── changes/           especificação de cada funcionalidade
├── backend/xano/table/    schema do banco em XanoScript
├── AGENTS.md              regras para agentes de IA
└── CONTRIBUTING.md        guia de ambiente e fluxo de trabalho da equipe
```

## Equipe

| Integrante | Papel |
|---|---|
| Leonardo dos Santos Ferreira | Product Owner · requisitos e regras de negócio · protótipo · banco de dados |
| Leonardo Machado | Backend |
| Luisa | Backend |
| Nicolas | Frontend |
| Gustavo Garcia | Frontend |

---

Quer rodar ou contribuir? Veja o [guia de contribuição](CONTRIBUTING.md).

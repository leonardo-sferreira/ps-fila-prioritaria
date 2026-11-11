# Proposta: Fila priorizada e chamada pelo médico

| Campo | Valor |
|---|---|
| Change | `add-fila-chamada-medico` |
| Sprint e entrega | Sprint 4, segunda 26/10 |
| Fatias no Trello | Fatia 7 — Médico chama e pode repetir a chamada · Fatia 8 — Comparecimento, desistência e impressão |
| Dupla | Fatia 7: Leonardo Machado · Nicolas. Fatia 8: Luisa · Nicolas |
| Depende de | `add-direcionamento-senha`, `add-cadastros-administrador` e `add-acompanhamento-administrador` (sessão/status e plantão) |
| Situação | Implementado; aceite manual posterior pelo PO |
| Rastreabilidade formal | Rev. 2.1, §7.1–7.2, §12 (RF22–RF28, RF36, RF38), §13 (RNF04), §14.1, §14.3 (itens 2 e 6), §19 (D02–D05, D16) |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/`. Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

O médico não escolhe quem atender (RN24): o sistema precisa selecionar a ficha no momento de "Chamar próximo", respeitar a ordem interna de cada especialidade e decidir entre filas próprias, descobertas e outras filas cobertas. A Rev. 2.1, §7.2 e §14.1 define essa seleção; a change antiga a deixava em aberto. A reserva precisa impedir que duas chamadas recebam a mesma ficha (RF38, RNF04).

## What Changes

- **Função única de ordenação** da fila de cada especialidade, usada pela chamada e pela previsão (RF22–RF27, RN20–RN23, RN25, seção 10).
- **Previsão das próximas N senhas** por especialidade (N configurável, inicial 5), sem reservar posição (RF34, RF35, RN26). Vai ser exibida no painel na change seguinte.
- **Tela do Médico:** filas visíveis e ficha sob responsabilidade do médico, com ação única "Chamar próximo", sem seleção manual da ficha.
- **Chamar próximo:** somente Médico elegível com sessão ativa e disponibilidade escolhida explicitamente, plantão vigente e nenhuma ficha CHAMADO pendente; uma candidata por especialidade, ordenada internamente por Vermelha, ciclo configurável inicial 2 Amarelas:1 Azul, condição prioritária e chegada.
- **Seleção entre filas:** o médico prefere suas especialidades próprias N:N. Vermelhas próprias vêm antes das demais próprias (chegada/ID entre elas); para Amarelas/Azuis há rodízio determinístico por médico entre as próprias, preservando o ciclo de cada fila. Fila descoberta supera a próxima própria só quando sua candidata tem cor mais grave; no empate, prevalece a própria. Sem ficha própria, apoiar descoberta e, na falta dela, outra coberta.
- **Reserva:** a seleção, a mudança para CHAMADO, o avanço do ciclo e o evento de chamada são atômicos e idempotentes; especialidade e senha da ficha não mudam.
- **Repetir chamada:** até 3 chamadas por oportunidade, com intervalo mínimo de 30 segundos. Após a primeira oportunidade sem resposta, a ficha volta uma única vez ao fim da mesma fila.
- **Confirmar comparecimento:** a ficha vira ATENDIDO e sai da fila (RF30, RN28, UC09).
- **Registrar desistência** explicitamente: a ficha vira DESISTÊNCIA e sai definitivamente da fila. Sem resposta após a primeira oportunidade, retorna uma vez ao fim da fila; ausência após a segunda oportunidade encerra conforme o estado final da ficha.
- **Pausar/encerrar plantão:** Médico em pausa não recebe novas atribuições; encerrar plantão exige fila atribuída zerada (`add-acompanhamento-administrador`).
- **Fila vazia:** aviso de ausência de pacientes aguardando entre todas as filas alcançáveis, sem criar chamada nem avançar ciclo (RF36, RN33, CA15).
- **Imprimir ficha de atendimento** pelo médico, com os dados da triagem (contexto do PO, 22/09/2026).
- Registro de cada chamada no histórico (RF37, RNF03).

### Fora do escopo

- Exibição no painel público: `add-painel-publico`.
- Consulta administrativa de status operacional: `add-acompanhamento-administrador`; esta change aplica elegibilidade operacional ao recebimento de atribuições.
- Diagnóstico, encaminhamento, finalização de consulta e duração do atendimento (RN31, RN32).
- Transferir uma ficha CHAMADO para outro médico.

## Capacidades

### Novas capacidades
- `fila-priorizada`: ordenação e ciclo por especialidade, previsão das próximas senhas e seleção determinística entre filas.
- `chamada-paciente`: chamar próximo, reserva atômica, repetir, comparecimento, desistência, concorrência e impressão da ficha pelo médico.

### Capacidades modificadas
As transições de chamada da ficha estão especificadas em `chamada-paciente`; a base `ficha-atendimento` já descreve o estado AGUARDANDO. Não há delta MODIFIED adicional nesta revisão.

## Impacto

- **Xano:** reutilizar `medico_especialidade`; tabelas `chamada` e `ciclo_fila` se ainda não existirem; campos de chamada em `ficha_atendimento` conforme o esquema existente; funções de seleção interna/entre filas e previsão; endpoints médicos, de impressão e de previsão citados no design.
- **Reflex:** página `/medico` com filas, ficha chamada e ações; página de impressão da ficha.
- **Testes:** `tests/api/test_ordenacao.py` (tabela de casos do ciclo), `tests/api/test_chamada.py` (inclusive concorrência).
- **Depende de:** `add-direcionamento-senha` (fichas AGUARDANDO com senha), `add-cadastros-administrador` (vínculo N:N, disponibilidade e parâmetros) e `add-acompanhamento-administrador` (sessão/status e plantão); suas mudanças de planejamento foram alinhadas à Rev. 2.1, mas ainda precisam ser implementadas.
- **Divergência formal:** a Rev. 2.1 traz a política operacional consolidada; o Confluence deve ser sincronizado pelo PO se ainda conservar o texto antigo de RF14 ou RF18/RF19. Não reintroduzir a especialidade única nem fallback de destino por falta de médico.

## Perguntas em aberto

- [x] A especialidade de referência do Médico não limita as filas que pode atender. · BASELINE
- [x] Encerrar plantão só é permitido com fila atribuída zerada. · BASELINE
- [x] Seleção entre especialidades próprias, descobertas e outras cobertas definida na Rev. 2.1, §7.2, §14.1 e D02–D05.
- [x] Decisão revisada pelo PO em 11/11/2026: novo login de Médico é permitido após perda de acesso e começa indisponível; a ativação é explícita na change `add-acompanhamento-administrador`.
- [x] "Repetir chamada" fica na Fatia 7 desta change, junto da seleção, das tentativas e do histórico (decisão do PO em 10/11/2026).

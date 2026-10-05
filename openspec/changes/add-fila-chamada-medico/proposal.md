# Proposta: Fila priorizada e chamada pelo médico

| Campo | Valor |
|---|---|
| Change | `add-fila-chamada-medico` |
| Sprint e entrega | Sprint 4, segunda 26/10 |
| Fatias no Trello | Fatia 7 — Médico chama o próximo · Fatia 8 — Atendimento |
| Dupla | Fatia 7: Leonardo Machado · Nicolas. Fatia 8: Luisa · Nicolas |
| Depende de | `add-direcionamento-senha` (Fatia 6) e `add-cadastros-administrador` (disponibilidade e parâmetros) |
| Situação | Em revisão |
| Rastreabilidade formal | RF14, RF22, RF29–RF38 e RF46 quando aplicáveis; a baseline local define 30 s, oportunidades de chamada e elegibilidade sem filtro por especialidade cadastral |

> Esquema físico: as tabelas já estão publicadas em `backend/xano/table/`. Onde as tasks dizem "criar a tabela", conferir o arquivo `.xs`; mudança de esquema passa pelo PO (ver CONTRIBUTING).

## Why

O médico não escolhe quem atender (RN24): o sistema precisa escolher sozinho, e de forma justa, o próximo paciente, aplicando vermelhos primeiro, o ciclo 2 amarelas : 1 azul, a condição prioritária e a ordem de chegada. O algoritmo precisa ser o mesmo que alimenta a previsão do painel (RN25). Esta change fecha o ciclo operacional do PS: triagem → fila → chamada → comparecimento ou desistência.

## What Changes

- **Função única de ordenação** da fila de cada especialidade, usada pela chamada e pela previsão (RF22–RF27, RN20–RN23, RN25, seção 10).
- **Previsão das próximas N senhas** por especialidade (N configurável, inicial 5), sem reservar posição (RF34, RF35, RN26). Vai ser exibida no painel na change seguinte.
- **Tela do Médico:** atendimentos atribuídos pelo sistema, que podem vir de qualquer fila de especialidade para a qual seja elegível, a ficha chamada no momento e as ações.
- **Chamar próximo:** somente Médico elegível; o sistema seleciona a ficha, faz reserva atômica e registra chamada, sem filtrar pela especialidade de referência.
- **Repetir chamada:** até 3 chamadas por oportunidade, com intervalo mínimo de 30 segundos. Após a primeira oportunidade sem resposta, a ficha volta uma única vez ao fim da mesma fila.
- **Confirmar comparecimento:** a ficha vira ATENDIDO e sai da fila (RF30, RN28, UC09).
- **Registrar desistência** explicitamente: a ficha vira DESISTÊNCIA e sai definitivamente da fila. Sem resposta após a primeira oportunidade, retorna uma vez ao fim da fila; ausência após a segunda oportunidade encerra conforme o estado final da ficha.
- **Pausar/encerrar plantão:** Médico em pausa não recebe novas atribuições; encerrar plantão exige fila atribuída zerada (`add-acompanhamento-administrador`).
- **Fila vazia:** mensagem "Não há pacientes aguardando nesta fila" (RF36, RN33, CA15).
- **Imprimir ficha de atendimento** pelo médico, com os dados da triagem (contexto do PO, 22/09/2026).
- Registro de cada chamada no histórico (RF37, RNF03).

### Fora do escopo

- Exibição no painel público: `add-painel-publico`.
- Consulta administrativa de status operacional: `add-acompanhamento-administrador`; esta change aplica elegibilidade operacional ao recebimento de atribuições.
- Diagnóstico, encaminhamento, finalização de consulta e duração do atendimento (RN31, RN32).
- Transferir uma ficha CHAMADO para outro médico.

## Capacidades

### Novas capacidades
- `fila-priorizada`: regras de ordenação, ciclo amarelo/azul por especialidade e previsão das próximas senhas.
- `chamada-paciente`: chamar próximo, repetir, comparecimento, desistência, concorrência e impressão da ficha pelo médico.

### Capacidades modificadas
Acrescenta campos e transições de estado (CHAMADO, ATENDIDO, DESISTÊNCIA) à `ficha-atendimento` (`add-triagem-classificacao`). Declarar como delta `MODIFIED`.

Aviso: o `openspec/specs/` ainda está vazio. Os deltas `MODIFIED` só funcionam depois que a change anterior for arquivada (`/opsx:archive`); arquive as changes na ordem.

## Impacto

- **Xano:** tabelas `chamada` e `ciclo_fila`; campos `medico_chamada_id`, `tentativas_chamada`, `chamada_em` e `finalizada_em` em `ficha_atendimento`; funções `ordenar_fila`, `proxima_ficha` e `prever_fila`; endpoints `GET medico/filas`, `POST medico/chamar-proximo`, `POST fichas/{id}/repetir-chamada`, `.../comparecimento`, `.../desistencia`, `GET fichas/{id}/impressao` e `GET filas/{especialidade}/previsao`.
- **Reflex:** página `/medico` com filas, ficha chamada e ações; página de impressão da ficha.
- **Testes:** `tests/api/test_ordenacao.py` (tabela de casos do ciclo), `tests/api/test_chamada.py` (inclusive concorrência).
- **Depende de:** `add-direcionamento-senha` (fichas AGUARDANDO com senha) e `add-cadastros-administrador` (disponibilidade, parâmetros).
- Referências RF/RN/CA são rastreabilidade, não autorização para inventar texto ausente. A seleção global entre filas de especialidades distintas permanece por definir antes da implementação.

## Perguntas em aberto

- [x] A especialidade de referência do Médico não limita as filas que pode atender. · BASELINE
- [x] Encerrar plantão só é permitido com fila atribuída zerada. · BASELINE
- [ ] Definir como o sistema escolhe entre filas de especialidades diferentes quando mais de uma está elegível. · PENDENTE PO
- [ ] A Sprint 4 é a mais pesada: o card da Fatia 7 prevê mover "repetir chamada" para a Fatia 8. Decidir na planning da sprint. · dupla

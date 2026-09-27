# Proposta

## Por quê

O médico não escolhe quem atender (RN24): o sistema precisa escolher sozinho, e de forma justa, o próximo paciente, aplicando vermelhos primeiro, o ciclo 2 amarelas : 1 azul, a condição prioritária e a ordem de chegada. O algoritmo precisa ser o mesmo que alimenta a previsão do painel (RN25). Esta change fecha o ciclo operacional do PS: triagem → fila → chamada → comparecimento ou desistência.

## O que muda

- **Função única de ordenação** da fila de cada especialidade, usada pela chamada e pela previsão (RF22–RF27, RN20–RN23, RN25, seção 10).
- **Previsão das próximas N senhas** por especialidade (N configurável, inicial 5), sem reservar posição (RF34, RF35, RN26). Vai ser exibida no painel na change seguinte.
- **Tela do médico:** as filas das suas especialidades, a ficha chamada no momento e as ações.
- **Chamar próximo:** somente médico disponível; o sistema escolhe a ficha, faz a reserva de forma atômica e registra a tentativa 1 (RF23, RF28, RF38, RN34, UC07, CA14).
- **Repetir chamada** até o máximo de tentativas configurado (RF29, RN27, UC08).
- **Confirmar comparecimento:** a ficha vira ATENDIDO e sai da fila (RF30, RN28, UC09).
- **Registrar desistência** depois da última tentativa: a ficha vira DESISTÊNCIA e sai da fila (RF31, RN29, UC10, CA13).
- **Fila vazia:** mensagem "Não há pacientes aguardando nesta fila" (RF36, RN33, CA15).
- **Imprimir ficha de atendimento** pelo médico, com os dados da triagem (contexto do PO, 22/09/2026).
- Registro de cada chamada no histórico (RF37, RNF03).

### Fora do escopo

- Exibição no painel público: `add-painel-publico`.
- Status operacional do médico (em atendimento, pausa): `add-acompanhamento-administrador`.
- Diagnóstico, encaminhamento, finalização de consulta e duração do atendimento (RN31, RN32).
- Transferir uma ficha CHAMADO para outro médico.

## Capacidades

### Novas capacidades
- `fila-priorizada`: regras de ordenação, ciclo amarelo/azul por especialidade e previsão das próximas senhas.
- `chamada-paciente`: chamar próximo, repetir, comparecimento, desistência, concorrência e impressão da ficha pelo médico.

### Capacidades modificadas
_Nenhuma._

## Impacto

- **Xano:** tabelas `chamada` e `ciclo_fila`; campos `medico_chamada_id`, `tentativas_chamada`, `chamada_em` e `finalizada_em` em `ficha_atendimento`; funções `ordenar_fila`, `proxima_ficha` e `prever_fila`; endpoints `GET medico/filas`, `POST medico/chamar-proximo`, `POST fichas/{id}/repetir-chamada`, `.../comparecimento`, `.../desistencia`, `GET fichas/{id}/impressao` e `GET filas/{especialidade}/previsao`.
- **Reflex:** página `/medico` com filas, ficha chamada e ações; página de impressão da ficha.
- **Testes:** `tests/api/test_ordenacao.py` (tabela de casos do ciclo), `tests/api/test_chamada.py` (inclusive concorrência).
- **Depende de:** `add-direcionamento-senha` (fichas AGUARDANDO com senha) e `add-cadastros-administrador` (disponibilidade, parâmetros).
- **Divergências com o documento formal:** (1) a seção 18 prevê CHAMADO → AGUARDANDO ("nova tentativa"); aqui a nova tentativa mantém a ficha CHAMADO com o mesmo médico, e ela só sai por comparecimento ou desistência; (2) "imprimir ficha" pelo médico vem do contexto do PO e não está no documento v1.0.

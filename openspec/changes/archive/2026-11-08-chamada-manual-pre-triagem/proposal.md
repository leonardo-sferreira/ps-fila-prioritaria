# Proposta: chamada manual na fila de pré-triagem

| Campo | Valor |
|---|---|
| Change | `chamada-manual-pre-triagem` |
| Sprint / card Trello | Sprint 3 (entrega seg 09/11/2026); card a definir |
| Depende de | `implementar-chamada-automatica-tickets` (arquivada em 02/11/2026), que criou a fila, as ações e os parâmetros de chamada |
| Situação | Proposta (decisão do PO em 08/11/2026) |
| Rastreabilidade formal | Regras de chamada da Documentação de Requisitos Rev. 2.1; confirmar o código do RF/RN no documento formal sem inventar requisito |

## Why

Hoje, depois de "Chamar próximo", a tela da Recepção chama de novo sozinha a cada 30 segundos e, esgotadas as tentativas, devolve o ticket à fila também sozinha. O PO quer que a pessoa responsável pela senha decida cada passo: chamar de novo quando achar necessário e registrar que o paciente não compareceu, sem nada acontecer automaticamente.

## What Changes

- **Fim do avanço automático:** a tela da fila deixa de enviar novas chamadas e de encerrar a oportunidade sozinha. Toda chamada e todo "não compareceu" passam a ser ações da Recepção/Triagem.
- **Botão "Chamar novamente":** repete a chamada do mesmo ticket. Fica liberado quando termina o intervalo da chamada atual e some quando a oportunidade atingir 3 chamadas (`TENTATIVAS_CHAMADA`).
- **Intervalos diferentes por chamada:** 30 segundos depois da 1ª chamada (`INTERVALO_CHAMADA_SEGUNDOS`, já existe) e 10 segundos depois da 2ª e da 3ª (novo parâmetro configurável `INTERVALO_REPETICAO_SEGUNDOS`).
- **Botão "Não compareceu":** fica liberado quando termina o intervalo da chamada atual, em qualquer das 3 chamadas. Na 1ª oportunidade devolve o ticket ao fim da fila, onde ele ganha uma nova oportunidade com até 3 chamadas; na 2ª encerra o ticket como `NAO_COMPARECEU`.
- **Contagem na tela:** o cartão do ticket chamado mostra quanto falta para liberar "Chamar novamente" e "Não compareceu", em vez de "próxima etapa".
- **Sem mudança:** confirmar presença, identificar o paciente, desistência, ordem de seleção (ciclo 2:1, Pediátrico antes de Preferencial) e reentrada única.
- **Remoção:** a ação `AVANCAR` do backend, usada apenas pelo avanço automático, deixa de existir. **BREAKING** para quem chamava `AVANCAR` (só a própria tela da fila).

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `fila-pre-triagem`: o requisito "Oportunidades de chamada" passa de automático para manual, com intervalo de 30 s após a 1ª chamada e 10 s após as seguintes; o requisito "Operação autorizada e acompanhamento" deixa de depender de uma tela aberta para avançar e passa a incluir "Chamar novamente" e "Não compareceu".

## Impact

- **Xano:** `api/triagem/tickets_acao_post.xs` (ações `REPETIR` e `AUSENCIA` com o intervalo da chamada atual; remove `AVANCAR`), `api/triagem/tickets_get.xs` (devolve também o intervalo de repetição) e `function/inicializar_parametros_fila.xs` (novo parâmetro com valor inicial 10).
- **Reflex:** `FilaTicketsState` (remove `atualizar_automaticamente` e o avanço no `monitorar`; contagem pelo intervalo da chamada atual) e o cartão do ticket chamado em `pagina_fila_tickets`.
- **Testes:** `tests/test_chamada_automatica.py` (substituído por casos manuais) e testes de estado da fila.
- **Documentos:** `docs/project-overview.md`, `docs/domain-model.md` e o resumo em `openspec/config.yaml`, que hoje descrevem tentativas automáticas a cada 30 s.

## Fora do escopo

- Fila e chamada do Médico (`add-fila-chamada-medico`): já prevê "Repetir chamada" manual com 30 s e não muda aqui.
- Painel público e qualquer exibição da chamada fora da tela da Recepção.
- Tela do Administrador para editar os parâmetros: os valores continuam configuráveis direto na tabela `parametro`.
- Concorrência entre dois operadores no mesmo ticket (limitação já aceita na change anterior).

## Perguntas em aberto

- "Não compareceu" fica liberado no fim do intervalo de **qualquer** chamada, como pedido ("só disponível após esses 30 segundos"). Se o PO preferir exigir as 3 chamadas antes do "Não compareceu", basta trocar a validação no Xano e a condição do botão.
- Na nova oportunidade (depois de voltar à fila), a 1ª chamada volta a esperar 30 s e as seguintes 10 s. Proposto assim por ser a mesma sequência da 1ª oportunidade.
- O documento formal (Confluence/Word Rev. 2.1) ainda descreve tentativas automáticas a cada 30 s; precisa ser atualizado pelo PO.

# Design da fila de pré-triagem

## Contexto

`ticket_pre_triagem` já tem tipo, número, emissão, estado, chamado_por e chamado_em, mas não controla oportunidade, tentativas nem posição de reentrada. `ficha_atendimento.ticket_id` é opcional; o POST atual o aceita sem validar o ticket nem alterar seu estado. `ciclo_fila` é por especialidade médica e não serve para esta fila. Há autenticação e telas `/recepcao/pacientes` e `/recepcao/ficha/[id]`; a emissão do Totem ainda não está implementada.

## Objetivos e limites

Selecionar no servidor, preservar identidade e conectar identificação à ficha. Sem worker, fila distribuída, lógica clínica ou reimplementação do Totem.

## Decisões

1. O ticket mantém oportunidade, tentativas, instante da última chamada e ordem efetiva de fila; uma posição global persistida controla o ciclo configurável, inicialmente prioritário, prioritário, Normal. Pediátrico precede Preferencial; dentro do tipo, usar ordem efetiva e id para desempate. A emissão inicial entra no fim do tipo e a reentrada também, sem trocar número ou identidade. Quando a classe prevista estiver vazia, chamar a outra sem avançar o ciclo; fila vazia não altera ciclo.
2. A Recepção inicia a primeira chamada e confirma presença. A tela aberta consulta o Xano periodicamente e solicita o avanço após o prazo: repetição até o limite configurado e encerramento após outro intervalo. O Xano valida relógio, estado e presença persistida antes de cada avanço. Na primeira ausência reentra em AGUARDANDO; na segunda passa a NAO_COMPARECEU. Sem tela autorizada aberta e conectada, o processamento para e é retomado ao abrir a fila; não há worker externo.
3. Usar `db.transaction` na sintaxe existente para agrupar validação de estado, alteração, ciclo e auditoria. Validar novamente o estado antes de cada alteração. Por decisão do PO, não exigir isolamento serializável nem bloqueio, e não usar sintaxe de isolamento rejeitada pelo validador. Transações comuns não comprovam exclusividade entre requisições concorrentes: duas chamadas simultâneas podem disputar o mesmo ticket ou ciclo; a equipe deve operar sequencialmente. Nenhum mecanismo adicional de concorrência é criado nesta sprint.
4. Qualquer operador Recepção/Triagem autorizado pode consultar e retomar ticket CHAMADO, confirmar presença ou identificar; `chamado_por` registra o autor da chamada, não propriedade exclusiva. Não há transferência. Cada evento registra o usuário que o executou.
5. A abertura com ticket valida paciente, ficha ativa, estado CHAMADO e presença confirmada; cria ficha, associa ticket, registra auditoria e passa o ticket a ATENDIDO atomicamente. Validar ticket e ficha ativa na transação; operações simultâneas podem ultrapassar essa validação, limitação aceita pelo PO. Sem ticket, preservar o fluxo existente. Reutilizar autenticação, pacientes, fichas e auditoria; reconciliar o contrato com `integrar-seguranca-auditoria-fichas`, sem substituir seus controles.
6. Desistência explícita altera o enum existente para `DESISTENCIA`, estado final distinto de `NAO_COMPARECEU`, a partir de AGUARDANDO ou CHAMADO. A operação autorizada remove imediatamente o ticket da fila ativa, impede chamada e reentrada e não altera fichas. Registrar auditoria na mesma transação. Não criar tabela ou fluxo adicional.
7. Reflex apresenta senha, tentativa e contagem regressiva, solicita avanços e recupera chamadas ativas após recarga; servidor decide permissões, estado e prazo. Sem workers ou infraestrutura externa.

## Dependências e riscos

- A emissão `add-totem` ainda não está pronta: usar dados de teste válidos para desenvolvimento e testes; o teste ponta a ponta real depende da emissão. A base compartilhada de parâmetros deve estar disponível para integração, sem impedir testes isolados.
- Autenticação e auditoria efetivas são obrigatórias antes de disponibilizar operações protegidas; a integração com a change de segurança de fichas é necessária na tarefa de abertura, não em toda a change.
- `project-overview.md` descreve ordem de emissão genericamente; `domain-model.md` consolida prioridade 2:1 e reentrada. Esta change segue o modelo, incluindo ordem efetiva após retorno. O Confluence é indisponível e sua divergência de prioridade já registrada no domínio permanece sem verificação; não alterar as referências protegidas nesta revisão.
- Decisão do PO: acrescentar `DESISTENCIA` ao enum existente; o modelo de domínio protegido ainda não enumera esse estado e deverá ser sincronizado oportunamente. Não confundir com `NAO_COMPARECEU`.
- Inventariar dados existentes e migrar sem perda; reversão deve preservar registros. A validação de estado e a transação não garantem exclusividade sob acessos simultâneos; operar sequencialmente nesta sprint.

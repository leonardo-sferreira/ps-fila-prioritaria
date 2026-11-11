# Design: fichas do dia e acesso à ficha atual do paciente

## Contexto

A rota `/recepcao/ficha/[id]` já abre qualquer ficha. Ela é editável em `EM_TRIAGEM` e `AGUARDANDO` e só para leitura nas demais situações. O que falta é chegar até ela.

`POST fichas` já devolve a ficha `EM_TRIAGEM` existente (com `ja_existente`), mas recusa `AGUARDANDO` e `CHAMADO` com `FICHA_NAO_FINALIZADA_EXISTENTE`. Um erro do Xano não carrega o ID da ficha, então a tela não consegue oferecer um atalho.

## Decisões

### D1. `GET fichas`: não finalizadas e finalizadas de hoje
`GET fichas`, com `auth = "usuario"` e `verificar_acesso` para `RECEPCAO_TRIAGEM`, devolve:
- as fichas em `EM_TRIAGEM`, `AGUARDANDO` e `CHAMADO`, de qualquer data, porque um paciente pode estar esperando desde antes da meia-noite;
- as fichas em `ATENDIDO`, `DESISTENCIA` e `CANCELADO` com `chegada_em` hoje, no fuso America/Sao_Paulo.

A ordem é `chegada_em` decrescente. A resposta é montada campo a campo: `id`, `status`, `chegada_em`, `senha`, `prioridade_atual`, nome da especialidade atribuída e `paciente: {id, nome}`. Não devolve CPF, sintomas nem sinais vitais, que só a ficha mostra.

- **Alternativa recusada:** paginação e filtro por período no Xano. O volume de um dia de PS acadêmico é pequeno e o PO não pediu histórico (YAGNI).

### D2. Filtro e busca no Reflex
O filtro por situação e a busca por nome ou senha rodam no estado, sobre a lista já carregada. A busca não diferencia acentos nem maiúsculas e reaproveita `_normalizar_texto` da ficha. As situações finais se agrupam em "Finalizadas".

### D3. `POST fichas` devolve a ficha atual do paciente na fila
Sem ticket, quando o paciente já tem ficha `AGUARDANDO` ou `CHAMADO`, o endpoint devolve essa ficha com `ja_existente: true` e `status`, sem alterá-la e sem auditoria, em vez de recusar. Continua não criando segunda ficha (RN03).

Com ticket, a recusa `FICHA_NAO_FINALIZADA_EXISTENTE` continua, porque associar o ticket a uma ficha que já está na fila não faz sentido.

- **Alternativa recusada:** um endpoint novo "ficha ativa do paciente". O `POST fichas` já faz essa busca e já devolve a ficha `EM_TRIAGEM`; estender o mesmo caminho evita duplicar a regra.

### D4. Tela de identificação
- Quando a resposta vem com `ja_existente` e `status` `EM_TRIAGEM`, a tela redireciona para a ficha, como hoje.
- Com `AGUARDANDO` ou `CHAMADO`, a tela não redireciona. Mostra o aviso "Este paciente já está na fila com a senha X" e o botão "Abrir ficha atual".

### D5. Atualização da lista
`rx.moment(interval=15000)` recarrega a lista enquanto a aba está aberta, como a fila de pré-triagem, além de um botão "Atualizar". A tela nunca altera fichas.

## Riscos

- Mudar a resposta de `POST fichas` para `AGUARDANDO`/`CHAMADO` muda um contrato. Mitigação: o único cliente é a tela de identificação, alterada na mesma change, e o teste de contrato `test_ficha_abertura_contract.py` é atualizado.

# Design técnico

## Contexto

A tabela `chamada` (change 6) registra toda tentativa, e `prever_fila` fornece a previsão sem dados pessoais. O ticket da pré-triagem guarda `chamado_em`, atualizado a cada rechamada (change 3); a rechamada mantém o mesmo ticket. A Sala é cadastro próprio e é informada pela relação operacional com o Médico, nunca inferida da especialidade.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Um único endpoint público que devolve só campos permitidos, com uma lista explícita de campos (nunca "retorna o registro inteiro").
- Atualização em até 5 s sem sobrecarregar o plano do Xano.

**Fora dos objetivos:**
- Push em tempo real (websocket/SSE).

## Decisões

### D1. Endpoint público `GET painel?especialidades=CLI,ORT`
Sem autenticação. Monta a resposta com campos escolhidos um a um:
```
{ atual: {senha, cor, especialidade, tentativa, chamado_em} | null,
  ultimas: [{senha, especialidade, chamado_em}] (até 4),
  previsoes: [{especialidade, sigla, senhas: [{senha, cor}]}],
  triagem: {ticket, chamado_em} | null,
  gerado_em }
```
- **Por quê:** a lista explícita de campos garante a privacidade por construção, e `test_painel.py` confere que a resposta não tem chaves proibidas.
- A previsão chama a mesma `prever_fila` da change 6 (RN25).

### D2. Polling de 5 s no Reflex com detecção de novidade

> Alterado em 20/11/2026: 5 s em vez de 3 s, porque o plano gratuito do Xano limita 10 requisições a cada 20 s para todo o sistema (cada tela aberta usa 4).
O state do painel guarda o `chamado_em` da chamada atual e do ticket; se algum mudar, dispara a animação de destaque e o som (arquivo curto em `assets/`). Em caso de erro, mantém o último estado e mostra "reconectando". O navegador pode bloquear o som até a primeira interação: a tela mostra "Toque para ativar o som" na primeira vez.
- **Alternativa:** SSE. Descartada por complexidade e pelo suporte limitado no Xano.

### D3. Sala da chamada
Para chamada médica, o endpoint público inclui a Sala operacional associada ao Médico no momento da chamada, quando houver, e a interface mostra “Sala {identificação}”. Especialidade permanece informação clínica distinta. Para chamadas de Recepção/Triagem, o painel mostra “Triagem”, sem inventar uma Sala.

### D4. Layout de TV (tela 5 do Figma)
Segue a tela "5 — Painel público — Chamando o paciente" do protótipo, no padrão visual do sistema (cabeçalho marinho com data e hora, fundo claro, cartões brancos, modo escuro pelas variáveis de `tema.css`): cartão "Chamando agora" com a senha, "Dirija-se à {especialidade} · {Sala} · {n}ª chamada" e faixa lateral na cor clínica; cartão "Triagem · Ticket chamado"; tabela "Últimas chamadas" com senha, especialidade, Sala e horário.

### D5. Sem previsão na tela (decisão do PO, 20/11/2026)
O painel mostra só a chamada atual, o ticket da triagem e as últimas chamadas; a previsão das próximas senhas não aparece. O endpoint ainda devolve `previsoes` (feito antes da decisão e coberto por `test_painel.py`); a tela ignora esse campo.

### D6. Duas telas: consultórios e triagem (decisão do PO, 20/11/2026)
Cada TV abre a sua: `/painel/medico` (senha chamada pelo médico e últimas chamadas, com filtro por especialidade) e `/painel/triagem` (ticket chamado pela Recepção/Triagem e últimos tickets). As duas usam o mesmo `GET painel`, que passou a devolver também `triagem_ultimas` (até 4 tickets chamados antes do atual, na janela `HORAS_PAINEL`). Cada tela só toca o aviso para as próprias chamadas. `/painel` mostra os dois endereços.

## Riscos / Compromissos

- [Endpoint público pode ser consultado em excesso] → Resposta pequena e só leitura; se necessário, ativar o rate limit do Xano.

## Plano de migração

Só um endpoint e uma página novos. A previsão é por especialidade, pois a regra global de interleaving entre filas para médicos que podem atender qualquer especialidade continua pendente em `add-fila-chamada-medico`; não apresentar uma sequência global como se já estivesse definida. Rollback: removê-los.

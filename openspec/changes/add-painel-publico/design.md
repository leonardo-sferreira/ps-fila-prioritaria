# Design técnico

## Contexto

A tabela `chamada` (change 6) registra toda tentativa, e `prever_fila` fornece a previsão sem dados pessoais. O ticket da pré-triagem guarda `chamado_em`, que é atualizado a cada rechamada (change 3). Falta um ponto público de leitura e a tela.

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

### D2. Polling de 3 s no Reflex com detecção de novidade
O state do painel guarda o `chamado_em` da chamada atual e do ticket; se algum mudar, dispara a animação de destaque e o som (arquivo curto em `assets/`). Em caso de erro, mantém o último estado e mostra "reconectando". O navegador pode bloquear o som até a primeira interação: a tela mostra "Toque para ativar o som" na primeira vez.
- **Alternativa:** SSE. Descartada por complexidade e pelo suporte limitado no Xano.

### D3. "Local" = especialidade
Salas e consultórios não são modelados. O painel mostra "Dirija-se à Clínica Geral". Se o PS quiser o número do consultório, isso vira um campo em Especialidade ou Médico numa change futura.

### D4. Layout de TV
Tela cheia em 16:9: à esquerda, a senha atual (fonte bem grande, fundo na cor da prioridade, usando `cores.py`); à direita, "Triagem" e as últimas chamadas; abaixo, uma coluna de previsão por especialidade. Contraste alto e texto legível a 5 m (RNF01, RNF10).

## Riscos / Compromissos

- [Endpoint público pode ser consultado em excesso] → Resposta pequena e só leitura; se necessário, ativar o rate limit do Xano.
- [Previsão diferente da chamada para médicos com várias especialidades] → Limitação conhecida (change 6, D3); o painel indica "previsão sujeita a mudança".

## Plano de migração

Só um endpoint e uma página novos. Rollback: removê-los.

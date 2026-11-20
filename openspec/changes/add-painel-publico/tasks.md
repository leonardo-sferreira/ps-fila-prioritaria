# Tarefas

## 1. Xano — endpoint do painel

- [x] 1.1 [Xano] Criar `GET painel` público com a resposta de campos explícitos (D1), usando `prever_fila` e o filtro `especialidades`; verificar com os testes 1.2
  - Concluída em 20/11/2026: `GET painel` já estava publicado na `v1` por outra pessoa da equipe, junto com `fila/previsao_especialidade` (a mesma montagem da previsão autenticada). Trazidos para o repositório sem mudança (simulação sem diferenças). Resposta com `chamada_id` e `ticket_id` para a tela detectar chamada nova; a Sala é a atual do médico que chamou.
  - 20/11/2026, decisão do PO: chamadas e ticket da triagem só aparecem dentro de uma janela desde a chamada (parâmetro `HORAS_PAINEL`, 1 a 24 h, padrão 2 h), em vez de "dia de hoje", porque o PS funciona 24 horas. A Sala continua sendo a vinculada ao médico no cadastro (sem mudança na tabela `chamada`).
- [x] 1.2 Escrever `tests/api/test_painel.py` cobrindo: acesso sem token; ausência de chaves proibidas (nome, cpf, nascimento, telefone, sintomas, sinais vitais) em toda a resposta, verificada recursivamente; chamada atual e indicação de repetição; 4 últimas chamadas em ordem; previsão com 8 e com 3 elegíveis; Vermelho entrando na primeira posição; desistência removida da previsão; coerência previsão × "Chamar próximo" (CA11); ticket da triagem e rechamada; filtro por especialidade; verificar que passam
  - Parcial (20/11/2026): `tests/api/test_painel.py` cobre, ao vivo, acesso sem token, ausência de chaves proibidas em toda a resposta, filtro por especialidade (e 400 sem nenhuma válida), Vermelha antes da Amarela, coerência com "Chamar próximo" (CA11), chamada atual e repetição (2ª chamada) e desistência fora da previsão. Ficam fora: 8 e 3 elegíveis (cobertos pelos testes nativos de `fila/prever_fila`) e ticket da triagem com rechamada (não chamado no teste para não mexer na fila real; só o formato é conferido).
  - Concluída em 20/11/2026: `test_tamanho_da_previsao_e_ticket_da_triagem` completa a 1.2 com pacientes e ticket fictícios de `fila/teste_painel_extras` (apagados no fim, inclusive o horário da chamada do ticket, para ele não ficar na TV real): 3 aguardando mostram 3, 8 mostram 5, ticket chamado aparece e a rechamada vira 2ª chamada. 2 testes e 9 subtestes passando.
- [x] 1.3 Exportar o XanoScript para `backend/xano/` e verificar que os arquivos estão no repositório
  - Concluída em 20/11/2026: `api/fila/painel_get.xs`, `function/fila/previsao_especialidade.xs` e `api/fila/filas_especialidade_previsao_get.xs` no repositório.

## 2. Reflex — página do painel

- [x] 2.1 [Reflex] Criar a página `/painel` sem login, com o layout de TV (D4) e o filtro por parâmetro de URL; verificar manualmente em tela cheia com duas especialidades
  - Implementada em 20/11/2026: `/painel` sem login (`paginas/painel.py`), refeita pela tela 5 do Figma a pedido do PO: cabeçalho padrão com data e hora, cartão "Chamando agora", cartão da triagem e tabela de últimas chamadas (senha, especialidade, Sala, horário); sem previsão das próximas senhas (D5); filtro `?especialidades=CAR,ORT`. Depois separada em duas telas (D6): `/painel/medico` e `/painel/triagem`, com `/painel` mostrando os dois endereços. Falta a verificação manual do PO.
  - Verificada pelo PO em 20/11/2026: painéis dos consultórios e da triagem testados no fluxo real.
- [x] 2.2 [Reflex] Implementar o polling de 3 s, a detecção de nova chamada com destaque e som, e o aviso "Toque para ativar o som" (D2); verificar manualmente com uma chamada e uma repetição feitas em outra aba
  - Implementada em 20/11/2026: polling de 5 s (`rx.moment`; era 3 s, mudado pelo limite do plano gratuito do Xano), destaque que pisca a cada chamada nova ou repetida e na rechamada de ticket, aviso sonoro de dois tons pela Web Audio API (sem arquivo em `assets/`) e botão "Toque para ativar o som". 6 testes em `frontend/tests/test_painel_state.py`. Falta a verificação manual do PO.
  - Verificada pelo PO em 20/11/2026: destaque e aviso sonoro funcionando na chamada e na repetição.
- [x] 2.3 [Reflex] Implementar o estado "reconectando", que mantém a última informação; verificar manualmente parando o acesso à rede por 30 s
  - Implementada em 20/11/2026: em falha de rede, mantém o último estado e mostra "Reconectando…". Falta a verificação manual do PO.
  - Aceita pelo PO em 20/11/2026 sem o teste manual de queda de rede (não havia como desligar a rede). O "Reconectando…" foi visto na prática quando o Xano recusou consultas por limite (429): o painel manteve a tela e mostrou o aviso.
- [x] 2.4 Adicionar ao README como abrir o painel numa TV (URL com filtro, tela cheia, ativação do som) e o roteiro manual da seção 2; verificar executando-o
  - Concluída em 20/11/2026: seção "Painel público" no README (TV, filtro, tela cheia, som e roteiro de 6 passos); a execução do roteiro fica com o PO.

## 3. Integração

- [x] 3.1 Verificação ponta a ponta com três janelas (recepção, médico e painel): chamar um ticket na pré-triagem, triar e confirmar um paciente, chamá-lo pelo médico e repetir a chamada, conferindo em cada passo o que o painel mostra e que nenhum dado pessoal aparece
  - Verificada pelo PO em 20/11/2026: fluxo do Totem até a chamada do médico, acompanhado nos painéis (ticket na triagem e senha nos consultórios), funcionando.

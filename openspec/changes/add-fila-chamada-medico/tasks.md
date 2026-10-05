# Tarefas

## 1. Xano — regra da fila e previsão

- [ ] 1.1 [Xano] Criar a tabela `ciclo_fila` (D1) com a reinicialização da posição quando os parâmetros do ciclo mudam; verificar no painel alterando `amarelas_por_ciclo`
- [ ] 1.2 [Xano] Criar as funções `proxima_ficha` e `prever_fila` (D2) e o endpoint `GET filas/{especialidade}/previsao` (autenticado; só senha e cor); verificar com os testes 1.3
- [ ] 1.3 Escrever `tests/api/test_ordenacao.py` com uma tabela de casos (fichas inseridas com cor, condição e chegada controladas) cobrindo: vermelho que chega depois, ciclo A-A-B-A-A-B, vermelho no meio do ciclo sem avançar a posição, só Azuis, Azul esperando na posição de Azul, idoso azul à frente de azul que chegou antes, prioritário que não ultrapassa a cor, empate de chegada, previsão com 3 e com 7 elegíveis, previsão sem dados pessoais e fichas não AGUARDANDO excluídas; verificar que passam

## 2. Xano — chamada

- [ ] 2.1 [Xano] Acrescentar à `ficha_atendimento` os campos `medico_chamada_id`, `tentativas_chamada`, `chamada_em` e `finalizada_em`, e criar a tabela `chamada` (D5); verificar no painel
- [ ] 2.2 [Xano] Criar `GET medico/filas` e `POST medico/chamar-proximo` sem filtro por especialidade de referência e com reserva atômica; não implementar seleção multi-fila antes da decisão do PO; verificar após decisão
- [ ] 2.3 [Xano] Criar chamadas/comparecimento/desistência com 30 s, 3 chamadas por oportunidade, uma reentrada e encerramento após a segunda oportunidade; verificar transições e responsabilidade pela ficha
- [ ] 2.4 [Xano] Criar `GET fichas/{id}/impressao` (MEDICO que chamou); verificar com os testes 2.5
- [ ] 2.5 Escrever `tests/api/test_chamada.py` cobrindo 403 para Recepção/Triagem e Administrador, elegibilidade sem filtro por especialidade, distribuição entre filas depois da decisão de produto, 30 s, tentativas 1–3 por oportunidade, uma reentrada sem novo número, encerramento após a segunda oportunidade, desistência explícita, concorrência, duplicidade, pausa/plantão encerrado, histórico e privacidade; verificar que passam
- [ ] 2.6 Exportar o XanoScript das seções 1 e 2 para `backend/xano/` e verificar que os arquivos estão no repositório

## 3. Reflex — tela do médico

- [ ] 3.1 [Reflex] Criar `/medico` com "Chamar próximo", ficha atribuída, Sala da chamada, tentativas por oportunidade e estado de pausa/plantão; não oferecer escolha manual de ficha nem filtrar por especialidade de referência
- [ ] 3.2 [Reflex] Ligar as ações "Repetir chamada", "Compareceu" e "Registrar desistência", com confirmação na desistência; verificar manualmente as 3 tentativas e a desistência
- [ ] 3.3 [Reflex] Criar `/medico/ficha/{id}/imprimir` (D7); verificar manualmente a visualização de impressão
- [ ] 3.4 Adicionar ao README o roteiro manual da seção 3, com o teste de dois navegadores chamando ao mesmo tempo; verificar executando-o

## 4. Integração e documentação

- [ ] 4.1 Verificação ponta a ponta: triar 6 pacientes em Clínica Geral (1 Vermelho, 3 Amarelos sendo 1 idoso, 2 Azuis), conferir a previsão e chamar até esvaziar, verificando a ordem V, A(idoso), A, B, A, B; em uma das fichas, fazer 3 tentativas e registrar desistência
- [ ] 4.2 Conferir `docs/domain-model.md` (estados CHAMADO/ATENDIDO/DESISTÊNCIA, Chamada e a divergência CHAMADO → AGUARDANDO) com a implementação e ajustar o que divergir

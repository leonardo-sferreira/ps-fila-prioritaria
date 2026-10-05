# Design técnico

## Contexto

Já existem fichas AGUARDANDO com `prioridade_atual`, `condicao_prioritaria`, `chegada_em`, especialidade atribuída e senha (changes 4 e 5), a função `medicos_disponiveis` e os parâmetros `amarelas_por_ciclo`, `azuis_por_ciclo`, `max_tentativas`, `intervalo_chamada_seg` e `tamanho_previsao` (change 2). O padrão de reserva atômica foi estabelecido no ticket (change 3, D3).

## Objetivos / Fora dos objetivos

**Objetivos:**
- Uma única implementação da regra, usada pela chamada e pela previsão (RN25), testável sem criar chamadas reais.
- Chamada sem duplicidade com vários médicos e cliques repetidos.

**Fora dos objetivos:**
- Atualização em tempo real por websocket: a tela do médico faz polling (ver D6).

## Decisões

### D1. Estado do ciclo persistido por fila de especialidade
O ciclo aprovado permanece por especialidade e preserva estado entre sessões/reinícios. O ciclo dentro de cada fila não define como o sistema intercala várias especialidades para Médicos elegíveis; a seleção global permanece como decisão pendente e bloqueia a implementação da chamada multi-fila.

### D2. Funções `ordenar_fila`, `proxima_ficha` e `prever_fila`
- `proxima_ficha(elegiveis, posicao)` → (ficha, avança_ciclo): aplica vermelho → cor prevista (ou a outra) → prioritário → `chegada_em` → `id`.
- `prever_fila(especialidade, n)`: carrega as elegíveis e a posição e chama `proxima_ficha` n vezes sobre uma cópia em memória, removendo a escolhida e avançando a posição simulada.
- `POST medico/chamar-proximo` usa `proxima_ficha` com os dados reais.
- **Por quê:** a mesma função nos dois caminhos garante CA11 por construção.

### D3. Elegibilidade sem filtro por especialidade de referência
Um Médico elegível pode receber ficha de qualquer fila. O sistema NÃO DEVE filtrar candidatos pela especialidade cadastrada no Médico nem pedir ao Médico para escolher a ficha. A política global de selecionar uma fila quando várias especialidades têm fichas elegíveis precisa ser definida pelo PO; dentro de cada fila vale D2.

### D4. Reserva atômica e idempotência
Dentro de uma transação: verifica se o médico já tem ficha CHAMADO (se tiver, recusa, e isso também torna o duplo clique idempotente); escolhe a candidata; faz `UPDATE ficha SET status=CHAMADO, medico_chamada_id=?, tentativas_chamada=1 WHERE id=? AND status=AGUARDANDO`. Se 0 linhas forem afetadas (outro médico levou a ficha), recalcula a candidata e tenta de novo, até 5 vezes. Depois grava a `chamada` e atualiza o `ciclo_fila`. Um índice único parcial em `ficha(medico_chamada_id) WHERE status=CHAMADO` protege a regra de uma ficha pendente por médico; se o Xano não suportar índice parcial, a checagem em transação cobre.

### D5. Histórico `chamada` por oportunidade
O histórico registra ficha, médico, número da oportunidade, tentativa (1–3) dentro dela, tipo (`CHAMADA|COMPARECIMENTO|DESISTENCIA`), timestamp e fila de origem. Uma ficha pode ter até duas séries 1–3, separadas por uma reentrada; não duplicar o mesmo evento. O painel lê as chamadas deste histórico.

### D6. Tela `/medico`
Topo: status operacional/plantão e botão "Chamar próximo". Cartão da ficha atribuída: senha, nome apenas após atribuição autorizada, oportunidade e tentativa atuais, botões "Repetir chamada", "Compareceu", "Registrar desistência" e "Imprimir ficha". Não restringir a especialidade de referência. Previsões entre filas distintas aguardam definição da regra global de distribuição.

### D7. Impressão da ficha
`GET fichas/{id}/impressao` (MEDICO que chamou) devolve os dados; `/medico/ficha/{id}/imprimir` renderiza em A4 e chama `window.print()`.

## Riscos / Compromissos

- [Regra do ciclo mal entendida] → A spec traz exemplos numéricos e `test_ordenacao.py` implementa uma tabela de casos (sequência de chegadas → sequência esperada de chamadas).
- [Polling de 5 s gera muitas requisições no plano gratuito] → Intervalo configurável no Reflex; a tela só consulta quando está visível.
- [Várias filas elegíveis para Médicos de qualquer especialidade] → Não implementar a seleção multi-fila até decisão do PO; não usar especialidade cadastral como substituto.

## Plano de migração

Tabelas e campos novos. Rollback: remover tabelas, campos e endpoints.

## Questões em aberto

- Qual regra global intercala filas de especialidades distintas para distribuir fichas a Médicos elegíveis? Preservar a ordem e o ciclo aprovados dentro de cada fila.

# Design técnico

## Contexto

Já existem fichas AGUARDANDO com `prioridade_atual`, `condicao_prioritaria`, `chegada_em`, especialidade atribuída e senha (changes 4 e 5), a função `medicos_disponiveis` e os parâmetros `amarelas_por_ciclo`, `azuis_por_ciclo`, `max_tentativas` e `tamanho_previsao` (change 2). O padrão de reserva atômica foi estabelecido no ticket (change 3, D3).

## Objetivos / Fora dos objetivos

**Objetivos:**
- Uma única implementação da regra, usada pela chamada e pela previsão (RN25), testável sem criar chamadas reais.
- Chamada sem duplicidade com vários médicos e cliques repetidos.

**Fora dos objetivos:**
- Atualização em tempo real por websocket: a tela do médico faz polling (ver D6).

## Decisões

### D1. Estado do ciclo persistido por especialidade
Tabela `ciclo_fila` (`especialidade_id` único, `posicao` 1..A+B). A posição prevista é Amarela se `posicao <= A`, senão Azul. Avança (`posicao % (A+B) + 1`) só quando a ficha chamada é da cor prevista. Se os parâmetros A ou B mudarem, a posição volta a 1.
- **Por quê:** o ciclo precisa sobreviver a reinícios (RNF08) e ser o mesmo para todos os médicos da especialidade.

### D2. Funções `ordenar_fila`, `proxima_ficha` e `prever_fila`
- `proxima_ficha(elegiveis, posicao)` → (ficha, avança_ciclo): aplica vermelho → cor prevista (ou a outra) → prioritário → `chegada_em` → `id`.
- `prever_fila(especialidade, n)`: carrega as elegíveis e a posição e chama `proxima_ficha` n vezes sobre uma cópia em memória, removendo a escolhida e avançando a posição simulada.
- `POST medico/chamar-proximo` usa `proxima_ficha` com os dados reais.
- **Por quê:** a mesma função nos dois caminhos garante CA11 por construção.

### D3. Escolha entre as especialidades do médico
Para cada especialidade do médico com fila não vazia, obtém a candidata com `proxima_ficha`. Entre as candidatas vence a de cor mais grave; em empate, a com condição prioritária; depois `chegada_em`. Só o ciclo da especialidade da vencedora é atualizado.
- **Consequência:** para um médico com várias especialidades, a previsão de uma fila pode não coincidir com a chamada dele, porque outra fila teve uma candidata mais grave. CA11 vale para médicos de uma única especialidade, que é o caso descrito no documento formal (seção 17: uma especialidade por médico).

### D4. Reserva atômica e idempotência
Dentro de uma transação: verifica se o médico já tem ficha CHAMADO (se tiver, recusa, e isso também torna o duplo clique idempotente); escolhe a candidata; faz `UPDATE ficha SET status=CHAMADO, medico_chamada_id=?, tentativas_chamada=1 WHERE id=? AND status=AGUARDANDO`. Se 0 linhas forem afetadas (outro médico levou a ficha), recalcula a candidata e tenta de novo, até 5 vezes. Depois grava a `chamada` e atualiza o `ciclo_fila`. Um índice único parcial em `ficha(medico_chamada_id) WHERE status=CHAMADO` protege a regra de uma ficha pendente por médico; se o Xano não suportar índice parcial, a checagem em transação cobre.

### D5. Tabela `chamada`
`ficha_id`, `medico_id`, `tentativa`, `tipo` (`CHAMADA|COMPARECIMENTO|DESISTENCIA`), `criado_em`; índice único (`ficha_id`, `tentativa`, `tipo`) contra duplicidade (RNF03). O painel (próxima change) lê as últimas linhas `CHAMADA` desta tabela.

### D6. Tela `/medico`
Topo: status de disponibilidade e botão "Chamar próximo" (desabilitado enquanto a requisição está em andamento). Cartão da ficha chamada: senha grande, nome do paciente, tentativa X de N, botões "Repetir chamada", "Compareceu", "Registrar desistência" (este só habilitado na última tentativa) e "Imprimir ficha". Abaixo, uma coluna por especialidade com a fila prevista (senha, cor, ícone de prioritário, espera em minutos), atualizada por polling a cada 5 s.

### D7. Impressão da ficha
`GET fichas/{id}/impressao` (MEDICO que chamou) devolve os dados; `/medico/ficha/{id}/imprimir` renderiza em A4 e chama `window.print()`.

## Riscos / Compromissos

- [Regra do ciclo mal entendida] → A spec traz exemplos numéricos e `test_ordenacao.py` implementa uma tabela de casos (sequência de chegadas → sequência esperada de chamadas).
- [Polling de 5 s gera muitas requisições no plano gratuito] → Intervalo configurável no Reflex; a tela só consulta quando está visível.
- [Médico fica indisponível com ficha CHAMADO] → A ficha continua com ele até comparecimento ou desistência (ver Questões em aberto).

## Plano de migração

Tabelas e campos novos. Rollback: remover tabelas, campos e endpoints.

## Questões em aberto

- O que fazer com uma ficha CHAMADO quando o médico sai do plantão sem resolvê-la (liberar para a fila ou exigir ação do Administrador)? Pode ser tratado numa change futura sem mudar estas specs.

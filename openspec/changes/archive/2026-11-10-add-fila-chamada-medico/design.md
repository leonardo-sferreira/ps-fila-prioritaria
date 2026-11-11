# Design técnico

## Contexto

O repositório contém `medico_especialidade` (N:N), `ciclo_fila`, `chamada` e campos de chamada em `ficha_atendimento`; a presença de arquivos `.xs` não comprova publicação/execução no servidor. As changes de cadastros, status operacional e direcionamento ainda são dependências funcionais. A Rev. 2.1, §7.1–7.2 e §14.1 define a seleção entre filas.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Uma única implementação da regra, usada pela chamada e pela previsão (RN25), testável sem criar chamadas reais.
- Chamada sem duplicidade com vários médicos e cliques repetidos.

**Fora dos objetivos:**
- Atualização em tempo real por websocket: a tela do médico faz polling (ver D6).

## Decisões

### D1. Estado do ciclo persistido por fila de especialidade
Reaproveitar `ciclo_fila`, com uma posição por especialidade. O ciclo configurável (inicial 2 Amarelas:1 Azul) só avança quando a cor chamada corresponde à posição prevista; Vermelha e uso da cor alternativa não o avançam. A seleção entre filas usa a candidata de cada especialidade, sem fundir os ciclos. Alternativa de ciclo global foi descartada porque mudaria o critério interno da fila aprovado na Rev. 2.1, §7.2.

### D2. Funções `ordenar_fila`, `proxima_ficha` e `prever_fila`
- `proxima_ficha(elegiveis, posicao)` → (ficha, avança_ciclo): aplica Vermelha → cor prevista (ou a outra) → condição prioritária → ordem efetiva da fila → `id`. Na entrada inicial, a ordem efetiva é `chegada_em`; após reentrada, passa ao fim sem alterar `chegada_em`.
- `prever_fila(especialidade, n)`: carrega as elegíveis e a posição e chama `proxima_ficha` n vezes sobre uma cópia em memória, removendo a escolhida e avançando a posição simulada.
- `POST medico/chamar-proximo` obtém uma candidata por especialidade com `proxima_ficha`, aplica D3 e reserva a escolhida.
- **Por quê:** a mesma função nos dois caminhos garante CA11 por construção.

### D3. Seleção determinística entre filas
Ler as especialidades próprias em `medico_especialidade`. Para cada uma, obter a próxima candidata pela regra interna. Havendo Vermelhas próprias, escolher a de `chegada_em` mais antigo e depois menor ID de ficha. Sem Vermelha própria, percorrer as especialidades próprias em ordem crescente de ID, ciclicamente após a última especialidade própria chamada por esse médico no histórico; pular filas próprias vazias. Chamadas próprias de qualquer cor atualizam a referência histórica. A candidata selecionada é a "próxima própria".

Uma fila é descoberta se nenhum médico vinculado a ela tiver usuário/Médico ativo, plantão e disponibilidade vigentes e sessão apta; PAUSA/AUSENTE retiram cobertura, EM_ATENDIMENTO não. Escolher a melhor candidata descoberta por cor, condição prioritária, ordem efetiva da fila e ID da ficha. Se sua cor for mais grave que a próxima própria, chamá-la; cor igual favorece a própria. Sem candidata própria, escolher descoberta; se não houver descoberta, escolher candidata de outra fila coberta pelo mesmo desempate. O vínculo N:N define preferência, nunca filtro absoluto. A ficha conserva especialidade e senha. Alternativas de distribuição antecipada e de escolha manual foram descartadas (D02 e RN24).

No esquema físico, `disponibilidade_medico.encerrado_em` registra o encerramento explícito do período vigente. Um período só cobre sua especialidade enquanto `inicio <= agora < fim` e `encerrado_em` estiver vazio. Isso preserva a disponibilidade cadastrada pelo Administrador e distingue encerrar o plantão de logout e PAUSA.

### D4. Reserva atômica e idempotência
Na operação transacional do Xano, validar perfil, médico/usuário ativos, disponibilidade, plantão, status e sessão operacional. Um novo login médico não concede disponibilidade; a chamada não cria sessão. Verificar a ausência de ficha CHAMADO pendente, selecionar com D2/D3, reservar condicionalmente a ficha ainda AGUARDANDO, registrar tentativa 1 e atualizar `ciclo_fila` se aplicável. Em disputa, reler candidatos/estado e tentar novamente; nenhum evento/ciclo é confirmado sem reserva. Duplo clique da mesma sessão não cria outra ficha nem evento. Validar no Xano a primitiva transacional e a atualização condicional antes de escolher implementação física; não presumir suporte a índice parcial SQL.

### D5. Histórico e reentrada
Refatorar `chamada.xs`: incluir oportunidade e ajustar a unicidade atual (`ficha_id`, `tentativa`, `tipo`), que impediria a tentativa 1 da segunda oportunidade. O histórico registra ficha, médico, oportunidade, tentativa, tipo e horário; a fila de origem é a especialidade atribuída da ficha, que não muda após a chamada. Acrescentar à ficha o identificador da oportunidade atual e a ordem efetiva da fila, inicialmente igual à chegada. Na única reentrada, atualizar a ordem efetiva para o fim da mesma especialidade sem mudar `chegada_em` ou senha. Cada evento deve ter unicidade por ficha, oportunidade, tentativa e tipo. O painel lê o histórico já existente.

### D6. Tela `/medico`
Topo: status operacional/plantão e botão "Chamar próximo". Cartão da ficha atribuída: senha, especialidade clínica, nome apenas após atribuição autorizada, oportunidade e tentativa atuais, botões "Repetir chamada", "Compareceu", "Registrar desistência" e "Imprimir ficha". Mostrar aviso de fila vazia quando não houver candidata nas próprias, descobertas nem outras cobertas. Não oferecer escolha de fila ou ficha.

### D7. Impressão da ficha
`GET fichas/{id}/impressao` (MEDICO que chamou) devolve os dados; `/medico/ficha/{id}/imprimir` renderiza em A4 e chama `window.print()`.

## Riscos / Compromissos

- [Regra do ciclo mal entendida] → A spec traz exemplos numéricos e `test_ordenacao.py` implementa uma tabela de casos (sequência de chegadas → sequência esperada de chamadas).
- [Polling de 5 s gera muitas requisições no plano gratuito] → Intervalo configurável no Reflex; a tela só consulta quando está visível.
- [Dois médicos disputam ficha/ciclo] → Reservar e avançar o ciclo na mesma transação, com teste de chamadas simultâneas.
- [Vínculo N:N ou cobertura mudam durante a seleção] → Revalidar elegibilidade e cobertura no ponto de reserva; repetir seleção em caso de conflito.
- [Tabelas `.xs` divergem do servidor] → Conferir esquema publicado antes de alterar `chamada` e `ficha_atendimento`; exportar a versão efetiva após a implementação.

## Plano de migração

Migrar as tabelas existentes `chamada`, `ciclo_fila` e `ficha_atendimento` sem perder registros. Preencher oportunidade 1 nos eventos legados e ordem efetiva com `chegada_em`; substituir a unicidade antiga de `chamada` somente após conferir dados existentes. Rollback deve preservar histórico já gravado e restaurar a versão anterior dos endpoints/esquema quando seguro.

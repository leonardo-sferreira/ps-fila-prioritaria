# Delta de especificação

## ADDED Requirements

### Requirement: Reavaliação da ficha em AGUARDANDO
A Recepção/Triagem DEVE poder alterar sintomas do catálogo, sintomas digitados, observação, sinais vitais, gestação e ajuste manual da prioridade de uma ficha em `AGUARDANDO`. Cada alteração DEVE, numa única operação: recalcular a classificação pelas regras vigentes; refazer o destino pelo requisito "Especialidade de destino pelos sintomas" e pela especialidade padrão, sem contar a própria ficha no critério de fila; atualizar a especialidade sugerida e a atribuída; e atualizar a senha conforme o requisito "Troca de senha na reavaliação". A ficha DEVE continuar em `AGUARDANDO` com o mesmo `chegada_em`. Se o resultado ficar sem prioridade atual, a alteração DEVE ser recusada sem mudar nada, informando as pendências, a menos que a mesma operação traga ajuste manual válido com justificativa. A auditoria da alteração DEVE registrar também a especialidade e a senha anteriores e novas. Fichas em `CHAMADO`, `ATENDIDO`, `DESISTENCIA` ou `CANCELADO` NÃO DEVEM ser alteradas. O backend DEVE exigir sessão do perfil Recepção/Triagem.

#### Scenario: Piora muda a cor
- **QUANDO** uma ficha `AGUARDANDO` Amarela em Cardiologia recebe SpO₂ que eleva o cálculo para Vermelha
- **ENTÃO** a prioridade atual passa a Vermelha, a ficha continua em Cardiologia e `AGUARDANDO`, e `chegada_em` não muda

#### Scenario: Novo sintoma muda a especialidade
- **QUANDO** uma ficha `AGUARDANDO` de adulto em Cardiologia com "Palpitações" (2) recebe "Convulsão em atividade" (3)
- **ENTÃO** a especialidade sugerida e a atribuída passam a Neurologia e a auditoria registra Cardiologia como anterior

#### Scenario: Própria ficha fora do critério de fila
- **QUANDO** a reavaliação empata duas candidatas até a soma, e a ficha reavaliada é a única `AGUARDANDO` em uma delas
- **ENTÃO** o critério de fila compara as filas sem contar a própria ficha

#### Scenario: Edição deixa a ficha sem cor
- **QUANDO** a gestação é marcada em ficha `AGUARDANDO` sem ajuste manual na mesma operação
- **ENTÃO** o backend recusa, informa as pendências e a ficha, a senha e a auditoria ficam como antes

#### Scenario: Edição com ajuste na mesma operação
- **QUANDO** a gestação é marcada em ficha `AGUARDANDO` junto com prioridade Amarela e justificativa
- **ENTÃO** a alteração é aceita, a prioridade atual é Amarela e a auditoria registra a alteração clínica e o ajuste

#### Scenario: Ficha chamada
- **QUANDO** se tenta alterar sintomas, sinais vitais ou prioridade de ficha `CHAMADO`
- **ENTÃO** o backend recusa sem alterar a ficha

#### Scenario: Perfil sem permissão
- **QUANDO** Médico, Administrador ou pessoa sem sessão válida tenta alterar ficha `AGUARDANDO`
- **ENTÃO** o backend recusa sem alterar a ficha nem registrar auditoria

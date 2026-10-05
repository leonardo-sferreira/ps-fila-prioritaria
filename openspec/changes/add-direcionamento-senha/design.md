# Design técnico

## Contexto

Já existem: consulta de Médico elegível (change 2), `sintoma_especialidade`, parâmetro `especialidade_padrao`, `ficha_atendimento` com classificação e `registrar_alteracao`. Esta change liga a ficha à fila da especialidade indicada pelos sintomas e gera senha. A especialidade do Médico não altera nem filtra o destino da ficha.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Uma única função `direcionar_ficha`, usada na confirmação e quando sintomas/dados de triagem forem atualizados antes de a ficha ser chamada.
- Numeração de senha sem repetição com confirmações simultâneas.

**Fora dos objetivos:**
- Escolher ou balancear médicos elegíveis entre filas de especialidades distintas; essa política fica em `add-fila-chamada-medico` e não pode ser inventada aqui.

## Decisões

### D1. Destino clínico estável
A unidade de fila é a especialidade indicada pelo conjunto de sintomas. A ficha mantém esse destino mesmo se o Médico que a atender tiver outra especialidade de referência ou se nenhum Médico estiver elegível naquele instante. Disponibilidade afeta distribuição operacional, nunca redirecionamento clínico.

### D2. `direcionar_ficha(ficha)`
Resolve o destino conforme o conjunto de sintomas e as relações do catálogo oficial, não por cor do sintoma nem disponibilidade/especialidade do Médico. A regra de empate quando sintomas apontam a diferentes especialidades permanece pendente de decisão funcional. Sem sintomas direcionáveis, aplica-se somente a regra-base de destino definida para esse caso, sem fallback por disponibilidade. Para criança dentro do limite configurado, o destino é Pediatria sem alterar o escore/classificação. A função não procura alternativas por falta de Médico e não grava; quem chama decide.

### D3. Contador de senha com linha por (data, especialidade)
Tabela `contador_senha` (`data`, `especialidade_id`, `ultimo_numero`) com índice único. `gerar_senha` faz upsert da linha e incremento condicional (`UPDATE ... SET ultimo_numero = ultimo_numero + 1 WHERE ultimo_numero = lido`), repetindo em caso de conflito, dentro da transação da confirmação.
- **Alternativa:** `max()+1` sobre as fichas, como no ticket. Descartada porque a senha muda quando a ficha é redirecionada, o que torna o `max` sobre fichas pouco confiável.

### D4. Confirmação em uma transação
`POST fichas/{id}/confirmar-triagem` com `{aceitar_sem_medico: bool}`: valida completude (reusa a validação da change 4), chama `direcionar_ficha`, decide (atribuída, recusa com aviso, ou sugerida marcada `sem_medico_no_direcionamento`), gera a senha, muda o status para AGUARDANDO e audita.

### D5. Atualização do destino da ficha
Em `PATCH fichas/{id}` e `ajustar-prioridade` da change de triagem, para ficha ainda não chamada, recalcular classificação e direcionamento conforme sintomas. Se o destino clínico ou a cor atual mudar, gera nova senha e auditoria, preservando `chegada_em`. Mudança de disponibilidade ou especialidade cadastral do Médico não redireciona fichas. Não criar `redirecionar_especialidade` por perda de Médico; distribuição/atribuição é responsabilidade da change de chamada.

### D6. Comprovante como página imprimível
`GET fichas/{id}/comprovante` devolve só os campos permitidos (senha, cor, especialidade, chegada). O Reflex renderiza `/recepcao/comprovante/{id}` com CSS `@page { size: 80mm auto }` e chama `window.print()` ao abrir. A reimpressão reabre a mesma página.
- **Alternativa:** gerar PDF no backend. Descartada porque o Xano não é bom nisso e a impressão pelo navegador atende uma impressora térmica configurada no sistema operacional.

## Riscos / Compromissos

- [Mudança de senha confunde o paciente com um comprovante antigo] → A tela de triagem mostra "Senha alterada: reimprima o comprovante" sempre que a senha muda.
- [Vários sintomas podem apontar a destinos diferentes] → Requer decisão explícita de desempate antes da implementação; preservar a lista e sua ordem conforme catálogo até isso ser definido.

## Plano de migração

Campos novos em `ficha_atendimento` (nulos em fichas EM_TRIAGEM) e uma tabela nova. Rollback: remover campos, tabela e endpoints, e voltar os endpoints das changes 2 e 4 à versão anterior.

## Questões em aberto

- Desempate quando sintomas selecionados apontarem a diferentes destinos clínicos.

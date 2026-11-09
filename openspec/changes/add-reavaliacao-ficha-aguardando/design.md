# Design técnico

## Contexto

A motivação está em `proposal.md`, seção Why. Na `main`:

- `PATCH /fichas/{id}` e `POST /fichas/{id}/prioridade` têm `precondition ($ficha.status == "EM_TRIAGEM")` com erro `FICHA_FORA_DA_TRIAGEM`.
- O PATCH grava as alterações, recalcula a classificação com `classificacao/avaliar_ficha` (descartando o ajuste) e audita `SINTOMAS_ALTERADOS` ou `SINAIS_VITAIS_ALTERADOS`.
- `POST /fichas/{id}/confirmar-triagem` chama `direcionamento/destino_da_ficha` (que lê a ficha gravada, a idade, as ligações e a fila `AGUARDANDO` das candidatas) e `direcionamento/gerar_senha` (que reserva o próximo número do dia da especialidade em `contador_senha`).
- `GET /fichas/{id}` devolve `senha` e `especialidade` fora de `EM_TRIAGEM`, e a tela mostra a ficha `AGUARDANDO` em modo leitura com "Reimprimir".
- O comprovante já lê a senha atual da ficha.

Decisões do usuário em 09/11/2026: só `AGUARDANDO` é editável; quando só a cor muda, o número é mantido; a edição é recusada se a ficha ficar sem cor; `chegada_em` não muda.

## Objetivos / Fora dos objetivos

**Objetivos:**

- Reaproveitar os endpoints, as funções de destino e de senha e a tela existentes, sem endpoint novo.
- Garantir que a ficha nunca fique na fila sem cor, sem destino ou com senha incoerente com cor e especialidade.

**Fora dos objetivos:**

- Mudar a regra de recálculo da classificação em `EM_TRIAGEM`.
- Concorrência entre reavaliação e chamada médica: ainda não existe chamada médica (`add-fila-chamada-medico`).

## Decisões

### D1. Mesmos endpoints, com o estado aceito ampliado

A precondição de estado do PATCH e do ajuste de prioridade passa a aceitar `EM_TRIAGEM` ou `AGUARDANDO`, e o erro `FICHA_FORA_DA_TRIAGEM` continua valendo para os demais estados. Para a ficha `AGUARDANDO`, depois do fluxo atual de gravação e recálculo, o endpoint executa a reavaliação (D3) na mesma transação.

- **Por quê:** a validação de entrada, o RN04, o recálculo e a auditoria já estão nesses endpoints. Um endpoint separado duplicaria tudo isso.
- **Alternativa descartada:** um `POST /fichas/{id}/reavaliar` separado. A tela teria dois caminhos de salvamento conforme o estado.

### D2. Ajuste opcional no próprio PATCH

O PATCH ganha os inputs opcionais `prioridade_ajuste` e `justificativa_ajuste`. Quando vêm, são aplicados depois do recálculo, com as mesmas validações e a auditoria `PRIORIDADE_ALTERADA` de `POST /fichas/{id}/prioridade`. A validação do ajuste é extraída para uma função `classificacao/aplicar_ajuste`, usada pelos dois endpoints, sem cópia.

- **Por quê:** como o recálculo descarta o ajuste anterior, a ficha `AGUARDANDO` de criança ou gestante (sempre com cálculo bloqueado) seria recusada em toda edição, pela decisão "recusar sem cor". Com o ajuste na mesma operação, a edição fica possível.
- **Alternativa descartada:** manter o ajuste anterior na ficha `AGUARDANDO`. Isso contrariaria o requisito "Recálculo descarta o ajuste manual" e poderia manter uma cor que não reflete o novo quadro.

### D3. Reavaliação depois do recálculo

Para ficha `AGUARDANDO`, ainda na transação:

1. Se `prioridade_atual` ficou vazia, falha com `FICHA_SEM_PRIORIDADE` e as pendências de `avaliar_ficha`, desfazendo tudo.
2. `destino_da_ficha` calcula o destino com os dados já gravados.
3. A senha é recalculada pela D4.
4. `especialidade_sugerida_id`, `especialidade_atribuida_id`, `senha` e `senha_numero` são gravados.
5. A auditoria da operação passa a incluir `especialidade_id` e `senha` em `valor_anterior` e `valor_novo`, sem criar evento novo.

`chegada_em` e `status` não são tocados.

- **Por quê:** uma única transação impede ficha com cor nova e senha velha. Registrar destino e senha na auditoria existente mantém um registro por ação do usuário.

### D4. Regra da senha separada da reserva de número

`gerar_senha` continua reservando número. Uma função pura nova, `direcionamento/senha_reavaliada` (com blocos `test`), recebe a senha, o número, a especialidade e a cor atuais, além da cor e da especialidade novas, e devolve uma de três ações:

| Mudança | Ação |
|---|---|
| nada mudou | mantém a senha |
| só a cor | troca a letra, mantém sigla e número, sem tocar no contador |
| especialidade | chama `gerar_senha` para a nova especialidade |

A resposta do PATCH e do ajuste ganha `senha_alterada`, `senha_anterior` e `senha`.

- **Por quê:** a regra de três casos é testável sem banco, e a numeração continua num único lugar.

### D5. Fila sem a própria ficha

`destino_da_ficha` passa a excluir a própria ficha ao contar as fichas `AGUARDANDO` por candidata (`id != ficha_id`). Na confirmação isso não muda nada, porque a ficha ainda está em `EM_TRIAGEM`.

- **Por quê:** sem a exclusão, a especialidade atual teria sempre uma ficha a mais e perderia no 3º critério.

### D6. Tela

A ficha `AGUARDANDO` volta a usar os mesmos componentes de edição da triagem, sem "Confirmar e gerar senha", com a senha e a especialidade atuais no topo e "Reimprimir".

- **Ao salvar:** quando `senha_alterada` vem verdadeiro, aparece um aviso fixo do tipo "Senha alterada de A-CAR-001 para V-CAR-001 — o comprovante impresso deixou de valer", com "Reimprimir".
- **Pendência de cor:** quando a resposta for `FICHA_SEM_PRIORIDADE`, a tela mostra as pendências e abre o diálogo de ajuste existente, que envia o ajuste junto com as alterações ainda não salvas (D2).

## Riscos / Compromissos

- [`avaliar_ficha` e `destino_da_ficha` podem não enxergar, dentro da transação, os dados que o PATCH acabou de gravar] → verificar no Run & Debug, logo na primeira tarefa do Xano; se não enxergarem, passar os dados resultantes como input em vez de reler a ficha.
- [O número da especialidade anterior fica sem uso] → aceito; o número é só identificador, e reutilizá-lo poderia confundir quem tem o comprovante antigo.
- [O paciente fica com comprovante inválido] → o aviso fixo e o "Reimprimir" na tela; o painel público fica para `add-painel-publico`.
- [Confirmações e reavaliações simultâneas disputando o contador] → mesma limitação já aceita em `add-direcionamento-senha`; a operação sequencial é suportada.
- [Edição concorrente quando a chamada médica existir] → a precondição de estado é validada dentro da transação; a reconciliação fica para `add-fila-chamada-medico`.

## Plano de migração

1. Publicar a função `senha_reavaliada`, o ajuste extraído e as alterações de `destino_da_ficha`, do PATCH e do ajuste de prioridade na `v1` (`--dry-run` antes, push restrito, sem tabelas), e rodar os testes unitários das funções.
2. Publicar o frontend.

Rollback: restaurar as versões anteriores dos dois endpoints, que voltam a recusar `AGUARDANDO`. As fichas reavaliadas permanecem válidas (senha, especialidade e auditoria coerentes).

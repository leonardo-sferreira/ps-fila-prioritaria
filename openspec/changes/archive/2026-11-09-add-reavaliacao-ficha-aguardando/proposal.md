# Proposta: Reavaliação da ficha em AGUARDANDO (RF12)

| Campo | Valor |
|---|---|
| Change | `add-reavaliacao-ficha-aguardando` |
| Sprint e entrega | A definir pelo PO |
| Card no Trello | A criar (pendência RF12 registrada na validação do card #39 em 09/11/2026) |
| Depende de | `add-classificacao-prioridade` e `add-direcionamento-senha`, ambas arquivadas e publicadas |
| Situação | Proposta para revisão |
| Rastreabilidade formal | Documentação de Requisitos Rev. 2.1: RF12 (§12), na parte que `add-classificacao-prioridade` e `add-direcionamento-senha` deixaram para outra change; §6, §9 (2º item) e §14.2 para destino e senha |

## Why

Depois de "Confirmar e gerar senha", a ficha vai para `AGUARDANDO` e passa a ser só de leitura: `PATCH /fichas/{id}` e o ajuste de prioridade recusam qualquer ficha fora de `EM_TRIAGEM`. Se o paciente piora na sala de espera ou a Recepção percebe um sintoma ou sinal vital registrado errado, não há como corrigir. A cor e a especialidade da fila ficam erradas, mesmo com a classificação já sabendo recalcular. As duas changes anteriores deixaram explicitamente para outra change essa parte do RF12: refazer classificação, destino e senha da ficha que já está na fila e avisar para reimprimir o comprovante.

## What Changes

- **Edição em `AGUARDANDO`:** a Recepção/Triagem passa a poder alterar sintomas (do catálogo e digitados), observação, sinais vitais, gestação e o ajuste manual de prioridade da ficha em `AGUARDANDO`, pelos mesmos endpoints da triagem. `CHAMADO` e os estados finais continuam recusados.
- **Recálculo completo numa única operação:** classificação (pelas regras atuais, inclusive o descarte do ajuste anterior), destino pela regra da §14.2 e senha, tudo na mesma transação e com uma auditoria que registra também a especialidade e a senha anteriores e novas.
- **Sem ficha na fila sem cor:** se a edição deixar a ficha sem prioridade atual (cálculo bloqueado, criança ou gestante), o backend recusa e informa as pendências. Para não travar essas fichas, o mesmo `PATCH` pode trazer um ajuste manual com justificativa.
- **Senha:**
  - nada de cor ou especialidade mudou: a senha continua a mesma;
  - só a cor mudou: a senha troca apenas a letra da cor e mantém o número (`A-CAR-001` vira `V-CAR-001`);
  - a especialidade mudou: a ficha recebe o próximo número do dia da nova especialidade (`A-CAR-001` vira `A-NEU-007`).
- **Posição na fila:** `chegada_em` não muda. A nova cor e a condição prioritária reposicionam a ficha pela regra normal da fila.
- **Aviso de reimpressão:** quando a senha muda, a tela mostra a senha anterior e a nova e oferece "Reimprimir". O comprovante já usa a senha atual da ficha.
- **Tela:** a ficha `AGUARDANDO` deixa o modo leitura e passa a ter edição e "Salvar". Não tem "Confirmar e gerar senha".
- **Documentos:** `docs/domain-model.md` e `docs/project-overview.md` passam a registrar a reavaliação em `AGUARDANDO`.

### Fora do escopo

- Editar ficha `CHAMADO` ou finalizada.
- Redirecionamento pelo Administrador (`POST admin/redirecionar`) e o botão "Reavaliar direcionamento" sem mudança clínica.
- Cancelar ficha.
- Avisar o paciente ou o painel público da troca de senha (`add-painel-publico`), e a distribuição a Médico (`add-fila-chamada-medico`).
- Mudar a regra de recálculo da classificação, o formato da senha ou o comprovante.

## Capabilities

### New Capabilities

_Nenhuma._

### Modified Capabilities

- `direcionamento`: reavaliação do destino da ficha `AGUARDANDO` depois de alteração clínica.
- `senha-comprovante`: troca de senha na reavaliação e aviso de reimpressão.
- `ficha-atendimento`: sinais vitais, gestação e sintomas digitados editáveis também em `AGUARDANDO`.
- `classificacao-prioridade`: ajuste manual também em `AGUARDANDO`, inclusive na mesma operação da alteração clínica.

## Impact

- **Xano:** `PATCH /fichas/{id}` e `POST /fichas/{id}/prioridade` aceitam `AGUARDANDO` e reaproveitam `direcionamento/destino_da_ficha` e `direcionamento/gerar_senha`; `escolher_destino` passa a não contar a própria ficha na fila. Nenhuma tabela é alterada; as colunas de especialidade, senha e número já existem.
- **Reflex:** `FichaState` e a tela da ficha passam a editar `AGUARDANDO` e a mostrar o aviso de reimpressão.
- **Testes:** testes do Xano para senha e destino na reavaliação; testes de estado do Reflex; roteiro manual.
- **Operação:** a senha impressa pode deixar de valer; a Recepção precisa entregar o novo comprovante ao paciente.

## Perguntas em aberto

- [ ] O texto formal do RF12 (Rev. 2.1, §12) não está no repositório. A proposta segue o que as changes anteriores registraram ("refazer destino e senha [...], troca de senha e aviso de reimpressão") e as decisões do usuário de 09/11/2026. O PO precisa confirmar que não há outro comportamento exigido.
- [ ] O card e a sprint ainda precisam ser criados ou vinculados pelo PO no Trello.

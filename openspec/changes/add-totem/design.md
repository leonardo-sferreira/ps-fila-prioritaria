# Design da emissão de tickets no Totem

## Contexto

Ver `proposal.md` e `specs/totem/spec.md`. A fila e as ações de Recepção/Triagem pertencem a futura change própria; esta change é dona da emissão e da experiência pública.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Emitir identificador diário único, persistente e impessoal.
- Não expor segredo de dispositivo no navegador.
- Usar o fuso oficial `America/Sao_Paulo`.

**Fora dos objetivos:**
- Identificação do paciente, chamada/rechamada ou encerramento do ticket.
- Escolha de especialidade, triagem clínica, senha de atendimento ou painel público.
- Integração com impressora ou hardware físico nesta change.

## Decisões

### D1. Xano como autoridade da numeração e persistência
O backend cria o ticket e atribui o próximo número da data operacional, com proteção contra colisão entre emissões simultâneas. A data operacional é calculada em `America/Sao_Paulo`, não por relógio local do navegador.
- **Alternativa:** incrementar a sequência no cliente. Descartada porque reinício, concorrência e adulteração fariam a sequência não confiável.

### D2. Credencial do Totem mantida no servidor
A chamada pública ao endpoint de emissão usa uma credencial de dispositivo configurada como segredo no ambiente do Xano e encaminhada somente pelo servidor Reflex. O navegador não recebe nem armazena essa credencial. Falha de credencial não cria ticket.
- **Alternativa:** colocar chave no JavaScript/URL do navegador. Descartada porque seria visível a qualquer pessoa no equipamento.

### D3. Ticket operacional sem dados pessoais
O registro guarda somente número/data/horário/status e identificador operacional necessário à fila. Não recebe nome, CPF, paciente ou sintoma. A futura capacidade de operação da fila consome esse mesmo ticket e controla seus estados e chamadas; rechamada não emite outro ticket.
- **Alternativa:** gerar outro ticket ao rechamar. Descartada porque quebraria identidade, ordem e histórico da fila.

### D4. Experiência pública
A tela apresenta a escolha do tipo de ticket (D5), o código retornado pelo backend em destaque e instrução para aguardar a Recepção/Triagem. Não há login ou coleta de dados identificáveis.

### D5. Tipos de ticket e numeração por tipo (decisão do PO em 25/10/2026)
O Totem oferece três tipos: `PEDIATRICO` (prefixo `C`), `PREFERENCIAL` (prefixo `P`) e `NORMAL` (prefixo `N`). O tipo é autodeclarado, não é conferido nesta change e vale só para a fila pré-triagem. Cada tipo tem sequência diária própria no fuso `America/Sao_Paulo`; o backend devolve `tipo`, `numero` e o código formatado (ex.: `P-007`). A unicidade passa de `(data, numero)` para `(data, tipo, numero)`.
- **Esquema:** `ticket_pre_triagem` precisa do campo `tipo` (enum) e do novo índice único. Como mudança de esquema passa pelo PO, a tarefa 1.1 depende dessa alteração publicada antes da implementação.
- **Prefixos:** `C` (criança) evita colisão com `P` de Preferencial e com as letras de cor da senha pós-triagem.
- **Ordem de chamada:** Pediátrico antes de Preferencial e ciclo de 2 prioritários : 1 normal (parâmetro configurável, carregado por `add-base-compartilhada`). Esta change não implementa a ordem; ela pertence à futura change de operação da fila pré-triagem.
- **Alternativa:** sequência única para todos os tipos (`032` com rótulo de tipo). Descartada porque o PO pediu código diferente por tipo, e o prefixo facilita a chamada em voz e no painel.
- **Alternativa:** Pediátrico como fila separada. Descartada: o PO definiu o Pediátrico como prioridade maior dentro da mesma fila pré-triagem.

## Riscos / Trade-offs

- [Credencial de dispositivo compartilhada pode ser copiada] → Manter somente no servidor e permitir sua rotação operacional; a decisão de mitigação adicional deverá ser registrada se a threat model mudar.
- [Paciente escolhe tipo prioritário sem ter direito] → Aceito nesta change: o tipo só antecipa a triagem e não altera cor nem condição prioritária; a conferência, se desejada, fica para a change de operação da fila.
- [Falha de rede durante uma solicitação pode deixar incerto se o ticket foi criado] → Mostrar erro sem inventar retry que possa emitir tickets duplicados; política de idempotência precisa ser definida antes da implementação caso a API não consiga responder com segurança.

## Plano de migração

A criação/numeração do ticket passa a pertencer a esta change e a operação da fila a futura change própria. Compatibilidade ou migração de registros existentes deve ser verificada no workspace Xano durante a implementação, sem alterar schema físico nesta revisão documental.

## Questões em aberto

- Confirmar sprint, fatia do Trello e responsáveis na planning.
- PO publicar o campo `tipo` e o índice `(data, tipo, numero)` em `ticket_pre_triagem` antes da tarefa 1.1.
- PO registrar no Confluence os tipos de ticket e o ciclo da pré-triagem (divergência com o documento formal).

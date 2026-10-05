# Design da emissão de tickets no Totem

## Contexto

Ver `proposal.md` e `specs/totem/spec.md`. A fila e as ações de Recepção/Triagem ficam em `add-pacientes-pre-triagem`; esta change é dona da emissão e da experiência pública.

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
O registro guarda somente número/data/horário/status e identificador operacional necessário à fila. Não recebe nome, CPF, paciente ou sintoma. `add-pacientes-pre-triagem` consome esse mesmo ticket e controla seus estados e chamadas; rechamada não emite outro ticket.
- **Alternativa:** gerar outro ticket ao rechamar. Descartada porque quebraria identidade, ordem e histórico da fila.

### D4. Experiência pública
A tela apresenta um único comando de emissão, o número retornado pelo backend em destaque e instrução para aguardar a Recepção/Triagem. Não há login ou coleta de dados identificáveis.

## Riscos / Trade-offs

- [Credencial de dispositivo compartilhada pode ser copiada] → Manter somente no servidor e permitir sua rotação operacional; a decisão de mitigação adicional deverá ser registrada se a threat model mudar.
- [Falha de rede durante uma solicitação pode deixar incerto se o ticket foi criado] → Mostrar erro sem inventar retry que possa emitir tickets duplicados; política de idempotência precisa ser definida antes da implementação caso a API não consiga responder com segurança.

## Plano de migração

A criação/numeração do ticket passa a pertencer a esta change e a operação da fila a `add-pacientes-pre-triagem`. Compatibilidade ou migração de registros existentes deve ser verificada no workspace Xano durante a implementação, sem alterar schema físico nesta revisão documental.

## Questões em aberto

- Confirmar sprint, fatia do Trello e responsáveis na planning.

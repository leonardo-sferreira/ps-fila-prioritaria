# Design: expiração automática após 24 horas

## Contexto

`ficha_atendimento` tem `chegada_em` e `status`; `DESISTENCIA` já é um estado final. `ticket_pre_triagem` tem `emitido_em` e `status`; `DESISTENCIA` também já existe.

A função `registrar_alteracao` exige um usuário ativo, porque foi feita para operações autenticadas. `historico_alteracao.usuario_id`, porém, aceita vazio.

## Decisões

### D1. Tarefa agendada + função testável
`task "expirar_registros"` roda a cada 3600 s e só chama `function "manutencao/expirar_registros"`. A função pode ser rodada à mão pelo CLI (`xano function run`), como o reparo de especialidade. O teste do prazo fica numa função pura, `manutencao/expirou`, com testes inline de valor-limite. Os testes do Xano neste projeto não usam o banco, e testar a `expirar_registros` alteraria dados reais.

- **Alternativa recusada:** expirar "sob demanda" ao consultar as filas. Espalha a regra por vários endpoints e não limpa nada se ninguém abrir a tela.

### D2. Corte por horário
`limite = now - HORAS_EXPIRACAO horas`.
- Fichas: `status in [EM_TRIAGEM, AGUARDANDO, CHAMADO] && chegada_em < limite`.
- Tickets: `status in [AGUARDANDO, CHAMADO] && emitido_em < limite`.

Exatamente 24 h ainda não expira; passou disso, expira. Quando `HORAS_EXPIRACAO` falta ou não é um inteiro positivo, a função não altera nada e devolve o motivo, como as outras regras com parâmetro.

### D3. Encerramento e auditoria na mesma transação
Para cada registro, dentro de `db.transaction`:
- `db.patch` com `status: "DESISTENCIA"`;
- `db.add historico_alteracao` com `tipo_evento: "EXPIRACAO"`, `entidade`, `registro_id`, `valor_anterior: {status}`, `valor_novo: {status: "DESISTENCIA"}`, `justificativa` e `usuario_id` vazio.

A função não usa `registrar_alteracao`, porque não há usuário. Ela não altera o ticket ligado à ficha nem a ficha ligada ao ticket: cada um expira pela sua própria data.

### D4. Parâmetro
`HORAS_EXPIRACAO = 24` entra em `inicializar_parametros_fila`, que já cria os parâmetros da fila sem sobrescrever os existentes. A tarefa também chama essa inicialização antes da primeira execução, para não depender de alguém ter usado a fila.

### D5. Resposta da função
`{horas_expiracao, fichas_expiradas: [ids], tickets_expirados: [ids], motivo}`, para o roteiro manual e o log da tarefa (`debug.log`). `motivo` só vem preenchido quando o parâmetro é inválido.

## Riscos

- Expirar um atendimento real que demorou mais de 24 h. Mitigação: o prazo é configurável, o histórico guarda o estado anterior e o paciente pode abrir nova ficha.
- A tarefa roda no fuso do servidor, mas a comparação usa timestamps absolutos, então o fuso não interfere.

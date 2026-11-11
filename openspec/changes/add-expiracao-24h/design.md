# Design: dispensa de fichas e tickets parados há mais de 24 horas

## Contexto

`ficha_atendimento` tem `chegada_em` e `status`, e `ticket_pre_triagem` tem `emitido_em` e `status`. Nas duas, `DESISTENCIA` já é um estado final, então nenhuma tabela muda.

O primeiro desenho usava uma tarefa agendada, mas o push foi recusado pelo Xano ("Please upgrade to access tasks"), porque o workspace está no plano gratuito. Por decisão do PO, a dispensa passou a ser uma ação do Administrador.

## Decisões

### D1. Ação do Administrador, com prévia
- `GET expiracao` devolve o que está parado, sem alterar nada.
- `POST expiracao` encerra tudo o que está parado no momento da chamada.

Os dois validam o perfil `ADMINISTRADOR` com `auth/verificar_acesso`. Ficam no grupo Triagem porque o Reflex já tem a URL desse grupo; o grupo Cadastros não tem URL configurada.

O POST recalcula a lista no servidor, em vez de receber IDs da tela. Assim, não encerra algo que mudou entre a prévia e o clique.

- **Alternativa recusada:** tarefa agendada, que exige plano pago.
- **Alternativa recusada:** expirar "sob demanda" ao consultar as filas. Espalha a regra por vários endpoints, e o PO preferiu a ação explícita.

### D2. Prazo numa função pura
`manutencao/expirou(horario, agora, horas)` diz se `horario < agora - horas × 3600000`, com testes inline de valor-limite:
- exatamente no prazo, ainda não expirou;
- horário vazio nunca expira;
- prazo que não seja positivo nunca expira.

Os testes do Xano neste projeto não usam o banco. Por isso, a regra testável fica separada da função que consulta e grava.

### D3. Prévia e aplicação na mesma função
`manutencao/expirar_registros(aplicar, usuario_id)` consulta as fichas `EM_TRIAGEM`/`AGUARDANDO`/`CHAMADO` e os tickets `AGUARDANDO`/`CHAMADO`, separa os expirados com `expirou` e devolve a lista.

Com `aplicar`, cada item, dentro de `db.transaction`:
- recebe `db.patch` com `status: "DESISTENCIA"`;
- é registrado com `registrar_alteracao`, com `tipo_evento: "EXPIRACAO"`, o estado anterior, a justificativa e o Administrador como usuário.

O ticket não tem `tentativas` alterado. A dispensa de uma ficha não mexe no ticket ligado a ela, porque cada um expira pela sua própria data.

### D4. Parâmetro
`HORAS_EXPIRACAO = 24` entra em `inicializar_parametros_fila`, que cria os padrões sem sobrescrever os existentes. Os dois endpoints chamam essa inicialização antes de ler o parâmetro. Com o parâmetro inválido, nada é alterado e a resposta traz `motivo`.

### D5. Resposta
`{horas_expiracao, aplicado, fichas: [{id, senha, status, chegada_em}], tickets: [{id, tipo, numero, status, emitido_em}], motivo}`.

Não há nome nem CPF: o Administrador decide pelo tempo parado, não pelo paciente.

### D6. Tela
- O cartão "Fichas e tickets parados" carrega a prévia ao abrir `/admin`.
- Mostra os totais e as listas: senha ou ticket, situação, e chegada ou emissão no horário de Brasília.
- "Dispensar todos" abre uma confirmação: "Encerrar N fichas e M tickets como desistência?".
- Depois da dispensa, o cartão mostra quantos itens foram encerrados e recarrega a prévia.
- Com a lista vazia, o botão fica desabilitado.

## Riscos

- **Dispensar um atendimento real que demorou mais de 24 h.** Mitigações:
  - a prévia mostra cada item antes da confirmação;
  - o prazo é configurável;
  - o histórico guarda o estado anterior e quem dispensou.

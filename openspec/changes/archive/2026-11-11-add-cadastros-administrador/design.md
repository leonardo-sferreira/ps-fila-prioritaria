# Design: cadastros do Administrador

## Contexto

Já existem as tabelas abaixo, e a fila médica (PR #39) as lê:

| Tabela | Campos |
|---|---|
| `especialidade` | `nome`, `nome_normalizado` único, `sigla` única, `ativo` |
| `sintoma` | `grupo`, `pontuacao` 1–3, `ativo` |
| `sintoma_especialidade` | `ordem` |
| `medico` | `usuario_id`, `registro_profissional` (CRM), `ativo` |
| `medico_especialidade` | — |
| `disponibilidade_medico` | `inicio`, `fim`, `encerrado_em` |
| `parametro` | `chave`, `valor`, `tipo` |
| `faixa_sinal_vital` | — |
| `historico_alteracao` | — |

As funções `registrar_alteracao` e `auth/verificar_acesso` também já existem. O grupo **Cadastros** do Xano já tem `GET`/`POST especialidades` e `PATCH parametros/{chave}`.

## Decisões

### D1. Grupo Cadastros e permissão
Todos os endpoints novos ficam no grupo Cadastros, com `auth = "usuario"` e `verificar_acesso(["ADMINISTRADOR"])`. A exceção é `GET medicos/me/disponibilidade`, que valida `MEDICO` e só devolve os plantões do próprio médico. O Reflex ganha a variável `XANO_CADASTROS_API_URL`.

### D2. Escritas em transação, com auditoria
Toda escrita fica dentro de `db.transaction` e chama `registrar_alteracao` com o Administrador, o estado anterior e o novo. Exemplos: `ESPECIALIDADE_CRIADA`, `MEDICO_DESATIVADO`, `PLANTAO_REMOVIDO`.

Nada é excluído fisicamente. A única exceção é o plantão que ainda não começou: o Administrador apenas desfaz o que registrou por engano.

### D3. Médico e Recepção/Triagem criam o login junto
`POST medicos` e `POST recepcao` recebem nome, e-mail e senha inicial (mínimo de 8 caracteres) e criam o `usuario` (perfil `MEDICO` ou `RECEPCAO_TRIAGEM`) e o cadastro na mesma transação. O e-mail é único, sem diferenciar caixa.

A edição altera nome e e-mail no usuário e os demais dados no cadastro. A senha não é editada aqui: o profissional usa "Esqueci minha senha".

**Desativar:**
- o cadastro e o login ficam inativos juntos (`usuario.ativo = false`);
- a próxima requisição do profissional é recusada por `verificar_acesso`;
- um médico com ficha `CHAMADO` pendente não pode ser desativado (`MEDICO_COM_FICHA_CHAMADA`).

### D4. Especialidades próprias e sala do médico
- **Especialidades:** `especialidade_ids` é a lista completa, com ao menos uma especialidade ativa. A gravação apaga e recria os vínculos em `medico_especialidade`, já que vínculo não tem histórico próprio.
- **Sala:** `sala_id` é opcional e só aceita sala ativa. Desativar uma sala desfaz o vínculo com os médicos que a tinham como sala atual.

### D5. Recepção/Triagem e Sala: tabelas novas
| Tabela | Campos |
|---|---|
| `recepcao_triagem` | `usuario_id` único, `cpf` único (11 dígitos, validado por `pacientes/normalizar_cpf`), `especialidade_referencia_id` opcional, `ativo` |
| `sala` | `nome`, `nome_normalizado` único, `descricao` opcional, `ativo` |

Além disso, `medico` ganha `sala_id` (nullable).

### D6. Plantões
A tela envia `data` (AAAA-MM-DD), `hora_inicio` e `hora_fim` (HH:MM). A função pura `cadastros/periodo_plantao` converte para `inicio` e `fim` no fuso America/Sao_Paulo:
- se `hora_fim` ≤ `hora_inicio`, o fim é no dia seguinte (plantão noturno, ex.: 19:00–07:00);
- a duração máxima é de 24 h.

**Validações:**
- o médico precisa estar ativo;
- não pode haver sobreposição com outro período do mesmo médico (`novo.inicio < existente.fim E novo.fim > existente.inicio`; intervalos semiabertos);
- alterar ou remover só vale para período **não iniciado**. Período em andamento só pode ter o `fim` alterado, para estender ou antecipar; o encerramento pelo próprio médico é da fila médica.

`GET disponibilidade?data=` devolve os períodos que tocam o dia, com nome do médico, sala e especialidades.

### D7. Parâmetros com limites centralizados
A função pura `cadastros/regra_parametro(chave)` devolve `{editavel, minimo, maximo, rotulo, unidade}` para cada chave conhecida. As chaves internas (`POSICAO_CICLO_PRE_TRIAGEM`) e desconhecidas não são editáveis.

O `PATCH parametros/{chave}` passa a usar essa função para todas as chaves e mantém o comportamento da fila médica: alterar o ciclo reinicia a posição.

**Coerência:**
- `IDADE_MAXIMA_CRIANCA` < `IDADE_MINIMA_TABELA_ADULTA` ≤ `IDADE_MINIMA_IDOSO`;
- `LIMIAR_AMARELA` < `LIMIAR_VERMELHA`;
- `ESPECIALIDADE_PADRAO` precisa ser uma especialidade ativa.

### D8. Faixas sem sobreposição
`PATCH faixas/{id}` altera `minimo`, `maximo` e `pontos` (0–3). A função pura `cadastros/faixa_sobrepoe` recusa sobreposição com outra faixa do mesmo parâmetro e da mesma condição de gravidade. Um limite vazio representa um extremo aberto. As faixas não são criadas nem apagadas pela tela: mudam os limites e os pontos das 30 existentes.

### D9. Telas
- **Menu do Administrador:** Início · Médicos · Recepção · Especialidades · Sintomas · Salas · Plantões · Parâmetros.
- **Telas de cadastro:** cada uma tem a lista com filtro de situação ("Ativos/Inativos/Todos"), busca, botão "Novo" e edição num diálogo. Um componente `tabela_cadastro`, reaproveitado, monta lista, filtro e diálogo.
- **Plantões:** seletor de dia, lista do dia e formulário (médico, data, início, fim).
- **Parâmetros:** formulário por parâmetro e tabela de faixas por sinal vital.
- **Erros:** as mensagens da API aparecem no diálogo.

### D10. Testes
- **Xano:** testes inline nas funções puras (`periodo_plantao`, `regra_parametro`, `faixa_sobrepoe`).
- **Reflex:** testes de estado com a API simulada, um arquivo por tela.
- **Roteiro manual ponta a ponta:** criar um médico, dar plantão, ficar disponível e chamar.

## Riscos

- Desativar especialidade com fichas na fila: recusado com `ESPECIALIDADE_COM_FICHAS` enquanto houver fichas `AGUARDANDO` ou `CHAMADO`; a `ESPECIALIDADE_PADRAO` não pode ser desativada.
- Senha inicial conhecida pelo Administrador: mitigada pelo "Esqueci minha senha"; a troca obrigatória no primeiro acesso fica fora do escopo.

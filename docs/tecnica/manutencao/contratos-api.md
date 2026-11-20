# Contratos de API (Xano)

> Arquivo gerado por `python scripts/gerar_docs.py`. Não edite à mão: altere o código e gere de novo.

Todos os endpoints ficam no Xano, divididos em grupos de API. Cada grupo tem uma URL base própria, configurada no `frontend/.env` (coluna "Variável"). As chamadas usam JSON; endpoints com **login** exigem o cabeçalho `Authorization: Bearer <token>` (o token vem de `POST /auth/login/verificar`). Erros seguem o formato do Xano: `{"code": "ERROR_CODE_...", "message": "..."}` com status 400 (entrada), 401 (sessão), 403 (perfil), 404 (não encontrado) ou 429 (limite de requisições do plano).

| Grupo | Variável da URL base | Endpoints |
|---|---|---|
| Autenticacao | `XANO_AUTH_API_URL` | 10 |
| Cadastros | `XANO_CADASTROS_API_URL` | 38 |
| Fila | `XANO_FILA_API_URL` | 6 |
| Pacientes | `XANO_API_URL` | 3 |
| Triagem | `XANO_TRIAGEM_API_URL` | 14 |

## Grupo Autenticacao

### `POST /auth/login`

Primeira etapa do login: confere e-mail, senha e usuário ativo e envia o código de verificação por e-mail.

- **Acesso:** público (sem login)
- **Código:** `backend/xano/api/autenticacao/auth_login_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `email` | text | não | filtros: trim, lower |
  | `senha` | text | não |  |
- **Resposta (200):**

  ```
  {
    codigo_enviado     : true
    mensagem           : "Enviamos um código de 6 dígitos para o seu e-mail."
    reenvio_em_segundos: $env.CODIGO_REENVIO_SEGUNDOS|to_int
  }
  ```
- **Mensagens de erro:** `E-mail ou senha inválidos`; `Informe a senha.`; `Informe o e-mail.`; `Usuário inativo. Procure o administrador.`

### `POST /auth/login/reenviar`

Reenvia o código do login sem pedir a senha de novo, dentro da validade do primeiro passo e após o intervalo de reenvio.

- **Acesso:** público (sem login)
- **Código:** `backend/xano/api/autenticacao/auth_login_reenviar_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `email` | text | não | filtros: trim, lower |
- **Resposta (200):**

  ```
  {
    codigo_enviado     : true
    mensagem           : "Enviamos um novo código para o seu e-mail."
    reenvio_em_segundos: $intervalo
  }
  ```
- **Mensagens de erro:** `Aguarde `; `Não foi possível reenviar o código. Faça login novamente.`; `Variáveis de ambiente CODIGO_TTL_SEGUNDOS e CODIGO_REENVIO_SEGUNDOS não configuradas.`

### `POST /auth/login/verificar`

Segunda etapa do login: confere o código enviado por e-mail, registra a sessão e devolve token, nome e perfil.

- **Acesso:** público (sem login)
- **Código:** `backend/xano/api/autenticacao/auth_login_verificar_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `email` | text | não | filtros: trim, lower |
  | `codigo` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  {
    token : $token
    nome  : $usuario.nome
    perfil: $usuario.perfil
  }
  ```
- **Mensagens de erro:** `Código inválido ou expirado`; `Informe o código.`; `Informe o e-mail.`; `Usuário inativo. Procure o administrador.`; `Variável de ambiente TOKEN_TTL_SEGUNDOS não configurada.`

### `POST /auth/logout`

Encerra a sessão aberta mais recente do usuário do token.

- **Acesso:** login
- **Código:** `backend/xano/api/autenticacao/auth_logout_post.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  {
    encerrada: true
  }
  ```
- **Mensagens de erro:** `Sessão inválida. Faça login novamente.`

### `GET /auth/me`

Devolve o usuário do token, recarregado do banco (usado pelo Reflex para proteger as rotas).

- **Acesso:** login: RECEPCAO_TRIAGEM, MEDICO, ADMINISTRADOR
- **Código:** `backend/xano/api/autenticacao/auth_me_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  {
    id                  : $usuario.id
    nome                : $usuario.nome
    email               : $usuario.email
    perfil              : $usuario.perfil
    inatividade_segundos: $env.INATIVIDADE_SEGUNDOS|to_int
    status_operacional  : ($sessao_atual == null) ? null : $sessao_atual.status_operacional
  }
  ```

### `POST /auth/senha/redefinir`

Troca a senha com o código de redefinição, usa o código e encerra as sessões abertas do usuário.

- **Acesso:** público (sem login)
- **Código:** `backend/xano/api/autenticacao/auth_senha_redefinir_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `email` | text | não | filtros: trim, lower |
  | `codigo` | text | não | filtros: trim |
  | `nova_senha` | text | não |  |
- **Resposta (200):**

  ```
  {
    senha_redefinida: true
  }
  ```
- **Mensagens de erro:** `A nova senha deve ter pelo menos 8 caracteres.`; `Código inválido ou expirado`; `Usuário inativo. Procure o administrador.`

### `POST /auth/senha/solicitar`

Esqueci minha senha: envia o código de redefinição a usuário ativo, com a mesma resposta para qualquer e-mail.

- **Acesso:** público (sem login)
- **Código:** `backend/xano/api/autenticacao/auth_senha_solicitar_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `email` | text | não | filtros: trim, lower |
- **Resposta (200):**

  ```
  {
    mensagem           : "Se o e-mail estiver cadastrado, enviamos um código"
    reenvio_em_segundos: $intervalo
  }
  ```
- **Mensagens de erro:** `Aguarde `; `Informe o e-mail.`; `Variável de ambiente CODIGO_REENVIO_SEGUNDOS não configurada.`

### `POST /auth/senha/verificar`

Confere o código de redefinição sem usá-lo, para liberar a tela da nova senha; o uso definitivo é em auth/senha/redefinir.

- **Acesso:** público (sem login)
- **Código:** `backend/xano/api/autenticacao/auth_senha_verificar_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `email` | text | não | filtros: trim, lower |
  | `codigo` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  {
    codigo_valido: true
  }
  ```
- **Mensagens de erro:** `Código inválido ou expirado`; `Informe o código.`

### `GET /me/status`

Consulta somente o status da própria sessão ativa; não altera sessão ou plantão.

- **Acesso:** login: MEDICO, RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/autenticacao/me_status_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  {
    status: $sessao.status_operacional
  }
  ```
- **Mensagens de erro:** `Sessão expirada. Faça login novamente.`

### `PATCH /me/status`

- **Acesso:** login: MEDICO, RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/autenticacao/me_status_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `status` | enum | sim |  |
- **Resposta (200):**

  ```
  {
    status: $atualizada.status_operacional
  }
  ```
- **Mensagens de erro:** `Médico inativo.`; `Não há plantão vigente para ficar disponível.`; `Sessão expirada. Faça login novamente.`


## Grupo Cadastros

### `GET /admin/auditoria`

Auditoria consolidada para o Administrador, só leitura (add-acompanhamento-administrador, D2, tarefa 2.3). Junta historico_alteracao (alterações), chamada (CHAMADA/COMPARECIMENTO/DESISTENCIA) e sessao (LOGIN/LOGOUT) num formato único, ordenado do mais recente para o mais antigo e paginado em 50. Período obrigatório no backend: sem datas, vale o dia de hoje (America/Sao_Paulo); no máximo 31 dias. Registro sem usuário é da carga automática ("Sistema").

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/admin_auditoria_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `data_inicio` | text | não | filtros: trim |
  | `data_fim` | text | não | filtros: trim |
  | `origem` | text | não | filtros: trim, upper |
  | `usuario_id` | int | não |  |
  | `pagina` | int | não |  |
- **Resposta (200):**

  ```
  {
    itens: $pagina_itens, total: $total, pagina: $pagina, por_pagina: 50, de: $dia_inicio, ate: $dia_fim
  }
  ```
- **Mensagens de erro:** `A data final deve ser igual ou posterior à inicial.`; `Consulte no máximo 31 dias por vez.`; `Data inválida.`

### `GET /admin/equipe`

Equipe com sessão ativa, para o dashboard do Administrador (add-acompanhamento-administrador, D6, tarefa 2.2). Sessão ativa: sem logout e ainda não expirada; vale a mais recente de cada usuário. Sem e-mail nem CPF.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/admin_equipe_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `perfil` | text | não | filtros: trim, upper |
- **Resposta (200):**

  ```
  {
    equipe: (($input.perfil ?? "") == "") ? $equipe : ($equipe|filter:($$.perfil == $input.perfil)), agora: now
  }
  ```

### `GET /admin/fichas/{ficha_id}`

Detalhe de uma ficha para o Administrador, só leitura (add-acompanhamento-administrador, tarefa 2.2). Triagem (sinais vitais, sintomas, escore e cor), especialidades sugerida e atribuída, senhas que a ficha teve, chamadas e histórico de alterações. Sem nome nem CPF do paciente.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/admin_fichas_id_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `ficha_id` | int | sim |  |
- **Resposta (200):**

  ```
  {
    id                       : $ficha.id
    status                   : $ficha.status
    senha                    : $ficha.senha
    senhas                   : $senhas
    chegada_em               : $ficha.chegada_em
    fila_em                  : $ficha.fila_em
    finalizada_em            : $ficha.finalizada_em
    cor                      : $ficha.prioridade_atual
    cor_calculada            : $ficha.prioridade_calculada
    justificativa_ajuste     : $ficha.justificativa_ajuste
    condicao_prioritaria     : $ficha.condicao_prioritaria
    escore                   : $ficha.escore_risco
    gestante                 : $ficha.gestante
    sinais                   : {pa_sistolica: $ficha.pa_sistolica, fc: $ficha.fc, fr: $ficha.fr, temperatura: $ficha.temperatura, spo2: $ficha.spo2, glicemia: $ficha.glicemia}
    observacao               : $ficha.observacao
    sintomas                 : $sintomas
    especialidade_sugerida   : ($sugerida == null) ? null : $sugerida.nome
    especialidade_atribuida  : ($atribuida == null) ? null : $atribuida.nome
    medico                   : ($quem_atual == null) ? null : $quem_atual.nome
    tentativas_chamada       : $ficha.tentativas_chamada
    oportunidade             : $ficha.oportunidade
    chamadas                 : $chamadas
    historico                : $historico
  }
  ```
- **Mensagens de erro:** `Ficha não encontrada.`

### `GET /admin/fila-geral`

Fila geral do plantão para o Administrador, só leitura (add-acompanhamento-administrador, D3, tarefa 2.1). Fichas EM_TRIAGEM, AGUARDANDO e CHAMADO de todas as especialidades. As AGUARDANDO recebem a posição prevista pela mesma regra da chamada (fila/prever_fila, até a 20ª de cada especialidade; depois disso, posicao = null). Sem nome nem CPF do paciente. A ordenação da tela fica no Reflex (chamadas, depois aguardando por posição).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/admin_fila_geral_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `especialidade_id` | int | não |  |
  | `cor` | text | não | filtros: trim, upper |
  | `status` | text | não | filtros: trim, upper |
- **Resposta (200):**

  ```
  $filtro_status
  ```

### `GET /disponibilidade`

Plantões que tocam um dia (America/Sao_Paulo), com médico, sala e especialidades (add-cadastros-administrador, D6).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/disponibilidade_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `data` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  {
    data: $dia, agora: $agora, plantoes: $lista
  }
  ```
- **Mensagens de erro:** `Data inválida.`

### `POST /disponibilidade`

Registra um plantão de médico ativo, sem sobreposição (add-cadastros-administrador, D6). Com data_fim, registra a escala 12x36 até essa data: um plantão a cada 48 h, tudo ou nada (add-plantao-12x36).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/disponibilidade_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `medico_id` | int | sim |  |
  | `data` | text | sim | filtros: trim |
  | `hora_inicio` | text | sim | filtros: trim |
  | `hora_fim` | text | sim | filtros: trim |
  | `data_fim` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  {
    id: $primeiro.id, medico_id: $primeiro.medico_id, inicio: $primeiro.inicio, fim: $primeiro.fim, criados: $criados|count
  }
  ```
- **Mensagens de erro:** `A escala pode ter no máximo 90 dias.`; `Data final inválida ou anterior à data inicial.`; `Data ou horário inválido.`; `Médico inexistente ou inativo.`; `PLANTAO_SOBREPOSTO`

### `DELETE /disponibilidade/{disponibilidade_id}`

Remove um plantão que ainda não começou: desfaz um registro feito por engano (add-cadastros-administrador, D2/D6). Plantão iniciado nunca é removido.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/disponibilidade_id_delete.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `disponibilidade_id` | int | sim |  |
- **Resposta (200):**

  ```
  {
    id: $anterior.id, removido: true
  }
  ```
- **Mensagens de erro:** `PLANTAO_INICIADO`; `Plantão não encontrado.`

### `PATCH /disponibilidade/{disponibilidade_id}`

Altera um plantão (add-cadastros-administrador, D6). Não iniciado: data e horários livres. Já iniciado: o início não muda; só o fim pode ser estendido ou antecipado, desde que fique no futuro.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/disponibilidade_id_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `disponibilidade_id` | int | sim |  |
  | `data` | text | sim | filtros: trim |
  | `hora_inicio` | text | sim | filtros: trim |
  | `hora_fim` | text | sim | filtros: trim |
- **Resposta (200):**

  ```
  {
    id: $plantao.id, medico_id: $plantao.medico_id, inicio: $plantao.inicio, fim: $plantao.fim
  }
  ```
- **Mensagens de erro:** `Data ou horário inválido.`; `PLANTAO_INICIADO`; `PLANTAO_SOBREPOSTO`; `Plantão já encerrado pelo médico.`; `Plantão não encontrado.`

### `GET /especialidades`

Lista especialidades; somente o Administrador consulta inativas e os dados de manutenção.

- **Acesso:** login: RECEPCAO_TRIAGEM, MEDICO, ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/especialidades_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `ativo` | bool | não |  |
- **Resposta (200):**

  ```
  $resultado
  ```
- **Mensagens de erro:** `Acesso negado para consultar especialidades inativas.`

### `POST /especialidades`

PREPARAÇÃO LOCAL — NÃO PUBLICAR antes da migração aprovada de especialidade. Dependência obrigatória: nome_normalizado textual, obrigatório/não nulo, calculado pelo servidor com lower(trim(nome)), com índice único não diferido. Preservar também o índice único de sigla. Ver design.md, Fatia 1B.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/especialidades_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `nome` | text | sim | filtros: trim |
  | `sigla` | text | sim | filtros: trim |
  | `descricao` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  $resultado
  ```
- **Mensagens de erro:** `A sigla deve ter exatamente 3 letras.`; `Informe o nome da especialidade.`; `Já existe especialidade com esta sigla.`; `Já existe especialidade com este nome.`; `Não foi possível cadastrar a especialidade.`

### `PATCH /especialidades/{especialidade_id}`

Edita nome e descrição da especialidade. A sigla não muda depois de criada: compõe as senhas já emitidas (add-cadastros-administrador).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/especialidades_id_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `especialidade_id` | int | sim |  |
  | `nome` | text | sim | filtros: trim |
  | `descricao` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  {
    id: $especialidade.id, nome: $especialidade.nome, sigla: $especialidade.sigla, descricao: $especialidade.descricao, ativo: $especialidade.ativo
  }
  ```
- **Mensagens de erro:** `Especialidade não encontrada.`; `Informe o nome da especialidade.`; `Já existe especialidade com este nome.`

### `PATCH /especialidades/{especialidade_id}/ativo`

Ativa ou desativa a especialidade. Não desativa a especialidade padrão nem a que tem fichas AGUARDANDO/CHAMADO (add-cadastros-administrador).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/especialidades_id_ativo_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `especialidade_id` | int | sim |  |
  | `ativo` | bool | sim |  |
- **Resposta (200):**

  ```
  {
    id: $especialidade.id, ativo: $especialidade.ativo
  }
  ```
- **Mensagens de erro:** `ESPECIALIDADE_COM_FICHAS`; `Especialidade não encontrada.`; `Esta é a especialidade padrão: troque o parâmetro antes de desativá-la.`

### `GET /faixas`

Faixas de pontuação dos sinais vitais, por parâmetro e limite inferior (add-cadastros-administrador, D8).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/faixas_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  $faixas|map:{id: $$.id, parametro: $$.parametro, minimo: $$.minimo, maximo: $$.maximo, pontos: $$.pontos, condicao_gravidade: $$.condicao_gravidade}
  ```

### `PATCH /faixas/{faixa_id}`

Altera mínimo, máximo e pontos (0–3) de uma faixa, sem sobrepor outra do mesmo parâmetro e condição (add-cadastros-administrador, D8). Limite vazio = extremo aberto. Faixas não são criadas nem apagadas aqui.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/faixas_id_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `faixa_id` | int | sim |  |
  | `minimo` | decimal | não |  |
  | `maximo` | decimal | não |  |
  | `pontos` | int | sim |  |
- **Resposta (200):**

  ```
  {
    id: $faixa.id, parametro: $faixa.parametro, minimo: $faixa.minimo, maximo: $faixa.maximo, pontos: $faixa.pontos, condicao_gravidade: $faixa.condicao_gravidade
  }
  ```
- **Mensagens de erro:** `FAIXA_SOBREPOSTA`; `Faixa não encontrada.`; `Informe ao menos um dos limites.`; `O mínimo deve ser menor ou igual ao máximo.`; `Os pontos devem ficar entre 0 e 3.`

### `GET /medicos`

Médicos com login, CRM, especialidades próprias e sala atual (add-cadastros-administrador).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/medicos_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  $lista|sort:"nome":"itext":true
  ```

### `POST /medicos`

Cria o login (perfil MEDICO) e o médico juntos, com especialidades próprias e sala opcional (add-cadastros-administrador, D3 e D4). A senha nunca vai para a auditoria nem para a resposta.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/medicos_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `nome` | text | sim | filtros: trim |
  | `email` | text | sim | filtros: trim, lower |
  | `senha` | text | sim |  |
  | `crm` | text | sim | filtros: trim |
  | `especialidade_ids` | json | sim |  |
  | `sala_id` | int | não |  |
- **Resposta (200):**

  ```
  {
    id: $medico.id, usuario_id: $login.id, nome: $login.nome, email: $login.email, crm: $medico.registro_profissional, ativo: true, especialidade_ids: $proprias, sala_id: $sala_id
  }
  ```
- **Mensagens de erro:** `A senha inicial deve ter 8 ou mais caracteres.`; `Informe o CRM.`; `Informe o nome do médico.`

### `GET /medicos/me/disponibilidade`

"Meus plantões": o Médico vê os próprios períodos em andamento e futuros, sem alterar (add-cadastros-administrador, D1).

- **Acesso:** login: MEDICO
- **Código:** `backend/xano/api/cadastros/medicos_me_disponibilidade_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  {
    agora: $agora, plantoes: $periodos|map:{id: $$.id, inicio: $$.inicio, fim: $$.fim}
  }
  ```
- **Mensagens de erro:** `Cadastro de médico não encontrado.`

### `PATCH /medicos/{medico_id}`

Edita nome e e-mail (no login), CRM, especialidades próprias e sala do médico (add-cadastros-administrador). A senha não muda aqui: o médico usa "Esqueci minha senha".

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/medicos_id_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `medico_id` | int | sim |  |
  | `nome` | text | sim | filtros: trim |
  | `email` | text | sim | filtros: trim, lower |
  | `crm` | text | sim | filtros: trim |
  | `especialidade_ids` | json | sim |  |
  | `sala_id` | int | não |  |
- **Resposta (200):**

  ```
  {
    id: $medico.id, nome: $login.nome, email: $login.email, crm: $medico.registro_profissional, ativo: $medico.ativo, especialidade_ids: $proprias, sala_id: $sala_id
  }
  ```
- **Mensagens de erro:** `CADASTRO_DE_OUTRO_PERFIL`; `Informe o CRM.`; `Informe o nome do médico.`; `Médico não encontrado.`

### `PATCH /medicos/{medico_id}/ativo`

Ativa ou desativa o médico e o login dele juntos (add-cadastros-administrador, D3). Não desativa enquanto houver ficha CHAMADO pendente com o médico.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/medicos_id_ativo_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `medico_id` | int | sim |  |
  | `ativo` | bool | sim |  |
- **Resposta (200):**

  ```
  {
    id: $medico.id, ativo: $medico.ativo
  }
  ```
- **Mensagens de erro:** `CADASTRO_DE_OUTRO_PERFIL`; `MEDICO_COM_FICHA_CHAMADA`; `Médico não encontrado.`

### `GET /parametros`

Parâmetros com valor atual, rótulo, unidade e limites; só os editáveis vêm marcados (add-cadastros-administrador, D7).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/parametros_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  $lista
  ```

### `PATCH /parametros/{chave}`

Altera um parâmetro editável dentro dos limites de cadastros/regra_parametro (add-cadastros-administrador, D7). Coerência: criança < tabela adulta <= idoso; limiar Amarela < Vermelha; especialidade padrão ativa. A alteração das quantidades do ciclo da fila médica reinicia a posição de todas as especialidades (PR #39).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/parametros_chave_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `chave` | text | sim | filtros: trim |
  | `valor` | int | sim |  |
- **Resposta (200):**

  ```
  $resultado
  ```
- **Mensagens de erro:** `IDADES_INCOERENTES`; `LIMIARES_INCOERENTES`; `PARAMETRO_FORA_DOS_LIMITES`; `PARAMETRO_NAO_CONFIGURADO`; `PARAMETRO_NAO_EDITAVEL_AQUI`

### `GET /recepcao`

Pessoas da Recepção/Triagem com login, CPF e especialidade de referência (add-cadastros-administrador).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/recepcao_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  $lista|sort:"nome":"itext":true
  ```

### `POST /recepcao`

Cria o login (perfil RECEPCAO_TRIAGEM) e o cadastro juntos, com CPF válido e único (add-cadastros-administrador, D3 e D5). A senha nunca vai para a auditoria nem para a resposta.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/recepcao_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `nome` | text | sim | filtros: trim |
  | `email` | text | sim | filtros: trim, lower |
  | `senha` | text | sim |  |
  | `cpf` | text | sim | filtros: trim |
  | `especialidade_referencia_id` | int | não |  |
- **Resposta (200):**

  ```
  {
    id: $cadastro.id, usuario_id: $login.id, nome: $login.nome, email: $login.email, cpf: $cpf, especialidade_referencia_id: $referencia, ativo: true
  }
  ```
- **Mensagens de erro:** `A senha inicial deve ter 8 ou mais caracteres.`; `CPF já cadastrado.`; `Informe o nome.`

### `PATCH /recepcao/{recepcao_id}`

Edita nome e e-mail (no login), CPF e especialidade de referência da Recepção/Triagem (add-cadastros-administrador).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/recepcao_id_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `recepcao_id` | int | sim |  |
  | `nome` | text | sim | filtros: trim |
  | `email` | text | sim | filtros: trim, lower |
  | `cpf` | text | sim | filtros: trim |
  | `especialidade_referencia_id` | int | não |  |
- **Resposta (200):**

  ```
  {
    id: $cadastro.id, nome: $login.nome, email: $login.email, cpf: $cpf, especialidade_referencia_id: $referencia, ativo: $cadastro.ativo
  }
  ```
- **Mensagens de erro:** `CADASTRO_DE_OUTRO_PERFIL`; `CPF já cadastrado.`; `Cadastro não encontrado.`; `Informe o nome.`

### `PATCH /recepcao/{recepcao_id}/ativo`

Ativa ou desativa a pessoa da Recepção/Triagem e o login dela juntos (add-cadastros-administrador, D3).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/recepcao_id_ativo_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `recepcao_id` | int | sim |  |
  | `ativo` | bool | sim |  |
- **Resposta (200):**

  ```
  {
    id: $cadastro.id, ativo: $cadastro.ativo
  }
  ```
- **Mensagens de erro:** `CADASTRO_DE_OUTRO_PERFIL`; `Cadastro não encontrado.`

### `GET /salas`

Salas com os médicos que as têm como sala atual (add-cadastros-administrador).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/salas_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  $lista
  ```

### `POST /salas`

Cria sala com nome único (sem diferenciar maiúsculas) e descrição opcional (add-cadastros-administrador, D5).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/salas_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `nome` | text | sim | filtros: trim |
  | `descricao` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  {
    id: $sala.id, nome: $sala.nome, descricao: $sala.descricao, ativo: true, medicos: 0
  }
  ```
- **Mensagens de erro:** `Informe o nome da sala.`; `Já existe sala com este nome.`

### `PATCH /salas/{sala_id}`

Edita nome e descrição da sala (add-cadastros-administrador).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/salas_id_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `sala_id` | int | sim |  |
  | `nome` | text | sim | filtros: trim |
  | `descricao` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  {
    id: $sala.id, nome: $sala.nome, descricao: $sala.descricao, ativo: $sala.ativo
  }
  ```
- **Mensagens de erro:** `Informe o nome da sala.`; `Já existe sala com este nome.`; `Sala não encontrada.`

### `PATCH /salas/{sala_id}/ativo`

Ativa ou desativa a sala. Ao desativar, desfaz o vínculo dos médicos que a tinham como sala atual (add-cadastros-administrador, D4).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/salas_id_ativo_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `sala_id` | int | sim |  |
  | `ativo` | bool | sim |  |
- **Resposta (200):**

  ```
  {
    id: $sala.id, ativo: $sala.ativo, medicos_desvinculados: $desvinculados
  }
  ```
- **Mensagens de erro:** `Sala não encontrada.`

### `GET /sintomas`

Catálogo completo para o Administrador: ativos e inativos, com os destinos em ordem (add-cadastros-administrador). A triagem continua usando GET sintomas do grupo Triagem (só ativos).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/sintomas_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  $lista
  ```

### `POST /sintomas`

Cria sintoma do catálogo com pontuação 1–3 e destinos em ordem de preferência (add-cadastros-administrador).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/sintomas_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `nome` | text | sim | filtros: trim |
  | `descricao` | text | não | filtros: trim |
  | `grupo` | text | sim | filtros: trim, upper |
  | `pontuacao` | int | sim |  |
  | `especialidade_ids` | json | sim |  |
- **Resposta (200):**

  ```
  {
    id: $sintoma.id, nome: $sintoma.nome, ativo: true, especialidade_ids: $destinos
  }
  ```
- **Mensagens de erro:** `A pontuação deve ser 1, 2 ou 3.`; `Grupo de sintoma inválido.`; `Informe o nome do sintoma (3 ou mais caracteres).`; `Já existe sintoma com este nome.`

### `PATCH /sintomas/{sintoma_id}`

Edita sintoma e substitui os destinos (add-cadastros-administrador). Fichas antigas mantêm o sintoma.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/sintomas_id_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `sintoma_id` | int | sim |  |
  | `nome` | text | sim | filtros: trim |
  | `descricao` | text | não | filtros: trim |
  | `grupo` | text | sim | filtros: trim, upper |
  | `pontuacao` | int | sim |  |
  | `especialidade_ids` | json | sim |  |
- **Resposta (200):**

  ```
  {
    id: $sintoma.id, nome: $sintoma.nome, ativo: $sintoma.ativo, especialidade_ids: $destinos
  }
  ```
- **Mensagens de erro:** `A pontuação deve ser 1, 2 ou 3.`; `Grupo de sintoma inválido.`; `Informe o nome do sintoma (3 ou mais caracteres).`; `Já existe sintoma com este nome.`; `Sintoma não encontrado.`

### `PATCH /sintomas/{sintoma_id}/ativo`

Ativa ou desativa o sintoma. Inativo deixa de aparecer na triagem; fichas antigas continuam com ele (add-cadastros-administrador).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/sintomas_id_ativo_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `sintoma_id` | int | sim |  |
  | `ativo` | bool | sim |  |
- **Resposta (200):**

  ```
  {
    id: $sintoma.id, ativo: $sintoma.ativo
  }
  ```
- **Mensagens de erro:** `Sintoma não encontrado.`

### `GET /usuarios`

Todos os usuários com nome, e-mail, perfil e situação, sem senha (add-autenticacao-perfis, gestao-usuarios). Para médico e Recepção/Triagem traz também o cadastro (CRM, especialidades e sala; CPF e especialidade de referência), para a edição na própria tela de Usuários (revisão de 14/11/2026).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/usuarios_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  $lista
  ```

### `POST /usuarios`

Cria um usuário de qualquer perfil (add-autenticacao-perfis, D14; revisão de 14/11/2026): o Administrador cadastra Administradores, Médicos e Recepção/Triagem. Para Médico e Recepção/Triagem cria também o cadastro do perfil, na mesma transação, com os dados exigidos. A senha nunca vai para a auditoria nem para a resposta.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/usuarios_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `nome` | text | sim | filtros: trim |
  | `email` | text | sim | filtros: trim, lower |
  | `senha` | text | sim |  |
  | `perfil` | text | não | filtros: trim, upper |
  | `crm` | text | não | filtros: trim |
  | `especialidade_ids` | json | não |  |
  | `sala_id` | int | não |  |
  | `cpf` | text | não | filtros: trim |
  | `especialidade_referencia_id` | int | não |  |
- **Resposta (200):**

  ```
  {
    id: $novo.id, nome: $novo.nome, email: $novo.email, perfil: $perfil, ativo: true
  }
  ```
- **Mensagens de erro:** `A senha inicial deve ter 8 ou mais caracteres.`; `CPF já cadastrado.`; `Informe o CRM.`; `Informe o nome.`; `Perfil inválido.`

### `PATCH /usuarios/{usuario_id}`

Edita um usuário de qualquer perfil (add-autenticacao-perfis, D14; revisão de 14/11/2026): nome e e-mail no login e, conforme o perfil atual, CRM/especialidades/sala do Médico ou CPF/especialidade de referência da Recepção/Triagem. Se o login não tiver o cadastro do perfil (usuário criado fora das telas), o cadastro é criado aqui, na mesma transação. O perfil não muda aqui: a troca é feita em usuarios/{id}/perfil.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/usuarios_id_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `usuario_id` | int | sim |  |
  | `nome` | text | sim | filtros: trim |
  | `email` | text | sim | filtros: trim, lower |
  | `crm` | text | não | filtros: trim |
  | `especialidade_ids` | json | não |  |
  | `sala_id` | int | não |  |
  | `cpf` | text | não | filtros: trim |
  | `especialidade_referencia_id` | int | não |  |
- **Resposta (200):**

  ```
  {
    id: $editado.id, nome: $editado.nome, email: $editado.email, perfil: $editado.perfil, ativo: $editado.ativo
  }
  ```
- **Mensagens de erro:** `CPF já cadastrado.`; `Informe o CRM.`; `Informe o nome.`; `Usuário não encontrado.`

### `PATCH /usuarios/{usuario_id}/ativo`

Ativa ou desativa um usuário de qualquer perfil (add-autenticacao-perfis, D9/D14; revisão de 14/11/2026). Não desativa a si mesmo nem o último administrador ativo. O cadastro de Médico ou Recepção/Triagem, quando existe, acompanha o login na mesma transação.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/usuarios_id_ativo_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `usuario_id` | int | sim |  |
  | `ativo` | bool | sim |  |
- **Resposta (200):**

  ```
  {
    id: $editado.id, ativo: $editado.ativo
  }
  ```
- **Mensagens de erro:** `MEDICO_COM_FICHA_CHAMADA`; `Não é possível desativar o próprio usuário`; `ULTIMO_ADMINISTRADOR`; `Usuário não encontrado.`

### `PATCH /usuarios/{usuario_id}/perfil`

Troca o perfil de um usuário (add-autenticacao-perfis, D14). Não troca o próprio perfil, não deixa o sistema sem administrador ativo e não troca médico com ficha CHAMADO. Na mesma transação: desativa o cadastro do perfil antigo, reativa (ou cria) o do perfil novo com os dados exigidos e grava o perfil. Vale na próxima requisição do usuário.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/cadastros/usuarios_id_perfil_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `usuario_id` | int | sim |  |
  | `perfil` | text | sim | filtros: trim, upper |
  | `crm` | text | não | filtros: trim |
  | `especialidade_ids` | json | não |  |
  | `sala_id` | int | não |  |
  | `cpf` | text | não | filtros: trim |
  | `especialidade_referencia_id` | int | não |  |
- **Resposta (200):**

  ```
  {
    id: $editado.id, perfil: $editado.perfil, ativo: $editado.ativo
  }
  ```
- **Mensagens de erro:** `CPF já cadastrado.`; `Informe o CRM.`; `MEDICO_COM_FICHA_CHAMADA`; `O usuário já tem este perfil.`; `PROPRIO_PERFIL`; `Perfil inválido.`; `ULTIMO_ADMINISTRADOR`; `Usuário não encontrado.`


## Grupo Fila

### `GET /fichas/{ficha_id}/impressao`

- **Acesso:** login: MEDICO
- **Código:** `backend/xano/api/fila/fichas_id_impressao_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `ficha_id` | int | sim |  |
- **Resposta (200):**

  ```
  {
    ficha          : {id: $ficha.id, senha: $ficha.senha, chegada_em: $ficha.chegada_em, status: $ficha.status, observacao: $ficha.observacao, pa_sistolica: $sinais_ficha.pa_sistolica, fc: $sinais_ficha.fc, fr: $sinais_ficha.fr, temperatura: $sinais_ficha.temperatura, spo2: $sinais_ficha.spo2, glicemia: $sinais_ficha.glicemia, glicemia_sinais_gravidade: $ficha.glicemia_sinais_gravidade, escore_risco: $ficha.escore_risco, classificacao_risco: $ficha.classificacao_risco, prioridade_atual: $ficha.prioridade_atual, condicao_prioritaria: $ficha.condicao_prioritaria, especialidade: ($especialidade == null) ? null : {id: $especialidade.id, nome: $especialidade.nome, sigla: $especialidade.sigla}}
    paciente       : {nome: $avaliacao.paciente.nome, idade: $avaliacao.idade}
    sintomas       : $avaliacao.sintomas|map:{nome: $$.nome, descricao: $$.descricao}
    sintomas_livres: $avaliacao.sintomas_livres|map:$$.descricao
    historico      : $eventos|map:{tipo: $$.tipo, oportunidade: $$.oportunidade, tentativa: $$.tentativa, medico_id: $$.medico_id, em: $$.created_at}
  }
  ```
- **Mensagens de erro:** `FICHA_NAO_ATRIBUIDA`

### `GET /filas/{especialidade}/previsao`

- **Acesso:** login: RECEPCAO_TRIAGEM, MEDICO, ADMINISTRADOR
- **Código:** `backend/xano/api/fila/filas_especialidade_previsao_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `especialidade` | int | sim |  |
- **Resposta (200):**

  ```
  $previsao
  ```
- **Mensagens de erro:** `ESPECIALIDADE_NAO_ENCONTRADA`

### `POST /medico/chamar-proximo`

- **Acesso:** login
- **Código:** `backend/xano/api/fila/medico_chamar_proximo_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `ficha_id` | json | não |  |
  | `id` | json | não |  |
- **Resposta (200):**

  ```
  $resultado
  ```
- **Mensagens de erro:** `ESCOLHA_MANUAL_PROIBIDA`

### `POST /medico/fichas/{ficha_id}/acao`

- **Acesso:** login
- **Código:** `backend/xano/api/fila/medico_fichas_id_acao_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `ficha_id` | int | sim |  |
  | `acao` | text | sim | filtros: trim |
- **Resposta (200):**

  ```
  $resultado
  ```

### `GET /medico/filas`

- **Acesso:** login: MEDICO
- **Código:** `backend/xano/api/fila/medico_filas_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  {
    medico     : {id: $medico.id, apto: ($apto != null), status: ($sessao == null) ? "SEM_SESSAO" : $sessao.status_operacional, plantao_vigente: $plantao}
    filas      : $filas
    ficha_atual: $ficha_atual
    historico  : $historico
  }
  ```
- **Mensagens de erro:** `MEDICO_INATIVO`

### `GET /painel`

Painel público da sala de espera (add-painel-publico, D2 e D3). Sem sessão e só de leitura: a resposta é montada campo a campo, sem nome, CPF, sintomas, sinais vitais ou identificação do Médico (RNF06, RN35). A Sala é a atual do Médico que chamou (sem mudança de schema). chamada_id e ticket_id são identificadores técnicos para o painel detectar chamada nova ou repetida. Chamada atual, últimas chamadas, ticket chamado na triagem e previsão por especialidade, para o painel público.

- **Acesso:** público (sem login)
- **Código:** `backend/xano/api/fila/painel_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `especialidades` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  {
    atual    : $atual
    ultimas  : $ultimas
    triagem  : ($ticket == null) ? null : {ticket_id: $ticket.id, tipo: $ticket.tipo, numero: $ticket.numero, tentativa: $ticket.tentativas, chamado_em: $ticket.chamado_em}
    triagem_ultimas: $tickets_anteriores
    previsoes: $previsoes
    gerado_em: now
  }
  ```
- **Mensagens de erro:** `FILTRO_SEM_ESPECIALIDADE_ATIVA`


## Grupo Pacientes

### `GET /pacientes`

Pesquisa um Paciente pelo CPF normalizado para Recepção/Triagem ou Administrador.

- **Acesso:** login: RECEPCAO_TRIAGEM, ADMINISTRADOR
- **Código:** `backend/xano/api/pacientes/pacientes_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `cpf` | text | sim | filtros: trim |
- **Resposta (200):**

  ```
  $paciente
  ```

### `POST /pacientes`

Cadastra um Paciente com CPF normalizado e único para Recepção/Triagem, com auditoria atômica.

- **Acesso:** login: RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/pacientes/pacientes_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `cpf` | text | sim | filtros: trim |
  | `nome` | text | não | filtros: trim |
  | `data_nascimento` | date | sim |  |
  | `telefone` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  $paciente
  ```
- **Mensagens de erro:** `CPF_DUPLICADO`; `Data de nascimento inválida`; `Nome inválido`

### `PATCH /pacientes/{paciente_id}`

Atualiza parcialmente os dados cadastrais de um Paciente para Recepção/Triagem, com auditoria atômica.

- **Acesso:** login: RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/pacientes/pacientes_id_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `paciente_id` | int | sim |  |
  | `cpf` | text | não | padrão "__CPF_AUSENTE__", filtros: trim |
  | `nome` | text | não | padrão "__NOME_AUSENTE__", filtros: trim |
  | `data_nascimento` | date | não | padrão "0001-01-01" |
  | `telefone` | text | não | padrão "__TELEFONE_AUSENTE__" |
- **Resposta (200):**

  ```
  {
    alterado: $houve_alteracao,
    paciente: $paciente_resultado
  }
  ```
- **Mensagens de erro:** `CPF não pode ser alterado`; `Data de nascimento inválida`; `Nenhum campo atualizável informado`; `Nome inválido`; `Paciente não encontrado`


## Grupo Triagem

### `GET /expiracao`

Prévia da dispensa por prazo (add-expiracao-24h, D1): fichas e tickets parados há mais de HORAS_EXPIRACAO horas. Só para o Administrador; não altera dados (além de criar o parâmetro padrão, se faltar).

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/triagem/expiracao_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  $previa
  ```

### `POST /expiracao`

Dispensa por prazo (add-expiracao-24h, D1): recalcula no servidor o que está parado agora e encerra tudo como DESISTENCIA, auditando EXPIRACAO em nome do Administrador. Não recebe IDs da tela, para não encerrar algo que mudou entre a prévia e o clique.

- **Acesso:** login: ADMINISTRADOR
- **Código:** `backend/xano/api/triagem/expiracao_post.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  $resultado
  ```

### `GET /fichas`

Fichas do dia da Recepção/Triagem (add-fichas-do-dia, D1); o Administrador também lê, para o dashboard (add-acompanhamento-administrador, D6): não finalizadas de qualquer data e finalizadas com chegada hoje (America/Sao_Paulo), da mais recente para a mais antiga. Sem CPF, sintomas ou sinais vitais.

- **Acesso:** login: RECEPCAO_TRIAGEM, ADMINISTRADOR
- **Código:** `backend/xano/api/triagem/fichas_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  {
    fichas: $lista, agora: now
  }
  ```

### `POST /fichas`

Abre ficha vazia em EM_TRIAGEM para paciente ativo, com ticket opcional e auditoria; sem ticket, devolve a ficha não finalizada que o paciente já tiver.

- **Acesso:** login: RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/triagem/fichas_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `paciente_id` | int | sim |  |
  | `ticket_id` | int | não |  |
- **Resposta (200):**

  ```
  {
    id: $ficha.id, paciente_id: $ficha.paciente_id, ticket_id: $ficha.ticket_id, status: $ficha.status, chegada_em: $ficha.chegada_em, senha: $ficha.senha, ja_existente: $ja_existente
  }
  ```
- **Mensagens de erro:** `FICHA_NAO_FINALIZADA_EXISTENTE`; `PACIENTE_INEXISTENTE_OU_INATIVO`; `TICKET_INVALIDO`

### `GET /fichas/{ficha_id}`

Retorna a ficha para edição, classificação e destino: paciente com idade, sintomas do catálogo e digitados, sinais vitais e resultado da classificação.

- **Acesso:** login: RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/triagem/fichas_id_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `ficha_id` | int | sim |  |
- **Resposta (200):**

  ```
  {
    ficha: {
    id                       : $ficha.id
    paciente_id              : $ficha.paciente_id
    ticket_id                : $ficha.ticket_id
    chegada_em               : $ficha.chegada_em
    status                   : $ficha.status
    observacao               : $ficha.observacao
    gestante                 : $ficha.gestante == true
    pa_sistolica             : $sinais_ficha.pa_sistolica
    fc                       : $sinais_ficha.fc
    fr                       : $sinais_ficha.fr
    temperatura              : $sinais_ficha.temperatura
    spo2                     : $sinais_ficha.spo2
    glicemia                 : $sinais_ficha.glicemia
    glicemia_sinais_gravidade: $ficha.glicemia_sinais_gravidade == true
    senha                    : $ficha.senha
    especialidade            : ($especialidade_atribuida == null) ? null : {id: $especialidade_atribuida.id, nome: $especialidade_atribuida.nome, sigla: $especialidade_atribuida.sigla}
    }
    destino_previsto: ($ficha.status == "EM_TRIAGEM") ? {especialidade: $destino.especialidade, motivo: $destino.motivo} : null
    paciente: {id: $paciente.id, cpf: $paciente.cpf, nome: $paciente.nome, data_nascimento: $paciente.data_nascimento, idade: $avaliacao.idade}
    sintomas: $avaliacao.sintomas|map:{id: $$.id, nome: $$.nome, descricao: $$.descricao, grupo: $$.grupo, pontuacao: $$.pontuacao}
    sintomas_livres: $avaliacao.sintomas_livres|map:{id: $$.id, descricao: $$.descricao, pontuacao: $$.pontuacao}
    referencias_sinais: $faixas_referencia|map:{parametro: $$.parametro, minimo: $$.minimo, maximo: $$.maximo}
    classificacao: {
    pontos_sinais       : $avaliacao.classificacao.pontos_sinais
    escore_sintomas     : $avaliacao.classificacao.escore_sintomas
    escore_sinais       : $avaliacao.classificacao.escore_sinais
    escore_total        : $avaliacao.classificacao.escore_total
    item_critico        : $avaliacao.classificacao.item_critico
    tabela_adulta       : $avaliacao.classificacao.tabela_adulta
    pendencias          : $avaliacao.classificacao.pendencias
    condicao_prioritaria: $avaliacao.classificacao.condicao_prioritaria
    prioridade_calculada: $avaliacao.classificacao.prioridade_calculada
    prioridade_atual    : $ficha.prioridade_atual
    justificativa_ajuste: $ficha.justificativa_ajuste
    }
  }
  ```

### `PATCH /fichas/{ficha_id}`

Atualiza observação, sintomas do catálogo, sintomas digitados e sinais vitais da ficha EM_TRIAGEM ou AGUARDANDO, valida RN04, recalcula a classificação (descartando o ajuste manual), aplica o ajuste opcional, reavalia destino e senha em AGUARDANDO e audita.

- **Acesso:** login: RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/triagem/fichas_id_patch.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `ficha_id` | int | sim |  |
  | `observacao` | text | não | padrão "__OMITTED__" |
  | `sintoma_ids` | json | não | padrão "__OMITTED__" |
  | `sinais_vitais` | json | não | padrão "__OMITTED__" |
  | `sintomas_livres` | json | não | padrão "__OMITTED__" |
  | `prioridade_ajuste` | text | não | filtros: trim, upper |
  | `justificativa_ajuste` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  {
    id             : $input.ficha_id
    observacao     : $observacao_resultante
    sintoma_ids    : $ids_resultantes
    sintomas_livres: $livres_resultantes
    sinais_vitais  : $sinais_resultantes
    classificacao  : $avaliacao.classificacao
    prioridade_atual: $prioridade_final
    especialidade  : ($reavaliacao == null) ? null : $reavaliacao.especialidade
    senha_anterior : ($reavaliacao == null) ? null : $reavaliacao.senha_anterior
    senha          : ($reavaliacao == null) ? null : $reavaliacao.senha
    senha_alterada : ($reavaliacao == null) ? false : $reavaliacao.senha_alterada
  }
  ```
- **Mensagens de erro:** `FICHA_FORA_DA_TRIAGEM`; `FICHA_NAO_ENCONTRADA`; `FICHA_SEM_SINTOMA_OU_OBSERVACAO`; `NENHUM_CAMPO_ATUALIZAVEL_INFORMADO`; `SINAIS_VITAIS_INVALIDO`; `SINAL_VITAL_INVALIDO:`; `SINTOMAS_LIVRES_INVALIDO`; `SINTOMAS_LIVRES_LIMITE`; `SINTOMA_IDS_INVALIDO`; `SINTOMA_INEXISTENTE_OU_INATIVO`; `SINTOMA_LIVRE_DESCRICAO_INVALIDA`; `SINTOMA_LIVRE_DUPLICADO`; `SINTOMA_LIVRE_EXISTE_NO_CATALOGO`; `SINTOMA_LIVRE_PONTUACAO_INVALIDA`

### `GET /fichas/{ficha_id}/comprovante`

Comprovante da senha (add-direcionamento-senha, D6; RF21/RF48, Rev. 2.1 §9): só senha, prioridade, especialidade e horário de entrada. Nada de nome, CPF, data de nascimento, sintomas ou sinais vitais.

- **Acesso:** login: RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/triagem/fichas_id_comprovante_get.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `ficha_id` | int | sim |  |
- **Resposta (200):**

  ```
  {
    senha        : $ficha.senha
    prioridade   : $ficha.prioridade_atual
    especialidade: ($especialidade == null) ? null : {nome: $especialidade.nome, sigla: $especialidade.sigla}
    chegada_em   : $ficha.chegada_em
  }
  ```
- **Mensagens de erro:** `FICHA_NAO_ENCONTRADA`; `SENHA_NAO_ATIVA`

### `POST /fichas/{ficha_id}/confirmar-triagem`

Confirmação da triagem (add-direcionamento-senha, D5; RF47/RF48): exige ficha EM_TRIAGEM com cor definida, define o destino pelos sintomas, gera a senha e leva a ficha a AGUARDANDO numa única transação auditada.

- **Acesso:** login: RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/triagem/fichas_id_confirmar_triagem_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `ficha_id` | int | sim |  |
- **Resposta (200):**

  ```
  {
    id           : $input.ficha_id
    status       : "AGUARDANDO"
    senha        : $senha.senha
    prioridade   : $ficha.prioridade_atual
    especialidade: $destino.especialidade
  }
  ```
- **Mensagens de erro:** `DESTINO_NAO_CONFIGURADO`; `FICHA_FORA_DA_TRIAGEM`; `FICHA_NAO_ENCONTRADA`; `FICHA_SEM_PRIORIDADE`; `FICHA_SEM_SINTOMA_OU_OBSERVACAO`

### `POST /fichas/{ficha_id}/prioridade`

Ajuste manual da prioridade pela Recepção/Triagem (add-classificacao-prioridade, D6). Também é a classificação manual excepcional quando o cálculo automático está bloqueado (menor de 16 anos, gestante ou dado pendente). Justificativa obrigatória e auditada. Em AGUARDANDO, a troca de cor troca também a letra da senha (add-reavaliacao-ficha-aguardando, D4).

- **Acesso:** login: RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/triagem/fichas_id_prioridade_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `ficha_id` | int | sim |  |
  | `prioridade` | text | não | filtros: trim, upper |
  | `justificativa` | text | não | filtros: trim |
- **Resposta (200):**

  ```
  {
    id                  : $input.ficha_id
    prioridade_calculada: $ajuste.prioridade_calculada
    prioridade_atual    : $ajuste.prioridade_atual
    justificativa_ajuste: $ajuste.justificativa_ajuste
    senha_anterior      : ($reavaliacao == null) ? null : $reavaliacao.senha_anterior
    senha               : ($reavaliacao == null) ? null : $reavaliacao.senha
    senha_alterada      : ($reavaliacao == null) ? false : $reavaliacao.senha_alterada
  }
  ```
- **Mensagens de erro:** `FICHA_FORA_DA_TRIAGEM`; `FICHA_NAO_ENCONTRADA`

### `GET /sintomas`

Lista o catálogo ativo de sintomas com a pontuação acadêmica da triagem.

- **Acesso:** login: RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/triagem/sintomas_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  $sintomas|map:{id: $$.id, nome: $$.nome, descricao: $$.descricao, grupo: $$.grupo, pontuacao: $$.pontuacao}
  ```

### `GET /tickets`

- **Acesso:** login: RECEPCAO_TRIAGEM, ADMINISTRADOR
- **Código:** `backend/xano/api/triagem/tickets_get.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  {
    tickets: $tickets, agora: now, intervalo_segundos: $segundos_intervalo, intervalo_repeticao_segundos: $segundos_repeticao, tentativas_maximas: $chamadas_maximas
  }
  ```

### `POST /tickets/proximo`

- **Acesso:** login: RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/triagem/tickets_proximo_post.xs`
- **Entrada:** nenhuma
- **Resposta (200):**

  ```
  $resultado
  ```
- **Mensagens de erro:** `FILA_VAZIA`; `PARAMETROS_INVALIDOS`; `PARAMETROS_NAO_CONFIGURADOS`; `TICKET_INDISPONIVEL`

### `POST /tickets/{ticket_id}/acao`

- **Acesso:** login: RECEPCAO_TRIAGEM
- **Código:** `backend/xano/api/triagem/tickets_acao_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `ticket_id` | int | sim |  |
  | `acao` | text | sim | filtros: trim |
- **Resposta (200):**

  ```
  $resultado
  ```
- **Mensagens de erro:** `ACAO_INVALIDA`; `AGUARDE_INTERVALO`; `LIMITE_DE_CHAMADAS`; `PARAMETROS_NAO_CONFIGURADOS`; `PRESENCA_CONFIRMADA`; `TICKET_INDISPONIVEL`; `TICKET_NAO_CHAMADO`

### `POST /totem/tickets`

Emissão pública de ticket pelo Totem (add-totem D1, D2, D5). Sem sessão de equipe e sem dados pessoais; a chave do dispositivo vem do servidor Reflex e é comparada com a variável de ambiente TOTEM_CHAVE.

- **Acesso:** público (sem login)
- **Código:** `backend/xano/api/triagem/totem_tickets_post.xs`
- **Entrada:**

  | Campo | Tipo | Obrigatório | Observação |
  |---|---|---|---|
  | `chave_dispositivo` | text | não |  |
  | `tipo` | text | não | filtros: trim, upper |
- **Resposta (200):**

  ```
  {
    tipo  : $ticket.tipo
    numero: $ticket.numero
    codigo: $prefixo ~ "-" ~ $numero_texto
  }
  ```
- **Mensagens de erro:** `Dispositivo não autorizado.`; `Não foi possível emitir o ticket. Tente novamente.`; `Tipo de ticket inválido.`


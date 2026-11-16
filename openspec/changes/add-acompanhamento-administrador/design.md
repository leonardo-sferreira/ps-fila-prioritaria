# Design técnico

## Contexto

Os dados já existem: `sessao` (change 1), `historico_alteracao` (change 2), `ficha_atendimento` e `chamada` (changes 4 a 6). Esta change acrescenta o status operacional e três consultas de leitura para o Administrador. Também mexe em dois endpoints existentes: login/logout (change 1) e chamada/comparecimento (change 6).

## Objetivos / Fora dos objetivos

**Objetivos:**
- Uma auditoria consultável num lugar só, sem duplicar dados que já estão em `chamada` e `sessao`.
- Nenhuma escrita a partir da tela do Administrador, que é só de leitura.

**Fora dos objetivos:**
- Retenção e arquivamento de auditoria antiga.

## Decisões

### D1. Status operacional e sessão
Campo `status_operacional` (enum opcional) representa disponibilidade operacional e não autenticação; nulo é o estado inicial indisponível do Médico e não se aplica ao Administrador, enquanto Recepção/Triagem começa DISPONIVEL. Sessão ativa continua determinada por `logout_em` nulo e `expira_em` futuro conforme `add-autenticacao-perfis`. `PATCH me/status` permite que a equipe escolha DISPONIVEL, PAUSA ou AUSENTE. `comparecimento` define EM_ATENDIMENTO e chamada aceita define DISPONIVEL, na mesma transação da operação. Sem status, PAUSA e AUSENTE impedem novas atribuições ao Médico, sem encerrar a sessão nem retirar fichas já atribuídas. O plantão possui estado próprio, separado da sessão/status; seu encerramento só é concluído com fila atribuída zerada.
- **Por quê:** autenticação, disponibilidade e ciclo do plantão são estados distintos; logout/expiração encerram a sessão, não uma pausa operacional.

### D2. Auditoria consolidada por consulta, não por cópia
`GET admin/auditoria` junta três fontes num formato único: `historico_alteracao` (alterações), `chamada` (tipos CHAMADA/COMPARECIMENTO/DESISTENCIA) e `sessao` (LOGIN em `login_em`, LOGOUT em `logout_em`). Ordena por data/hora decrescente, filtra e pagina no Xano.
- **Por quê:** evita gravar o mesmo fato duas vezes (RNF03).
- **Alternativa:** gravar tudo em `historico_alteracao`. Descartada porque duplicaria chamadas e sessões. Se a consulta ficar lenta, a alternativa é uma "view" materializada, sem mudar a spec.
- Assim, o requisito "login registrado na auditoria" é atendido pela leitura de `sessao`, sem mudar o endpoint de login.

### D3. Fila geral reutilizando a ordenação
`GET admin/fila-geral` lista as fichas não finalizadas. Para as AGUARDANDO, a ordem de cada especialidade reutiliza diretamente `fila/proxima_ficha(fichas, posicao, amarelas, azuis)`, a seleção pura usada por chamada e previsão. A consulta percorre todas as fichas, pois `fila/prever_fila` limita uma previsão a 20 itens. O tempo de espera é calculado no backend a partir de `chegada_em`.

### D4. Tela `/admin/acompanhamento`
Blocos de Fila geral (tabela com cores, filtros e posições por especialidade) e Equipe (componente existente do dashboard). A Auditoria fica na página própria, conforme decisão da tarefa 3.5, acessível pelo menu. Polling de 10 s só na rota e aba visíveis. O detalhe em `/admin/fichas/{id}` continua na tarefa 3.3; o link só será disponibilizado após essa entrega. Nenhuma ação de triagem, chamada ou edição.

### D5. Seletor de status para a equipe
Um componente no cabeçalho de `/recepcao` e `/medico` mostra o status atual e permite trocar entre Disponível, Pausa e Ausente; EM_ATENDIMENTO aparece como texto, não como opção.

### D6. Dashboard do Administrador na tela inicial (decisão do PO em 11/11/2026)
A tela `/admin` passa a abrir com o mesmo painel do plantão da Recepção/Triagem, mais blocos que só o Administrador vê:
- **Reaproveitado da Recepção:** na espera (pré-triagem e fila médica), cores da fila médica, espera mais longa, percurso do dia, fila por especialidade e chegadas por hora. A função `resumir_plantao` é a mesma; no Administrador os cartões do percurso não levam a telas da Recepção.
- **Só do Administrador:**
  - indicadores do dia: atendidas, desistências, canceladas e espera média de quem está na fila médica agora;
  - equipe agora: pessoas com sessão ativa, com perfil e status operacional, e a contagem de médicos por status (Disponível, Em atendimento, Pausa, Ausente, sem status).
- O cartão "Fichas e tickets parados" (expiração de 24 h) continua no fim da tela.
- **Backend:** `GET fichas` e `GET tickets` (grupo Triagem) passam a aceitar também `ADMINISTRADOR`, só leitura. O novo `GET admin/equipe` (grupo Cadastros, só `ADMINISTRADOR`) lista as sessões ativas (`logout_em` nulo e `expira_em` no futuro), a mais recente por usuário, com nome, perfil, status e horário de login. É a parte "equipe" da tarefa 2.2.
- Atualiza sozinho a cada 30 s, como o painel da Recepção.
- **Por quê:** o PO pediu que a tela inicial do Administrador tenha o mesmo dashboard da Recepção, mais detalhado. Indicadores estatísticos, antes fora do escopo, entram só nesse recorte do dia.

### D7. "Visualizar como" Recepção ou Médico (decisão do PO em 11/11/2026)
O Administrador pode abrir as telas da Recepção/Triagem e do Médico só para ver, sem trocar o próprio perfil. A tela mostra uma faixa "Visualizando como …" e as ações ficam desabilitadas; o backend continua recusando ações de quem não é do perfil, então nada muda mesmo que um botão escape. Detalhamento na próxima fatia desta change (seção 6 das tasks).

## Riscos / Compromissos

- [Consulta unificada de auditoria pesada com muitos dados] → Paginação e filtro por período obrigatório no backend (padrão: últimas 24 h).
- [Mudar endpoints de changes anteriores pode quebrar testes existentes] → A tarefa de integração roda a suíte `pytest tests/api` completa.

## Plano de migração

Campo já existente em `sessao`. A migração das sessões médicas ativas que receberam DISPONIVEL automaticamente deixa o status nulo até o Médico escolher DISPONIVEL; não altera PAUSA, AUSENTE ou EM_ATENDIMENTO. Rollback: restaurar o comportamento anterior do login e dos endpoints de status.

## Entrega local de status da Recepção — 15/11/2026

Recorte autorizado da Sprint 4: concluir o seletor da Recepção e acrescentar testes locais dos status já existentes do Médico. Não recriar dashboard/auditoria, alterar a chamada, publicar recursos ou executar escritas no Live. RF44/RF45 são as referências fornecidas para a tarefa; esta fatia não atribui texto formal novo aos códigos sem consulta à fonte formal.

- Reutilizar o grupo Autenticacao e o PATCH me/status publicado. Como auth/me não informa o status, preparar localmente GET me/status: auth usuario, somente Médico/Recepção ativo, sessão do próprio usuário ainda não encerrada/expirada, a mais recente. Retornar somente status, com 401 sem sessão; nenhum input de identidade e nenhuma escrita.
- O GET novo precisa de publicação seletiva autorizada. Não afirmar que o status atual foi consultado se o servidor retornar 404 ou resposta inválida. Mostrar indisponibilidade, manter seletor bloqueado até consulta válida e permitir Atualizar status.
- StatusRecepcaoState usa api.py e AuthState existentes. A página /recepcao consulta na abertura; renderização e abertura nunca fazem PATCH. Disponível, Pausa e Ausente são as únicas opções manuais; Em atendimento continua automático no Médico.
- Aceitar mudança somente após HTTP 200 e status correspondente ao solicitado. Em timeout, erro de conexão ou resposta incerta, não repetir, não anunciar sucesso e orientar atualização. Não presumir o estado anterior após resultado incerto. Publicar o estado de carregamento antes do HTTP, liberar o bloqueio mesmo no encerramento do evento e ignorar uma repetição do status já confirmado. Bloquear reentrada durante consulta/envio e validar o perfil local sem substituir a autorização do Xano.
- Os testes novos usam transporte HTTP simulado. Contratos XS estáticos conferem permissões, sessão inicial, enum manual e transições médicas existentes; não comprovam execução do engine, rollback ou bloqueios concorrentes.
- GET admin/fila-geral, detalhe administrativo, polling de 10 s e Visualizar como permanecem nas tarefas próprias, fora desta fatia. O dashboard e a auditoria existentes são preservados.

## Recorte local da Fila Geral — 15/11/2026
D3: a assinatura antiga prever_fila(especialidade,total) não existe. A função recebe fichas/posicao/amarelas/azuis/limite e limita a 20. O GET reutiliza fila/proxima_ficha até percorrer todas as AGUARDANDO de cada especialidade, alterando a posição somente em memória. Não inventa uma ordem global entre especialidades. Filtros de especialidade/cor/status são aplicados depois da previsão: a posição refere a fila completa.

Contrato preservado: lista simples com id, senha, status, cor, condicao_prioritaria, especialidade_id, especialidade, chegada_em, posicao, medico, tentativa e oportunidade. A correção local acrescenta espera_minutos, consultado_em, avisos e medico_id por item, sem remover campos publicados. Sem paciente/CPF/e-mail/sintomas/sinais vitais. Médico e tentativa somente para CHAMADO; usuários consultados apenas pelos IDs necessários. Toda ficha não finalizada aparece exatamente uma vez, inclusive sem catálogo, sem cor válida ou sem posição calculável (posicao=null). Parâmetros ausentes/inválidos e ciclo inválido geram aviso, não valores clínicos inventados nem desaparecimento de fichas. Ciclo ausente inicia em 1, como a previsão existente. Espera em minutos desde chegada, nunca negativa.

D4: /admin/acompanhamento apresenta Fila Geral e reutiliza Equipe. Auditoria permanece em sua página própria, conforme tarefa 3.5. Polling de 10 s somente na rota e aba visíveis. O detalhe da ficha continua em outra tarefa: não criar link quebrado nem ações de triagem/chamada/edição. Publicação e aceite integrado permanecem pendentes. O PR #60 está integralmente presente na base 324e0d8 deste worktree de integração. Seus módulos de status e sua documentação são preservados.


### Compatibilidade remota verificada por leitura
O GET admin/fila-geral já existe no workspace 147348/v1, grupo Cadastros 438024, endpoint 4128628, com autenticação usuario e autorização ADMINISTRADOR. Não criar uma segunda rota. Sua definição publicada retorna lista simples, calcula somente 20 posições por especialidade usando prever_fila, associa posições por senha e adota 2/1 quando parâmetros estão ausentes. Essa definição não foi alterada nesta entrega.

O arquivo local é uma proposta de correção desse endpoint existente: associação por ID, todas as posições calculáveis, parâmetros configurados e consulta restrita dos usuários necessários. Exige revisão seletiva da diferença com o proprietário do endpoint e autorização antes de qualquer publicação. O frontend aceita a lista publicada, ordenando apenas as posições fornecidas dentro da mesma especialidade, sem recalcular prioridade clínica nem inventar uma ordem entre especialidades. Mantém fichas sem posição no final dos espaços daquela especialidade. Sem os novos metadados, mostra espera indisponível e aviso das limitações da previsão; não apresenta a versão remota como corrigida.

Os filtros de especialidade usam IDs/nomes observados na fila consultada, preservados ao trocar filtros; não são um segundo cadastro nem incluem especialidades sem fichas observadas. A hora de última consulta é o recebimento confirmado no Reflex; a espera clínica só é exibida quando fornecida pelo servidor. Lista vazia é resposta válida e não permite identificar a versão do backend.

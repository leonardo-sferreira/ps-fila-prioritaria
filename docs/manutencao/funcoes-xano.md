# Funções do Xano (regras de negócio no código)

> Arquivo gerado por `python scripts/gerar_docs.py`. Não edite à mão: altere o código e gere de novo.

Funções reutilizadas pelos endpoints (`backend/xano/function/`). Funções puras têm testes nativos do Xano (coluna "Testes nativos"), que rodam na suíte `xano-safe` do CI. As funções `teste_*` existem só para os testes de integração e não têm endpoint público.

## (raiz)

| Função | O que faz | Testes nativos |
|---|---|---|
| `inicializar_parametros_fila` | — | — |
| `registrar_alteracao` | Grava a trilha imutável da operação autenticada. O chamador DEVE passar $auth.id após verificar_acesso e executá-la na mesma db.transaction da escrita de domínio. A carga automática (funções inicializar_*) passa sistema = true e nenhum usuário: o registro fica com usuario_id vazio e a tela de auditoria mostra "Sistema" (add-base-compartilhada, task 4.3). Endpoints NUNCA passam sistema = true (tests/api/test_base_compartilhada.py). | — |

## auth

| Função | O que faz | Testes nativos |
|---|---|---|
| `auth/conferir_codigo` | Confere o código de verificação aberto do usuário e o marca como usado quando confere (design D12/D13). | — |
| `auth/emitir_codigo` | Gera e envia por e-mail um código de verificação, invalidando o anterior da mesma finalidade (design D12/D13). | — |
| `auth/teste_sessao_unica` *(só teste)* | Cenário sintético executado somente pelo CLI; não possui endpoint público. | — |
| `auth/verificar_acesso` | Ponto único de autorização por perfil (design D3), chamado no início de todo endpoint protegido. | — |

## cadastros

| Função | O que faz | Testes nativos |
|---|---|---|
| `cadastros/email_livre` | Recusa e-mail já usado por outro usuário, sem diferenciar maiúsculas (add-cadastros-administrador, D3). Na edição, `ignorar_usuario_id` é o próprio usuário. Devolve o e-mail normalizado. | — |
| `cadastros/especialidades_validas` | Confere uma lista ordenada de IDs de especialidade: ao menos uma, todas existentes e ativas (add-cadastros-administrador, D4). Remove repetições mantendo a ordem. Usada por sintomas e médicos. | — |
| `cadastros/faixa_sobrepoe` | Diz se uma faixa de sinal vital se sobrepõe a alguma outra do mesmo parâmetro (add-cadastros-administrador, D8). Extremos inclusivos; limite null = extremo aberto. Condição de gravidade null vale para as duas condições. Função pura: as outras faixas (já do mesmo parâmetro e sem a própria) vêm na entrada. | 7 |
| `cadastros/gravar_vinculos` | Substitui os vínculos de um sintoma (destinos, com ordem) ou de um médico (especialidades próprias) (add-cadastros-administrador, D4). Vínculo não tem histórico próprio: apaga os antigos e grava os novos. Deve ser chamada dentro da transação do endpoint; os IDs já vêm validados por cadastros/especialidades_validas. | — |
| `cadastros/periodo_plantao` | Converte data + horas de um plantão em início e fim (epoch ms) no fuso America/Sao_Paulo (add-cadastros-administrador, D6). Fim menor ou igual ao início cai no dia seguinte (plantão noturno), então o período tem no máximo 24 h. Função pura: não acessa o banco. | 5 |
| `cadastros/plantao_sobreposto` | Diz se [inicio, fim) se sobrepõe a outro plantão não encerrado do mesmo médico (add-cadastros-administrador, D6). Intervalos semiabertos: um plantão pode começar exatamente quando o outro termina. | — |
| `cadastros/regra_parametro` | Limites dos parâmetros editáveis pelo Administrador (add-cadastros-administrador, D7). Função pura. Chave interna (POSICAO_CICLO_PRE_TRIAGEM) ou desconhecida: editavel = false. ESPECIALIDADE_PADRAO é do tipo ESPECIALIDADE: sem mínimo/máximo, validada contra as especialidades ativas. | 5 |
| `cadastros/sala_valida` | Sala opcional do médico: vazia é aceita; informada, precisa existir e estar ativa (add-cadastros-administrador, D4). | — |

## classificacao

| Função | O que faz | Testes nativos |
|---|---|---|
| `classificacao/aplicar_ajuste` | Ajuste manual da prioridade (add-classificacao-prioridade, D6), extraído do endpoint de prioridade para ser usado também pelo PATCH da ficha na mesma operação da alteração clínica (add-reavaliacao-ficha-aguardando, D2). Deve ser chamada dentro da transação do chamador, depois da validação de estado e do recálculo. Com reavaliar_senha (ajuste isolado em AGUARDANDO), troca a letra da senha antes de auditar, para a auditoria registrar a senha anterior e a nova. O PATCH passa falso: ele refaz destino e senha e audita depois. | — |
| `classificacao/avaliar_ficha` | Lê a ficha e tudo o que a classificação usa e chama a regra pura `pontuar` (add-classificacao-prioridade, D4). Só leitura: o PATCH grava o resultado; o GET apenas devolve. Faixa ou parâmetro ausente vira pendência. | — |
| `classificacao/faixas_padrao` | Faixas iniciais de pontuação dos sinais vitais (Rev. 2.1, §21.2 e §21.3), fonte única usada pela carga (inicializar_classificacao) e pelos testes de pontuar. Extremos inclusivos; null = limite aberto. Pontuação acadêmica de simulação a partir da tabela adulta do NEWS2; não é NEWS2 nem protocolo clínico. | 1 |
| `classificacao/inicializar_classificacao` | Carga idempotente dos parâmetros e das faixas de sinais vitais da classificação (add-classificacao-prioridade, D2). Faixas da Rev. 2.1, §21.2 e §21.3: extremos inclusivos, null = limite aberto. Faixas só são inseridas com a tabela vazia, para não sobrescrever ajustes do ADM. | 1 |
| `classificacao/pontuar` | Regra pura da classificação (add-classificacao-prioridade, D3): não acessa o banco. Escore = soma dos sintomas distintos (catálogo + digitados, 1–3) + pontos dos sinais vitais (0–3) pelas faixas. Vermelha se qualquer item tiver 3 pontos; senão Azul abaixo de LIMIAR_AMARELA, Amarela abaixo de LIMIAR_VERMELHA, Vermelha a partir dele. Dado ausente não vira zero: entra em `pendencias` e a prioridade fica null. Tabela adulta só para idade >= IDADE_MINIMA_TABELA_ADULTA e não gestante (Rev. 2.1, §21.1). | 39 |
| `classificacao/sinais_da_ficha` | Sinais vitais lidos da ficha, com 0 tratado como "não medido". No servidor, as colunas de sinais vitais de ficha_atendimento são int/decimal sem null, então um campo deixado em branco é gravado como 0. Nenhum 0 é válido (o PATCH aceita PA ≥ 40, FC ≥ 20, FR ≥ 4, T ≥ 25, SpO2 ≥ 50, glicemia ≥ 10), então 0 volta a ser null antes da classificação e da tela. Sem isso, PA em branco viraria "PA 0" e geraria 3 pontos (Vermelha), e a pendência "Informe a PA" nunca apareceria. | 3 |

## direcionamento

| Função | O que faz | Testes nativos |
|---|---|---|
| `direcionamento/destino_da_ficha` | Destino atual da ficha (add-direcionamento-senha, D3): lê idade e sintomas do catálogo via avaliar_ficha, as ligações sintoma → especialidade ativa, a fila AGUARDANDO das candidatas, Pediatria e a especialidade padrão, e chama a regra pura escolher_destino. Só leitura: usada na prévia (GET), na confirmação e na reavaliação. | — |
| `direcionamento/escolher_destino` | Regra pura do destino da ficha (add-direcionamento-senha, D2; Rev. 2.1 §6, §14.2 e D09). Não acessa o banco. Até a idade máxima de criança → Pediatria. Sem sintoma do catálogo ligado a especialidade → especialidade padrão. Senão, entre as especialidades ligadas aos sintomas: 1º maior pontuação individual, 2º maior soma, 3º menos fichas AGUARDANDO, 4º menor ID. Cor e disponibilidade de Médico não entram. | 9 |
| `direcionamento/formatar_senha` | Formata a senha COR-ESP-NNN (add-direcionamento-senha, D4): V/A/B pela cor, sigla da especialidade e número com no mínimo 3 dígitos. Função pura, separada de gerar_senha para ser testada sem banco. | 3 |
| `direcionamento/gerar_senha` | Senha COR-ESP-NNN (add-direcionamento-senha, D4). Número diário por especialidade em America/Sao_Paulo, compartilhado entre cores, guardado em contador_senha (índice único data + especialidade). Deve ser chamada dentro da transação da confirmação. O contador é sempre gravado com valor explícito, porque no servidor `ultimo_numero` não tem default (tabela divergente, não republicada). Exclusividade sob confirmações simultâneas não comprovada (limitação registrada no proposal). | — |
| `direcionamento/inicializar_direcionamento` | Carga idempotente do direcionamento (add-direcionamento-senha, D1): especialidades com sigla de senha, ligação de cada sintoma do catálogo de docs/domain-model.md à sua especialidade e ESPECIALIDADE_PADRAO. Ligações só são inseridas com a tabela vazia, para não sobrescrever ajustes futuros do Administrador. | — |
| `direcionamento/reavaliar_senha` | Reavaliação da ficha AGUARDANDO (add-reavaliacao-ficha-aguardando, D3 e D4), usada pelo PATCH da ficha e pelo ajuste de prioridade. Deve ser chamada dentro da transação do chamador, depois do recálculo e do ajuste, com a prioridade e a especialidade que a ficha tinha antes da operação. Refaz o destino quando pedido, decide a senha por senha_reavaliada e grava especialidade, senha e número. Não muda status nem chegada_em. | — |
| `direcionamento/senha_reavaliada` | Regra da senha na reavaliação da ficha AGUARDANDO (add-reavaliacao-ficha-aguardando, D4). Função pura: nada mudou → MANTER; só a cor → TROCAR_COR (mesma sigla e número, sem tocar no contador); especialidade mudou → NOVO_NUMERO (o chamador reserva o número com gerar_senha). | 4 |

## fila

| Função | O que faz | Testes nativos |
|---|---|---|
| `fila/agir_chamada` | Repete a chamada ou conclui a ficha atribuída ao médico autenticado. | — |
| `fila/avaliar_cobertura` | Regras puras de elegibilidade e cobertura; a leitura dos registros fica em cobertura_atual. Calcula médicos aptos e especialidades cobertas pelos próprios médicos. | 1 |
| `fila/chamar_proximo` | Seleciona e reserva uma ficha para o médico em transação com bloqueio de registro. | — |
| `fila/cobertura_atual` | Carrega médicos com plantão e sessão vigentes e calcula cobertura das especialidades próprias. | — |
| `fila/migrar_chamadas` | Migração idempotente após adicionar os campos da oportunidade e da ordem efetiva. Preenche oportunidade 1 e ordem inicial sem alterar chegada nem senha. | — |
| `fila/prever_fila` | Simula chamadas sem alterar ficha, ciclo ou histórico. Prevê as próximas senhas pela mesma seleção usada na chamada real. | 1 |
| `fila/previsao_especialidade` | Previsão das próximas senhas de uma especialidade (add-painel-publico, D1): monta parâmetros do ciclo, posição atual e fichas AGUARDANDO e chama a regra pura prever_fila. Compartilhada pelo endpoint autenticado de previsão e pelo painel público, para os dois mostrarem a mesma ordem da chamada real (RN25, CA11). Só leitura. Devolve [{senha, cor}] das próximas senhas da especialidade pela mesma regra da chamada. | — |
| `fila/proxima_ficha` | Seleção pura dentro de uma especialidade. A chamada e a previsão usam esta mesma função. Escolhe a próxima ficha AGUARDANDO e informa se o ciclo amarelo/azul avança. | 4 |
| `fila/selecionar_atual` | Lê o estado de todas as filas e aplica as duas etapas da seleção sem reservar ficha. Obtém uma candidata por especialidade e escolhe a próxima para o médico. | — |
| `fila/selecionar_entre_filas` | Recebe uma candidata já ordenada internamente por especialidade. A cobertura e a lista de especialidades próprias são calculadas pelo backend antes desta função. Escolhe entre própria, descoberta e outra coberta pela política da Rev. 2.1. | — |
| `fila/teste_adiantar_chamada` *(só teste)* | Apoio aos testes da change: altera apenas fichas sintéticas criadas por teste_criar_cenario. | — |
| `fila/teste_ajustar_cenario` *(só teste)* | Ajusta somente registros fictícios identificados pelo marcador do teste. | — |
| `fila/teste_criar_cenario` *(só teste)* | Uso restrito ao CLI do workspace para testes de integração. Não há endpoint público. Cria dois médicos e duas fichas inteiramente fictícios para testar a chamada. | — |
| `fila/teste_encerrar_cenario` *(só teste)* | Encerra o acesso de um cenário sintético, preservando fichas e auditoria históricas. | — |
| `fila/teste_marcar_ajuste` *(só teste)* | Apoio ao teste do detalhe da ficha (add-acompanhamento-administrador, tarefa 2.4): grava na ficha Amarela do cenário sintético um ajuste de cor com justificativa (calculada AZUL, atual AMARELA) e a auditoria PRIORIDADE_ALTERADA em nome da Recepção do cenário. Não troca a senha, para teste_encerrar_cenario continuar achando a ficha. Altera apenas fichas criadas por teste_criar_cenario. | — |
| `fila/teste_painel_extras` *(só teste)* | Apoio a tests/api/test_painel.py (add-painel-publico, tarefa 1.2). Uso restrito ao CLI; não há endpoint público. FICHAS: cria `quantidade` fichas AGUARDANDO fictícias na especialidade da sigla, marcadas em observacao com "teste-painel-<marcador>", para medir o tamanho da previsão (8 e 3 elegíveis). TICKET: cria um ticket de pré-triagem fictício já CHAMADO (número a partir de 900, para reconhecer na tela da Recepção). RECHAMAR: rechama o ticket fictício (tentativas + 1 e chamado_em = agora). LIMPAR: cancela as fichas fictícias do marcador, inativa os pacientes e encerra o ticket como DESISTENCIA, sem horário de chamada, para ele não continuar no painel real dentro da janela HORAS_PAINEL. | — |

## manutencao

| Função | O que faz | Testes nativos |
|---|---|---|
| `manutencao/desativar_status_auto_medicos` | Revisão do PO: sessões médicas antigas não foram ativadas manualmente. Executar antes de liberar PATCH me/status; preservar PAUSA, AUSENTE e EM_ATENDIMENTO. | — |
| `manutencao/expirar_registros` | Dispensa por prazo (add-expiracao-24h, D2–D5): lista as fichas EM_TRIAGEM/AGUARDANDO/CHAMADO e os tickets AGUARDANDO/CHAMADO parados há mais de HORAS_EXPIRACAO horas desde a chegada/emissão. Sem `aplicar`, só devolve a prévia; com `aplicar`, encerra cada um como DESISTENCIA e audita EXPIRACAO em nome de `usuario_id` (Administrador), na mesma transação. Registros finais não entram na consulta. | — |
| `manutencao/expirou` | Regra pura da expiração (add-expiracao-24h, D2): um registro ativo expira quando o seu horário (chegada da ficha ou emissão do ticket) ficou mais de `horas` horas antes de `agora`. Exatamente no prazo ainda não expira. Horário vazio ou prazo que não seja positivo nunca expira. Não acessa o banco. | 6 |
| `manutencao/inicializar_status_sessoes` | Migração idempotente: preenche apenas sessões ativas da Recepção/Triagem sem status. | — |
| `manutencao/reparar_especialidade_fichas` | Reparo único após a migração de `especialidade` na v1 (PR #30): a migração apagou as especialidades e a carga do direcionamento as recriou com IDs novos. Fichas confirmadas antes ficaram apontando para IDs que não existem mais, fora de qualquer fila. Este reparo reaponta cada ficha para a especialidade de mesma sigla, lida da senha (COR-ESP-NNN). Sem `aplicar`, só relata o que encontrou; com `aplicar`, corrige e audita em nome de `email`. Rodar pelo terminal: xano function run manutencao/reparar_especialidade_fichas (ver README do PR). | — |

## pacientes

| Função | O que faz | Testes nativos |
|---|---|---|
| `pacientes/normalizar_cpf` | Normaliza e valida CPF para todas as operações de Paciente. | 5 |
| `pacientes/normalizar_telefone` | Regra do telefone na edição de Paciente, extraída de PATCH pacientes/{paciente_id} para ser testável sem sessão: o endpoint exige login e o teste unitário do Xano não simula usuário autenticado. Texto vazio ou null limpam o telefone (no banco, telefone ausente é null); `alterado` compara com o valor atual. | 5 |

## sintomas

| Função | O que faz | Testes nativos |
|---|---|---|
| `sintomas/carregar_catalogo_inicial` | Carga idempotente do catálogo acadêmico existente em docs/domain-model.md. | 1 |

## usuarios

| Função | O que faz | Testes nativos |
|---|---|---|
| `usuarios/deixa_sem_admin` | Regra do último administrador (add-autenticacao-perfis, D9/D14). Função pura: recebe os IDs dos administradores ativos e o usuário afetado; true quando tirar esse usuário deixaria o sistema sem nenhum administrador ativo. | 3 |


# Configuração, secrets e regras de negócio no código

Onde ficam as configurações, as credenciais e cada regra de negócio. Nenhum segredo fica no repositório: o `.env` do frontend está no `.gitignore`, e as variáveis do Xano ficam no próprio Xano.

## Variáveis de ambiente do Xano

Configuradas em **Xano → Settings → Environment Variables** do workspace. O código as lê como `$env.NOME`. A coluna "Valor usado" traz o valor combinado no projeto (README e modelo de domínio); confira no Xano o valor efetivo.

| Variável | Tipo | Valor usado | Onde é usada | Para quê |
|---|---|---|---|---|
| `TOKEN_TTL_SEGUNDOS` | Inteiro | 43200 (12 h) | `api/autenticacao/auth_login_verificar_post.xs` | Validade do token e da sessão |
| `INATIVIDADE_SEGUNDOS` | Inteiro | 3600 (1 h) | `api/autenticacao/auth_me_get.xs` | Tempo sem uso até a saída automática (devolvido ao frontend) |
| `CODIGO_TTL_SEGUNDOS` | Inteiro | 600 (10 min) | `function/auth/emitir_codigo.xs`, `auth_login_reenviar_post.xs` | Validade do código por e-mail |
| `CODIGO_REENVIO_SEGUNDOS` | Inteiro | 60 | `auth_login_post`, `auth_login_reenviar_post`, `auth_senha_solicitar_post` | Intervalo mínimo para reenviar o código |
| `CODIGO_TENTATIVAS` | Inteiro | 5 | `function/auth/conferir_codigo.xs` | Tentativas erradas até bloquear o código |
| `BREVO_API_KEY` | Secret | — | `function/auth/emitir_codigo.xs` | Chave da API de e-mail Brevo |
| `BREVO_REMETENTE` | E-mail | — | `function/auth/emitir_codigo.xs` | Remetente dos e-mails |
| `TOTEM_CHAVE` | Secret | — | `api/triagem/totem_tickets_post.xs` | Chave do dispositivo do Totem; o Xano recusa emissão sem ela |

Se uma variável numérica faltar, o endpoint responde com a mensagem "Variável de ambiente ... não configurada." ([runbook](../sustentacao/runbooks-e-depuracao.md)).

## Variáveis do frontend (`frontend/.env`)

Copie `frontend/.env.example` para `frontend/.env` e preencha. São lidas por `os.getenv` no servidor Reflex e nunca vão para o navegador.

| Variável | Obrigatória | Uso |
|---|---|---|
| `XANO_API_URL` | Sim | URL base do grupo **Pacientes** |
| `XANO_TRIAGEM_API_URL` | Sim | URL base do grupo **Triagem** (Totem, tickets, fichas) |
| `XANO_AUTH_API_URL` | Sim | URL base do grupo **Autenticacao** |
| `XANO_FILA_API_URL` | Sim | URL base do grupo **Fila** (médico e painéis) |
| `XANO_CADASTROS_API_URL` | Sim | URL base do grupo **Cadastros** (Administrador) |
| `TOTEM_CHAVE` | Para o Totem | Mesmo valor da variável do Xano. Lida em `estados/totem.py` só no servidor |
| `TEST_ADMIN_EMAIL`, `TEST_ADMIN_SENHA`, `TEST_RECEPCAO_*`, `TEST_MEDICO_*` | Só para testes | Contas reais de teste de cada perfil (`frontend/tests/test_api_autenticacao.py`) |

Variáveis usadas só pelos testes e pelo CI: `XANO_TEST_PROFILE` (perfil do Xano CLI, padrão `ps-impacta`), `REFLEX_E2E_BASE_URL` (endereço do app no E2E), `XANO_ISOLATED_API_HOST` e `XANO_ISOLATED_CONFIRMATION` (guarda da suíte controlled). No GitHub Actions, as URLs e o token do Xano ficam em **Settings → Secrets and variables → Actions**.

## Parâmetros editáveis pelo Administrador

Ficam na tabela `parametro` e são editados em **Administrador → Parâmetros**. Os limites estão em `function/cadastros/regra_parametro.xs`, e a carga inicial nas funções `inicializar_*`, que criam o valor quando ele falta, com auditoria "Sistema".

| Chave | Inicial | Limites | Regra que controla | Carga inicial |
|---|---|---|---|---|
| `LIMIAR_AMARELA` | 5 | 1–50 pontos | Escore a partir do qual a ficha é Amarela | `classificacao/inicializar_classificacao` |
| `LIMIAR_VERMELHA` | 10 | 2–60 pontos | Escore a partir do qual é Vermelha | idem |
| `IDADE_MINIMA_TABELA_ADULTA` | 16 | 12–21 anos | Idade mínima para o cálculo automático | idem |
| `IDADE_MINIMA_IDOSO` | 60 | 50–80 anos | Condição prioritária de idoso | idem |
| `IDADE_MAXIMA_CRIANCA` | 11 | 5–15 anos | Criança: Pediatria e condição prioritária | idem |
| `CICLO_PRE_TRIAGEM_PRIORITARIOS` | 2 | 1–10 tickets | Prioritários por ciclo na pré-triagem | `inicializar_parametros_fila` |
| `CICLO_PRE_TRIAGEM_NORMAIS` | 1 | 1–10 tickets | Normais por ciclo | idem |
| `INTERVALO_CHAMADA_SEGUNDOS` | 30 | 10–300 s | Espera depois da 1ª chamada (e entre chamadas do médico) | idem |
| `INTERVALO_REPETICAO_SEGUNDOS` | 10 | 5–120 s | Espera depois da 2ª e da 3ª chamada do ticket | idem |
| `TENTATIVAS_CHAMADA` | 3 | 1–10 | Chamadas por oportunidade | idem |
| `HORAS_EXPIRACAO` | 24 | 6–168 h | Prazo para registro parado | idem |
| `amarelas_por_ciclo` | 2 | 1–10 | Ciclo da fila médica: Amarelas por rodada | idem |
| `azuis_por_ciclo` | 1 | 1–10 | Azuis por rodada | idem |
| `tamanho_previsao` | 5 | 1–20 | Senhas da previsão (endpoint de previsão) | idem |
| `HORAS_PAINEL` | 2 | 1–24 h | Tempo que uma chamada fica nos painéis | idem |
| `ESPECIALIDADE_PADRAO` | Clínica Geral | especialidade ativa | Destino da ficha sem sintoma do catálogo | `direcionamento/inicializar_direcionamento` |
| `POSICAO_CICLO_PRE_TRIAGEM` | 0 | interno, não editável | Posição atual do ciclo da pré-triagem | `inicializar_parametros_fila` |

As **faixas de sinais vitais** (tabela `faixa_sinal_vital`) também são editáveis em Parâmetros. As iniciais estão em `function/classificacao/faixas_padrao.xs`, e o sistema impede faixas sobrepostas (`cadastros/faixa_sobrepoe`).

## Constantes fixas no código

| Constante | Valor | Onde |
|---|---|---|
| Fuso do PS | `America/Sao_Paulo` (UTC−3) | Xano (`format_timestamp`) e `frontend/ps_fila_prioritaria/comum.py` (`FUSO_BRASILIA`) |
| Limites aceitos dos sinais vitais | PA 40–300, FC 20–250, FR 4–80, T 25–45, SpO₂ 50–100, glicemia 10–1500 | `api/triagem/fichas_id_patch.xs` |
| Sintomas não listados por ficha | até 10, descrição de 3 a 80 caracteres | `estados/ficha.py` e `fichas_id_patch.xs` |
| Prefixo do ticket | `C` pediátrico, `P` preferencial, `N` normal | `comum.PREFIXO_TICKET` e `totem_tickets_post.xs` |
| Letra da senha | `V` Vermelha, `A` Amarela, `B` Azul | `function/direcionamento/formatar_senha.xs` |
| Sigla de especialidade | exatamente 3 letras, fixa depois de criada | `api/cadastros/especialidades_post.xs` |
| Página da auditoria | 50 registros; período até 31 dias | `api/cadastros/admin_auditoria_get.xs` |
| Atualização dos painéis | 5 s | `paginas/painel.py` (`INTERVALO_MS`) |

## Onde cada regra de negócio está implementada

| Regra | Implementação | Testes |
|---|---|---|
| Autorização por perfil | `function/auth/verificar_acesso.xs`, chamada no início de cada endpoint protegido | `tests/api/test_base_compartilhada.py`, testes 403 em `test_acompanhamento.py` e `test_chamada.py` |
| Login em duas etapas e código único | `auth_login_post.xs`, `auth_login_verificar_post.xs` (consumo atômico), `auth/emitir_codigo`, `auth/conferir_codigo` | `frontend/tests/test_api_autenticacao.py` |
| Pontuação e cor | `function/classificacao/pontuar.xs` (pura), `avaliar_ficha`, `sinais_da_ficha` | Testes nativos de `pontuar` (bordas das faixas) |
| Ajuste manual da cor | `classificacao/aplicar_ajuste`, `api/triagem/fichas_id_prioridade_post.xs` | Testes de estado da ficha |
| Destino da ficha | `direcionamento/escolher_destino` (pura), `destino_da_ficha` | Testes nativos |
| Senha e renumeração | `direcionamento/gerar_senha`, `formatar_senha`, `senha_reavaliada`, `reavaliar_senha` | Testes nativos |
| Ordem da pré-triagem | `api/triagem/tickets_proximo_post.xs` | Testes do estado da fila |
| Ordem da fila médica | `fila/proxima_ficha` (pura), `fila/prever_fila` | `tests/api/test_ordenacao.py`, testes nativos |
| Escolha entre filas e cobertura | `fila/selecionar_entre_filas`, `avaliar_cobertura`, `cobertura_atual`, `selecionar_atual` | `tests/api/test_selecao_entre_filas.py` |
| Chamada atômica, repetição, reentrada e desistência | `fila/chamar_proximo`, `fila/agir_chamada` | `tests/api/test_chamada.py` |
| Status operacional | `api/autenticacao/me_status_*.xs`; "Em atendimento" em `agir_chamada` | `test_base_compartilhada.py`, `test_status_equipe.py` |
| Auditoria | `function/registrar_alteracao.xs`, `api/cadastros/admin_auditoria_get.xs` | `test_base_compartilhada.py`, `test_acompanhamento.py` |
| Registros parados | `manutencao/expirou` (pura), `manutencao/expirar_registros`, `api/triagem/expiracao_*.xs` | Testes nativos e de estado |
| Painéis públicos | `api/fila/painel_get.xs` | `tests/api/test_painel.py` |
| Não deixar o sistema sem Administrador | `usuarios/deixa_sem_admin` | Testes de estado de usuários |

A lista completa das funções, com a descrição de cada uma, está em [funcoes-xano.md](funcoes-xano.md).

# Design técnico

## Contexto

As tabelas desta change já estão publicadas no Xano e versionadas em `backend/xano/table/`: `historico_alteracao`, `parametro`, `especialidade`, `especialidade_alternativa`, `sintoma` e `sintoma_especialidade`. Faltam as funções, a variável de ambiente, os endpoints de leitura e a carga. As decisões D1, D5, D6 e D7 do design de `add-cadastros-administrador` já descreviam esses itens; aqui eles são antecipados sem mudar o que foi decidido (motivação em proposal.md, seção Why). A base de autenticação (`verificar_acesso`, `api.py`, `tests/api/`) vem de `add-autenticacao-perfis`.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Um único jeito de gravar auditoria e de ler parâmetros, usado por todas as changes a partir da Fatia 2.
- Dados de exemplo disponíveis com um comando, para que as duplas das Fatias 2 a 4 testem sem depender de telas administrativas.

**Fora dos objetivos:**
- Cache de parâmetros: a leitura vai direto ao banco, o que basta para o volume acadêmico.
- Versionamento da carga inicial (migrations de dados): a carga é um ponto de partida, e depois os dados são mantidos pelo Administrador.

## Decisões

### D1. `registrar_alteracao(usuario_id, tipo_evento, entidade, registro_id, anterior, novo, justificativa?)`
É uma função do Xano chamada **dentro** do `db.transaction` da operação que altera os dados. O endpoint autenticado chama `verificar_acesso` e passa exclusivamente `$auth.id` como `usuario_id`; a função recarrega esse usuário e grava em `historico_alteracao`. Nenhum endpoint da API faz escrita, edição ou exclusão nessa tabela.
- **Por quê:** deixa a auditoria atômica com a operação (spec `auditoria`) e o formato fica centralizado.
- **Alternativa:** gatilho genérico por tabela. Descartada porque o XanoScript não oferece gatilho de banco e a justificativa depende da operação.
- **Observação:** a data/hora é o `created_at` da tabela já publicada. O design de `add-cadastros-administrador` (D1) chama esse campo de `criado_em`; vale o `.xs`.

### D2. Validar transações primeiro
A primeira task confere, com Run & Debug, que `db.transaction` desfaz a auditoria quando a operação falha depois de gravá-la. Se a transação não estiver disponível, a task fica bloqueada e a função NÃO DEVE ser usada como último passo nem fora da transação, pois isso violaria a atomicidade exigida pela spec.

### D3. `FUSO_HORARIO` como variável de ambiente
`FUSO_HORARIO = America/Sao_Paulo` no Xano. As changes que precisam de "o dia do PS" (ticket, senha, disponibilidade) convertem o instante com essa variável. Não existe tabela nem endpoint para isso.
- **Alternativa:** guardar o fuso como parâmetro na tabela `parametro`. Descartada porque o fuso não é regra clínica nem operacional editável pelo Administrador, e trocá-lo com dados já gravados deslocaria os dias.

### D4. `obter_parametro(chave)` e chaves definidas
A função lê `parametro` pela `chave` e converte o `valor` conforme o `tipo` (`INTEIRO` → número; `ESPECIALIDADE` → sigla, resolvida para a especialidade). Uma chave inexistente gera erro explícito, nunca um valor padrão escondido no código. Chaves e valores iniciais:

| Chave | Tipo | Valor inicial |
|---|---|---|
| `idade_minima_idoso` | INTEIRO | 60 |
| `idade_maxima_crianca` | INTEIRO | 11 |
| `amarelas_por_ciclo` | INTEIRO | 2 |
| `azuis_por_ciclo` | INTEIRO | 1 |
| `prioritarios_por_ciclo_pretriagem` | INTEIRO | 2 |
| `normais_por_ciclo_pretriagem` | INTEIRO | 1 |
| `tamanho_previsao` | INTEIRO | 5 |
| `especialidade_padrao` | ESPECIALIDADE | CLI |

As chaves do ciclo da fila pré-triagem vêm da decisão do PO de 25/10/2026 sobre os tipos de ticket do Totem (ver `add-totem` D5 e `docs/domain-model.md`): Pediátrico antes de Preferencial formam os prioritários, que alternam com os normais nessa proporção. São carregadas aqui e consumidas pela futura change de operação da fila pré-triagem. Os nomes de chave das idades são definidos aqui; os demais seguem o que as changes 4 a 7 já usam. O intervalo de 30 segundos, até 3 chamadas por oportunidade e uma reentrada são invariantes operacionais da baseline, não parâmetros editáveis. `limiar_risco_moderado` e `limiar_risco_alto` continuam na carga de `add-triagem-classificacao` (task 1.1 daquela change).

### D5. Carga inicial idempotente que não sobrescreve
A função `carga_inicial` é exposta por `POST admin/carga-inicial` (ADMINISTRADOR). Ela insere só o que falta: especialidades por `sigla`, sintomas por `nome`, parâmetros por `chave`. As relações (`especialidade_alternativa` e `sintoma_especialidade`) só são criadas para registros que a própria execução inseriu. Registros que já existem não são alterados. Cada inserção é auditada com tipo `CADASTRO`.
- **Por quê:** a spec exige que dados alterados depois da carga sejam mantidos. Um upsert que sobrescreve violaria isso.
- **Conteúdo:** catálogo de sintomas de `docs/domain-model.md` e especialidades iniciais. A carga não cria fallback por disponibilidade médica nem altera a especialidade clínica escolhida pelo direcionamento. Sala e vínculo operacional ficam em `add-cadastros-administrador`.

### D6. Endpoints de leitura
- `GET parametros`: autenticado, todos os perfis; devolve `chave`, `valor` e `tipo`.
- `GET especialidades`: autenticado; só ativas; `id`, `nome` e `sigla`.
- `GET sintomas`: autenticado; só ativos; `id`, `nome`, `grupo`, `pontuacao` (1–3) e destinos ordenados, conforme `docs/domain-model.md`, ordenados por grupo e nome.
Todos chamam `verificar_acesso` com os três perfis. A `add-cadastros-administrador` depois amplia `GET especialidades` e `GET sintomas` para que o Administrador veja também os inativos, sem mudar o contrato dos outros perfis.

## Riscos / Compromissos

- [A Sprint 1 entrega em 05/10 e já tem o [Setup] e a Fatia 1] → As tasks estão em ordem de dependência: auditoria e fuso primeiro (para a Fatia 2), depois parâmetros e carga (para a Fatia 3, na Sprint 2).
- [Duplicação temporária com `add-cadastros-administrador`] → Até ela passar por `/opsx:update`, as duas changes descrevem os mesmos itens. Vale esta change, que é a anterior na ordem de arquivamento.
- [A carga roda num workspace compartilhado pelas branches do Xano] → Por ser idempotente e não sobrescrever, rodar duas vezes em branches diferentes não corrompe dados.

## Plano de migração

As tabelas já existem. Implantação: criar a variável `FUSO_HORARIO`, publicar as funções e os endpoints e executar `POST admin/carga-inicial` uma vez com o primeiro Administrador. Rollback: remover os endpoints e as funções. Os dados carregados podem ficar, pois a `add-cadastros-administrador` vai precisar deles.

## Revisão de 13/11/2026

As changes seguintes entregaram esta base com outro desenho. Vale o que está publicado; as decisões abaixo substituem as anteriores.

- **D1 mantida.** `registrar_alteracao` é a única gravação em `historico_alteracao` e é chamada dentro do `db.transaction` de 31 endpoints. `tests/api/test_base_compartilhada.py` garante isso de forma estática: falha se um endpoint gravar no histórico diretamente, chamar a auditoria fora da transação ou usar `$input.usuario_id` como responsável.
- **D2 parcial.** A atomicidade foi validada em POST e PATCH de Pacientes (26/10/2026). A prova de falha induzida depois da auditoria continua pendente: exige função temporária no workspace compartilhado.
- **D3 substituída.** O fuso é fixo em `America/Sao_Paulo` no XanoScript, conforme `openspec/config.yaml` ("fuso fixo"). Não há variável `FUSO_HORARIO`. O teste falha se aparecer outro fuso.
- **D4 substituída.** Não há `obter_parametro`; cada regra lê `parametro` pela chave, e `cadastros/regra_parametro` define tipo e limites. As chaves seguem os nomes publicados (`IDADE_MINIMA_IDOSO`, `IDADE_MAXIMA_CRIANCA`, `CICLO_PRE_TRIAGEM_PRIORITARIOS`, `CICLO_PRE_TRIAGEM_NORMAIS`, `amarelas_por_ciclo`, `azuis_por_ciclo`, `tamanho_previsao`, `ESPECIALIDADE_PADRAO` etc.).
- **D5 substituída.** Não há `POST admin/carga-inicial`. As funções `inicializar_parametros_fila`, `classificacao/inicializar_classificacao` e `direcionamento/inicializar_direcionamento` inserem só o que falta quando a operação precisa. Os sintomas são cadastrados pelo Administrador. A carga automática não grava auditoria porque não há usuário responsável (pergunta aberta na proposta).
- **D6 substituída.** `GET parametros` é só do Administrador (`add-cadastros-administrador`, D7). `GET especialidades` e `GET sintomas` seguem as specs `especialidades` e `sintomas`.

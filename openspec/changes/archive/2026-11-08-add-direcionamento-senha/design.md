# Design técnico

## Contexto

- A ficha já tem cor (`prioridade_atual`, calculada ou ajustada), sintomas do catálogo (`ficha_sintoma`), sintomas digitados (`ficha_sintoma_livre`) e a função `classificacao/avaliar_ficha`, que lê ficha, paciente, idade na chegada e sintomas (change `add-classificacao-prioridade`).
- As tabelas `especialidade`, `sintoma_especialidade` (com `ordem`), `contador_senha` (índice único `data, especialidade_id`) e as colunas `especialidade_sugerida_id`, `especialidade_atribuida_id`, `senha`, `senha_numero` em `ficha_atendimento` já existem no servidor `v1`. Nenhum endpoint usa especialidades hoje; a carga do catálogo (`sintomas/carregar_catalogo_inicial`) não cria especialidades nem ligações.
- `ficha_atendimento` e `contador_senha` estão entre as tabelas divergentes (card do Backlog); no servidor, `contador_senha.ultimo_numero` não tem default.
- `parametro.tipo` já aceita `ESPECIALIDADE`.
- O `PATCH /fichas/{id}` só aceita ficha `EM_TRIAGEM`; não há edição depois da confirmação.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Regra de destino numa função pura, testável com blocos `test` como a `classificacao/pontuar`.
- Confirmação atômica que reaproveita `avaliar_ficha` e a auditoria existente.

**Fora dos objetivos:**
- Alterar ou republicar tabelas.
- Redirecionar fichas `AGUARDANDO` e trocar senha (outra change).

## Decisões

### D1. Carga `direcionamento/inicializar_direcionamento`
Cria, se não existirem pela sigla, as especialidades CAR (Cardiologia), CLI (Clínica Geral), NEU (Neurologia), ORT (Ortopedia) e PED (Pediatria); para cada linha do catálogo de `docs/domain-model.md` (nome do sintoma → especialidade), cria a ligação em `sintoma_especialidade` com `ordem` 1 se ainda não existir (sintoma localizado pelo nome; sintoma ausente é ignorado); cria `ESPECIALIDADE_PADRAO` (tipo `ESPECIALIDADE`, valor = ID de CLI) se não existir. Chamada no início da confirmação e no GET da ficha não (GET não grava; sem dados, a prévia fica vazia).
- *Alternativa:* estender `carregar_catalogo_inicial`. Descartada: aquela função tem teste próprio e escopo de catálogo; mexer nela mistura cargas.

### D2. Função pura `direcionamento/escolher_destino`
Entrada: idade, idade máxima de criança, ID de Pediatria, ID da especialidade padrão, lista de `{pontuacao, especialidade_ids[]}` dos sintomas do catálogo e mapa `especialidade_id → fichas AGUARDANDO`. Saída: `especialidade_id` e `motivo` (`PEDIATRIA`, `SINTOMAS`, `PADRAO`). Algoritmo: se idade ≤ idade de criança → Pediatria; se não há sintoma ligado → padrão; senão, para cada candidata, maior pontuação e soma; ordena por maior, soma (decrescentes), fila, ID (crescentes) e pega a primeira. Sem banco, os casos da spec viram blocos `test`.

### D3. Função `direcionamento/destino_da_ficha`
Lê a ficha via `classificacao/avaliar_ficha` (idade e sintomas), as ligações dos sintomas, a contagem de `AGUARDANDO` por especialidade candidata, Pediatria (sigla PED) e o parâmetro padrão, e chama `escolher_destino`. Usada pelo GET (prévia) e pela confirmação. Devolve também a especialidade (nome e sigla).

### D4. Senha via `contador_senha` dentro da transação
`direcionamento/gerar_senha` (data em `America/Sao_Paulo`, especialidade): lê a linha `(data, especialidade)`; se não existe, cria com `ultimo_numero: 1` (o índice único recusa uma criação simultânea, que é tentada de novo até 5 vezes, como o Totem); se existe, grava `ultimo_numero + 1` com valor explícito. Formata `COR-SIGLA-NNN` (mínimo 3 dígitos). Exclusividade sob concorrência real não comprovada (ver proposal).
- *Alternativa:* `max(senha_numero)+1` sobre fichas. Descartada: exigiria índice novo em `ficha_atendimento`, tabela divergente.

### D5. `POST fichas/{ficha_id}/confirmar-triagem`
Recepção/Triagem; em `db.transaction`: `inicializar_direcionamento`; ficha `EM_TRIAGEM`; `avaliar_ficha` sem pendência de RN04 e `prioridade_atual` não nula (`FICHA_SEM_PRIORIDADE`); `destino_da_ficha`; `gerar_senha`; grava `especialidade_sugerida_id`, `especialidade_atribuida_id`, `senha`, `senha_numero`, `status: AGUARDANDO`; `registrar_alteracao` com evento `TRIAGEM_CONFIRMADA`. Resposta: id, senha, especialidade.

### D6. `GET fichas/{ficha_id}/comprovante`
Recepção/Triagem; ficha `AGUARDANDO` ou `CHAMADO`; devolve só senha, prioridade, nome e sigla da especialidade e `chegada_em`. O Reflex renderiza `/recepcao/comprovante/[id]` com `@page { size: 80mm auto }` e chama `window.print()` ao abrir; "Reimprimir" reabre a mesma página.
- *Alternativa:* PDF no backend. Descartada: impressora térmica configurada no sistema operacional atende pelo navegador.

### D7. Tela da ficha
`GET fichas/{id}` passa a devolver `destino_previsto` (especialidade e motivo) para `EM_TRIAGEM`, e `senha`/`especialidade` para as demais. A ficha `EM_TRIAGEM` mostra "Destino previsto: Cardiologia" e o botão "Confirmar e gerar senha" (desabilitado sem cor, com as pendências); após confirmar, redireciona para o comprovante. A ficha que não está `EM_TRIAGEM` aparece só para leitura, com senha, especialidade e "Reimprimir".

## Riscos / Compromissos

- [Dados de especialidade ausentes no servidor] → A carga D1 roda na primeira confirmação; a prévia mostra "destino indisponível" até lá.
- [Concorrência na senha] → Limitação registrada; operação sequencial suportada.
- [Sintoma do catálogo renomeado no servidor] → A carga liga pelo nome; sintoma não encontrado fica sem ligação e cai na especialidade padrão.

## Plano de migração

1. Publicar funções e endpoints novos e `fichas/{ficha_id}` GET (`--dry-run` antes, push restrito, sem tabelas).
2. Publicar o Reflex.
3. Reversão: republicar o GET anterior e remover os endpoints novos; especialidades e ligações podem ficar.

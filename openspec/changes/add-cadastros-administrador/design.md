# Design técnico

## Contexto

Esta change parte da base criada por `add-autenticacao-perfis`: tabela `usuario`, função `verificar_acesso(perfis_permitidos)`, cliente `api.py` e `AuthState` no Reflex, testes pytest em `tests/api/`. Aqui entram as tabelas de configuração do domínio e a trilha de auditoria. As próximas changes (triagem, direcionamento, fila e painel) apenas leem essas tabelas.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Criar funções reutilizáveis para auditoria (`registrar_alteracao`) e parâmetros (`obter_parametro`), para que nenhuma change futura grave auditoria ou leia parâmetros de outro jeito.
- Criar uma única função "médico disponível agora", reutilizada pelo direcionamento e pela fila.
- Ter um componente Reflex de "tabela + formulário" reaproveitado pelas cinco telas administrativas.

**Fora dos objetivos:**
- Edição em massa ou importação por planilha.
- Disponibilidade recorrente (ex.: "toda segunda"): cada período é registrado por data.

## Decisões

### D1. Tabelas
- `especialidade`: `nome` (único, sem diferenciar caixa), `sigla` (3 letras, maiúsculas, única), `descricao`, `ativo`.
- `especialidade_alternativa`: `especialidade_id`, `alternativa_id`, `ordem`; único (`especialidade_id`, `alternativa_id`).
- `sintoma`: `nome` (único), `descricao`, `grupo` (enum), `prioridade_padrao` (enum `VERMELHA|AMARELA|AZUL`), `ativo`.
- `sintoma_especialidade`: `sintoma_id`, `especialidade_id`, `ordem`.
- `medico`: `usuario_id` (único), `registro_profissional`, `ativo`; `medico_especialidade`: `medico_id`, `especialidade_id`.
- `disponibilidade_medico`: `medico_id`, `inicio` e `fim` (timestamps).
- `parametro`: `chave` (única), `valor` (texto), `tipo` (`inteiro|especialidade`).
- `historico_alteracao`: `tipo_evento`, `entidade`, `registro_id`, `valor_anterior` (JSON), `valor_novo` (JSON), `justificativa`, `usuario_id`, `criado_em`.
- **Por quê:** segue o modelo conceitual (seção 17 do documento formal), com a troca de `medico.especialidade_id` por N:N (ver proposal.md, Impacto).

### D2. Listas ordenadas gravadas por substituição
As alternativas de uma especialidade e as especialidades de um sintoma são enviadas como lista completa (`PUT .../alternativas` com `[id1, id2]`). O backend valida a lista, apaga as linhas antigas e grava as novas, com `ordem` = posição, tudo dentro de uma transação.
- **Por quê:** evita endpoints de "subir/descer" item e deixa a validação de repetição num único lugar.
- **Alternativa:** CRUD item a item. Descartada porque exige lógica de reordenação e deixa estados intermediários inválidos.

### D3. Disponibilidade com `inicio`/`fim` como timestamp no fuso do PS
A tela envia data, hora inicial e hora final; o Xano converte para `inicio` e `fim` no fuso `America/Sao_Paulo` (variável de ambiente `FUSO_HORARIO`). A sobreposição é verificada com `novo.inicio < existente.fim E novo.fim > existente.inicio`. O intervalo é semiaberto: `[inicio, fim)`.
- **Por quê:** uma comparação só resolve "disponível agora" e os valores-limite ficam sem ambiguidade.
- Plantões que viram a noite (ex.: 19:00–07:00) são registrados como dois períodos, um em cada data.

### D4. Função `medicos_disponiveis(instante, especialidade_id?)`
Retorna os médicos ativos, com usuário ativo, que têm um período contendo `instante`, com filtro opcional por especialidade. O endpoint `GET especialidades/disponiveis` usa essa função. `add-direcionamento-senha` e `add-fila-chamada-medico` vão reutilizá-la.

### D5. Parâmetros em tabela chave-valor com validação por chave
`obter_parametro(chave)` lê e converte o valor. `PATCH parametros/{chave}` valida conforme a chave: limites e coerência entre idades (ver spec `parametros-regras`). Os valores iniciais são gravados pela carga inicial (D7).
- **Alternativa:** uma tabela com uma coluna por parâmetro. Descartada porque cada parâmetro novo exigiria migration e mudança de tela.

### D6. Auditoria via função `registrar_alteracao` dentro da transação da operação
Cada endpoint que altera dados abre uma transação no Xano (`db.transaction`), faz a alteração e chama `registrar_alteracao(tipo_evento, entidade, registro_id, anterior, novo, justificativa)`, que pega o usuário do token. Não existem endpoints de escrita para `historico_alteracao`.
- **Por quê:** garante o requisito "auditoria atômica com a operação" e centraliza o formato.

### D7. Carga inicial idempotente
A função `carga_inicial` do Xano, chamada por um endpoint restrito a ADMINISTRADOR (`POST admin/carga-inicial`), faz upsert por `sigla` (especialidades), `nome` (sintomas) e `chave` (parâmetros). Tabela de sintomas de exemplo (baseada na seção 6 do documento formal):

| Grupo | Vermelha | Amarela | Azul |
|---|---|---|---|
| Cardiovascular | Dor no peito (CAR), Desmaio (CAR) | Palpitação (CAR), Pressão no peito (CAR) | — |
| Respiratório | Falta de ar (CLI) | Chiado (CLI), Dor ao respirar (CLI) | Tosse (CLI) |
| Neurológico | Convulsão (NEU), Alteração da fala (NEU), Fraqueza localizada (NEU) | Confusão (NEU), Tontura (NEU) | Dor de cabeça (CLI) |
| Gastrointestinal | Sangramento (CLI) | Dor abdominal (CLI), Vômito (CLI) | Náusea (CLI), Diarreia (CLI) |
| Traumático/Ortopédico | — | Suspeita de fratura (ORT), Corte (ORT) | Queda (ORT), Torção (ORT), Dor em membro (ORT) |
| Geral | Reação alérgica (CLI) | Febre (CLI) | Dor (CLI), Mal-estar (CLI), Fraqueza (CLI) |

Alternativas iniciais: CAR → [CLI], NEU → [CLI], ORT → [CLI], PED → [CLI]. As prioridades de exemplo são modelagem acadêmica e devem ser revisadas pelo PO.

### D8. Telas administrativas no Reflex
Um componente `tabela_cadastro` (lista com filtro de situação, botão "Novo", edição em modal e ação ativar/desativar) é usado em `/admin/especialidades`, `/admin/sintomas` e `/admin/medicos`. `/admin/disponibilidade` mostra uma agenda por data, com a lista de períodos do dia. `/admin/parametros` mostra um formulário com os parâmetros. As mensagens de erro da API aparecem no campo correspondente.

## Riscos / Compromissos

- [Transações no plano gratuito do Xano] → Validar cedo (tarefa 1.2) que `db.transaction` está disponível. Se não estiver, gravar a auditoria por último e registrar a limitação no design.
- [Fuso horário errado desloca a disponibilidade] → Fuso em variável de ambiente e testes com valores-limite (06:59/07:00/19:00).
- [Prioridades de exemplo podem parecer protocolo clínico] → Aviso de "modelagem acadêmica" na tela de sintomas e no README.

## Plano de migração

Tabelas novas, sem impacto nas existentes. Rollback: remover as tabelas e endpoints criados.

## Questões em aberto

- Lista final de sintomas e prioridades padrão: a carga é só um ponto de partida, e o Administrador pode ajustá-la pela tela.

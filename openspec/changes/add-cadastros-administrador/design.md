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
- `sintoma`: `nome` (único), `descricao`, `grupo`, `pontuacao` (inteiro 1–3), `ativo`.
- `sintoma_especialidade`: `sintoma_id`, `especialidade_id`, `ordem`.
- `medico`: vínculo 1:1 com `usuario`, nome profissional/de exibição, CRM, especialidade de referência não restritiva e situação. `recepcao_triagem`: vínculo 1:1 com `usuario`, nome, CPF e especialidade de referência quando aplicável. A definição física dos vínculos pertence à implementação.
- `sala`: identificador, nome/número, descrição opcional e situação; associação operacional ao Médico atual, sem confundir Sala com especialidade.
- `disponibilidade_medico`: `medico_id`, `inicio` e `fim` (timestamps).
- `parametro`: `chave` (única), `valor` (texto), `tipo` (`inteiro|especialidade`).
- `historico_alteracao`: `tipo_evento`, `entidade`, `registro_id`, `valor_anterior` (JSON), `valor_novo` (JSON), `justificativa`, `usuario_id`, `criado_em`.
- **Por quê:** segue o modelo conceitual (seção 17 do documento formal), com a troca de `medico.especialidade_id` por N:N (ver proposal.md, Impacto).

### D2. Relação de direcionamento de sintomas
Os destinos e sua ordem seguem o catálogo consolidado em `docs/domain-model.md`. A relação sintoma–especialidade representa destino clínico, não uma cor. A regra de combinação quando vários sintomas são selecionados pertence à change `add-direcionamento-senha`. Alternativas entre especialidades não são fallback por ausência de Médico da especialidade.

### D3. Disponibilidade com `inicio`/`fim` como timestamp no fuso do PS
A tela envia data, hora inicial e hora final; o Xano converte para `inicio` e `fim` no fuso `America/Sao_Paulo` (variável de ambiente `FUSO_HORARIO`). A sobreposição é verificada com `novo.inicio < existente.fim E novo.fim > existente.inicio`. O intervalo é semiaberto: `[inicio, fim)`.
- **Por quê:** uma comparação só resolve "disponível agora" e os valores-limite ficam sem ambiguidade.
- Plantões que viram a noite (ex.: 19:00–07:00) são registrados como dois períodos, um em cada data.

### D4. Elegibilidade operacional de Médico
Retorna Médicos elegíveis ativos, com usuário ativo, período contendo o instante em `America/Sao_Paulo`, plantão não encerrado e status que permita novas atribuições. A especialidade de referência não é filtro. A distribuição entre médicos elegíveis e filas distintas deve seguir regra a definir em `add-fila-chamada-medico`; esta change não inventa balanceamento.

### D5. Parâmetros em tabela chave-valor com validação por chave
`obter_parametro(chave)` lê e converte o valor. `PATCH parametros/{chave}` valida conforme a chave: limites e coerência entre idades (ver spec `parametros-regras`). Os valores iniciais são gravados pela carga inicial (D7).
- **Alternativa:** uma tabela com uma coluna por parâmetro. Descartada porque cada parâmetro novo exigiria migration e mudança de tela.

### D6. Auditoria via função `registrar_alteracao` dentro da transação da operação
Cada endpoint que altera dados abre uma transação no Xano (`db.transaction`), faz a alteração e chama `registrar_alteracao(tipo_evento, entidade, registro_id, anterior, novo, justificativa)`, que pega o usuário do token. Não existem endpoints de escrita para `historico_alteracao`.
- **Por quê:** garante o requisito "auditoria atômica com a operação" e centraliza o formato.

### D7. Carga inicial idempotente
A função `carga_inicial` do Xano, chamada por um endpoint restrito a ADMINISTRADOR (`POST admin/carga-inicial`), faz carga idempotente de especialidades, catálogo de sintomas e parâmetros. O catálogo completo, com nome, grupo, pontos (1–3) e destino, é o da seção de sintomas em `docs/domain-model.md`; a carga é implementada por `add-base-compartilhada`, sem duplicação aqui. Não usar alternativas como fallback por disponibilidade de Médico. Pacientes dentro do limite pediátrico configurado são direcionados a Pediatria sem alterar seu escore ou prioridade.

### D8. Telas administrativas no Reflex
Um componente `tabela_cadastro` (lista com filtro de situação, botão "Novo", edição em modal e ação ativar/desativar) é usado em `/admin/especialidades`, `/admin/sintomas` e `/admin/medicos`. `/admin/disponibilidade` mostra uma agenda por data, com a lista de períodos do dia. `/admin/parametros` mostra um formulário com os parâmetros. As mensagens de erro da API aparecem no campo correspondente.

## Riscos / Compromissos

- [Transações no plano gratuito do Xano] → Validar cedo (tarefa 1.2) que `db.transaction` está disponível. Se não estiver, gravar a auditoria por último e registrar a limitação no design.
- [Fuso horário errado desloca a disponibilidade] → Fuso em variável de ambiente e testes com valores-limite (06:59/07:00/19:00).
- [Prioridades de exemplo podem parecer protocolo clínico] → Aviso de "modelagem acadêmica" na tela de sintomas e no README.

## Plano de migração

Tabelas novas, sem impacto nas existentes. Rollback: remover as tabelas e endpoints criados.

## Questões em aberto

- Definir na change funcional de direcionamento o desempate entre especialidades quando sintomas selecionados apontarem a destinos diferentes; manter pontuação e catálogo desta baseline sem atribuir cor ao sintoma.

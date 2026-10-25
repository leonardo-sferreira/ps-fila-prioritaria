# Design: Documentos do Paciente (RG e CRNM)

## Contexto

Ver `proposal.md` (Why) e `specs/pacientes/spec.md` (regras). Hoje a tabela `paciente` tem `cpf` obrigatório com índice único. A API (`pacientes_get.xs`, `pacientes_post.xs` e `pacientes_id_patch.xs`) usa a função `pacientes/normalizar_cpf`. O PATCH distingue "campo omitido" de "limpar" com um valor sentinela no telefone (`__TELEFONE_AUSENTE__`). No Reflex, `PacienteState` concentra pesquisa, cadastro e edição da tela `/recepcao/pacientes`.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Regras de documento validadas só no Xano, com códigos de erro estáveis que o Reflex traduz em mensagens.
- Reaproveitar o padrão já existente: função de normalização compartilhada e sentinela de campo omitido no PATCH.
- Manter válidos, sem migração, os pacientes já cadastrados.

**Fora dos objetivos:**
- Pesquisa textual ou parcial por documento.
- Qualquer mudança em ficha, triagem ou painel além de garantir que RG e CRNM não são expostos.

## Decisões

### D1. Esquema da tabela `paciente`
Novos campos: `estrangeiro` (bool, padrão `false`), `rg` (texto opcional), `rg_uf` (enum opcional com as 27 siglas) e `crnm` (texto opcional, índice único). `cpf` passa a ser opcional, mantendo o índice único. Documento ausente é gravado como `null`, nunca como texto vazio, para que vários estrangeiros sem CPF não colidam no índice único.
- **Alternativa:** tabela separada `documento_paciente` (tipo, número, emissor). Descartada porque, com só dois documentos e regras fixas por tipo de paciente, a tabela extra só aumenta joins e telas sem ganho.
- **Mudança de esquema passa pelo PO** (tarefa 1.1), como nas demais tabelas compartilhadas.

### D2. Funções de validação reutilizáveis
Criar `pacientes/validar_rg` (recebe RG e UF, devolve os dois normalizados ou erro `RG_INVALIDO` / `RG_UF_INVALIDA`) e `pacientes/normalizar_crnm` (remove espaços das pontas, converte para maiúsculas e valida tamanho e caracteres, ou devolve `CRNM_INVALIDA`). As duas são usadas por GET, POST e PATCH, como já acontece com `normalizar_cpf`.
- **Alternativa:** validar no Reflex. Descartada porque regras de negócio ficam no Xano (AGENTS.md); o Reflex pode ajudar com máscara, mas não decide.

### D3. Pesquisa: um endpoint com `cpf` ou `crnm`
`GET /pacientes` passa a aceitar exatamente um dos parâmetros `cpf` ou `crnm`. Os dois juntos, ou nenhum, retornam 400. A resposta é a mesma de hoje, acrescida de `estrangeiro`, `rg`, `rg_uf` e `crnm`.
- **Alternativa:** novo endpoint `GET /pacientes/crnm`. Descartada para não duplicar autorização, resposta e tratamento de erro.

### D4. Regras do cadastro por tipo de paciente
O `POST /pacientes` recebe `estrangeiro` (padrão `false`) e decide os obrigatórios:

```
estrangeiro = false  ->  CPF obrigatório e único | RG + UF obrigatórios (opcionais se criança) | CRNM proibida
estrangeiro = true   ->  CRNM obrigatória e única | CPF opcional (se vier: válido e único) | RG + UF opcionais (se vier um, vêm os dois)
```

Criança é quem tem, na data do cadastro em `America/Sao_Paulo`, idade até `idade_maxima_crianca`, lida com `obter_parametro` de `add-base-compartilhada` — nunca um 11 fixo no código. No PATCH vale a idade na data da alteração: a criança que fez 12 anos não é obrigada a completar o RG para mudar outro campo, mas não pode mais apagá-lo.

Erros de negócio: `CPF_DUPLICADO` (já existe), `RG_OBRIGATORIO`, `RG_INVALIDO`, `RG_UF_INVALIDA`, `CRNM_OBRIGATORIA`, `CRNM_INVALIDA`, `CRNM_DUPLICADA` e `CRNM_SOMENTE_ESTRANGEIRO`.

### D5. PATCH com RG e UF
RG e UF entram com o mesmo padrão de sentinela do telefone (`__RG_AUSENTE__`): omitido não altera; vazio limpa RG e UF juntos, mas só para estrangeiro (para brasileiro retorna `RG_OBRIGATORIO`). `cpf`, `crnm` ou `estrangeiro` no corpo retornam 400. Paciente brasileiro antigo, sem RG, pode completar RG e UF, e não é obrigado a fazê-lo para alterar outro campo.

### D6. Tela da Recepção/Triagem
Uma opção "Paciente estrangeiro" no topo da identificação muda a pesquisa de CPF para CRNM e define os campos do formulário: brasileiro com CPF, RG e UF obrigatórios; estrangeiro com CRNM obrigatória e CPF, RG e UF opcionais. A UF é uma lista de seleção com as 27 siglas. Os códigos de erro do D4 viram mensagens em português. Na edição, CPF, CRNM e a opção de estrangeiro aparecem só para leitura.

## Riscos / Trade-offs

- [`obter_parametro` ainda não implementado (`add-base-compartilhada`)] → A tarefa 2.2 depende da 2.1 de `add-base-compartilhada`; não usar valor fixo como atalho.
- [Índice único com `cpf` nulo] → Gravar sempre `null` em vez de texto vazio (D1) e testar dois estrangeiros sem CPF na tarefa 2.6.
- [Cadastro de brasileiro sem RG deixa de funcionar para quem chama a API] → O único cliente é o Reflex, atualizado na mesma change; o grupo 3 das tasks é entregue junto com o Xano.
- [Estrangeiro que depois obtém CPF não consegue incluí-lo] → Aceito nesta change (fora do escopo); fica registrado para uma change futura de correção cadastral.
- [Documentos são dados pessoais sensíveis] → Mesmas regras do CPF: só operações autorizadas, nunca no painel nem em logs de erro.

## Plano de migração

1. PO publica os campos de D1 na tabela `paciente` (registros existentes ficam com `estrangeiro = false` e documentos nulos).
2. Publicar funções e endpoints do Xano; rodar os testes de API.
3. Publicar o Reflex com a tela nova.
4. Rollback: voltar os endpoints à versão anterior. Os campos novos podem ficar no esquema, porque são opcionais e não afetam a versão antiga.

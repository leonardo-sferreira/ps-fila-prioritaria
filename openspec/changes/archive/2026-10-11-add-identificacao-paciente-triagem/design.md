# Design técnico

## Contexto

Esta change usa `verificar_acesso` de `add-autenticacao-perfis` e `registrar_alteracao` de `add-base-compartilhada`. Ela é limitada a Paciente: não consome, cria ou altera tickets e não abre Fichas.

## Objetivos / Fora dos objetivos

**Objetivos:**

- Validar CPF no backend, com representação canônica de 11 dígitos.
- Garantir uma única pessoa por CPF pela validação da API e pelo índice único existente.
- Expor pesquisa, cadastro e atualização parcial autorizados e auditáveis.

**Fora dos objetivos:**

- Ticket, fila, chamada, painel, Ficha e classificação.
- Alteração de schema da tabela `paciente`.

## Decisões

### D1. Dados de Paciente

A tabela `paciente` existente contém `id`, `created_at`, `cpf`, `nome`, `data_nascimento`, `telefone`, `ativo` e índice único em CPF. Ela atende esta Sprint. O CPF persistido é o valor canônico sem pontuação.

### D2. CPF normalizado e validado no Xano

A função reutilizável `normalizar_cpf` remove a formatação aceita, exige 11 dígitos, recusa sequências repetidas e confere os dois dígitos verificadores. GET, POST e a verificação de duplicidade a usam antes de consultar ou gravar. A máscara Reflex é somente usabilidade.

### D3. API, acesso e auditoria

- `GET /pacientes?cpf=` normaliza e valida o CPF antes de pesquisar e não cria cadastro.
- `POST /pacientes` exige CPF válido e único, nome e nascimento; o índice único é a barreira final contra duplicidade e o conflito retorna 400 com o erro de negócio `CPF_DUPLICADO`.
- `PATCH /pacientes/{id}` aceita somente nome, data de nascimento e telefone. CPF no corpo, corpo vazio ou dados inválidos retornam 400; Paciente inexistente retorna 404.
- PATCH com valores iguais retorna 200 e `alterado: false`, sem update ou auditoria. Alteração real retorna 200 e `alterado: true`, executa update e registra auditoria.
- A integração de autorização por perfil e auditoria permanece pendente das changes `add-autenticacao-perfis` e `add-base-compartilhada`. Nesta Sprint não há substituto, mock ou infraestrutura paralela.

### D4. Interface

A área protegida de Recepção/Triagem recebe CPF, busca o Paciente e apresenta seus dados ou formulário de cadastro. A edição não permite CPF. `Continuar` é visual e não persistente: não cria ou abre Ficha, não cria/altera ticket, não inicia classificação e não preserva `paciente_id` para Sprint futura.

## Riscos e pendências

- Confirmar no Confluence os textos formais de RF03–RF05 e CA01 antes do aceite final.
- Validar em ambiente Xano a infraestrutura de auditoria de `add-base-compartilhada`, sem criar mecanismo paralelo.

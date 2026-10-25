# Tarefas

## 1. Decisões e esquema (PO)

- [x] 1.0 [PO] Confirmar se o RG é obrigatório para crianças — decidido em 25/10/2026: opcional até `idade_maxima_crianca`; registrado no D4 e nos cenários "Criança brasileira sem RG" e "Limite de idade do RG opcional"
- [ ] 1.1 [PO] Publicar na tabela `paciente` os campos do D1 (`estrangeiro` bool padrão false, `rg` opcional, `rg_uf` enum opcional com as 27 siglas, `crnm` opcional com índice único) e tornar `cpf` opcional mantendo o índice único; verificar o `.xs` exportado em `backend/xano/table/paciente.xs` e que os pacientes existentes ficaram com `estrangeiro = false` e documentos nulos
- [ ] 1.2 Atualizar `docs/domain-model.md` (Paciente: campos, tipos de paciente, RN01 com pesquisa por CPF ou CRNM, RN02 com unicidade de CPF e CRNM) e verificar que o texto bate com a spec delta

## 2. Xano — validação e API

- [ ] 2.1 [Xano] Criar as funções `pacientes/validar_rg` e `pacientes/normalizar_crnm` (D2); verificar com Run & Debug os valores-limite do RG (4, 5, 14 e 15 caracteres), RG com ponto/traço/espaço, RG com X final, UF inválida, RG sem UF e UF sem RG, e da CRNM (6, 7, 10 e 11 caracteres, minúsculas convertidas)
- [ ] 2.2 [Xano] Ajustar `POST /pacientes` às regras do D4 para brasileiro, criança brasileira e estrangeiro, lendo `idade_maxima_crianca` com `obter_parametro` (depende da tarefa 2.1 de `add-base-compartilhada`) e gravando documento ausente como `null`; verificar cada código de erro do D4, o limite de 11/12 anos sem RG e o cadastro de estrangeiro só com CRNM, com CPF e com RG
- [ ] 2.3 [Xano] Ajustar `GET /pacientes` para aceitar exatamente um entre `cpf` e `crnm` (D3) e devolver `estrangeiro`, `rg`, `rg_uf` e `crnm`; verificar pesquisa por CRNM em maiúsculas e minúsculas, CRNM inexistente, CRNM inválida e 400 com os dois parâmetros ou nenhum
- [ ] 2.4 [Xano] Ajustar `PATCH /pacientes/{id}` com RG e UF pelo sentinela `__RG_AUSENTE__` (D5); verificar completar RG de paciente antigo, apagar RG de brasileiro (400 `RG_OBRIGATORIO`), limpar RG de estrangeiro, RG omitido, `alterado: false` para valores iguais e 400 com `cpf`, `crnm` ou `estrangeiro` no corpo
- [ ] 2.5 [Xano] Exportar os XanoScripts alterados e criados para `backend/xano/` e verificar que correspondem ao publicado na branch `v1`
- [ ] 2.6 [Testes] Escrever testes de API cobrindo os cenários da spec delta, incluindo os valores-limite de RG e CRNM, CRNM duplicada em caixa diferente, mesmo RG em UFs diferentes e dois estrangeiros sem CPF cadastrados sem colisão no índice; verificar que todos passam

## 3. Reflex — tela de identificação

- [ ] 3.1 [Reflex] Incluir em `PacienteState` os campos `estrangeiro`, `rg`, `rg_uf` e `crnm`, a pesquisa por CRNM e o envio no cadastro e na edição (RG com controle de campo alterado, como o telefone); verificar com testes em `frontend/tests/test_paciente_state.py` o corpo enviado em cada caso
- [ ] 3.2 [Reflex] Na tela `/recepcao/pacientes`, adicionar a opção "Paciente estrangeiro", que troca a pesquisa de CPF para CRNM e ajusta os campos obrigatórios (D6), com UF em lista de seleção; verificar manualmente brasileiro com CPF, RG e UF, estrangeiro só com CRNM e estrangeiro com CPF
- [ ] 3.3 [Reflex] Traduzir os códigos de erro do D4 em mensagens em português e mostrar CPF, CRNM e a opção de estrangeiro só para leitura na edição; verificar com testes de estado e pelo roteiro manual de cada erro
- [ ] 3.4 [Reflex] Verificar que `reflex compile` (ou `reflex run`) conclui sem erro e que a suíte `python -m pytest` passa

## 4. Integração, documentação externa e aceite

- [ ] 4.1 [Aceite] Verificar ponta a ponta, pela tela e contra o Xano: cadastro de brasileiro com RG, cadastro de estrangeiro com CRNM, pesquisa por CPF e por CRNM, completar RG de paciente antigo e abrir ficha (`Continuar`) para um estrangeiro
- [ ] 4.2 [Figma] Atualizar as telas 3 e 3a a 3e com a opção "Paciente estrangeiro", RG/UF e CRNM, incluindo uma variante de estrangeiro; verificar pela captura da seção
- [ ] 4.3 [PO] Registrar no Confluence a mudança da seção 5, RF03 a RF05, RN01 e RN02 (página de atualização ligada ao documento formal, como a do Totem) e verificar o link no card do Trello

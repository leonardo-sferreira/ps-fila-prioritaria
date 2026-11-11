# Tarefas

Revisada em 11/11/2026 (decisões do PO: escopo completo do card; o cadastro de médico e o de Recepção/Triagem criam o login junto). Ver `proposal.md` e `design.md` (D1–D10).

## 1. Documentos

- [x] 1.1 Atualizar `docs/domain-model.md` e `docs/project-overview.md`:
  - Sala, com vínculo `medico.sala_id` e desativação que desfaz o vínculo;
  - Recepção/Triagem, com login junto;
  - plantão noturno e regra de remoção;
  - parâmetros e faixas editáveis.

  Verificar com `openspec validate add-cadastros-administrador`
  - Evidência (11/11/2026): Sala (`medico.sala_id`), Recepção/Triagem com login, regras do plantão (noturno, sobreposição, remoção) em `docs/domain-model.md`; regra global em `docs/project-overview.md`. `openspec validate` aceita a change.

## 2. Xano — esquema e funções puras

- [x] 2.1 Tabelas novas `sala` e `recepcao_triagem` e campo `sala_id` em `medico` (D5). Verificar com `xano_validate_xanoscript` e com a comparação de campos contra o servidor
  - Evidência (11/11/2026): `table/sala.xs`, `table/recepcao_triagem.xs` e `sala_id` em `table/medico.xs`, válidos. Antes, um `xano workspace pull` (CLI 1.3.4) confirmou que os campos de `medico` no servidor são os mesmos do repositório.

- [x] 2.2 Funções puras com testes inline:
  - `cadastros/periodo_plantao` (D6): diurno, noturno, fim igual ao início, formato inválido;
  - `cadastros/regra_parametro` (D7): limites e chaves internas e desconhecidas;
  - `cadastros/faixa_sobrepoe` (D8): sobreposição, encostadas, extremos abertos, condição diferente.

  Verificar com `xano_validate_xanoscript`
  - Evidência (11/11/2026): 16 testes inline: `periodo_plantao` 5, `regra_parametro` 5, `faixa_sobrepoe` 6. Todos os arquivos válidos no `xano_validate_xanoscript`.

## 3. Xano — endpoints (grupo Cadastros, ADMINISTRADOR, transação e auditoria)

- [x] 3.1 Especialidades: `PATCH especialidades/{id}` (nome e descrição) e `PATCH especialidades/{id}/ativo`, com as recusas `ESPECIALIDADE_COM_FICHAS` e especialidade padrão. `GET especialidades` já existe
  - Evidência (11/11/2026): `especialidades_id_patch.xs` e `especialidades_id_ativo_patch.xs`, com recusa da especialidade padrão e `ESPECIALIDADE_COM_FICHAS`.

- [x] 3.2 Sintomas: `GET sintomas` (todos, com destinos), `POST sintomas`, `PATCH sintomas/{id}` e `PATCH sintomas/{id}/ativo`
  - Evidência (11/11/2026): 4 endpoints; destinos gravados por `cadastros/gravar_vinculos` com ordem; especialidades conferidas por `cadastros/especialidades_validas`.

- [x] 3.3 Médicos: `GET medicos`, `POST medicos` (cria o login), `PATCH medicos/{id}` e `PATCH medicos/{id}/ativo` (login junto; recusa com ficha CHAMADO) (D3, D4)
  - Evidência (11/11/2026): 4 endpoints; o `POST` cria `usuario` (MEDICO) e `medico` na mesma transação; a desativação leva o login junto e recusa `MEDICO_COM_FICHA_CHAMADA`.

- [x] 3.4 Recepção/Triagem: `GET recepcao`, `POST recepcao`, `PATCH recepcao/{id}` e `PATCH recepcao/{id}/ativo` (D3, D5)
  - Evidência (11/11/2026): 4 endpoints; CPF por `pacientes/normalizar_cpf` e único; login junto.

- [x] 3.5 Salas: `GET salas`, `POST salas`, `PATCH salas/{id}` e `PATCH salas/{id}/ativo` (desfaz o vínculo com médicos)
  - Evidência (11/11/2026): 4 endpoints; desativar a sala zera `sala_id` dos médicos e registra quem foi desvinculado na auditoria.

- [x] 3.6 Plantões:
  - `GET disponibilidade` (por dia);
  - `POST disponibilidade`;
  - `PATCH disponibilidade/{id}`;
  - `DELETE disponibilidade/{id}` (só não iniciado);
  - `GET medicos/me/disponibilidade` (MEDICO) (D6).
  - Evidência (11/11/2026): 5 endpoints e `cadastros/plantao_sobreposto` (semiaberto); `PLANTAO_INICIADO` impede remover ou mudar o início de período iniciado.

- [x] 3.7 Parâmetros e faixas:
  - `GET parametros` (com limites);
  - `PATCH parametros/{chave}` generalizado (D7), mantendo o reinício do ciclo;
  - `GET faixas`;
  - `PATCH faixas/{id}` (D8).
  - Evidência (11/11/2026): `GET parametros`, `PATCH parametros/{chave}` generalizado (mantém o `guid` e o reinício do ciclo da fila médica), `GET faixas` e `PATCH faixas/{id}`.

- [x] 3.8 Validar todos os arquivos com `xano_validate_xanoscript`; publicar na `v1` (`--dry-run` antes; o PO roda o push) e rodar `xano unit_test run_all`
  - Evidência (11/11/2026): o `--dry-run` mostrou 2 tabelas criadas, `medico` com ADD_FIELD, 8 funções e 26 endpoints criados e 1 atualizado, sem remoções; o PO publicou os 41 arquivos.
  - O `unit_test run_all` pegou uma falha em `faixa_sobrepoe`: o Xano compara de forma frouxa (`false == null` e `0 == null` são verdadeiros), então a glicemia sem gravidade colidia com a com gravidade. Corrigido com `is_null` (também no `PATCH faixas/{id}`) e com um teste novo para limite 0.
  - Depois da republicação: **102 passando, 0 falhas**.

## 4. Reflex

- [x] 4.1 `XANO_CADASTROS_API_URL` no `.env.example`; menu do Administrador e área inicial com atalhos (D9)
  - Evidência (11/11/2026): `XANO_CADASTROS_API_URL` no `.env.example`; `menu_admin` com 8 abas, usando o `menu_abas` comum com a Recepção.

- [x] 4.2 Componente `tabela_cadastro` e páginas `/admin/especialidades`, `/admin/sintomas` e `/admin/salas`
  - Evidência (11/11/2026): mixin `CadastroBase` (lista, filtro, busca, diálogo, salvar, ativar) e as telas de especialidades, sintomas (destinos em ordem) e salas.

- [x] 4.3 Páginas `/admin/medicos` e `/admin/recepcao` (login junto, várias especialidades, sala)
  - Evidência (11/11/2026): telas de médicos e Recepção/Triagem, com senha só na criação, várias especialidades e sala.

- [x] 4.4 Página `/admin/disponibilidade` (seletor de dia, lista e formulário)
  - Evidência (11/11/2026): tela de plantões com seletor de dia, "+1 dia" no noturno e "Remover" só em plantão agendado.

- [x] 4.5 Página `/admin/parametros` (parâmetros e faixas)
  - Evidência (11/11/2026): tela de parâmetros (lista com limites; especialidade padrão por seleção) e faixas (diálogo de edição).

- [x] 4.6 "Meus plantões" na tela do Médico, só leitura
  - Evidência (11/11/2026): cartão "Meus plantões" na tela do Médico, carregado no `on_load` de `/medico`.

- [x] 4.7 Testes de estado das telas com a API simulada; verificar que a suíte unitária passa e que o app compila e abre
  - Evidência (11/11/2026): `tests/test_cadastros_state.py` com 20 casos; suíte unitária com 217 passando. Prévia com dados de exemplo (rota temporária, já removida) em Médicos, diálogo "Novo médico", Especialidades, Sintomas, Plantões e Parâmetros, sem erro de JS; `/admin/*` sem sessão volta para o login.

## 5. Verificação ponta a ponta

- [x] 5.1 Roteiro manual com o Administrador logado:
  - criar uma sala, um médico com duas especialidades e sala, e um plantão para agora;
  - como Médico, ver "Plantão vigente", ficar disponível e chamar;
  - ajustar um parâmetro e uma faixa;
  - desativar a sala e conferir que o médico ficou sem sala;
  - conferir os eventos na auditoria.
  - Evidência (11/11/2026): roteiro manual feito pelo PO com o Administrador logado; aprovado ("testei e gostei"). Ajustes futuros entram em changes novas.

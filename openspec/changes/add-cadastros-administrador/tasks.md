# Tarefas

Revisada em 11/11/2026 (decisões do PO: escopo completo do card; o cadastro de médico e o de Recepção/Triagem criam o login junto). Ver `proposal.md` e `design.md` (D1–D10).

## 1. Documentos

- [ ] 1.1 Atualizar `docs/domain-model.md` e `docs/project-overview.md`:
  - Sala, com vínculo `medico.sala_id` e desativação que desfaz o vínculo;
  - Recepção/Triagem, com login junto;
  - plantão noturno e regra de remoção;
  - parâmetros e faixas editáveis.

  Verificar com `openspec validate add-cadastros-administrador`

## 2. Xano — esquema e funções puras

- [ ] 2.1 Tabelas novas `sala` e `recepcao_triagem` e campo `sala_id` em `medico` (D5). Verificar com `xano_validate_xanoscript` e com a comparação de campos contra o servidor
- [ ] 2.2 Funções puras com testes inline:
  - `cadastros/periodo_plantao` (D6): diurno, noturno, fim igual ao início, formato inválido;
  - `cadastros/regra_parametro` (D7): limites e chaves internas e desconhecidas;
  - `cadastros/faixa_sobrepoe` (D8): sobreposição, encostadas, extremos abertos, condição diferente.

  Verificar com `xano_validate_xanoscript`

## 3. Xano — endpoints (grupo Cadastros, ADMINISTRADOR, transação e auditoria)

- [ ] 3.1 Especialidades: `PATCH especialidades/{id}` (nome e descrição) e `PATCH especialidades/{id}/ativo`, com as recusas `ESPECIALIDADE_COM_FICHAS` e especialidade padrão. `GET especialidades` já existe
- [ ] 3.2 Sintomas: `GET sintomas` (todos, com destinos), `POST sintomas`, `PATCH sintomas/{id}` e `PATCH sintomas/{id}/ativo`
- [ ] 3.3 Médicos: `GET medicos`, `POST medicos` (cria o login), `PATCH medicos/{id}` e `PATCH medicos/{id}/ativo` (login junto; recusa com ficha CHAMADO) (D3, D4)
- [ ] 3.4 Recepção/Triagem: `GET recepcao`, `POST recepcao`, `PATCH recepcao/{id}` e `PATCH recepcao/{id}/ativo` (D3, D5)
- [ ] 3.5 Salas: `GET salas`, `POST salas`, `PATCH salas/{id}` e `PATCH salas/{id}/ativo` (desfaz o vínculo com médicos)
- [ ] 3.6 Plantões:
  - `GET disponibilidade` (por dia);
  - `POST disponibilidade`;
  - `PATCH disponibilidade/{id}`;
  - `DELETE disponibilidade/{id}` (só não iniciado);
  - `GET medicos/me/disponibilidade` (MEDICO) (D6).
- [ ] 3.7 Parâmetros e faixas:
  - `GET parametros` (com limites);
  - `PATCH parametros/{chave}` generalizado (D7), mantendo o reinício do ciclo;
  - `GET faixas`;
  - `PATCH faixas/{id}` (D8).
- [ ] 3.8 Validar todos os arquivos com `xano_validate_xanoscript`; publicar na `v1` (`--dry-run` antes; o PO roda o push) e rodar `xano unit_test run_all`

## 4. Reflex

- [ ] 4.1 `XANO_CADASTROS_API_URL` no `.env.example`; menu do Administrador e área inicial com atalhos (D9)
- [ ] 4.2 Componente `tabela_cadastro` e páginas `/admin/especialidades`, `/admin/sintomas` e `/admin/salas`
- [ ] 4.3 Páginas `/admin/medicos` e `/admin/recepcao` (login junto, várias especialidades, sala)
- [ ] 4.4 Página `/admin/disponibilidade` (seletor de dia, lista e formulário)
- [ ] 4.5 Página `/admin/parametros` (parâmetros e faixas)
- [ ] 4.6 "Meus plantões" na tela do Médico, só leitura
- [ ] 4.7 Testes de estado das telas com a API simulada; verificar que a suíte unitária passa e que o app compila e abre

## 5. Verificação ponta a ponta

- [ ] 5.1 Roteiro manual com o Administrador logado:
  - criar uma sala, um médico com duas especialidades e sala, e um plantão para agora;
  - como Médico, ver "Plantão vigente", ficar disponível e chamar;
  - ajustar um parâmetro e uma faixa;
  - desativar a sala e conferir que o médico ficou sem sala;
  - conferir os eventos na auditoria.

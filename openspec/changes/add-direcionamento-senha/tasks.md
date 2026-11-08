# Tarefas

Revisada em 08/11/2026 (Rev. 2.1 e decisões do PO). Ver `proposal.md` e `design.md` (D1–D7).

## 1. Documentos de domínio

- [x] 1.1 Atualizar `docs/domain-model.md` (Especialidade: siglas CAR/CLI/NEU/ORT/PED; regras de destino com o desempate da §14.2 e a especialidade padrão; Ficha: confirmação exige cor; parâmetro "Especialidade padrão" deixa de ser condicional) e `docs/project-overview.md` (fluxo da triagem até a senha). Verificar com busca por "pertence à spec funcional de direcionamento" e "se prevista pela spec" que as pendências antigas saíram

## 2. Xano — dados e regra de destino

- [x] 2.1 Criar `function/direcionamento/inicializar_direcionamento.xs` (D1; usada pela 3.1) com as 5 especialidades, as ligações do catálogo e `ESPECIALIDADE_PADRAO`, idempotente. Verificar com `xano_validate_xanoscript`
- [x] 2.2 Criar `function/direcionamento/escolher_destino.xs`, função pura (D2; usada pela 2.3), com blocos `test`: um sintoma; maior pontuação vence; empate na maior decidido pela soma; empate decidido pela fila; empate total pelo menor ID; 11 anos → Pediatria; 12 anos segue os sintomas; sem sintoma ligado → padrão. Verificar com `xano_validate_xanoscript`
- [x] 2.3 Criar `function/direcionamento/destino_da_ficha.xs` (D3; usada pela 3.1 e 3.3). Verificar com `xano_validate_xanoscript`
- [x] 2.4 Criar `function/direcionamento/gerar_senha.xs` (D4; usada pela 3.1) com teste de formatação (`V-CLI-001`, `B-CLI-1000`). Verificar com `xano_validate_xanoscript`

## 3. Xano — endpoints

- [x] 3.1 Criar `api/triagem/fichas_id_confirmar_triagem_post.xs` (D5) com as recusas de ficha fora de `EM_TRIAGEM`, sem prioridade, sem sintoma/observação, especialidade padrão ausente e perfil sem permissão, e auditoria `TRIAGEM_CONFIRMADA`. Verificar com `xano_validate_xanoscript`
- [x] 3.2 Criar `api/triagem/fichas_id_comprovante_get.xs` (D6) só com os campos permitidos e recusa para fichas sem senha ativa. Verificar com `xano_validate_xanoscript`
- [x] 3.3 Em `api/triagem/fichas_id_get.xs`, devolver `destino_previsto` para `EM_TRIAGEM` e `senha`/`especialidade` para as demais (D7). Verificar com `xano_validate_xanoscript`
- [x] 3.4 Publicar na `v1` os arquivos das tarefas 2.1–3.3 (`--dry-run` antes, push restrito, sem tabelas); rodar os testes unitários das funções no Xano; conferir com `xano workspace pull`
  - Evidência (08/11/2026): `--dry-run` com 5 funções novas, 2 endpoints novos e `fichas/{ficha_id}` GET alterado, sem tabelas; push feito pelo PO. A primeira rodada de `xano unit_test run_all` mostrou 4 falhas em `escolher_destino` com duas ou mais candidatas (`Unable to locate var: atual.soma`: dentro de objeto literal, `get:$chave:0, soma:` engolia a chave seguinte); corrigido calculando os valores em variáveis próprias, também em `destino_da_ficha`, e republicado. Rodada final: os 12 testes do direcionamento passam (9 de `escolher_destino`, 3 de `formatar_senha`); os 3 que falham são de `pacientes/{paciente_id}` (telefone), anteriores. `xano workspace pull` confirmou as funções, `comprovante` GET, `confirmar-triagem` POST e `destino_previsto` no GET da ficha. Suíte do Reflex com 143 passando; `reflex export` compila.

## 4. Reflex

- [x] 4.1 No `FichaState`: ler `destino_previsto`, `senha` e `especialidade`; criar `confirmar_triagem` (bloqueado sem cor ou com alteração não salva; redireciona para o comprovante) e `reimprimir`. Testes de estado: envio, bloqueios, redirecionamento e leitura dos campos. Verificar que a suíte unitária passa
- [x] 4.2 Criar `ComprovanteState` e a página `/recepcao/comprovante/[id]` em 80 mm com impressão automática e "Voltar" (D6), sem dados pessoais. Teste de estado da carga do comprovante. Verificar que `reflex export` compila
- [x] 4.3 Na tela da ficha: "Destino previsto", botão "Confirmar e gerar senha" e, fora de `EM_TRIAGEM`, modo leitura com senha, especialidade e "Reimprimir" (D7). Verificar que `reflex export` compila

## 5. Verificação ponta a ponta

- [ ] 5.1 Logado como Recepção/Triagem: ficha de adulto com "Dor ou pressão no peito" e cor Amarela → confirmar → `A-CAR-001` no comprovante sem nome/CPF; ficha com "Palpitações" e "Convulsão em atividade" → Neurologia; paciente de 11 anos → Pediatria; ficha só com observação → Clínica Geral; ficha sem cor → confirmação recusada; reimpressão com a mesma senha. Roteiro manual, pois o login exige código por e-mail

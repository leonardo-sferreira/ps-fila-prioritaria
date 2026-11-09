# Tarefas

## 1. Documentos de domínio

- [ ] 1.1 Atualizar `docs/domain-model.md` (Ficha: em `AGUARDANDO`, sintomas, sinais vitais, gestação e ajuste continuam editáveis pela Recepção/Triagem, com recálculo, novo destino e troca de senha; a cor nunca fica vazia em `AGUARDANDO`; `chegada_em` não muda; regra da senha na reavaliação) e `docs/project-overview.md` (fluxo da triagem: correção depois da senha com aviso de reimpressão). Verificar com busca por "AGUARDANDO" que os dois documentos descrevem a reavaliação sem contradizer a tabela de estados.

## 2. Xano — funções

- [ ] 2.1 Verificar no Run & Debug, antes de alterar endpoints, se `classificacao/avaliar_ficha` e `direcionamento/destino_da_ficha` enxergam, dentro de `db.transaction`, os dados gravados antes na mesma transação; registrar o resultado aqui e, se não enxergarem, ajustar a D3 do design antes de seguir.
- [ ] 2.2 Criar `function/direcionamento/senha_reavaliada.xs` (D4; usada pela 3.1 e 3.2), função pura com blocos `test`: nada muda → mesma senha; só a cor → `A-CAR-001` vira `V-CAR-001` sem reservar número; especialidade muda → pede número novo. Verificar com `xano_validate_xanoscript` e com `xano unit_test` após a publicação.
- [ ] 2.3 Extrair de `api/triagem/fichas_id_prioridade_post.xs` a validação e a gravação do ajuste para `function/classificacao/aplicar_ajuste.xs` (D2; usada pela 3.1 e 3.2), sem mudar o comportamento atual do endpoint; verificar com `xano_validate_xanoscript` e repetindo no Run & Debug os cenários do requisito "Ajuste manual da prioridade" em `EM_TRIAGEM`.
- [ ] 2.4 Em `function/direcionamento/destino_da_ficha.xs`, excluir a própria ficha da contagem de fichas `AGUARDANDO` por candidata (D5); verificar com `xano_validate_xanoscript` e com os testes existentes de `escolher_destino`.

## 3. Xano — endpoints

- [ ] 3.1 Em `api/triagem/fichas_id_patch.xs`: aceitar `EM_TRIAGEM` ou `AGUARDANDO`; aceitar `prioridade_ajuste` e `justificativa_ajuste` opcionais aplicados por `aplicar_ajuste` depois do recálculo; para `AGUARDANDO`, recusar com `FICHA_SEM_PRIORIDADE` e pendências quando ficar sem cor, refazer destino e senha (`destino_da_ficha`, `senha_reavaliada`, `gerar_senha`) e gravar especialidades, senha e número na mesma transação; incluir especialidade e senha na auditoria e devolver `senha_alterada`, `senha_anterior` e `senha`. Verificar com `xano_validate_xanoscript`.
- [ ] 3.2 Em `api/triagem/fichas_id_prioridade_post.xs`: usar `aplicar_ajuste`, aceitar `AGUARDANDO` e, nesse estado, atualizar a senha por `senha_reavaliada` (só a cor muda) e devolver os mesmos campos de senha. Verificar com `xano_validate_xanoscript`.
- [ ] 3.3 Publicar na `v1` os arquivos de 2.2–3.2 (`--dry-run` antes, push restrito, sem tabelas), rodar os testes unitários das funções e conferir com `xano workspace pull`; no Run & Debug, verificar em ficha `AGUARDANDO` os cenários das specs: só a cor (`A-CAR-001` → `V-CAR-001`, contador intacto), especialidade nova (próximo número da nova), nada muda (mesma senha), gestante sem ajuste (recusa sem alterar nada), gestante com ajuste (aceita), ficha `CHAMADO` preparada no painel (recusa) e `chegada_em` inalterado. Registrar a evidência.

## 4. Reflex

- [ ] 4.1 No `FichaState` de `frontend/ps_fila_prioritaria/ps_fila_prioritaria.py`: permitir salvar e ajustar em `AGUARDANDO`; guardar `senha_alterada`/`senha_anterior` da resposta para o aviso; em `FICHA_SEM_PRIORIDADE`, mostrar as pendências e abrir o diálogo de ajuste, que envia o ajuste junto com as alterações pendentes no PATCH (D6). Testes em `frontend/tests/test_ficha_state.py`: salvar em `AGUARDANDO` com e sem troca de senha, recusa sem cor seguida de ajuste no mesmo envio, e ficha `CHAMADO` sem edição. Verificar que a suíte unitária passa.
- [ ] 4.2 Na tela da ficha: em `AGUARDANDO`, mostrar edição, senha, especialidade e "Reimprimir", sem "Confirmar e gerar senha", e o aviso fixo "Senha alterada de X para Y — o comprovante impresso deixou de valer" com "Reimprimir" (D6); demais estados continuam em modo leitura. Verificar que `reflex compile --dry` compila.

## 5. Verificação ponta a ponta

- [ ] 5.1 Logado como Recepção/Triagem, com fichas confirmadas: adulto `A-CAR-xxx` com piora de SpO₂ → `V-CAR-xxx`, mesmo número, aviso e reimpressão com a senha nova; adulto em Cardiologia que recebe "Convulsão em atividade" → Neurologia com novo número; alteração só de observação → mesma senha sem aviso; gestante `AGUARDANDO` editada sem ajuste → recusa com pendências e, com ajuste no diálogo → salva; tentativa como Médico → recusada; auditoria com especialidade e senha anteriores e novas. Registrar o roteiro e o resultado aqui.
- [ ] 5.2 Rodar `openspec validate add-reavaliacao-ficha-aguardando --strict` e verificar que não há erro estrutural.

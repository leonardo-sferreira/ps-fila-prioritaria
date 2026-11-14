## 1. Backend (Xano)

- [x] 1.1 `api/cadastros/disponibilidade_post.xs`: input `data_fim?`; valida data final (≥ inicial, ≤ 90 dias); gera períodos a cada 48 h; checa sobreposição de todos antes de gravar; grava e audita na mesma transação; responde `criados`
- [ ] 1.2 Push no workspace Xano (aguarda aval do Nicolas)

## 2. Frontend (Reflex)

- [x] 2.1 `PlantoesState`: campos `repetir` e `data_fim`; exige "Até" quando repetir; envia `data_fim` só no novo plantão com repetição; mensagem com a quantidade criada
- [x] 2.2 Diálogo "Novo plantão": caixa "Repetir em escala 12x36" e campo "Até"

## 3. Documentação

- [x] 3.1 `docs/domain-model.md` (Disponibilidade_Médico)

## 4. Verificação

- [x] 4.1 Testes em `tests/test_cadastros_state.py`: exige data final, envia `data_fim`, plantão único não envia
- [ ] 4.2 Manual (após o push): criar escala de 12/11 a 18/11, 07:00–19:00, e conferir plantões em 12, 14, 16 e 18/11; repetir com um dia já ocupado e conferir que nada é criado

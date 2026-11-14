# Proposta: Escala 12x36 de plantões

| Campo | Valor |
|---|---|
| Change | `add-plantao-12x36` |
| Depende de | `add-cadastros-administrador` (arquivada) |
| Situação | Pedido do PO em 12/11/2026; push no Xano aguarda aval do dono do workspace |

## Why

Hoje cada plantão é cadastrado dia a dia em `/admin/disponibilidade`. O Administrador precisa abrir o formulário todo dia para manter a escala, o que é repetitivo e sujeito a esquecimento.

## What Changes

- No "Novo plantão", a opção "Repetir em escala 12x36" com o campo "Até" cria o mesmo horário a cada 2 dias até a data final.
- `POST /disponibilidade` aceita `data_fim` opcional. Sem ele, nada muda. Com ele, o Xano valida todos os dias (sobreposição, prazo máximo de 90 dias) e cria tudo numa transação: tudo ou nada. Cada plantão gera sua própria auditoria `PLANTAO_CRIADO`.
- A resposta ganha `criados` (quantidade).
- Edição e remoção continuam por plantão individual.

### Fora do escopo

- Outras escalas (dias da semana, 24x72) e edição/remoção em lote.

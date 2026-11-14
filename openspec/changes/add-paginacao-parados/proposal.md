# Proposta: Paginação e ordenação dos parados no dashboard do Administrador

| Campo | Valor |
|---|---|
| Change | `add-paginacao-parados` |
| Depende de | `add-expiracao-24h` (arquivada), dashboard do Administrador |
| Situação | Pedido do PO em 12/11/2026 |

## Why

O cartão "Fichas e tickets parados" da tela inicial do Administrador mostra todos os itens numa lista única. Com muitos tickets esquecidos, a lista fica longa e empurra o resto do dashboard para baixo.

## What Changes

- Fichas e tickets parados aparecem numa só lista, com o tipo (Ficha ou Ticket) em cada linha.
- A lista é paginada: 10 itens por página por padrão, com anterior/próxima e "Página X de Y".
- O Administrador escolhe a quantidade por página: 10, 25 ou 50.
- O Administrador ordena por "Maior tempo parado" (padrão; mais antigo primeiro) ou "Menor tempo parado".
- Apenas apresentação no Reflex: o endpoint `/expiracao` e a dispensa não mudam. "Dispensar todos" continua encerrando tudo o que está parado, não só a página visível.

### Fora do escopo

- Paginação no backend (o volume de parados é pequeno).
- Dispensa individual ou por página.

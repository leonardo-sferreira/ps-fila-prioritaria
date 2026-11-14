# Proposta: Base compartilhada (auditoria, fuso, parâmetros e dados de referência)

| Campo | Valor |
|---|---|
| Change | `add-base-compartilhada` |
| Card no Trello | #67 "Base compartilhada — auditoria, fuso e parâmetros" (Sprint 4, entrega 16/11) |
| Depende de | `add-autenticacao-perfis` (`usuario` e `verificar_acesso`) |
| Situação | Revisada em 13/11/2026 para refletir o que as changes seguintes já entregaram (ver design.md, "Revisão de 13/11/2026") |
| RFs | RF37 (auditoria); RF49 (consulta dos parâmetros); RNF07 e RNF09 |

## Why

Auditoria, fuso e parâmetros são usados por todas as funcionalidades. A change foi escrita na Sprint 1 para antecipar essa base, mas as changes seguintes (`add-cadastros-administrador`, `add-direcionamento-senha`, `add-triagem-classificacao`, `add-fila-chamada-medico`, `add-expiracao-24h`) acabaram entregando cada peça ao precisar dela, às vezes com outro desenho. Esta revisão alinha a change ao que existe e fecha o que faltava: a garantia, verificada por teste, de que a auditoria é atômica e imutável e de que os parâmetros nascem com os valores da baseline.

## What Changes

- **Auditoria:** a função `registrar_alteracao` é a única que grava em `historico_alteracao`, sempre dentro do `db.transaction` da operação e com o usuário da sessão. Nenhum endpoint grava, edita ou apaga auditoria (RF37, RNF07). Testes estáticos sobre o XanoScript versionado garantem isso em todos os endpoints.
- **Fuso horário:** fixo em `America/Sao_Paulo` em todas as conversões de data do XanoScript. Não é variável de ambiente nem parâmetro (substitui a antiga D3).
- **Parâmetros:** os valores iniciais são criados, sem sobrescrever, pelas funções `inicializar_*` quando a operação precisa deles. Consulta e alteração ficam com o Administrador em `GET`/`PATCH parametros` (`add-cadastros-administrador`, D7). Testes estáticos conferem os valores da baseline e que cada um está dentro dos limites editáveis.
- **Dados de referência:** especialidades (CAR, CLI, NEU, ORT, PED), ligações sintoma → especialidade e `ESPECIALIDADE_PADRAO` são criadas por `direcionamento/inicializar_direcionamento`. Os sintomas são mantidos pelo Administrador nos cadastros.

### Fora do escopo

- Endpoint `POST admin/carga-inicial` e função `obter_parametro`: substituídos pelas funções `inicializar_*` e por `cadastros/regra_parametro`.
- Telas, consulta da auditoria pelo Administrador e CRUD de cadastros: changes próprias.

## Capacidades

### Novas capacidades
- `dados-referencia`: carga automática e idempotente das especialidades e ligações.

### Capacidades modificadas
- `auditoria`: amplia a regra dos cadastros para toda operação relevante e acrescenta atomicidade e imutabilidade.
- `parametros-regras`: acrescenta os valores iniciais e a criação sem sobrescrita.

## Impacto

- **Xano:** nenhuma alteração. O que esta change descreve já está publicado na `v1`.
- **Reflex:** nenhum impacto.
- **Testes:** `tests/api/test_base_compartilhada.py`.

## Perguntas em aberto

- [ ] A carga automática (`inicializar_*`) roda sem usuário responsável e não grava auditoria. Aceitar como dado de sistema, ou exigir auditoria da carga? · PENDENTE PO
- [ ] Prova de rollback (falha depois da auditoria não deixa registro): exige função temporária no workspace e aval do dono do workspace. · PENDENTE

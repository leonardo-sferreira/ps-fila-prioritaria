## 1. Frontend (Reflex)

- [x] 1.1 `ExpiracaoState`: lista única com tipo e instante; estado de página, tamanho (10/25/50) e ordem (maior/menor tempo); variáveis computadas da página visível e do total de páginas
- [x] 1.2 Cartão `cartao_parados`: coluna de tipo, seletores de ordem e quantidade, controles anterior/próxima com "Página X de Y"
- [x] 1.3 Recarregar ou dispensar volta à página 1; trocar ordem ou tamanho volta à página 1

## 2. Verificação

- [x] 2.1 Testes em `tests/test_expiracao_state.py`: 10 por padrão, limites (10, 11, 25 itens), troca de tamanho, ordem maior/menor tempo, página não passa do fim
- [ ] 2.2 Manual: em `/admin`, com mais de 10 parados, navegar páginas, trocar para 25 e alternar a ordem

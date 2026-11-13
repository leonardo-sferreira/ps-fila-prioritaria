# Tarefas

## 1. Testes dos passos disponíveis

- [x] 1.1 [Reflex] Acrescentar em `frontend/tests/test_fila_tickets_state.py` asserções para contagem apenas de tickets AGUARDANDO por tipo e para a ação manual de marcar presença; verificar com `pytest` nesse arquivo.
- [x] 1.2 [Reflex] Fortalecer os testes do comprovante em `frontend/tests/test_ficha_state.py` com resposta que contém campos pessoais e clínicos extras e inspeção do componente renderizado, comprovando que só os campos permitidos chegam à impressão; verificar com `pytest` nesse arquivo.
- [x] 1.3 [Xano] Relacionar os testes puros já versionados de escore, destino, senha e fila aos passos dos cards 102–104, sem criar casos duplicados nem escrever no Xano; verificar que os seletores do catálogo encontram os casos no inventário de `run_test_evidence.py`.

## 2. Evidência legível para a documentação

- [x] 2.1 Criar em `scripts/roteiros_sprint5.py` o catálogo dos seis cards abertos 101–106 e a geração de `roteiros-sprint5.md` a partir do JSON consolidado; verificar que cada verificação mostra status real, tipo de teste, limite da evidência e pendência do roteiro.
- [x] 2.2 Criar `tests/test_roteiros_sprint5.py` para verificar seleção de casos, falhas, `NOT_RUN`, seletor ausente e exclusão de cards fechados/ponta a ponta; verificar com `pytest` nesse arquivo.
- [x] 2.3 Integrar o gerador em `scripts/merge_test_evidence.py` e no autoteste do CI; verificar que o diretório consolidado contém `roteiros-sprint5.md` ao mesclar evidências locais.
- [x] 2.4 Documentar em `docs/testes-roteiros-sprint5.md` o comando de geração, o significado dos estados e as pendências das partes não entregues; verificar que a documentação aponta para os seis cards corretos.

## 3. Verificação conjunta

- [x] 3.1 Executar os testes Reflex afetados e os autotestes do gerador, compilar o Reflex com `reflex compile --dry`, gerar um relatório local e validar a change com `openspec validate`; conferir que nenhuma falha ou aprovação integral indevida aparece.

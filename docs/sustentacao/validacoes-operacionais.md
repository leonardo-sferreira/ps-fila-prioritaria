# Validações operacionais

Verificações que confirmam o funcionamento do sistema antes e depois de uma mudança, além dos testes unitários.

| Validação | Quando | Como | O que comprova |
|---|---|---|---|
| **Simulação de publicação (dry-run)** | Antes de toda publicação no Xano | `xano workspace push ... --dry-run -i <arquivos>` | Que só os itens esperados serão criados ou atualizados; revela mudanças feitas direto no Xano |
| **Validação das especificações** | Antes de arquivar uma change | `openspec validate <change>` e `openspec validate --specs` | Requisitos e cenários bem formados |
| **Compilação do frontend** | Antes de PR com mudança de tela | `reflex compile --dry` (dentro de `frontend/`) | Que todas as telas compilam |
| **CI com evidências** | Todo push e PR | GitHub Actions (6 jobs) | Testes de estado, contratos, funções puras no Xano e E2E públicos, com relatório consolidado |
| **Testes ao vivo (suíte controlled)** | Ao mudar endpoints de fila, painel, acompanhamento ou login | `python -m pytest tests/api/<arquivo>.py` | O comportamento real na `v1`, com dados sintéticos apagados no fim |
| **Testes ponta a ponta manuais** | Antes de cada entrega | Roteiros dos cards de teste do Trello e do README | O fluxo completo com telas reais |
| **Teste de concorrência (ponto cego)** | Ao mudar chamada ou login | `tests/api/test_chamada.py` (dois médicos ao mesmo tempo) e o teste de código de login duplicado | Que operações simultâneas não duplicam ficha nem sessão |

## Testes ponta a ponta

### Automatizados

- **E2E público** (`tests/e2e/test_publico.py`, Playwright): sobe o app, abre o login, o aviso de privacidade e confere que uma rota protegida sem sessão volta ao login.
- **Ao vivo na `v1`** (`tests/api/`): cada arquivo cria um cenário sintético (médicos, fichas e tokens de teste com um marcador único), executa o fluxo e encerra o cenário no fim, inclusive se o teste falhar.

| Arquivo | Fluxo validado |
|---|---|
| `test_chamada.py` | Dois médicos chamando ao mesmo tempo, repetição, reentrada, desistência e comparecimento |
| `test_recuperacao_sessao_medico.py` | Novo login do médico sem esperar a sessão anterior expirar |
| `test_acompanhamento.py` | Fila geral, detalhe com ajuste e duas tentativas, equipe, auditoria paginada e `me/status` |
| `test_painel.py` | Painel público sem dados pessoais, chamada e repetição, desistência, ticket da triagem e tamanho da previsão |
| `test_base_compartilhada.py` | Auditoria, parâmetros e status da equipe |

### Manuais

Roteiros publicados nos cards de teste da Sprint 5 no Trello (101 a 106), no README (seções "Fila e chamada do médico", "Acompanhamento do Administrador" e "Painel público") e mapeados aos testes automatizados em [testes-roteiros-sprint5.md](../testes-roteiros-sprint5.md). Resultado registrado em comentário no card, com o passo e um print.

## Perfilamento e desempenho

Não há ferramenta de perfilamento configurada. O tempo de cada endpoint aparece no Request History do Xano, e os testes ao vivo registram a duração de cada caso nas evidências (`duracao_segundos`). Pontos de atenção conhecidos:

- Endpoints que montam listas (fila geral, painel, auditoria) fazem várias consultas por requisição. Mantêm-se rápidos com o volume de um PS, mas crescem com o histórico: a auditoria limita o período a 31 dias, e o painel, a 2 horas.
- O gargalo atual é o **limite de requisições** do plano, não o tempo de resposta ([métricas](erros-e-metricas.md#métricas-e-monitoramento)).

## Evidências

Cada execução gera, em `test-evidence/<execução>/<suíte>/`:

- `resultados.json`: cada caso, com ID do catálogo, status, motivo e duração;
- `resultados.xml`: formato JUnit;
- `resumo.md`: totais e diagnóstico.

No CI, essas pastas viram artefatos (`evidencias-reflex`, `evidencias-xano`…), e o job "Consolidar evidências" junta tudo num relatório só. Detalhes: [guia de QA](../testes-qualidade.md).

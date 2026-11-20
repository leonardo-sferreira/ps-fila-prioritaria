# Estratégia de testes

Quais testes o projeto tem, como são feitos, como rodar e como ler o resultado. A lista de todos os casos, com entrada e saída esperada, está no [catálogo de testes](catalogo-de-testes.md); a infraestrutura de evidências, no [guia de QA](../testes-qualidade.md).

## Tipos de teste

| Suíte | Tipo | O que testa | Como é feito | Entrada | Saída verificada | Onde roda |
|---|---|---|---|---|---|---|
| `reflex` | Unitário (estado da tela) | Lógica de cada tela: validação, formatação, mensagens e chamadas à API | pytest; a API do Xano é simulada (respostas fixas) | Ações do usuário e respostas simuladas da API | Estado da tela, mensagens e chamadas feitas | CI e local |
| `xano-static` | Estático | Contratos dos endpoints lidos dos arquivos `.xs` (auditoria, parâmetros, status) | pytest lendo o código, sem rede | Arquivos `.xs` | Presença de autorização, campos e auditoria | CI e local |
| `xano-safe` | Unitário real | Funções puras no próprio Xano: pontuação, ordem da fila, senha, destino, registros parados | Testes nativos (`test "..."` dentro do `.xs`) e testes Python que chamam as funções pelo CLI | Dados sintéticos de entrada | Resposta exata da função | CI (com o CLI do Xano) |
| `controlled` | Integração ao vivo | Fluxos reais na branch `v1`: chamada concorrente, acompanhamento, painel, login concorrente | pytest com cenário sintético criado e apagado pelo próprio teste | Médicos, fichas e tokens de teste com marcador único | Respostas HTTP reais e estado gravado | Local, com autorização |
| `e2e` | Ponta a ponta | Telas públicas no navegador | Playwright (Chromium) sobre o app rodando | Navegação | Elementos e redirecionamentos na tela | CI |
| `autotestes` | Unitário | A própria ferramenta de evidências | pytest | Resultados simulados | Relatórios e códigos de saída | CI e local |
| Manual | Ponta a ponta | Fluxo completo com pessoas | Roteiros nos cards de teste do Trello e no README | Ações nas telas reais | O que a tela mostra em cada passo | Antes das entregas |

## Como os testes são escritos

**Estado da tela (Reflex):** o teste cria o estado, substitui `api.requisitar` por uma resposta pronta e chama o evento. Exemplo de `frontend/tests/test_painel_state.py`:

| Entrada | Saída esperada |
|---|---|
| Resposta do painel com chamada atual `V-CAR-003`, Sala `2` e tentativa 2 | `destino = "Cardiologia · Sala 2"`, `tentativa = "2ª chamada"` |
| Mesma resposta com `chamada_id` diferente | A chave de novidade muda e o painel destaca e toca o aviso |

**Função pura no Xano:** o teste fica no próprio arquivo. Exemplo de `function/classificacao/pontuar.xs`:

| Entrada | Saída esperada |
|---|---|
| PA 90, FC 90, FR 8, T 35,0, SpO₂ 91 | Cada sinal na borda da faixa recebe os pontos da tabela; com 3 pontos isolados, a cor é Vermelha |
| SpO₂ ausente | Cálculo bloqueado (classificação manual) |

**Integração ao vivo:** o teste cria o cenário (`fila/teste_criar_cenario`), executa o fluxo pela API e encerra o cenário no fim, mesmo se falhar (`fila/teste_encerrar_cenario`). Exemplo de `tests/api/test_painel.py`:

| Passo | Entrada | Saída esperada |
|---|---|---|
| Painel sem login | `GET /painel` sem token | 200, sem nenhuma chave de dado pessoal em toda a resposta |
| Chamada | Médico chama o próximo | A senha chamada é a primeira que estava prevista e vira a chamada atual |
| Repetição | Repetir chamada após o intervalo | Volta como 2ª chamada, com outro `chamada_id` |
| Desistência | Duas oportunidades sem comparecimento | A senha sai da previsão |

**Concorrência:** dois pedidos simultâneos, por exemplo dois médicos chamando ou o mesmo código de login enviado duas vezes; o teste confere que só um vence.

## Como rodar

```bash
# raiz do repositório, venv do frontend ativo (no Windows: $env:PYTHONUTF8=1)
python scripts/run_test_evidence.py --suite reflex
python scripts/run_test_evidence.py --suite xano-static
python scripts/run_test_evidence.py --suite xano-safe            # precisa do Xano CLI autenticado
python -m pytest tests/api/test_painel.py                        # um teste ao vivo (escreve dados sintéticos na v1)
python scripts/run_reflex_e2e_ci.py --output test-evidence/e2e   # E2E com Chromium
```

Não rode `pytest tests/api` inteiro sem necessidade: são testes que escrevem dados (sintéticos) no Xano, e o plano tem limite de requisições.

## Como ler o resultado

O runner imprime uma linha por suíte, por exemplo:

```
reflex: técnico=PASSED validação=COMPLETA {'PASSED': 298, 'FAILED': 0, 'ERROR': 0, 'SKIPPED': 0, 'NOT_RUN': 0, 'BLOCKED': 0}
```

| Estado | Significado |
|---|---|
| `PASSED` | O caso passou |
| `FAILED` | A verificação falhou: comportamento diferente do esperado |
| `ERROR` | O teste não chegou a verificar (exceção, rede, limite do Xano) |
| `SKIPPED` / `NOT_RUN` | Não executado (falta configuração ou foi pulado) |
| `BLOCKED` | Impedido por pré-condição (credencial, ferramenta, guarda de segurança) |
| validação `COMPLETA` / `PARCIAL` / `BLOQUEADA` | Se todos os casos esperados do catálogo apareceram e passaram |

As evidências ficam em `test-evidence/<execução>/<suíte>/` (`resultados.json`, `resultados.xml` e `resumo.md`).

## Regras

- **Todo teste novo vai para o catálogo** `tests/catalogo_testes.json`, com ID permanente (`CT-REFLEX-nnnn`, `CT-XANO-nnnn`). Sem registro, o CI bloqueia com `CATALOGO_INVALIDO`.
- **Defeito corrigido ganha teste** que o reproduz antes da correção.
- **Dados de teste** são sempre sintéticos e identificados por marcador ("Paciente Fictício ...", tickets a partir do número 900), e o próprio teste apaga o que criou.
- **Contagens** nos autotestes vêm do catálogo, não de números fixos.

## Situação atual

| Suíte | Casos |
|---|---|
| Reflex | 297 |
| Xano funções puras | 97 |
| Integração ao vivo | 33 |
| Xano estático | 13 |
| E2E | 2 |
| Autotestes | 41 |
| **Total** | **483** |

Números do catálogo na data desta documentação; o [catálogo gerado](catalogo-de-testes.md) sempre traz os atuais. Os testes manuais da Sprint 5 e sua relação com os automatizados estão em [testes-roteiros-sprint5.md](../testes-roteiros-sprint5.md).

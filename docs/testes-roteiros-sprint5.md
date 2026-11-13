# Testes dos roteiros abertos da Sprint 5

Esta página acompanha somente os cards de teste **101 a 106**, abertos na lista “Sprint 5 — Painel Público, Testes e Apresentação” do export do Trello de 12/11/2026. O card de integração ponta a ponta e todos os cards fechados ficam fora deste recorte.

## Como obter a evidência

O CI produz `roteiros-sprint5.md` dentro do artifact `evidencias-consolidadas`. O arquivo reúne os testes técnicos por roteiro em frases curtas e mostra quantos testes de cada tipo sustentam cada verificação. `resumo.md` e `resultados.json` guardam os nomes e identificadores dos casos para auditoria detalhada.

Para gerar o mesmo resumo localmente, depois de executar as suites existentes:

```bash
.venv/bin/python scripts/run_test_evidence.py --suite reflex --output test-evidence/sprint5-reflex --require-execution
.venv/bin/python scripts/run_test_evidence.py --suite xano-safe --output test-evidence/sprint5-xano --require-execution
.venv/bin/python scripts/merge_test_evidence.py --input test-evidence/sprint5-reflex --input test-evidence/sprint5-xano --output test-evidence/sprint5-consolidado
```

A suite `xano-safe` precisa do CLI Xano autenticado e executa somente funções puras na branch `v1`. O arquivo final fica em `test-evidence/sprint5-consolidado/roteiros-sprint5.md`. O diretório `test-evidence/` é ignorado pelo Git para evitar versionar logs e respostas de execução.

## Como ler o resultado

| Estado | Significado |
|---|---|
| **PASS técnico** | Os casos automatizados associados passaram. A coluna “Falta para concluir o roteiro” ainda precisa ser verificada. |
| **FALHOU** | Pelo menos um caso associado falhou ou teve erro. |
| **NÃO EXECUTADO** | Há caso ignorado ou não executado. |
| **SEM EVIDÊNCIA** | Um caso esperado não apareceu na coleta; conferir o seletor ou a execução. |
| **PENDENTE** | A verificação depende de funcionalidade ou ambiente ainda indisponível. |

Os testes de estado Reflex usam respostas simuladas e verificam as ações da interface. Os testes nativos e de função pura Xano verificam regras com dados sintéticos. Nenhum dos dois, sozinho, comprova que o roteiro manual completo foi executado no sistema integrado.

## Escopo dos seis cards

| Card aberto | Evidência automatizada disponível | Etapa que ainda depende de execução real ou entrega |
|---|---|---|
| [101 — Totem e pré-triagem](https://trello.com/c/U2NEx9ZV/101-teste-totem-e-fila-de-pr%C3%A9-triagem) | Emissão no estado Reflex, apresentação e contagem da fila, intervalos e ações manuais | API real, emissão simultânea, ordem 2:1, reentrada e ausência final |
| [102 — Paciente e classificação](https://trello.com/c/q6VyShFt/102-teste-identifica%C3%A7%C3%A3o-do-paciente-e-classifica%C3%A7%C3%A3o-na-ficha) | CPF, abertura de ficha, escore, limites, glicemia e classificação manual em funções puras | Cadastro, edição, mensagens e descarte do ajuste na ficha real |
| [103 — Direcionamento e comprovante](https://trello.com/c/4bgJ3BKZ/103-teste-direcionamento-senha-e-comprovante) | Destino, formato e troca de senha, ações de confirmação e privacidade do estado e do componente impresso | Numeração diária, persistência, impressão física de 80 mm e dados reais da API |
| [104 — Fila do médico](https://trello.com/c/CllOO9y9/104-teste-fila-do-m%C3%A9dico-e-atendimento) | Ordenação, apoio entre filas e ações da tela médica | Concorrência, chamadas, comparecimento e plantão em ambiente isolado |
| [105 — Painel e privacidade](https://trello.com/c/LcyWdDfe/105-teste-painel-p%C3%BAblico-e-privacidade) | Máscara de CPF, aviso público e estado de encerramento por inatividade | Conferência visual; painel, som, previsão e reconexão após a entrega |
| [106 — Administrador](https://trello.com/c/vFMKYEh1/106-teste-administrador-usu%C3%A1rios-cadastros-acompanhamento-e-permiss%C3%B5es) | Login, código, redefinição e proteção de perfil no estado Reflex | E-mail e autorização na API real; cadastros e acompanhamento após a entrega |

O relatório gerado contém o resultado de cada verificação disponível, o tipo de teste que a sustenta e a pendência correspondente. Ele pode ser anexado à documentação de entrega sem copiar a tabela técnica completa de centenas de casos.

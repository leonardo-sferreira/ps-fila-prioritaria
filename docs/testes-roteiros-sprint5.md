# Testes dos roteiros abertos da Sprint 5

Esta página acompanha somente os cards de teste **101 a 106**, abertos na lista “Sprint 5 — Painel Público, Testes e Apresentação” do export do Trello de 12/11/2026. O card de integração ponta a ponta e todos os cards fechados ficam fora deste recorte.

## Como obter a evidência

O [guia comum de QA](testes-qualidade.md) define os comandos seguros, o catálogo, os estados e a consolidação. O snapshot agora está em `tests/roteiros/sprint5.json`, preservando os cards, links e pendências deste documento. As verificações referenciam IDs permanentes de `tests/catalogo_testes.json`, sem duplicar nomes ou resultados esperados. O CI não seleciona uma sprint fixa automaticamente.

Para acrescentar o roteiro histórico a uma consolidação local, selecione-o explicitamente:

```bash
.venv/bin/python scripts/merge_test_evidence.py \
  --input test-evidence/revisao-reflex --expected-suite reflex \
  --input test-evidence/revisao-xano --expected-suite xano-safe \
  --roteiro tests/roteiros/sprint5.json --output test-evidence/sprint5-consolidado
```

As entradas devem ter sido produzidas nesta execução, com identidade compatível. A suíte `xano-safe` depende do CLI autenticado e do guardião; sua ausência gera impedimento, sem execução presumida. `--require-complete` também exige resolver as pendências do roteiro selecionado; este snapshot continua parcial mesmo quando todos os casos automatizados passam.

O adaptador `scripts/roteiros_sprint5.py --input <resultados.json> --output <arquivo-novo.md>` permanece disponível. O gerador comum `scripts/roteiros_testes.py` recebe `--config` para outros ciclos. `resultados.json` contém os detalhes por ID/variante e as referências; as assertions continuam no código, e mensagens livres sensíveis não entram nos relatórios. Evidências antigas não são reescritas.

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
| [106 — Administrador](https://trello.com/c/vFMKYEh1/106-teste-administrador-usu%C3%A1rios-cadastros-acompanhamento-e-permiss%C3%B5es) | Login, código, redefinição, usuários, cadastros, parâmetros, plantões e dashboard com API simulada | Conferir as operações na API real; acompanhamento detalhado de fila, equipe, fichas e auditoria após a entrega da change ativa |

O relatório gerado contém o resultado de cada verificação disponível, o tipo de teste que a sustenta e a pendência correspondente. Ele pode ser anexado à documentação de entrega sem copiar a tabela técnica completa de centenas de casos.

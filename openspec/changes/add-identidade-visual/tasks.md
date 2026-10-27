# Tarefas

## 1. Arquivos do logo (D1)

- [x] 1.1 [Reflex] Gerar em `frontend/assets/logo/` os SVGs `logo-prioriza.svg`, `icone-prioriza.svg` e `icone-prioriza-branco.svg` a partir dos arquivos do PO, com as cores do projeto; usar o `favicon.ico` do PO em `frontend/assets/`. Verificar abrindo cada SVG e conferindo as cores `#123C6B`/`#1565C0`
  - Evidência (27/10/2026): três SVGs gerados dos arquivos do PO com `#123C6B`/`#1565C0` (cores conferidas no arquivo); servidos pelo app (HTTP 200), assim como o `favicon.ico`.

## 2. Telas (D2, D3)

- [x] 2.1 [Reflex] Refatorar `logo_ps()` para o ícone colorido e `cartao_acesso()` para aceitar título vazio; no login, usar o logo completo sem título. Verificar por captura que login, código do login, A1 a A4 e aviso mostram o logo como no Figma
  - Evidência: captura do login (logo completo, sem o título antigo) e da A1 (ícone colorido) iguais ao Figma; código do login, A2–A4 e aviso usam o mesmo `logo_ps()`.
- [x] 2.2 [Reflex] Refatorar `cabecalho()` para o ícone branco, sem o parâmetro `sigla`, e ajustar as chamadas; verificar com `reflex compile` e captura de uma área interna
  - Evidência: `reflex compile` sem erros; ícone branco conferido sobre o azul do cabeçalho (`#123C6B`) em captura. As áreas internas exigem login com código por e-mail, então a tela completa fica para o PO conferir ao entrar.
- [x] 2.3 Rodar a suíte de testes e `reflex compile`; verificar que tudo passa e restaurar `frontend/reflex.lock` antes do commit
  - Evidência: 109 testes passando, `reflex compile` sem erros e `frontend/reflex.lock` restaurado. Os 4 testes de `test_xano_api_integration.py` falham com 401 já no `main`: o PR #16 passou a exigir login em pacientes e triagem e esse teste ainda chama sem token. Não é desta change.

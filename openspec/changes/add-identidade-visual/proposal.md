# Proposta: Logo Prioriza no app

| Campo | Valor |
|---|---|
| Change | `add-identidade-visual` |
| Sprint e entrega | A definir pelo PO |
| Card no Trello | A criar ("Identidade visual: logo Prioriza") |
| Depende de | `add-autenticacao-perfis` e `add-privacidade` (telas de acesso e aviso já existem) |
| Situação | Em revisão |

## Why

O PO criou o logo Prioriza (27/10/2026) e o protótipo no Figma já o usa. O app ainda mostra um círculo com "PS" nas telas de acesso e um círculo com a sigla do perfil no cabeçalho, diferente do protótipo.

## What Changes

- Logo completo (ícone e nome "Prioriza · Fila de atendimento") no lugar do círculo "PS" e do título "Sistema de Fila Prioritária" na tela de login.
- Ícone colorido no lugar do círculo "PS" nas demais telas de acesso (código do login, redefinição de senha) e no aviso de privacidade.
- Ícone branco no lugar do círculo com a sigla do perfil (R, M, A) no cabeçalho azul das áreas internas.
- Favicon do Prioriza.
- Cores do logo adaptadas à paleta do projeto, como no Figma: azul-marinho `#123C6B` e azul `#1565C0`.

### Fora do escopo

- Menu de navegação, modo escuro e demais ajustes do Figma: changes próprias.
- Trocar o nome do sistema em textos, e-mails e documentos; só o logo traz o nome.

## Capabilities

### New Capabilities
_Nenhuma: só apresentação (`skip_specs`)._

### Modified Capabilities
_Nenhuma._

## Impact

- **Reflex:** `logo_ps()`, `cartao_acesso()`, `login()` e `cabecalho()` em `ps_fila_prioritaria.py`; arquivos em `frontend/assets/logo/` e `frontend/assets/favicon.ico`.
- **Xano:** nenhum.

## Perguntas em aberto

- [x] Logo e cores adaptadas: aprovados no Figma pelo PO em 26/10/2026. · DECIDIDO PO

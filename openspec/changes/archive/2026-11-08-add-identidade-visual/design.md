# Design técnico

## Contexto

As telas de acesso usam `logo_ps()` (círculo "PS") dentro de `cartao_acesso()`; o cabeçalho azul das áreas internas (`cabecalho()`) mostra um círculo com a sigla do perfil. No Figma, os componentes `Marca/Logo Prioriza` e `Marca/Ícone Prioriza` (versões Colorida e Branca) substituíram esses círculos.

## Objetivos / Fora dos objetivos

**Objetivos:** reproduzir no app o uso do logo do protótipo, com os mesmos arquivos e cores.

**Fora dos objetivos:** versões do logo que nenhuma tela usa agora (PNGs, ícone de 1024 px), modo escuro.

## Decisões

### D1. SVGs adaptados em `frontend/assets/logo/`
Três arquivos, os usados nesta change: `logo-prioriza.svg` (login), `icone-prioriza.svg` (telas de acesso e aviso) e `icone-prioriza-branco.svg` (cabeçalho). São os SVGs do PO com `#0B3C73` → `#123C6B` e `#1E6FD9` → `#1565C0`, como no Figma. Exibidos com `rx.image` e texto alternativo.
- **Por quê:** SVG fica nítido em qualquer tamanho e é leve; os PNGs do PO não são necessários.

### D2. `logo_ps()` vira o ícone; `cartao_acesso()` aceita título vazio
`logo_ps()` passa a devolver o ícone colorido (64 px). No login, o cartão recebe o logo completo e nenhum título, porque o nome já está no logo.

### D3. Cabeçalho sem sigla
`cabecalho()` perde o parâmetro `sigla` e mostra o ícone branco (48 px); as chamadas (`area_inicial`, identificação do paciente) deixam de passar a sigla. O perfil continua no título do cabeçalho.

## Riscos / Compromissos

- [Nome "Prioriza" só no logo] → Os textos continuam "Sistema de Fila Prioritária"/"PS" onde aparecem; unificar o nome é decisão do PO fora desta change.

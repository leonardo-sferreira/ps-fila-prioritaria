# AGENTS.md — Instruções para agentes de IA

## Documentação
- Ler o contexto nesta ordem: `docs/project-overview.md` (fluxo, escopo, perfis e regras globais), `docs/domain-model.md` (entidades, relações e estados), `openspec/config.yaml` (resumo global), as specs/changes da funcionalidade e, para consultar o texto formal de RF/RNF/RN, o Confluence.
- Usar o Confluence como referência formal para identificação e texto de RF/RNF/RN. Se o documento formal ainda não estiver sincronizado com uma decisão consolidada do PO nos documentos-base, apontar a divergência sem reintroduzir uma regra antiga já substituída.
- Tratar `docs/project-overview.md` e `docs/domain-model.md` como contexto consolidado do PO. Se uma change antiga conflitar com essa base, registrar o conflito e revisar a change antes de implementá-la; não aplicar silenciosamente a regra antiga.
- Ao alterar regra de domínio ou entidade, atualizar `docs/project-overview.md`, `docs/domain-model.md` e as specs correspondentes antes do código, na mesma change.
- Escrever documentação e artefatos OpenSpec em português brasileiro. Só ficam em inglês os marcadores que o CLI do OpenSpec exige (`## Why` e `## What Changes` no proposal, `## Purpose`, `## ADDED Requirements` e similares, `### Requirement:`, `#### Scenario:`).

## Desenvolvimento
- Toda mudança funcional passa pelo OpenSpec: explore → propose → review → apply → archive.
- Implementar apenas o que está no `tasks.md` da change ativa; decisões não previstas devem voltar para a change, não ser improvisadas.
- Trabalhar em fatias verticais: backend (Xano) e frontend (Reflex) de uma mesma funcionalidade na mesma change.
- Os fluxos do OpenSpec estão em `.claude/` (Claude Code), `.gemini/` (Gemini CLI) e `.agents/skills/` (Codex). Sem eles, usar o CLI: `openspec status --change <change>` e `openspec instructions apply --change <change> --json`.

## Arquitetura
- Frontend em Reflex (Python); backend e banco no Xano (XanoScript). Não introduzir outras tecnologias sem justificativa registrada no `design.md`.
- Regras de negócio e persistência ficam no Xano; o Reflex apenas apresenta e envia dados.
- Parâmetros clínicos (faixas de risco, limiares, ciclo 2:1, tentativas de chamada) devem ser configuráveis, nunca fixos no código.

## Segurança
- Autorização por perfil (Recepção/Triagem, Médico, Administrador) é aplicada no backend; esconder um botão no frontend não é controle de acesso.
- Nunca expor CPF ou nome completo no painel público.
- Não versionar credenciais, tokens ou URLs privadas do Xano; usar variáveis de ambiente.

## Código
- Reutilizar componentes e endpoints existentes; evitar duplicação.
- Não modificar funcionalidades não relacionadas à change atual.
- Nomes de domínio em português, consistentes com `docs/domain-model.md`.

## Testes
- Toda change funcional define como será verificada (testes automatizados quando possível; caso contrário, roteiro de verificação manual no `tasks.md`).
- Regras de prioridade e de fator de risco devem ter casos de teste com valores-limite.

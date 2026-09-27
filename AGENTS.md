# AGENTS.md — Instruções para agentes de IA

## Documentação
- Antes de qualquer alteração significativa, ler `docs/project-overview.md`, `docs/domain-model.md` e `openspec/config.yaml`.
- A fonte formal de requisitos (RF/RNF/RN) é o documento v1.0 no Confluence; em caso de conflito com os documentos locais, apontar a divergência em vez de escolher um lado.
- Ao alterar regras de negócio ou entidades, atualizar `docs/domain-model.md` na mesma change.
- Escrever documentação e artefatos OpenSpec em português brasileiro. Só ficam em inglês os marcadores que o CLI do OpenSpec exige (`## Purpose`, `## ADDED Requirements` e similares, `### Requirement:`, `#### Scenario:`).

## Desenvolvimento
- Toda mudança funcional passa pelo OpenSpec: explore → propose → review → apply → archive.
- Implementar apenas o que está no `tasks.md` da change ativa; decisões não previstas devem voltar para a change, não ser improvisadas.
- Trabalhar em fatias verticais: backend (Xano) e frontend (Reflex) de uma mesma funcionalidade na mesma change.

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

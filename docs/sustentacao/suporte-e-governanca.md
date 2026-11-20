# Suporte e governança

Quem cuida de quê no projeto, como pedir suporte e como registrar e escalonar um incidente.

## Equipe e responsabilidades

| Pessoa | Papel | Responde por |
|---|---|---|
| Leonardo dos Santos Ferreira | Product Owner (PO) | Regras de negócio, prioridades, aceite das entregas, documentação, esquema do banco, publicação no Xano e merges na `main` |
| Nicolas Rissato | Frontend | Telas em Reflex |
| Gustavo Garcia | Frontend | Telas em Reflex |
| Luisa Jeronimo de Lima | Backend e QA | Endpoints, infraestrutura de testes, evidências e CI |
| Leonardo Machado | Backend | Endpoints e funções no Xano |

O workspace do Xano pertence à conta de um membro da equipe; publicações e mudanças de configuração no Xano precisam do aval dele e do PO.

## Matriz de suporte

| Tipo de problema | Primeiro a acionar | Escalonar para | Onde registrar |
|---|---|---|---|
| Dúvida de uso, acesso, senha, usuário inativo | Administrador do sistema (tela Usuários) | PO | — |
| Regra de negócio parece errada (cor, ordem, senha) | PO | Backend | Card no Trello, lista da sprint atual |
| Tela com erro, layout, Reflex não sobe | Frontend | PO | Issue no GitHub ou card no Trello |
| Erro de endpoint (4xx/5xx inesperado), dado gravado errado | Backend | PO | Issue no GitHub, com o Request History do Xano |
| CI vermelho, teste instável, evidências | QA (Luisa) | Backend | Comentário no PR |
| Xano fora do ar, limite do plano, variáveis de ambiente | PO / dono do workspace | Suporte do Xano | Card no Trello |
| E-mail de código não chega | Backend | PO (conta Brevo) | Card no Trello |
| Suspeita de vazamento de dado pessoal | PO, imediatamente | Toda a equipe, com prioridade sobre o resto | Card no Trello marcado como incidente, com o registro da auditoria |

## Como pedir suporte

1. **Dúvida de uso:** consulte o [FAQ](../uso/inicio-rapido-e-faq.md). Se não resolver, fale com o Administrador do sistema.
2. **Defeito:** abra uma issue no GitHub (`leonardo-sferreira/ps-fila-prioritaria`) ou um card no Trello (quadro "Projeto PS — Fila de Atendimento por Urgência") com:
   - o que você fez (tela e passos), o que esperava e o que aconteceu;
   - a mensagem exata e um print;
   - data e hora, perfil e, se houver, a senha ou o ticket envolvido (nunca o CPF ou o nome do paciente).
3. **Correção:** quem pega o problema cria uma branch `fix/...`, adiciona um teste que reproduz o defeito, corrige, publica no Xano com simulação e abre um PR. O PO aceita e faz o merge.

## Registro de incidentes

Todo incidente que afete o uso (sistema fora, dado errado, falha de segurança) recebe um registro com:

| Campo | Conteúdo |
|---|---|
| Quando | Início e fim, no fuso do PS |
| Impacto | Quem foi afetado e o que deixou de funcionar |
| Causa | O que provocou, com a evidência (Request History, auditoria, log do Reflex) |
| Ação | O que foi feito para resolver (correção, rollback, reinício) |
| Prevenção | Teste ou mudança que impede a repetição |

Exemplo real: o mesmo código de login enviado duas vezes ao mesmo tempo abria duas sessões. Foi corrigido com o consumo do código numa transação, e o teste `test_mesmo_codigo_enviado_duas_vezes_ao_mesmo_tempo_abre_uma_sessao` impede a volta.

## Governança das mudanças

- **Requisitos:** documento formal no Confluence (RF, RNF, RN, UC, CA) e decisões do PO em [project-overview.md](../project-overview.md) e [domain-model.md](../domain-model.md).
- **Toda funcionalidade** passa por uma change do OpenSpec (proposta, specs, design e tarefas) antes do código, e é arquivada quando validada pelo PO.
- **Código** só entra na `main` por Pull Request com CI verde. Commits sem coautoria de IA.
- **Banco:** mudança de esquema só com o PO; nenhuma exclusão de registro com histórico.
- **Planejamento:** Trello, com sprints semanais entregues às segundas-feiras.
- **Auditoria:** toda alteração relevante fica em `historico_alteracao`, consultável em `/admin/auditoria`.

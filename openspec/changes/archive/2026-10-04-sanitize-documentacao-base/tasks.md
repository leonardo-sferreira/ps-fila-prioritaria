# Tarefas

> **Change exclusivamente documental.** Não alterar `backend/`, `frontend/`, testes, migrations nem o conteúdo das changes funcionais existentes. O objetivo é sanear a fonte de verdade antes de atualizar as changes.


## 0. Isolar a execução no Git antes de editar qualquer arquivo

- [x] 0.1 Executar `git status` e verificar se existem alterações locais preexistentes; não descartar, sobrescrever, fazer stash automático ou modificar trabalho do usuário
- [x] 0.2 Garantir que a sanitização partirá da `main` sem realizar alterações nela; se alterações locais impedirem a troca segura de branch, interromper e reportar o bloqueio
- [x] 0.3 Criar ou trocar para a branch `docs/sanitize-documentacao-base`
- [x] 0.4 Executar `git branch --show-current` e só continuar se o resultado for exatamente `docs/sanitize-documentacao-base`
- [x] 0.5 Manter todas as edições, verificações e commits desta change exclusivamente nessa branch; não fazer merge/rebase/push forçado nem alterar a `main` durante o apply

## 1. Sanitizar a visão geral do projeto

- [x] 1.1 Atualizar `docs/project-overview.md` para refletir o fluxo oficial com Totem dentro do escopo, fila de Recepção/Triagem, triagem, direcionamento automático por especialidade, distribuição para médico elegível, Sala e painel público; verificar que não permanece a frase de que o Totem não é desenvolvido pela equipe
- [x] 1.2 Atualizar a seção de usuários/perfis com o cadastro administrativo de Médico e Recepção/Triagem, incluindo os dados aprovados no D2; verificar que a especialidade do Médico está descrita como cadastral e não como restrição de atendimento
- [x] 1.3 Atualizar as funcionalidades globais com Pausar, Retomar e Encerrar plantão com fila zerada (D9), e com a regra de chamada de 30 segundos / 3 tentativas / uma reentrada ao fim da fila (D10)
- [x] 1.4 Substituir a descrição antiga de prioridade por cor de sintoma pela composição numérica do escore (D6), sem afirmar escore máximo 18
- [x] 1.5 Inserir uma seção de matriz global de permissões baseada no D13 e verificar explicitamente que autorização continua no Xano
- [x] 1.6 Atualizar `## 12. Fonte de verdade e documentação` para RF01–RF50 (D14) e ajustar a tabela de divergências conhecidas para remover decisões já encerradas por esta sanitização
- [x] 1.7 Atualizar a sequência planejada para registrar a futura change do Totem sem implementar nem criar a change funcional nesta tarefa

## 2. Sanitizar o modelo de domínio

- [x] 2.1 Atualizar o diagrama conceitual de `docs/domain-model.md`: `Usuario` 1:1 com `Medico` ou `Recepcao_Triagem` conforme o perfil; incluir `Sala`; remover do desenho a ideia de que `Medico_Especialidade` limita as filas atendidas; manter a especialidade de referência como dado cadastral
- [x] 2.2 Atualizar a seção `Médico` com CRM, especialidade de referência, disponibilidade, Sala, pausa e encerramento do plantão; verificar que médico pode atender qualquer especialidade quando elegível
- [x] 2.3 Criar a seção `Recepcao_Triagem` com usuário, nome, CPF, especialidade de referência e regras de vínculo 1:1
- [x] 2.4 Criar a seção `Sala` e descrever seu uso na chamada pública sem decidir ainda o schema físico do vínculo
- [x] 2.5 Atualizar `Sintoma`: remover `prioridade padrão (cor)` e definir `pontuacao` inteira de 1 a 3; documentar que todos os sintomas selecionados somam ao escore
- [x] 2.6 Adicionar o catálogo inicial completo do D8 e a regra pediátrica; conferir que não ficou nenhuma linha do catálogo usando Vermelha/Amarela/Azul como atributo do sintoma
- [x] 2.7 Atualizar `Ficha_Atendimento`: escore total = sintomas + sinais vitais; remover limite máximo fixo 18; preservar condição prioritária sem pontuação; documentar glicemia conforme D7
- [x] 2.8 Atualizar os parâmetros de regra: `intervalo_chamada_seg = 30`, máximo de 3 tentativas por oportunidade, uma nova oportunidade após reentrada, fuso fixo `America/Sao_Paulo`; não tratar o fuso como parâmetro editável pelo Administrador
- [x] 2.9 Documentar a máquina de estados do Ticket Pré-Triagem conforme D11, incluindo `CHAMADO → AGUARDANDO` para retorno ao fim da fila e a única nova oportunidade
- [x] 2.10 Documentar o ciclo da Sessão e o status operacional conforme D12, diferenciando logout/expiração, PAUSA/AUSENTE e encerramento de plantão
- [x] 2.11 Revisar a máquina de estados da Ficha para remover a afirmação antiga de desistência definitiva logo após a primeira sequência de três chamadas; manter a terminologia final compatível com a regra do D10 sem inventar schema

## 3. Sanitizar o contexto global para agentes

- [x] 3.1 Atualizar `openspec/config.yaml` conforme D15, mantendo-o curto; retirar menções a prioridade por "pior cor do sintoma", médico restrito à especialidade e intervalo de 10 segundos
- [x] 3.2 Atualizar `AGENTS.md` com a hierarquia de fonte de verdade do D1 e instrução explícita para não reintroduzir decisões antigas de changes quando conflitarem com a base sanitizada
- [x] 3.3 Garantir em `AGENTS.md` que mudanças futuras em regras de domínio atualizem `docs/project-overview.md`/`docs/domain-model.md` e suas specs correspondentes antes do código

## 4. Sincronizar documentação derivada

- [x] 4.1 Revisar `README.md` e corrigir somente trechos que contradigam a base: Totem no escopo, pontuação numérica, médico não restrito à especialidade, Sala, chamada de 30 s e referência atual
- [x] 4.2 Revisar `CONTRIBUTING.md` e corrigir a lista/descrição das fatias apenas onde a nova base torne o texto factualmente incorreto; não replanejar responsáveis ou datas sem decisão do PO

## 5. Verificação de saneamento

- [x] 5.1 Executar busca nos documentos-base/derivados (excluindo `openspec/changes/*`, `backend/` e `.git/`) por expressões obsoletas equivalentes a: `RF01–RF38`, `10 segundos`, `intervalo_chamada_seg.*10`, `prioridade_padrao`, `médico.*uma especialidade`, `médico.*várias especialidades`, `totem.*não.*desenvolvido`, `externo/abstraído`, `escore.*0.*18`; revisar manualmente cada ocorrência restante
- [x] 5.2 Verificar que `America/Sao_Paulo`, `30 segundos`, RF01–RF50, entidade Sala, entidade Recepcao_Triagem, Pausar e Encerrar plantão aparecem na base sanitizada
- [x] 5.3 Verificar que nenhuma alteração foi feita em `backend/`, `frontend/`, testes ou nas changes funcionais existentes
- [x] 5.4 Produzir uma seção final de impacto (no resultado do apply ou commit) listando, sem editar, as changes funcionais que agora conflitam com a base e o motivo resumido de cada conflito

## 6. Impactos mínimos esperados para revisão posterior

> Esta seção é checklist de descoberta, não autorização para editar as changes nesta sanitização.

- [x] 6.1 `add-base-compartilhada`: sintomas ainda usam `prioridade_padrao`; `intervalo_chamada_seg` ainda é 10; carga/fallback de especialidade precisa ser revista
- [x] 6.2 `add-cadastros-administrador`: médico/especialidade, cadastro de Recepção/Triagem, Sala, pausa e encerramento de plantão precisam ser reconciliados
- [x] 6.3 `add-pacientes-pre-triagem`: regra de chamada da Recepção/Triagem e Totem precisam ser reconciliadas com 30 s, reentrada e futura change do Totem
- [x] 6.4 `add-triagem-classificacao`: cálculo ainda compara cor de sintoma com risco; deve futuramente usar soma de pontos de sintomas + sinais vitais
- [x] 6.5 `add-direcionamento-senha`: fallback por especialidade de médico e regra de especialidade sugerida com `prioridade_padrao` precisam ser revistos
- [x] 6.6 `add-fila-chamada-medico`: 10 s, desistência após primeira sequência, fila restrita à especialidade e ausência de pausa/encerramento precisam ser revistos
- [x] 6.7 `add-painel-publico`: chamada deve passar a considerar Sala e a nova regra de reentrada, sem expor dados pessoais

## Impactos documentais tratados na segunda etapa

As changes funcionais abertas foram revisadas e alinhadas à baseline sanitizada. As tasks funcionais permanecem não executadas; esta etapa alterou somente planejamento e especificações OpenSpec.

| Change | Alinhamento documental realizado |
|---|---|
| `add-base-compartilhada` | Catálogo oficial com pontuação e direcionamento, sem cor/prioridade de sintoma; intervalo fixo de 30 s e fuso oficial não editável; sem fallback por disponibilidade/especialidade médica. |
| `add-autenticacao-perfis` | `Usuario` como autenticação; perfil Recepção/Triagem único e entidades de domínio Médico/Recepção-Triagem vinculadas 1:1; sessão distinta de status operacional. |
| `add-cadastros-administrador` | Cadastro de Médico, Recepção/Triagem e Sala; especialidade médica informativa; eligibility sem filtro pela especialidade de referência; sintomas e parâmetros coerentes com baseline. |
| `add-pacientes-pre-triagem` | Totem em change própria, ticket emitido sem duplicação na fila, chamadas a 30 s e até 3 por oportunidade, rechamada preserva ticket e estados alinhados à baseline. |
| `add-triagem-classificacao` | Soma dos pontos de todos os sintomas (1–3) e sinais vitais; glicemia exata; sem teto de 18; limiares configuráveis conforme valores iniciais da baseline; pediatria não substitui cálculo. |
| `add-direcionamento-senha` | Destino pelos sintomas/critérios pediátricos; sem fallback por elegibilidade médica; Sala distinta de especialidade; comprovante alinhado à regra de chamadas. |
| `add-fila-chamada-medico` | Elegibilidade sem filtro por especialidade cadastral; intervalos e oportunidades alinhados; Sala, pausa/plantão e transições da ficha documentados. Interleaving global entre especialidades permanece dependência de produto. |
| `add-painel-publico` | Sala da chamada e ticket de triagem exibidos sem dados pessoais; previsões por especialidade sem presumir ordem global ainda indefinida. |
| `add-acompanhamento-administrador` | Pausa/Ausência sem novas atribuições e sem remover fichas sob responsabilidade; sessão, status e plantão separados; encerramento condicionado à fila atribuída zerada. |
| `add-totem` | Nova change OpenSpec especifica emissão do ticket impessoal e entrada na fila de Recepção/Triagem; sem implementação funcional nesta etapa. |

Persistem como dependências antes da implementação funcional: regra de desempate quando sintomas apontam para destinos diferentes e política global de seleção entre filas de especialidades distintas. A abrangência de impressão física do Totem continua fora do escopo especificado nesta change e pode ser decidida se vier a ser necessária.

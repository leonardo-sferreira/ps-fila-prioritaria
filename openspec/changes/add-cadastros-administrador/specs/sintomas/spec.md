# Delta de especificação

## Purpose

Permite ao Administrador manter o catálogo de sintomas pontuados e os destinos clínicos de cada sintoma.

## ADDED Requirements

### Requirement: Cadastro de sintomas e destinos
O Administrador DEVE poder listar todos os sintomas (ativos e inativos), criar e editar sintoma com nome único, descrição opcional, grupo do catálogo, pontuação inteira de 1 a 3 e ao menos uma especialidade ativa de destino, em ordem de preferência, e ativar ou desativar o sintoma. A edição DEVE substituir o conjunto de destinos. Sintoma NÃO DEVE ser excluído; sintoma inativo deixa de aparecer na triagem, mas permanece nas fichas antigas.

#### Scenario: Criar sintoma com destinos
- **QUANDO** o Administrador cria "Palpitação" com pontuação 2 e destinos Cardiologia e Clínica Geral, nessa ordem
- **ENTÃO** o sintoma é criado ativo, os destinos são gravados com ordem 1 e 2 e a operação é auditada

#### Scenario: Pontuação fora do limite
- **QUANDO** a pontuação é 0 ou 4
- **ENTÃO** a gravação é recusada

#### Scenario: Sem destino ou destino inativo
- **QUANDO** nenhum destino é informado ou algum destino é uma especialidade inativa
- **ENTÃO** a gravação é recusada e nada é alterado

#### Scenario: Desativar sintoma
- **QUANDO** o Administrador desativa um sintoma
- **ENTÃO** ele deixa de ser oferecido na ficha, e as fichas que já o têm continuam com ele

#### Scenario: Perfil sem permissão
- **QUANDO** a Recepção/Triagem ou o Médico tentam alterar o catálogo
- **ENTÃO** o backend recusa e nada é alterado

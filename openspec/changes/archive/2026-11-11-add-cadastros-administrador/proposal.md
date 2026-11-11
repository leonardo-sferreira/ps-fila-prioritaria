# Proposta: cadastros do Administrador

| Campo | Valor |
|---|---|
| Change | `add-cadastros-administrador` |
| Sprint e entrega | Sprint 4, segunda 16/11/2026 |
| Card no Trello | "Cadastros do administrador — médicos, especialidades, sintomas e disponibilidade" |
| Depende de | `add-autenticacao-perfis` (usuário, perfis e `verificar_acesso`); fila médica (PR #39), que lê médicos, especialidades e disponibilidade |
| Situação | Revisada em 11/11/2026 (escopo completo do card, decisão do PO) e em implementação |
| Rastreabilidade formal | RF13–RF16 (§12), RF49 (§23), vínculos do médico (§7.1), administração (§10), N:N médico–especialidade (§11.1–11.2, D01), Rev. 2.1 |

## Why

Hoje especialidades, sintomas, médicos, plantões e parâmetros só podem ser alterados direto no banco do Xano. A fila médica já depende desses dados: um médico só fica disponível com plantão cadastrado, e as especialidades próprias dele decidem a ordem de chamada. O Administrador precisa mantê-los pelo sistema, com auditoria e sem apagar histórico.

A versão anterior desta change foi escrita antes de existirem a auditoria (`historico_alteracao`, `registrar_alteracao`), a tabela de parâmetros, o catálogo de sintomas, a tabela de disponibilidade e a elegibilidade dos médicos. Esta revisão parte do que já existe.

## What Changes

- **Especialidades:** listar, criar, editar (nome e descrição) e ativar/desativar. A sigla, usada nas senhas já emitidas, não muda depois de criada.
- **Sintomas:** listar todos (ativos e inativos), criar, editar (nome, descrição, grupo, pontuação 1–3) e ativar/desativar, com os **destinos** (especialidades, em ordem de preferência).
- **Médicos:** o formulário "Novo médico" cria **o login e o médico juntos**: nome, e-mail, senha inicial, CRM, especialidades próprias (várias) e sala atual. Editar, ativar/desativar (o login acompanha).
- **Recepção/Triagem:** cadastro com login junto: nome, e-mail, senha inicial, CPF e especialidade de referência. Editar e ativar/desativar.
- **Salas:** listar, criar, editar e ativar/desativar. O médico pode ter uma **sala atual**.
- **Disponibilidade (plantões):** por médico e por dia, criar, editar e remover períodos (data, hora de início e de fim). O plantão que passa da meia-noite é aceito. Não pode haver sobreposição para o mesmo médico. Período já iniciado não é removido.
- **Parâmetros e faixas:** listar e alterar os parâmetros configuráveis, com limites e coerência entre idades e limiares, e as faixas de pontuação dos sinais vitais, sem sobreposição.
- **Minha agenda:** o Médico vê os próprios plantões, sem editar.
- **Auditoria:** toda alteração registra o evento em `historico_alteracao`, em nome do Administrador, na mesma transação.
- **Nada é excluído**, exceto plantão futuro: o que tem histórico é desativado.

### Fora do escopo

- Gestão de usuários do Administrador e da equipe em geral (tela `/admin/usuarios`), que fica em `add-autenticacao-perfis`. Aqui só são criados os logins de Médico e Recepção/Triagem junto do cadastro.
- Consulta da auditoria na tela: fica em `add-acompanhamento-administrador`.
- Disponibilidade recorrente ("toda segunda"): cada período é registrado por data.
- Redistribuir fichas quando um médico é desativado.

## Capabilities

### New Capabilities
- `especialidades`: cadastro de especialidades.
- `sintomas`: cadastro de sintomas e destinos.
- `medicos-disponibilidade`: médicos, Recepção/Triagem, salas e plantões.
- `parametros-regras`: parâmetros e faixas configuráveis.
- `auditoria`: registro das alterações administrativas.

### Modified Capabilities
_Nenhuma._

## Impacto

- **Xano (grupo Cadastros):**
  - endpoints de especialidades, sintomas, médicos, Recepção/Triagem, salas, disponibilidade, parâmetros e faixas, todos validando `ADMINISTRADOR` (exceto "Minha agenda", do `MEDICO`);
  - funções puras de validação, com testes.
- **Tabelas novas:**
  - `sala`;
  - `recepcao_triagem`.
- **Campo novo:** `medico.sala_id`, a sala atual.
- O PATCH de parâmetros da fila médica (`parametros/{chave}`) passa a aceitar todos os parâmetros editáveis.
- **Reflex:**
  - páginas `/admin/especialidades`, `/admin/sintomas`, `/admin/medicos`, `/admin/recepcao`, `/admin/salas`, `/admin/disponibilidade` e `/admin/parametros`;
  - menu do Administrador;
  - "Minha agenda" na tela do Médico.
- **Configuração:** nova variável `XANO_CADASTROS_API_URL`.
- **Documentos:** `docs/domain-model.md` (Sala, Recepção/Triagem, vínculo médico–sala) e `docs/project-overview.md`.

## Perguntas em aberto

- [x] Escopo: tudo do card, incluindo salas, Recepção/Triagem, parâmetros e faixas (decisão do PO em 11/11/2026).
- [x] Como cadastrar o médico: o formulário cria o login (perfil Médico) junto com o médico (decisão do PO em 11/11/2026).
- [x] Vínculo médico–sala: `medico.sala_id` (sala atual), sem histórico de salas. Basta para o painel mostrar a sala de quem chamou.

# Proposta: Documentos do Paciente (RG e CRNM para estrangeiros)

| Campo | Valor |
|---|---|
| Change | `add-documentos-paciente` |
| Sprint e entrega | A definir |
| Fatias no Trello | Complemento da Fatia 2 — Cadastro de paciente (card a criar) |
| Dupla | A definir (sugestão: a mesma da Fatia 2 — Luisa na API e dados, Nicolas na tela) |
| Depende de | `add-identificacao-paciente-triagem` (arquivada); `add-base-compartilhada` (`obter_parametro` e `idade_maxima_crianca`); mudança de esquema da tabela `paciente` pelo PO |
| Situação | Proposta — decisões do PO em 25/10/2026 |
| Rastreabilidade | Seção 5 (Cadastro de pacientes), RF03, RF04, RF05, RN01 e RN02 do documento formal — todos alterados por esta change |

## Why

O cadastro de Paciente hoje exige CPF e não guarda nenhum outro documento. O PO decidiu em 25/10/2026 que o PS precisa registrar o RG dos pacientes brasileiros e atender estrangeiros que não têm CPF nem RG, identificando-os pela Carteira de Registro Nacional Migratório (CRNM). Como a Fatia 2 já foi entregue e arquivada, a mudança precisa de change própria.

## What Changes

- **Opção "Estrangeiro" no cadastro**, marcada pela Recepção/Triagem. Ela define quais documentos são obrigatórios:
  - **Paciente brasileiro (padrão):** CPF válido e único obrigatório, como hoje, e **RG com UF emissora obrigatórios**, exceto para **criança** (idade até o parâmetro `idade_maxima_crianca`, inicialmente 11 anos), para quem o RG é opcional.
  - **Paciente estrangeiro:** **CRNM obrigatória e única**; CPF e RG passam a ser opcionais. Se o estrangeiro tiver CPF, ele é validado e continua único.
- **RG:** número de 5 a 14 caracteres, só letras e números (`X` aceito), com UF entre as 27 siglas. Não é único (o mesmo número pode existir em estados diferentes) e não é chave de busca.
- **CRNM:** número de 7 a 10 caracteres, só letras e números, gravado em maiúsculas; único entre os pacientes.
- **Pesquisa:** por CPF, como hoje, **ou por CRNM** para estrangeiros sem CPF.
- **Atualização parcial:** RG e UF passam a ser atualizáveis. CPF, CRNM e a marcação de estrangeiro continuam não editáveis, por serem dados de identificação.
- RG e CRNM seguem a privacidade do CPF: nunca aparecem no painel público nem em operações sem autorização.
- Pacientes já cadastrados continuam válidos: são brasileiros com CPF e ficam com RG vazio até a próxima atualização. **BREAKING** para clientes da API: `POST /pacientes` de brasileiro passa a recusar cadastro sem RG.

### Fora do escopo

- Passaporte, CNH, CNS ou outros documentos; estrangeiro sem CRNM.
- Paciente sem nenhum documento (inconsciente ou não identificado), que precisa de fluxo próprio.
- Validação de dígito verificador do RG por estado ou da CRNM.
- Pesquisa por RG.
- Alterar CPF, CRNM ou a marcação de estrangeiro depois do cadastro, inclusive incluir CPF obtido depois por um estrangeiro.
- Autorização por perfil e auditoria reais, que continuam dependentes de `add-autenticacao-perfis` e `add-base-compartilhada` (mesmas pendências deferidas da Fatia 2).

## Capabilities

### New Capabilities

- Nenhuma.

### Modified Capabilities

- `pacientes`: a pesquisa aceita CRNM além do CPF; o cadastro passa a ter a opção de estrangeiro, RG com UF obrigatórios para brasileiros e CRNM obrigatória para estrangeiros; a atualização parcial passa a aceitar RG e UF.

## Impact

- **Xano — esquema:** tabela `paciente` ganha `estrangeiro`, `rg`, `rg_uf` e `crnm`; `cpf` passa a aceitar vazio para estrangeiros, mantendo a unicidade quando preenchido; `crnm` ganha índice único. A mudança de esquema passa pelo PO.
- **Xano — API:** `pacientes_get.xs` (pesquisa por CRNM), `pacientes_post.xs` (regras por tipo de paciente) e `pacientes_id_patch.xs` (RG e UF); nova função de validação de documentos reaproveitada pelos dois.
- **Reflex:** `PacienteState` e a tela `/recepcao/pacientes` (opção Estrangeiro, campos RG/UF e CRNM, pesquisa por CRNM).
- **Testes:** `frontend/tests/test_paciente_state.py` e testes de API de Paciente, com valores-limite.
- **Documentação:** `docs/domain-model.md` (Paciente, RN01 e RN02) e registro no Confluence (seção 5, RF03 a RF05, RN01 e RN02).
- **Figma:** telas 3 e 3a a 3e.

## Perguntas em aberto

- ~~RG obrigatório para crianças brasileiras~~: decidido pelo PO em 25/10/2026 — para criança o RG não é obrigatório.
- Confirmar sprint, card no Trello e dupla responsável.
- PO publicar as alterações da tabela `paciente` antes da implementação.
- Registrar no Confluence a mudança de RN01, RN02 e da seção 5 (o documento formal prevê só o CPF).

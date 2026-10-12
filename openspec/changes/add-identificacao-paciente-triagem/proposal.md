# Proposta: Identificação e cadastro de Paciente na Triagem

| Campo | Valor |
|---|---|
| Change | `add-identificacao-paciente-triagem` |
| Sprint e entrega | Sprint 1 — identificação e cadastro de Paciente |
| Fatias no Trello | Fatia 2 — Cadastro de paciente |
| Dupla | Luisa (API e dados) · Nicolas (tela) |
| Depende de | `add-autenticacao-perfis` e `add-base-compartilhada` |
| Situação | Em implementação |
| Rastreabilidade | RF03, RF04, RF05, RN01, RN02 e CA01 |

> Esquema físico: a tabela `paciente` já está publicada em `backend/xano/table/`. Não há mudança de esquema prevista nesta Sprint.

## Why

A Recepção/Triagem precisa localizar um Paciente pelo CPF e cadastrá-lo quando ainda não existir, evitando duplicidade. Esta fatia entrega identificação e atualização cadastral sem acoplamento à operação de ticket/fila ou à abertura posterior de Ficha.

## What Changes

- **Pacientes:** pesquisa por CPF, cadastro quando não encontrado e atualização parcial dos dados cadastrais. CPF é obrigatório, válido, normalizado, único e imutável; nome completo e data de nascimento são obrigatórios; telefone é opcional.
- **Autorização e auditoria:** Recepção/Triagem pesquisa, cadastra e atualiza; Administrador somente consulta; Médico não acessa. Cadastros e alterações reais usam a infraestrutura de auditoria compartilhada.
- **Reflex:** área protegida de Recepção/Triagem para busca, cadastro e atualização, com confirmação visual de Paciente encontrado.
- **Contrato:** `GET /pacientes?cpf=`, `POST /pacientes` e `PATCH /pacientes/{id}`. PATCH parcial retorna `alterado: false` quando não há mudança e não audita esse caso.

### Fora do escopo

- Emissão e operação de ticket/fila, chamada, rechamada, tentativas, desistência, não comparecimento, vínculo operacional Paciente × ticket e painel público.
- Abertura/edição de Ficha, sintomas, sinais vitais, classificação e direcionamento de senha.
- CA02 e CA03.
- Busca por nome e desativação pela interface.

## Capacidades

### Novas capacidades

- `pacientes`: pesquisa, cadastro e atualização de Pacientes por CPF.

### Capacidades modificadas

_Nenhuma._

## Impacto

- **Xano:** função reutilizável de normalização/validação de CPF e endpoints de Paciente usando a tabela existente.
- **Reflex:** fluxo protegido de identificação, cadastro e atualização em Recepção/Triagem.
- **Testes:** CPF, busca, cadastro, PATCH, autorização, auditoria e CA01.
- **Dependências:** `add-autenticacao-perfis` fornece token, acesso e 401/403; `add-base-compartilhada` fornece `registrar_alteracao`.

## Perguntas em aberto

- [x] O contrato adotado é `PATCH /pacientes/{id}`; CPF é imutável e nome, nascimento e telefone são parciais. · DECIDIDO
- [x] `Continuar` é apenas confirmação visual nesta Sprint; não cria ou abre Ficha, não cria/altera ticket e não persiste seleção. · DECIDIDO
- [ ] Os textos formais completos de RF03–RF05 e CA01 não estão no repositório; devem ser conferidos no Confluence antes do aceite final. · PENDENTE

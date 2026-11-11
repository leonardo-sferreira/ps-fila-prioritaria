# Proposta: fichas do dia e acesso à ficha atual do paciente

| Campo | Valor |
|---|---|
| Change | `add-fichas-do-dia` |
| Sprint / card Trello | Sprint 4; card "Reavaliação da ficha" (complemento) |
| Depende de | `add-reavaliacao-ficha-aguardando` (arquivada em 09/11/2026), que torna a ficha AGUARDANDO editável (RF12) |
| Situação | Proposta (pedido do PO em 10/11/2026), aguardando revisão |
| Rastreabilidade formal | RF12 (reavaliação da ficha aguardando) e RN03 (uma ficha não finalizada por paciente), Documentação de Requisitos Rev. 2.1 |

## Why

A Recepção/Triagem não tem onde ver as fichas já criadas. A ficha **em triagem** só é reaberta redigitando o CPF. A ficha **aguardando** (já com senha) não pode ser aberta pela identificação, que recusa com "o paciente já está na fila". Depois de sair do comprovante, a Recepção perde o acesso a ela.

Na prática, a reavaliação do RF12 fica inacessível: se o paciente piora na sala de espera, a triagem não consegue reabrir a ficha para reclassificar. Também não há como consultar o que foi atendido no dia.

## What Changes

- **Nova aba "Fichas do dia"** no menu da Recepção/Triagem (`/recepcao/fichas`). Lista as fichas não finalizadas (de qualquer dia) e as finalizadas de hoje, com hora de chegada, nome do paciente, senha, cor, especialidade e situação, da chegada mais recente para a mais antiga.
- **Filtro por situação** (Todas, Em triagem, Aguardando, Chamadas, Finalizadas) e **busca por nome ou senha** na própria tela.
- **Botão "Abrir"** em cada linha, que leva à ficha. Em triagem e aguardando, a ficha continua editável como hoje. Chamada e finalizada continuam só para leitura.
- **Atalho na identificação:** quando o paciente identificado pelo CPF já tem ficha aguardando ou chamada, a tela mostra "Este paciente já está na fila" com o botão **"Abrir ficha atual"**, em vez de só o erro. Continua sem criar segunda ficha (RN03).
- **Xano:**
  - novo `GET fichas`, só para a Recepção/Triagem;
  - `POST fichas` passa a devolver a ficha existente também quando ela está aguardando ou chamada (sem ticket), indicando a situação, em vez de recusar.

### Fora do escopo

- Histórico de dias anteriores e busca por período (só hoje, mais as não finalizadas).
- Lista de fichas para o Médico e para o Administrador (ficam com `add-fila-chamada-medico` e `add-acompanhamento-administrador`).
- Edição de ficha chamada ou finalizada.
- Mudança nas regras de classificação, direcionamento ou senha.

## Capabilities

### New Capabilities
_Nenhuma._

### Modified Capabilities
- `ficha-atendimento`: nova consulta das fichas do dia; a abertura passa a devolver a ficha atual do paciente na fila, em vez de recusar.

## Impacto

- **Xano:**
  - novo `api/triagem/fichas_get.xs`;
  - ajuste em `api/triagem/fichas_post.xs`.
  - Nenhuma tabela é alterada (`ficha_atendimento` está entre as tabelas divergentes do servidor).
- **Reflex:**
  - nova página e estado `fichas_do_dia`;
  - aba no menu da Recepção;
  - atalho na identificação (`estados/pacientes.py` e `paginas/pacientes.py`).
- **Testes:** testes unitários dos estados novos e alterados; teste da função de filtro; roteiro manual com fichas reais.
- **Documentos:** `docs/project-overview.md` (telas da Recepção e reavaliação acessível pela lista).

## Perguntas em aberto

- [ ] Mostrar o nome completo do paciente na lista? Proposta: sim. É uma tela interna da Recepção, como a própria ficha, e o CPF não aparece.
- [ ] A lista deve se atualizar sozinha? Proposta: sim, a cada 15 segundos, sem ação sobre as fichas, além do botão "Atualizar".
- [ ] Ao identificar um paciente com ficha aguardando, abrir a ficha direto ou mostrar o aviso com o botão? Proposta: mostrar o aviso com "Abrir ficha atual", para a Recepção perceber que é a mesma ficha e não uma nova chegada.

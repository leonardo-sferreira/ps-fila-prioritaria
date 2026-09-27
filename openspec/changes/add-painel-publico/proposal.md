# Proposta

## Por quê

Os pacientes que aguardam precisam saber quando e para onde ir, sem ter seus dados expostos. O painel público é a única interface do sistema voltada ao paciente e mostra, em tempo quase real, a senha chamada e a previsão das próximas, com o mesmo algoritmo da chamada real.

## O que muda

- **Página pública do painel**, sem login, para TV na sala de espera (RF33, UC11).
- **Senha atual em destaque**, com especialidade e local, e com aviso visual e sonoro a cada chamada nova ou repetida (seção 11.3).
- **Últimas chamadas** (histórico curto).
- **Previsão das próximas N senhas por especialidade** (inicial 5), vinda da função de previsão da fila (RF34, RF35, RN25, RN26, CA10–CA12).
- **Ticket da pré-triagem chamado pela Recepção/Triagem**, para o paciente saber que é a vez dele na triagem.
- **Filtro por especialidade** na URL, para ter vários painéis.
- **Privacidade:** nenhum nome, CPF ou dado pessoal; só senhas e especialidades (RN35, RNF06).

### Fora do escopo

- Chamada por voz sintetizada (só um aviso sonoro curto).
- Cadastro de salas ou consultórios: o "local" exibido é a especialidade (ver design.md, D3).
- Qualquer mudança nas regras da fila (a previsão vem de `add-fila-chamada-medico`).

## Capacidades

### Novas capacidades
- `painel-publico`: exibição pública das chamadas, das últimas chamadas e da previsão das próximas senhas.

### Capacidades modificadas
_Nenhuma._

## Impacto

- **Xano:** endpoint público somente leitura `GET painel?especialidades=`, que agrega as últimas `chamada`, as previsões (`prever_fila`) e os tickets pré-triagem chamados, só com campos não pessoais.
- **Reflex:** página `/painel` em tela cheia, com polling, destaque e som.
- **Testes:** `tests/api/test_painel.py` (conteúdo, privacidade e coerência com a chamada).
- **Depende de:** `add-fila-chamada-medico` (chamadas e previsão) e `add-pacientes-pre-triagem` (tickets).

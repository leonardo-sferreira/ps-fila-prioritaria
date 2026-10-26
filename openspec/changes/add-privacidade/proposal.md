# Proposta: Aviso de privacidade, CPF mascarado e saída por inatividade

| Campo | Valor |
|---|---|
| Change | `add-privacidade` |
| Sprint e entrega | A definir pelo PO |
| Card no Trello | A criar ("Privacidade: aviso, CPF mascarado e saída por inatividade") |
| Depende de | `add-autenticacao-perfis` (login, `auth/me`, `auth/logout` e telas de acesso) |
| Situação | Em revisão |

## Why

O sistema guarda dados pessoais da equipe e de pacientes, incluindo dados de saúde, e é usado em computadores compartilhados da recepção. Hoje ninguém consegue saber, pela tela, quais dados são tratados e para quê; o CPF aparece inteiro onde não precisa; e uma sessão esquecida aberta deixa dados de pacientes à vista de quem passar. A Documentação de Requisitos (Rev. 2.1) só trata privacidade no painel público e no Totem (RNF06, §13; §15, item 9); estas três medidas são decisão do PO de 26/10/2026.

## What Changes

- **Aviso de privacidade:** link "Aviso de privacidade" na tela de login (e nas demais telas de acesso), abrindo uma página pública `/privacidade`, sem login, que explica quais dados da equipe e dos pacientes o sistema trata, para quê, com quem são compartilhados, por quanto tempo são guardados e quais são os direitos do titular. O texto fica versionado em `docs/aviso-de-privacidade.md` e a página mostra exatamente esse texto. Não há aceite nem registro de leitura.
- **CPF mascarado:** nas telas internas que mostram o CPF de um paciente sem precisar dele inteiro, o CPF aparece no formato `***.456.789-**`. Os campos em que o CPF é digitado (busca e cadastro) continuam completos. Hoje isso vale para o cabeçalho da ficha de atendimento.
- **Saída por inatividade:** nas áreas internas, depois de um tempo sem uso (padrão de 1 hora, configurável no Xano), o sistema encerra a sessão como no "Sair" e volta ao login com a mensagem "Sua sessão foi encerrada por inatividade."

### Fora do escopo

- Aceite do aviso, registro de consentimento e versão aceita por usuário.
- Pedidos do titular pelo sistema (acesso, correção, exclusão) e canal automatizado do encarregado; o aviso só informa como pedir.
- Mascarar o CPF nas respostas da API: o Xano continua devolvendo o CPF completo às telas autorizadas; esta change trata da exibição.
- Exigir login nos endpoints de pacientes e triagem: a spec `pacientes` já exige ("Privacidade e autorização"), mas os endpoints publicados hoje não pedem token. É uma divergência existente, registrada nas perguntas em aberto, a ser corrigida numa change própria.
- Bloqueio de inatividade aplicado pelo Xano (expirar o token por falta de uso). Nesta change, a inatividade é medida no navegador; o token continua com a validade de 12 h.
- Políticas de retenção automática (apagar dados após um prazo).

## Capabilities

### New Capabilities
- `privacidade`: aviso de privacidade público, exibição mascarada do CPF nas telas internas e encerramento da sessão por inatividade.

### Modified Capabilities
_Nenhuma. A `autenticacao` ainda está na change `add-autenticacao-perfis`; esta change só reutiliza o login, o `auth/me` e o `auth/logout`._

## Impact

- **Xano:** variável de ambiente `INATIVIDADE_SEGUNDOS` (padrão 3600); o `auth/me` passa a devolver esse valor para a tela.
- **Reflex:** página pública `/privacidade`; link nas telas de acesso; função de máscara de CPF usada no cabeçalho da ficha; contador de inatividade nas páginas protegidas e mensagem no login.
- **Documentação:** novo `docs/aviso-de-privacidade.md`; `docs/project-overview.md` (funcionalidades e regras globais de privacidade).
- **Testes:** testes de estado (máscara de CPF, encerramento por inatividade, página do aviso) e teste ao vivo do `auth/me` com o novo campo.
- **Rastreabilidade:** RNF06 e §15, item 9 (privacidade), estendidos por decisão do PO; registrar no documento de requisitos.

## Perguntas em aberto

- [x] Aviso só com link, sem aceite: decidido pelo PO em 26/10/2026. · DECIDIDO PO
- [x] Regras na tela: CPF mascarado e saída por inatividade: decidido pelo PO em 26/10/2026. · DECIDIDO PO
- [x] Tempo de inatividade: 1 hora, decidido pelo PO em 26/10/2026. · DECIDIDO PO
- [x] Controlador e encarregado: o PO decidiu em 26/10/2026 não incluir essa seção no aviso; os pedidos do titular vão à Recepção/Triagem ou ao Administrador. · DECIDIDO PO
- [ ] Prazos de guarda dos dados: o aviso diz "a definir pelo PO" até a decisão. · PENDENTE PO
- [ ] Endpoints de pacientes e triagem sem exigir token (divergência com a spec `pacientes`): abrir change própria. · PENDENTE PO
- [ ] Registrar no documento de requisitos e no Confluence a extensão do RNF06. · PENDENTE PO

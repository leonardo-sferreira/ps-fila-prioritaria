# Tasks

## 1. Xano — emissão segura de tickets

- [x] 1.0 [PO] Publicar em `ticket_pre_triagem` o campo `tipo` (`PEDIATRICO`, `PREFERENCIAL`, `NORMAL`) e o índice único `(data, tipo, numero)` (D5); verificar o `.xs` exportado em `backend/xano/table/`
  - Evidência (25/10/2026): push na branch `v1` (apenas `table/ticket_pre_triagem.xs`); `xano workspace pull` confirmou o campo `tipo` com padrão `NORMAL`, o índice único `(data, tipo, numero)` e as FKs para `usuario` e `paciente` preservadas; o `.xs` do repositório foi substituído pelo exportado.
- [x] 1.1 Criar o registro de ticket e mecanismo de numeração diária por tipo no fuso `America/Sao_Paulo`; verificar primeira emissão de cada tipo, sequência, sequências independentes entre tipos, virada de dia e emissões concorrentes sem número duplicado no mesmo tipo
  - Evidência (08/11/2026): `api/triagem/totem_tickets_post.xs` publicado na `v1` (dry-run antes; a tabela já era igual ao repositório). Próximo número = maior do dia e tipo + 1, com a data em `America/Sao_Paulo`; colisão no índice único `(data, tipo, numero)` gera nova tentativa (até 5). Ao vivo: primeiro de cada tipo `C-001`/`P-001`/`N-001`, sequências independentes e 4 emissões simultâneas com números distintos. A virada do dia não é reproduzível ao vivo: fica coberta pela data no fuso oficial e conferida no roteiro manual.
- [x] 1.2 Criar a operação de emissão protegida por segredo de dispositivo no servidor, exigindo o tipo e devolvendo `tipo`, `numero` e código formatado (`C-001`, `P-001`, `N-001`); verificar que credencial ausente/incorreta ou tipo ausente/inválido não cria ticket e que a resposta não contém dados pessoais
  - Evidência: chave de dispositivo na variável `TOTEM_CHAVE` do Xano (gerada aleatoriamente, sem exibir o valor); chave ausente ou errada → 401 sem ticket; tipo ausente ou inválido → 400 sem ticket; resposta só com `tipo`, `numero` e `codigo`.
- [x] 1.3 Criar testes de API para emissões sucessivas/concorrentes por tipo, sequências independentes, mudança de data operacional, tipo ausente/inválido, credencial inválida, ausência de sessão de equipe e ausência de campos pessoais; verificar que todos passam
  - Evidência: `frontend/tests/test_api_totem.py`, 7 testes ao vivo passando (cada tipo, sequência independente, chave inválida, tipo inválido, simultâneas, ausência de campos pessoais). Ausência de sessão de equipe: o endpoint não usa `auth` e emite só com a chave do dispositivo.

## 2. Reflex — experiência pública do Totem

- [ ] 2.1 Criar a página pública do Totem com escolha do tipo (Pediátrico, Preferencial, Normal), ação de emissão e apresentação do código retornado; verificar manualmente a emissão de cada tipo, o prefixo exibido e a instrução para aguardar Recepção/Triagem
  - Parcial: página `/totem` igual à tela 1 do Figma (captura), com os três tipos e o código em destaque no cartão de "ticket emitido"; `test_totem_state.py` cobre emissão e Concluir. Falta o PO tocar em cada tipo no navegador (o navegador automático não toca na tela).
- [x] 2.2 Encaminhar a credencial exclusivamente pela chamada server-side; verificar no navegador/rede que segredo não está no HTML, JavaScript, URL ou payload acessível ao paciente
  - Evidência: `TotemState.emitir` lê `TOTEM_CHAVE` no servidor e não guarda a chave no estado; conferido que a chave não aparece no HTML da página nem em nenhum arquivo do frontend gerado (`.web`).
- [x] 2.3 Verificar estados de carregamento e falha de emissão, sem retry automático que possa produzir tickets duplicados
  - Evidência: estados "emitindo", "ticket emitido" e "falha" em `aviso_totem()`; falha de API ou de conexão mostra o erro com uma única chamada, sem nova tentativa automática (testes de estado).

- [x] 2.4 [Reflex] Na tela de login, link "Abrir o Totem de autoatendimento" para `/totem`; o Totem não tem link de volta ao login (decisão do PO em 08/11/2026). Verificar por captura que o link aparece no login e que a tela do Totem não tem nenhum caminho para o login
  - Evidência (08/11/2026): captura do login com "Abrir o Totem de autoatendimento →" abaixo de "Esqueci minha senha"; o HTML de `/totem` não tem nenhum link (só a folha de estilo).

## 3. Integração e documentação

- [ ] 3.1 Verificar ponta a ponta, quando a futura change de operação da fila existir, que o ticket emitido pelo Totem é consumido com a mesma identidade, tipo e número
  - Parcial: a emissão grava `AGUARDANDO` com `emitido_em`, que é o que `tickets/proximo` (PR #18) usa para ordenar. Falta chamar pela tela da Recepção um ticket emitido no Totem, o que exige login com código por e-mail.
- [x] 3.2 Documentar configuração segura da credencial e roteiro manual de emissão; verificar instruções sem incluir valor real de segredo
  - Evidência: README (seção "Totem", com configuração da chave e roteiro manual) e `frontend/.env.example` (`TOTEM_CHAVE` sem valor).

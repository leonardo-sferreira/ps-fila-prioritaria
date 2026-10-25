# Tasks

## 1. Xano — emissão segura de tickets

- [x] 1.0 [PO] Publicar em `ticket_pre_triagem` o campo `tipo` (`PEDIATRICO`, `PREFERENCIAL`, `NORMAL`) e o índice único `(data, tipo, numero)` (D5); verificar o `.xs` exportado em `backend/xano/table/`
  - Evidência (25/10/2026): push na branch `v1` (apenas `table/ticket_pre_triagem.xs`); `xano workspace pull` confirmou o campo `tipo` com padrão `NORMAL`, o índice único `(data, tipo, numero)` e as FKs para `usuario` e `paciente` preservadas; o `.xs` do repositório foi substituído pelo exportado.
- [ ] 1.1 Criar o registro de ticket e mecanismo de numeração diária por tipo no fuso `America/Sao_Paulo`; verificar primeira emissão de cada tipo, sequência, sequências independentes entre tipos, virada de dia e emissões concorrentes sem número duplicado no mesmo tipo
- [ ] 1.2 Criar a operação de emissão protegida por segredo de dispositivo no servidor, exigindo o tipo e devolvendo `tipo`, `numero` e código formatado (`C-001`, `P-001`, `N-001`); verificar que credencial ausente/incorreta ou tipo ausente/inválido não cria ticket e que a resposta não contém dados pessoais
- [ ] 1.3 Criar testes de API para emissões sucessivas/concorrentes por tipo, sequências independentes, mudança de data operacional, tipo ausente/inválido, credencial inválida, ausência de sessão de equipe e ausência de campos pessoais; verificar que todos passam

## 2. Reflex — experiência pública do Totem

- [ ] 2.1 Criar a página pública do Totem com escolha do tipo (Pediátrico, Preferencial, Normal), ação de emissão e apresentação do código retornado; verificar manualmente a emissão de cada tipo, o prefixo exibido e a instrução para aguardar Recepção/Triagem
- [ ] 2.2 Encaminhar a credencial exclusivamente pela chamada server-side; verificar no navegador/rede que segredo não está no HTML, JavaScript, URL ou payload acessível ao paciente
- [ ] 2.3 Verificar estados de carregamento e falha de emissão, sem retry automático que possa produzir tickets duplicados

## 3. Integração e documentação

- [ ] 3.1 Verificar ponta a ponta, quando a futura change de operação da fila existir, que o ticket emitido pelo Totem é consumido com a mesma identidade, tipo e número
- [ ] 3.2 Documentar configuração segura da credencial e roteiro manual de emissão; verificar instruções sem incluir valor real de segredo

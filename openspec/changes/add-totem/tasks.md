# Tasks

## 1. Xano — emissão segura de tickets

- [ ] 1.1 Criar o registro de ticket e mecanismo de numeração diária no fuso `America/Sao_Paulo`; verificar primeira emissão, sequência, virada de dia e emissões concorrentes sem número duplicado
- [ ] 1.2 Criar a operação de emissão protegida por segredo de dispositivo no servidor; verificar que credencial ausente/incorreta não cria ticket e que a resposta não contém dados pessoais
- [ ] 1.3 Criar testes de API para emissões sucessivas/concurrentes, mudança de data operacional, credencial inválida, ausência de sessão de equipe e ausência de campos pessoais; verificar que todos passam

## 2. Reflex — experiência pública do Totem

- [ ] 2.1 Criar a página pública do Totem com ação de emissão e apresentação do ticket retornado; verificar manualmente emissão e instrução para aguardar Recepção/Triagem
- [ ] 2.2 Encaminhar a credencial exclusivamente pela chamada server-side; verificar no navegador/rede que segredo não está no HTML, JavaScript, URL ou payload acessível ao paciente
- [ ] 2.3 Verificar estados de carregamento e falha de emissão, sem retry automático que possa produzir tickets duplicados

## 3. Integração e documentação

- [ ] 3.1 Verificar ponta a ponta que o ticket emitido pelo Totem aparece na fila da change `add-pacientes-pre-triagem` com a mesma identidade e número
- [ ] 3.2 Documentar configuração segura da credencial e roteiro manual de emissão; verificar instruções sem incluir valor real de segredo

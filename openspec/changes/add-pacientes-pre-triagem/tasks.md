# Tarefas

## 1. Xano — pacientes

- [ ] 1.1 [Xano] Criar a tabela `paciente` (D1) e a função `normalizar_cpf` (D5); verificar com Run & Debug um CPF válido, um com pontuação, "111.111.111-11" e um com 10 dígitos
- [ ] 1.2 [Xano] Criar `GET pacientes?cpf=` (RECEPCAO_TRIAGEM e ADMINISTRADOR), `POST pacientes` e `PATCH pacientes/{id}` (RECEPCAO_TRIAGEM, auditados, CPF imutável); verificar com os testes 1.3
- [ ] 1.3 Escrever `tests/api/test_pacientes.py` cobrindo CPF com e sem pontuação, CPF inválido, não encontrado, duplicado, data futura, campos ausentes, tentativa de alterar CPF, auditoria da atualização, 403 para Médico, 403 para o Administrador ao cadastrar e 401 sem token; verificar que passam

## 2. Xano — tickets e fila pré-triagem

- [ ] 2.1 [Xano] Criar a tabela `ticket_pre_triagem`, a variável `TOTEM_CHAVE` e `POST totem/tickets` com numeração diária (D2, D4); verificar com os testes 2.4
- [ ] 2.2 [Xano] Criar `GET pre-triagem/tickets` e `POST pre-triagem/chamar-proximo` com atualização condicional (D3); verificar com os testes 2.4
- [ ] 2.3 [Xano] Criar `POST pre-triagem/tickets/{id}/rechamar`, `.../nao-compareceu` e `.../identificado` (com `paciente_id`), aceitos só para quem chamou o ticket; verificar com os testes 2.4
- [ ] 2.4 Escrever `tests/api/test_pre_triagem.py` cobrindo o primeiro ticket do dia, a sequência, a virada do dia (com data simulada via parâmetro de teste ou dado inserido), 10 emissões paralelas sem número repetido, chave ausente ou errada, chamada em ordem, duas chamadas paralelas recebendo tickets diferentes, fila vazia, usuário com ticket pendente, conclusão por outro usuário e 403 para Médico; verificar que passam
- [ ] 2.5 Exportar o XanoScript das seções 1 e 2 para `backend/xano/` e verificar que os arquivos estão no repositório

## 3. Reflex — totem, recepção e pacientes

- [ ] 3.1 [Reflex] Criar a página `/totem` (D6) com a chamada feita pelo servidor usando `TOTEM_CHAVE`; verificar manualmente a emissão e, pelo DevTools do navegador, que a chave não aparece em nenhuma requisição do navegador
- [ ] 3.2 [Reflex] Criar em `/recepcao` o painel "Fila pré-triagem" com atualização automática a cada 5 s e os botões Chamar próximo, Rechamar e Não compareceu; verificar manualmente com duas abas logadas como usuários diferentes
- [ ] 3.3 [Reflex] Criar a busca por CPF com máscara, o formulário de cadastro (com o CPF preenchido quando não encontrado) e a edição de dados; verificar manualmente os casos encontrado, não encontrado, inválido e duplicado
- [ ] 3.4 [Reflex] Ligar a ação "Paciente identificado" ao ticket chamado; verificar manualmente que o ticket sai da lista
- [ ] 3.5 [Reflex] Criar `/admin/pacientes` (consulta somente leitura por CPF); verificar manualmente que não há ações de edição
- [ ] 3.6 Adicionar ao README o roteiro manual da seção 3 e a configuração de `TOTEM_CHAVE`; verificar executando-o

## 4. Integração e documentação

- [ ] 4.1 Verificação ponta a ponta: emitir 3 tickets pelo `/totem`, chamar o primeiro na recepção, cadastrar um paciente novo, marcar "Paciente identificado", marcar o segundo como "Não compareceu" e conferir no Xano os status e a auditoria do cadastro
- [ ] 4.2 Conferir `docs/domain-model.md` (Paciente e Ticket_Pré-Triagem) com as tabelas criadas e ajustar o que divergir

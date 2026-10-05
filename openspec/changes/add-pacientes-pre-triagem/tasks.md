# Tarefas

## 1. Xano — pacientes

- [ ] 1.1 [Xano] Criar a tabela `paciente` (D1) e a função `normalizar_cpf` (D5); verificar com Run & Debug um CPF válido, um com pontuação, "111.111.111-11" e um com 10 dígitos
- [ ] 1.2 [Xano] Criar `GET pacientes?cpf=` (RECEPCAO_TRIAGEM e ADMINISTRADOR), `POST pacientes` e `PATCH pacientes/{id}` (RECEPCAO_TRIAGEM, auditados, CPF imutável); verificar com os testes 1.3
- [ ] 1.3 Escrever `tests/api/test_pacientes.py` cobrindo CPF com e sem pontuação, CPF inválido, não encontrado, duplicado, data futura, campos ausentes, tentativa de alterar CPF, auditoria da atualização, 403 para Médico, 403 para o Administrador ao cadastrar e 401 sem token; verificar que passam

## 2. Xano — tickets e fila pré-triagem

- [ ] 2.1 [Xano] Integrar à fila os tickets emitidos por `add-totem`, sem duplicar tabela/operação de criação; verificar que a lista retorna exatamente o número e a identidade persistidos pelo Totem
- [ ] 2.2 [Xano] Criar `GET pre-triagem/tickets` e `POST pre-triagem/chamar-proximo` com atualização condicional; verificar ordem de emissão, concorrência e um ticket CHAMADO por operador
- [ ] 2.3 [Xano] Criar chamadas/rechamadas, retorno único ao fim da fila após a primeira oportunidade, encerramento como NAO_COMPARECEU após a segunda, desistência explícita e identificação do paciente; verificar 30 s, 3 chamadas por oportunidade, mesma identidade do ticket e acesso só por Recepção/Triagem
- [ ] 2.4 Escrever `tests/api/test_pre_triagem.py` cobrindo chamada em ordem, chamadas concorrentes, fila vazia, limite de 30 s, tentativas 1–3, única reentrada com o mesmo número, NAO_COMPARECEU após a segunda oportunidade, desistência explícita, conclusão por outro usuário e 403 para Médico; verificar que passam
- [ ] 2.5 Exportar o XanoScript das seções 1 e 2 para `backend/xano/` e verificar que os arquivos estão no repositório

## 3. Reflex — recepção e pacientes

- [ ] 3.1 [Reflex] Criar em `/recepcao` o painel "Fila de Recepção/Triagem" com atualização e botões Chamar próximo, Rechamar, Registrar desistência e Paciente identificado; verificar tentativas, reentrada e concorrência com duas sessões
- [ ] 3.3 [Reflex] Criar a busca por CPF com máscara, o formulário de cadastro (com o CPF preenchido quando não encontrado) e a edição de dados; verificar manualmente os casos encontrado, não encontrado, inválido e duplicado
- [ ] 3.4 [Reflex] Ligar a ação "Paciente identificado" ao ticket chamado; verificar manualmente que o ticket sai da lista e abre a ficha pela change seguinte
- [ ] 3.5 [Reflex] Criar `/admin/pacientes` (consulta somente leitura por CPF); verificar manualmente que não há ações de edição
- [ ] 3.6 Adicionar ao README o roteiro manual da seção 3 e a dependência do Totem; verificar executando-o

## 4. Integração e documentação

- [ ] 4.1 Verificação ponta a ponta com `add-totem`: emitir tickets, chamar o primeiro, validar o ciclo 3 chamadas + reentrada, identificar paciente e registrar desistência explícita do segundo; conferir status e auditoria no Xano
- [ ] 4.2 Conferir `docs/domain-model.md` (Paciente e Ticket_Pré-Triagem) com as tabelas criadas e ajustar o que divergir

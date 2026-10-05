# Tarefas

## 1. Xano — auditoria e parâmetros

- [ ] 1.1 [Xano] Criar a tabela `historico_alteracao` (D1) sem endpoints de escrita e verificar no painel que nenhum endpoint da API faz PATCH/DELETE nela
- [ ] 1.2 [Xano] Criar a função `registrar_alteracao` e verificar, com Run & Debug, que uma transação com erro forçado depois da chamada não deixa registro (D6)
- [ ] 1.3 [Xano] Criar a tabela `parametro`, a função `obter_parametro` e os endpoints `GET parametros` (autenticado) e `PATCH parametros/{chave}` (ADMINISTRADOR, com validação por chave e auditoria) (D5); verificar com os testes 1.4
- [ ] 1.4 Escrever `tests/api/test_parametros.py` e `tests/api/test_auditoria.py` cobrindo valores iniciais, os limites 0/1/20/21 da previsão, a coerência de idades, 401 sem token, 403 para outros perfis, operação recusada sem auditoria e alteração válida com auditoria; verificar que passam

## 2. Xano — especialidades e sintomas

- [ ] 2.1 [Xano] Criar a tabela `especialidade` e os endpoints de listagem (autenticado; só ativas para quem não é ADMINISTRADOR), criação, edição e ativar/desativar (ADMINISTRADOR), todos auditados; não implementar fallback por especialidade alternativa; verificar com os testes 2.4
- [ ] 2.2 [Xano] Criar as tabelas `sintoma` e `sintoma_especialidade` e os endpoints equivalentes, incluindo `PUT sintomas/{id}/especialidades`, com recusa de especialidade inativa; verificar com os testes 2.4
- [ ] 2.3 [Xano] Criar a função `carga_inicial` e o endpoint `POST admin/carga-inicial` (D7); verificar que duas execuções seguidas não duplicam registros
- [ ] 2.4 Escrever `tests/api/test_cadastros.py` cobrindo sigla (2, 3 e 4 letras, com número, minúscula convertida), duplicidades sem diferenciar caixa, pontuações 0/1/3/4, especialidade inativa na relação, desativação, auditoria de edição e 403 para os outros perfis; verificar que passam

## 3. Xano — médicos e disponibilidade

- [ ] 3.1 [Xano] Criar os cadastros de `medico`, `recepcao_triagem` e `sala`, seus vínculos 1:1 a `usuario` e vínculo operacional Médico–Sala, com operações administrativas auditadas; verificar com os testes 3.4
- [ ] 3.2 [Xano] Criar a tabela `disponibilidade_medico`, a variável `FUSO_HORARIO` e os endpoints de criar, alterar e remover período (ADMINISTRADOR, auditados) e `GET medicos/me/disponibilidade` (MEDICO, só leitura) (D3); verificar com os testes 3.4
- [ ] 3.3 [Xano] Criar a consulta de Médicos elegíveis considerando usuário/Médico ativo, disponibilidade, plantão e status operacional, sem filtrar pela especialidade de referência; verificar com os testes 3.4
- [ ] 3.4 Escrever `tests/api/test_disponibilidade.py` cobrindo vínculos 1:1, elegibilidade de Médico cuja especialidade de referência difere da fila, período inválido, sobreposição, Médico/usuário inativo, valores-limite 06:59/07:00/18:59/19:00 no fuso oficial, pausa/plantão encerrado, Sala e 403 do Médico ao alterar disponibilidade; verificar que passam
- [ ] 3.5 Exportar o XanoScript das seções 1–3 para `backend/xano/` e verificar que os arquivos estão no repositório

## 4. Reflex — telas administrativas

- [ ] 4.1 [Reflex] Criar o componente `tabela_cadastro` (D8) e a página `/admin/especialidades`; verificar criação, sigla inválida e permissões
- [ ] 4.2 [Reflex] Criar a página `/admin/sintomas` com filtro por grupo, pontuação 1–3 e destinos conforme catálogo; verificar limites e ausência de cores fixas
- [ ] 4.3 [Reflex] Criar páginas administrativas para cadastro vinculado de Médico e Recepção/Triagem, Sala e agenda; verificar vínculos 1:1, CRM/CPF e distinção entre especialidade e Sala
- [ ] 4.4 [Reflex] Criar a página `/admin/disponibilidade` (seletor de data, lista de períodos por médico, criar/editar/remover); verificar manualmente o registro, a sobreposição e a remoção
- [ ] 4.5 [Reflex] Criar a página `/admin/parametros` e o link das novas telas no menu do `/admin`; verificar manualmente a alteração válida e a recusa fora do limite
- [ ] 4.6 [Reflex] Criar a página somente leitura "Minha agenda" em `/medico`; verificar manualmente que o médico vê os próprios períodos e não tem ações de edição
- [ ] 4.7 Adicionar ao README o roteiro de verificação manual da seção 4 e o passo da carga inicial; verificar executando-o

## 5. Integração e documentação

- [ ] 5.1 Verificação ponta a ponta: executar a carga inicial, cadastrar um médico de Cardiologia, registrar a disponibilidade para agora e conferir em `GET especialidades/disponiveis` que Cardiologia aparece e que a auditoria registrou as operações
- [ ] 5.2 Conferir `docs/domain-model.md` (Especialidade, Sintoma, Médico, Disponibilidade, Parâmetros e Histórico) com as tabelas criadas e ajustar o que divergir

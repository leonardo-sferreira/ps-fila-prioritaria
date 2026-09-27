# Tarefas

## 1. Xano — auditoria e parâmetros

- [ ] 1.1 [Xano] Criar a tabela `historico_alteracao` (D1) sem endpoints de escrita e verificar no painel que nenhum endpoint da API faz PATCH/DELETE nela
- [ ] 1.2 [Xano] Criar a função `registrar_alteracao` e verificar, com Run & Debug, que uma transação com erro forçado depois da chamada não deixa registro (D6)
- [ ] 1.3 [Xano] Criar a tabela `parametro`, a função `obter_parametro` e os endpoints `GET parametros` (autenticado) e `PATCH parametros/{chave}` (ADMINISTRADOR, com validação por chave e auditoria) (D5); verificar com os testes 1.4
- [ ] 1.4 Escrever `tests/api/test_parametros.py` e `tests/api/test_auditoria.py` cobrindo valores iniciais, os limites 0/1/20/21 da previsão, a coerência de idades, 401 sem token, 403 para outros perfis, operação recusada sem auditoria e alteração válida com auditoria; verificar que passam

## 2. Xano — especialidades e sintomas

- [ ] 2.1 [Xano] Criar as tabelas `especialidade` e `especialidade_alternativa` e os endpoints de listagem (autenticado; só ativas para quem não é ADMINISTRADOR), criação, edição, ativar/desativar e `PUT especialidades/{id}/alternativas` (ADMINISTRADOR, D2), todos auditados; verificar com os testes 2.4
- [ ] 2.2 [Xano] Criar as tabelas `sintoma` e `sintoma_especialidade` e os endpoints equivalentes, incluindo `PUT sintomas/{id}/especialidades`, com recusa de especialidade inativa; verificar com os testes 2.4
- [ ] 2.3 [Xano] Criar a função `carga_inicial` e o endpoint `POST admin/carga-inicial` (D7); verificar que duas execuções seguidas não duplicam registros
- [ ] 2.4 Escrever `tests/api/test_cadastros.py` cobrindo sigla (2, 3 e 4 letras, com número, minúscula convertida), duplicidades sem diferenciar caixa, alternativas inválidas, prioridade "Verde", especialidade inativa na relação, desativação, auditoria de edição e 403 para os outros perfis; verificar que passam

## 3. Xano — médicos e disponibilidade

- [ ] 3.1 [Xano] Criar as tabelas `medico` e `medico_especialidade` e os endpoints de cadastro, edição e ativar/desativar (ADMINISTRADOR) com as validações da spec; verificar com os testes 3.4
- [ ] 3.2 [Xano] Criar a tabela `disponibilidade_medico`, a variável `FUSO_HORARIO` e os endpoints de criar, alterar e remover período (ADMINISTRADOR, auditados) e `GET medicos/me/disponibilidade` (MEDICO, só leitura) (D3); verificar com os testes 3.4
- [ ] 3.3 [Xano] Criar a função `medicos_disponiveis` e o endpoint `GET especialidades/disponiveis` (D4); verificar com os testes 3.4
- [ ] 3.4 Escrever `tests/api/test_disponibilidade.py` cobrindo usuário sem perfil Médico, médico sem especialidade, usuário já vinculado, período inválido, sobreposição, médico inativo, valores-limite 06:59/07:00/18:59/19:00, usuário desativado durante o período, 403 do Médico ao alterar a própria disponibilidade e auditoria de remoção; verificar que passam
- [ ] 3.5 Exportar o XanoScript das seções 1–3 para `backend/xano/` e verificar que os arquivos estão no repositório

## 4. Reflex — telas administrativas

- [ ] 4.1 [Reflex] Criar o componente `tabela_cadastro` (D8) e a página `/admin/especialidades`, com a edição de alternativas em lista ordenável; verificar manualmente a criação, a sigla inválida e a definição de alternativas
- [ ] 4.2 [Reflex] Criar a página `/admin/sintomas` com filtro por grupo, cor da prioridade padrão e edição das especialidades ordenadas; verificar manualmente a criação, a prioridade e a relação
- [ ] 4.3 [Reflex] Criar a página `/admin/medicos` (seleção de usuário Médico, registro e especialidades); verificar manualmente o cadastro e as mensagens de erro
- [ ] 4.4 [Reflex] Criar a página `/admin/disponibilidade` (seletor de data, lista de períodos por médico, criar/editar/remover); verificar manualmente o registro, a sobreposição e a remoção
- [ ] 4.5 [Reflex] Criar a página `/admin/parametros` e o link das novas telas no menu do `/admin`; verificar manualmente a alteração válida e a recusa fora do limite
- [ ] 4.6 [Reflex] Criar a página somente leitura "Minha agenda" em `/medico`; verificar manualmente que o médico vê os próprios períodos e não tem ações de edição
- [ ] 4.7 Adicionar ao README o roteiro de verificação manual da seção 4 e o passo da carga inicial; verificar executando-o

## 5. Integração e documentação

- [ ] 5.1 Verificação ponta a ponta: executar a carga inicial, cadastrar um médico com duas especialidades, registrar a disponibilidade para agora e conferir em `GET especialidades/disponiveis` que as duas especialidades aparecem e que a auditoria registrou as operações
- [ ] 5.2 Conferir `docs/domain-model.md` (Especialidade, Sintoma, Médico, Disponibilidade, Parâmetros e Histórico) com as tabelas criadas e ajustar o que divergir

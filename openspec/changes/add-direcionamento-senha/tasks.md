# Tarefas

## 1. Xano — direcionamento e senha

- [ ] 1.1 [Xano] Acrescentar à `ficha_atendimento` os campos `especialidade_sugerida_id`, `especialidade_atribuida_id`, `senha`, `senha_numero` e `sem_medico_no_direcionamento`; verificar no painel
- [ ] 1.2 [Xano] Criar a função `direcionar_ficha` (D2) e um endpoint de simulação `POST triagem/simular-direcionamento` (RECEPCAO_TRIAGEM e ADMINISTRADOR); verificar com os testes 1.5
- [ ] 1.3 [Xano] Criar a tabela `contador_senha` e a função `gerar_senha` (D3); verificar com os testes 1.5
- [ ] 1.4 [Xano] Criar `POST fichas/{id}/confirmar-triagem` (D4) e `GET fichas/{id}/comprovante`; verificar com os testes 1.5
- [ ] 1.5 Escrever `tests/api/test_direcionamento.py` e `tests/api/test_senha.py` cobrindo direcionamento pelo conjunto de sintomas, pontuação e casos de conflito de destinos conforme decisão de produto, ficha sem sintomas direcionáveis conforme regra-base, nenhuma fila, confirmação de ficha incompleta, 403 do Médico, formato e numeração da senha, reinício diário em `America/Sao_Paulo`, número 1000, 10 confirmações paralelas sem repetição, comprovante sem nome/CPF, Sala distinta da especialidade, reimpressão sem novo número e comprovante de ficha finalizada; verificar que passam

## 2. Xano — redirecionamento

- [ ] 2.1 [Xano] Acrescentar o gancho de redirecionamento e troca de senha em `PATCH fichas/{id}` e em `ajustar-prioridade` para fichas AGUARDANDO (D5); verificar com os testes 2.4
- [ ] 2.2 [Xano] Criar `redirecionar_especialidade` e chamá-la nos endpoints de disponibilidade e de ativação de médico e usuário (D5); verificar com os testes 2.4
- [ ] 2.3 [Xano] Criar `POST admin/redirecionar` (ADMINISTRADOR); verificar com os testes 2.4
- [ ] 2.4 Escrever `tests/api/test_redirecionamento.py` cobrindo alteração dos sintomas que muda o destino (chegada preservada e auditoria de origem e destino), alteração do escore/classificação sem atribuição de cor direta a sintomas, ausência de destino segundo decisão documentada, ficha CHAMADO não redirecionada e reavaliação sob demanda; verificar que passam e que `pytest tests/api` passa por completo
- [ ] 2.5 Exportar o XanoScript das seções 1 e 2 para `backend/xano/` e verificar que os arquivos estão no repositório

## 3. Reflex — confirmação e comprovante

- [ ] 3.1 [Reflex] Acrescentar à tela de triagem a prévia do destino clínico determinado pelos sintomas e o botão "Confirmar e gerar senha"; não condicionar o destino à disponibilidade ou à especialidade de referência do Médico; verificar os caminhos especificados
- [ ] 3.2 [Reflex] Criar `/recepcao/comprovante/{id}` com o layout de 80 mm e impressão automática (D6), e o botão "Reimprimir" na ficha; verificar manualmente pela visualização de impressão do navegador que não aparecem nome nem CPF
- [ ] 3.3 [Reflex] Mostrar o aviso "Senha alterada: reimprima o comprovante" quando a senha de uma ficha AGUARDANDO mudar; verificar manualmente com um ajuste de prioridade
- [ ] 3.4 [Reflex] Acrescentar "Reavaliar direcionamento" para alterações clínicas/sintomas pertinentes em `/admin/disponibilidade`, sem redirecionar fichas só por mudança na disponibilidade ou especialidade de referência do Médico; verificar manualmente
- [ ] 3.5 Adicionar ao README o roteiro manual da seção 3 e a configuração da impressora térmica; verificar executando-o

## 4. Integração e documentação

- [ ] 4.1 Verificação ponta a ponta: selecionar sintomas do catálogo que direcionem a Cardiologia e confirmar uma ficha, validando especialidade clínica, senha e comprovante; conferir que a disponibilidade/especialidade cadastral de Médicos não altera o destino da ficha
- [ ] 4.2 Conferir `docs/domain-model.md` (Ficha_Atendimento: especialidades, senha e estados EM_TRIAGEM → AGUARDANDO) com a implementação e ajustar o que divergir

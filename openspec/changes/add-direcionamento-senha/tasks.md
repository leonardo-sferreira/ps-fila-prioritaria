# Tarefas

## 1. Xano — direcionamento e senha

- [ ] 1.1 [Xano] Acrescentar à `ficha_atendimento` os campos `especialidade_sugerida_id`, `especialidade_atribuida_id`, `senha`, `senha_numero` e `sem_medico_no_direcionamento`; verificar no painel
- [ ] 1.2 [Xano] Criar a função `direcionar_ficha` (D2) e um endpoint de simulação `POST triagem/simular-direcionamento` (RECEPCAO_TRIAGEM e ADMINISTRADOR); verificar com os testes 1.5
- [ ] 1.3 [Xano] Criar a tabela `contador_senha` e a função `gerar_senha` (D3); verificar com os testes 1.5
- [ ] 1.4 [Xano] Criar `POST fichas/{id}/confirmar-triagem` (D4) e `GET fichas/{id}/comprovante`; verificar com os testes 1.5
- [ ] 1.5 Escrever `tests/api/test_direcionamento.py` e `tests/api/test_senha.py` cobrindo sintoma mais grave, empate pela ordem de registro, ficha só com observação, fallback para a primeira e para a segunda alternativa, alternativa inativa ignorada, nenhuma fila (recusa sem aceite e entrada com aceite), confirmação de ficha incompleta, 403 do Médico, formato V/A/B, numeração compartilhada entre cores e independente por especialidade, reinício diário, número 1000, 10 confirmações paralelas sem repetição, comprovante sem nome/CPF, reimpressão sem novo número e comprovante de ficha finalizada; verificar que passam

## 2. Xano — redirecionamento

- [ ] 2.1 [Xano] Acrescentar o gancho de redirecionamento e troca de senha em `PATCH fichas/{id}` e em `ajustar-prioridade` para fichas AGUARDANDO (D5); verificar com os testes 2.4
- [ ] 2.2 [Xano] Criar `redirecionar_especialidade` e chamá-la nos endpoints de disponibilidade e de ativação de médico e usuário (D5); verificar com os testes 2.4
- [ ] 2.3 [Xano] Criar `POST admin/redirecionar` (ADMINISTRADOR); verificar com os testes 2.4
- [ ] 2.4 Escrever `tests/api/test_redirecionamento.py` cobrindo sintomas que mudam a especialidade (chegada preservada e auditoria de origem e destino), ajuste de prioridade que troca a senha, remoção do último médico (fichas vão para a alternativa na ordem de chegada), ausência de destino (fichas ficam), ficha CHAMADO não redirecionada e reavaliação sob demanda; verificar que passam e que `pytest tests/api` passa por completo
- [ ] 2.5 Exportar o XanoScript das seções 1 e 2 para `backend/xano/` e verificar que os arquivos estão no repositório

## 3. Reflex — confirmação e comprovante

- [ ] 3.1 [Reflex] Acrescentar à tela de triagem a prévia do direcionamento (sugerida e atribuída) e o botão "Confirmar e gerar senha", com o diálogo "Nenhum médico disponível… Deseja colocar na fila de <sugerida> mesmo assim?"; verificar manualmente os dois caminhos
- [ ] 3.2 [Reflex] Criar `/recepcao/comprovante/{id}` com o layout de 80 mm e impressão automática (D6), e o botão "Reimprimir" na ficha; verificar manualmente pela visualização de impressão do navegador que não aparecem nome nem CPF
- [ ] 3.3 [Reflex] Mostrar o aviso "Senha alterada: reimprima o comprovante" quando a senha de uma ficha AGUARDANDO mudar; verificar manualmente com um ajuste de prioridade
- [ ] 3.4 [Reflex] Acrescentar "Reavaliar direcionamento" por especialidade em `/admin/disponibilidade`; verificar manualmente
- [ ] 3.5 Adicionar ao README o roteiro manual da seção 3 e a configuração da impressora térmica; verificar executando-o

## 4. Integração e documentação

- [ ] 4.1 Verificação ponta a ponta: com cardiologista indisponível e Clínica Geral como alternativa, confirmar uma ficha com "Dor no peito" e conferir sugerida CAR, atribuída CLI, senha `V-CLI-NNN` e comprovante impresso; depois registrar disponibilidade para um cardiologista, acionar "Reavaliar direcionamento" em Clínica Geral e conferir que a ficha continua em CLI (só é redirecionada quem perdeu médico)
- [ ] 4.2 Conferir `docs/domain-model.md` (Ficha_Atendimento: especialidades, senha e estados EM_TRIAGEM → AGUARDANDO) com a implementação e ajustar o que divergir

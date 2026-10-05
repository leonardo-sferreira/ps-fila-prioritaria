# Tarefas

## 1. Xano — configuração e função de classificação

- [ ] 1.1 [Xano] Criar a tabela `faixa_sinal_vital` e ampliar a carga inicial com as faixas da spec e os parâmetros `limiar_risco_moderado` (3) e `limiar_risco_alto` (6); verificar que duas execuções da carga não duplicam registros
- [ ] 1.2 [Xano] Criar a função `classificar_ficha` (D2) e o endpoint `POST triagem/simular-classificacao`; verificar com os testes 1.4
- [ ] 1.3 [Xano] Criar `GET/PUT risco/faixas/{parametro}` e o PATCH dos limiares (ADMINISTRADOR, com verificação de cobertura D3 e auditoria); verificar com os testes 1.4
- [ ] 1.4 Escrever `tests/api/test_classificacao.py` cobrindo valores-limite dos sinais vitais e os quatro casos oficiais de glicemia, soma de sintomas e parâmetros, escores 2/3/5/6, sintoma ou parâmetro isolado com 3 pontos, ficha só com observação, destino pediátrico sem alterar classificação, idades 11/12/59/60, faixas sobrepostas, lacuna, limiares incoerentes e 403 para quem não é ADMINISTRADOR; verificar que passam

## 2. Xano — ficha de atendimento

- [ ] 2.1 [Xano] Criar as tabelas `ficha_atendimento` e `ficha_sintoma` (D1) e `POST fichas` (a partir do paciente, com ou sem ticket), com a regra de uma ficha não finalizada por paciente; verificar com os testes 2.4
- [ ] 2.2 [Xano] Criar `PATCH fichas/{id}` (sintomas, observação, sinais vitais, gestante), que reclassifica, reinicia a prioridade atual e audita na mesma transação, e `POST fichas/{id}/concluir-triagem` (D5); verificar com os testes 2.4
- [ ] 2.3 [Xano] Criar `POST fichas/{id}/ajustar-prioridade` e `POST fichas/{id}/cancelar`, com justificativa mínima e restrição de status; `GET fichas/{id}` para RECEPCAO_TRIAGEM e ADMINISTRADOR; verificar com os testes 2.4
- [ ] 2.4 Escrever `tests/api/test_ficha.py` cobrindo a abertura com e sem ticket (horário de chegada), a ficha duplicada, o retorno após desistência (inserindo uma ficha DESISTÊNCIA), sintoma inativo, ficha sem queixa, sinais implausíveis e ausentes, glicemia não medida, auditoria de sintomas, ajuste com e sem justificativa, descarte do ajuste após reclassificação, cancelamento (válido, sem justificativa, ficha CHAMADO), alteração de ficha finalizada e 403 para Médico; verificar que passam
- [ ] 2.5 Exportar o XanoScript das seções 1 e 2 para `backend/xano/` e verificar que os arquivos estão no repositório

## 3. Reflex — triagem e configuração do risco

- [ ] 3.1 [Reflex] Criar o módulo `cores.py` (paleta única de Vermelha/Amarela/Azul e status) e usá-lo nas telas desta change; verificar visualmente que as cores são as mesmas em todos os componentes
- [ ] 3.2 [Reflex] Acrescentar "Abrir ficha" ao cartão do paciente identificado em `/recepcao` e criar `/recepcao/ficha/{id}` (D6) com sintomas, observação, sinais vitais e caixa de classificação; verificar manualmente que a cor muda ao informar SpO2 91 e que a mensagem de erro aparece com SpO2 101
- [ ] 3.3 [Reflex] Criar o modal "Ajustar prioridade" e a ação "Cancelar ficha", com o aviso de descarte do ajuste; verificar manualmente o ajuste, a recusa sem justificativa e o cancelamento
- [ ] 3.4 [Reflex] Criar `/admin/risco`, com as faixas de cada parâmetro e os limiares editáveis; verificar manualmente a alteração válida e a recusa de sobreposição
- [ ] 3.5 Adicionar ao README o roteiro manual da seção 3 e o aviso de "modelagem acadêmica"; verificar executando-o

## 4. Integração e documentação

- [ ] 4.1 Verificação ponta a ponta: do ticket até a ficha concluída de um paciente idoso com "Dor de cabeça" e SpO2 90, conferindo prioridade Vermelha, condição "idoso" e a auditoria das alterações
- [ ] 4.2 Conferir `docs/domain-model.md` (Ficha_Atendimento, Ficha_Sintoma e Faixas de sinais vitais) com as tabelas criadas e ajustar o que divergir

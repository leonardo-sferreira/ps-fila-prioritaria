# Tarefas

## 1. Xano — endpoint do painel

- [ ] 1.1 [Xano] Criar `GET painel` público com a resposta de campos explícitos (D1), usando `prever_fila` e o filtro `especialidades`; verificar com os testes 1.2
- [ ] 1.2 Escrever `tests/api/test_painel.py` cobrindo: acesso sem token; ausência de chaves proibidas (nome, cpf, nascimento, telefone, sintomas, sinais vitais) em toda a resposta, verificada recursivamente; chamada atual e indicação de repetição; 4 últimas chamadas em ordem; previsão com 8 e com 3 elegíveis; Vermelho entrando na primeira posição; desistência removida da previsão; coerência previsão × "Chamar próximo" (CA11); ticket da triagem e rechamada; filtro por especialidade; verificar que passam
- [ ] 1.3 Exportar o XanoScript para `backend/xano/` e verificar que os arquivos estão no repositório

## 2. Reflex — página do painel

- [ ] 2.1 [Reflex] Criar a página `/painel` sem login, com o layout de TV (D4) e o filtro por parâmetro de URL; verificar manualmente em tela cheia com duas especialidades
- [ ] 2.2 [Reflex] Implementar o polling de 3 s, a detecção de nova chamada com destaque e som, e o aviso "Toque para ativar o som" (D2); verificar manualmente com uma chamada e uma repetição feitas em outra aba
- [ ] 2.3 [Reflex] Implementar o estado "reconectando", que mantém a última informação; verificar manualmente parando o acesso à rede por 30 s
- [ ] 2.4 Adicionar ao README como abrir o painel numa TV (URL com filtro, tela cheia, ativação do som) e o roteiro manual da seção 2; verificar executando-o

## 3. Integração

- [ ] 3.1 Verificação ponta a ponta com três janelas (recepção, médico e painel): chamar um ticket na pré-triagem, triar e confirmar um paciente, chamá-lo pelo médico e repetir a chamada, conferindo em cada passo o que o painel mostra e que nenhum dado pessoal aparece

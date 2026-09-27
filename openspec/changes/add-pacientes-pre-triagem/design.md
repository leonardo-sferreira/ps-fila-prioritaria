# Design técnico

## Contexto

Reutiliza `verificar_acesso`, `registrar_alteracao` e a variável `FUSO_HORARIO` das changes anteriores. O totem é externo, então o sistema só precisa de um ponto de entrada que um totem real possa chamar. Nesta fase ele é acionado pelo simulador.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Numeração diária sem buracos nem repetições, mesmo com emissões simultâneas.
- Chamada de ticket atômica entre várias estações de Recepção/Triagem.
- Validação de CPF no backend, sem depender do frontend.

**Fora dos objetivos:**
- Estimativa de tempo de espera na pré-triagem.

## Decisões

### D1. Tabelas
- `ticket_pre_triagem`: `data` (dia no fuso do PS), `numero`, `emitido_em`, `status` (`AGUARDANDO|CHAMADO|ATENDIDO|NAO_COMPARECEU`), `chamado_por` (usuário), `chamado_em`, `paciente_id` (preenchido ao identificar); índice único (`data`, `numero`).
- `paciente`: `cpf` (11 dígitos, sem pontuação, único), `nome`, `data_nascimento`, `telefone`, `ativo`.

### D2. Numeração diária com contador e índice único
A emissão calcula `numero = max(numero do dia) + 1` e insere. Se o índice único (`data`, `numero`) recusar a inserção por causa de uma emissão concorrente, a operação tenta de novo, até 3 vezes.
- **Por quê:** simples no Xano e protegido pelo índice único; o volume de emissões é baixo.
- **Alternativa:** tabela de contador com incremento atômico. Guardada como plano B se os testes de concorrência falharem.

### D3. Chamada atômica por atualização condicional
"Chamar próximo" seleciona o ticket AGUARDANDO mais antigo e o atualiza para CHAMADO com a condição `status = AGUARDANDO`. Se nenhuma linha for afetada (outra estação pegou antes), a operação tenta o próximo ticket. Antes disso, a operação verifica se o usuário já tem um ticket CHAMADO. Esse mesmo padrão será usado em `add-fila-chamada-medico` (RN34).

### D4. Autenticação do totem por chave em header
`POST totem/tickets` exige o header `X-Totem-Chave`, comparado com a variável de ambiente `TOTEM_CHAVE` do Xano. A página `/totem` do Reflex chama o Xano a partir do event handler (que roda no servidor Python), lendo `TOTEM_CHAVE` do ambiente, então a chave nunca vai para o navegador.
- **Alternativa:** um usuário "totem" com login. Descartada porque um token de 12 h num equipamento público é pior do que uma chave de dispositivo que pode ser trocada.

### D5. CPF normalizado e validado no Xano
A função `normalizar_cpf` remove a pontuação, exige 11 dígitos, recusa sequências repetidas e confere os dois dígitos verificadores. Todos os endpoints de paciente a usam. O Reflex aplica máscara apenas por usabilidade.

### D6. Telas
- `/totem`: tela cheia com o botão "Retirar senha" e o número emitido; sem login.
- `/recepcao`: painel "Fila pré-triagem" (lista e botão "Chamar próximo"), cartão do ticket chamado (Rechamar / Não compareceu) e busca por CPF. Quando o CPF é encontrado ou cadastrado, a ação "Paciente identificado" conclui o ticket. A próxima change acrescenta "Abrir ficha" nesse mesmo ponto.
- `/admin/pacientes`: consulta somente leitura por CPF.

## Riscos / Compromissos

- [A chave do totem vaza] → Ela fica só em variáveis de ambiente e pode ser trocada sem mudar código.
- [Várias estações chamando ao mesmo tempo] → Coberto por D3 e por um teste com chamadas paralelas.
- [Rechamar não aparece no painel ainda] → Nesta change, "Rechamar" só atualiza `chamado_em`; o painel vai exibir isso em `add-painel-publico`.

## Plano de migração

Tabelas novas. Rollback: remover as tabelas e endpoints.

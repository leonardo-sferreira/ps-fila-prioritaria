# Delta de especificação

## ADDED Requirements

### Requirement: Troca de senha na reavaliação
Quando a reavaliação de uma ficha `AGUARDANDO` mantém a cor e a especialidade, a senha NÃO DEVE mudar. Quando muda só a cor, a senha DEVE trocar apenas a letra da cor e manter a sigla e o número. Quando muda a especialidade, a ficha DEVE receber o próximo número do dia da nova especialidade, com a cor atual, pela mesma regra de numeração da confirmação; o número anterior NÃO DEVE ser reutilizado. A senha e o número novos DEVEM substituir os anteriores na ficha, e a resposta da operação DEVE informar se a senha mudou, com a senha anterior e a nova. Quando a senha muda, a tela DEVE avisar que o comprovante impresso deixou de valer e oferecer "Reimprimir".

#### Scenario: Cor e especialidade mantidas
- **QUANDO** a observação de uma ficha `AGUARDANDO` `A-CAR-001` é alterada sem mudar cor nem especialidade
- **ENTÃO** a senha continua `A-CAR-001` e a resposta informa que a senha não mudou

#### Scenario: Só a cor muda
- **QUANDO** a ficha `A-CAR-001` passa a Vermelha e continua em Cardiologia
- **ENTÃO** a senha passa a `V-CAR-001`, sem consumir número do contador

#### Scenario: Especialidade muda
- **QUANDO** a ficha `A-CAR-001` passa a Neurologia e a última senha de Neurologia no dia é a 006
- **ENTÃO** a senha passa a `A-NEU-007` e a próxima ficha confirmada em Cardiologia não recebe o número 001

#### Scenario: Aviso de reimpressão
- **QUANDO** a Recepção/Triagem salva uma reavaliação que muda a senha
- **ENTÃO** a tela mostra a senha anterior e a nova, avisa que o comprovante impresso deixou de valer e oferece "Reimprimir" com a senha nova

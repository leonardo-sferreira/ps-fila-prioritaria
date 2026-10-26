# Aviso de privacidade

**Versão:** 1.0, de 26/10/2026.

O Sistema de Fila Prioritária organiza o atendimento de um pronto-socorro: identifica o paciente, registra a triagem, calcula a prioridade e chama o paciente para o atendimento. Este aviso explica quais dados pessoais o sistema guarda, para quê, com quem eles são compartilhados, por quanto tempo ficam guardados e como o titular pode exercer seus direitos, conforme a Lei Geral de Proteção de Dados (LGPD, Lei nº 13.709/2018).

Este é um projeto acadêmico. Use apenas dados de teste, nunca dados reais de pacientes.

## Dados da equipe

Vale para Recepção/Triagem, Médico e Administrador.

- **Quais dados:**
  - nome, e-mail e perfil de acesso;
  - situação da conta (ativa ou inativa);
  - senha, guardada apenas de forma cifrada (hash), nunca em texto;
  - horários de entrada, saída e expiração de cada sessão, e o status de trabalho durante a sessão;
  - códigos de verificação enviados por e-mail, guardados apenas de forma cifrada, com os horários de envio e uso e o número de tentativas;
  - registro de quem fez alterações relevantes no sistema.
- **Para quê:** permitir o acesso de cada pessoa só ao que o seu perfil autoriza, confirmar a identidade no login e na troca de senha, e manter o histórico de quem fez o quê.
- **Base legal:** execução das atividades de trabalho e legítimo interesse na segurança do sistema (LGPD, art. 7º).

## Dados dos pacientes

- **Quais dados:**
  - nome, CPF, data de nascimento e telefone;
  - dados da triagem: sintomas, sinais vitais (pressão, frequência cardíaca, frequência respiratória, temperatura, saturação de oxigênio e glicemia), gestação, observações, classificação de risco e prioridade;
  - horários de chegada e de chamada, senha de atendimento e especialidade de destino.
- **Para quê:** identificar o paciente, classificar o risco e organizar a fila de atendimento por prioridade.
- **Dados sensíveis:** as informações de saúde são dados pessoais sensíveis. Elas são tratadas apenas para a proteção da saúde do paciente, por profissionais de saúde (LGPD, art. 11, II, "f").
- **O que é público:** o painel da sala de espera mostra só a senha de atendimento e a sala, nunca nome ou CPF. O ticket do Totem não tem dados pessoais.

## Com quem compartilhamos

- **Xano:** serviço onde ficam o banco de dados e as regras do sistema. Guarda todos os dados descritos neste aviso.
- **Brevo:** serviço de envio de e-mail. Recebe o nome e o e-mail da pessoa da equipe para enviar os códigos de login e de redefinição de senha.

Nenhum dado é vendido nem usado para propaganda.

## Por quanto tempo guardamos

- **Dados da equipe:** a definir pelo PO. Contas não são excluídas, apenas desativadas, para manter o histórico.
- **Dados dos pacientes:** a definir pelo PO.
- **Códigos de verificação:** valem por 10 minutos e só podem ser usados uma vez. O prazo de guarda do registro está a definir pelo PO.

## Como protegemos

- Senhas e códigos são guardados apenas de forma cifrada.
- As telas internas exigem login, e cada perfil só vê as telas da sua função.
- O login pede um código enviado por e-mail, além da senha.
- A sessão termina após 12 horas, ou após 1 hora sem uso do sistema.
- Nas telas internas, o CPF aparece parcialmente oculto quando não precisa ser lido inteiro.

## Seus direitos

O titular dos dados pode pedir (LGPD, art. 18):

- confirmação de que seus dados são tratados e acesso a eles;
- correção de dados incompletos, inexatos ou desatualizados;
- anonimização, bloqueio ou eliminação de dados desnecessários ou tratados em desacordo com a lei;
- informação sobre com quem os dados são compartilhados;
- revisão de decisões tomadas apenas por tratamento automatizado.

**Como pedir:** o paciente pode pedir à equipe da Recepção/Triagem, que corrige os dados de cadastro no momento do atendimento e encaminha os demais pedidos ao Administrador do sistema. A pessoa da equipe pode pedir diretamente ao Administrador.

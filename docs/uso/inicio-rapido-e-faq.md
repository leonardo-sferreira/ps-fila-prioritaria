# Início rápido e FAQ

## Onde acessar

O sistema é um site; não há aplicativo para baixar. Em desenvolvimento, roda em `http://localhost:3000` (veja o [guia de desenvolvimento](../manutencao/guia-de-desenvolvimento.md)). Em uma instalação de produção, o endereço é o do servidor onde o Reflex foi publicado ([deploy](../sustentacao/deploy-e-ambientes.md)).

| Quem | Endereço | Precisa de login |
|---|---|---|
| Paciente, no totem da entrada | `/totem` | Não |
| TV da sala de espera da triagem | `/painel/triagem` | Não |
| TV da sala de espera dos consultórios | `/painel/medico` | Não |
| Equipe (Recepção/Triagem, Médico, Administrador) | `/login` | Sim |

## Quem cadastra quem

Ninguém se cadastra sozinho. A ordem é:

1. **Primeiro Administrador:** criado uma única vez, direto no Xano, por quem administra o workspace (passo a passo no README, seção "Primeiro administrador").
2. **Administrador → equipe:** em **Usuários**, cria o login de cada pessoa, com nome, e-mail, perfil e senha inicial. Para Médico, informa também CRM, especialidades e sala; para Recepção/Triagem, o CPF.
3. **Administrador → operação:** cadastra especialidades, sintomas, salas e os **plantões** dos médicos. Sem plantão vigente, o médico não consegue ficar disponível.
4. **Recepção/Triagem → pacientes:** o paciente é cadastrado na triagem, pelo CPF, na primeira visita.

## Primeiros passos por perfil

### Administrador

1. Entre em `/login` com o e-mail e a senha recebidos e digite o código de 6 dígitos que chegou por e-mail.
2. Em **Usuários**, crie a equipe do plantão.
3. Em **Plantões**, cadastre a disponibilidade dos médicos do dia (use "Repetir em escala 12x36" para a escala).
4. Confira **Especialidades**, **Sintomas**, **Salas** e **Parâmetros**. Os valores iniciais já vêm carregados.
5. Durante o plantão, acompanhe pelo **Início**, pela **Fila geral** e pela **Auditoria**.

### Recepção/Triagem

1. Entre com e-mail, senha e código. Escolha **Meu status: Disponível**.
2. Abra **Fila de pré-triagem** e use **Chamar próximo**.
3. Com o paciente presente: **Marcar presente** → **Identificar paciente** → pesquise o CPF (cadastre se for a primeira vez) → **Continuar**.
4. Na ficha, marque os sintomas, preencha os sinais vitais e confira a cor. Ajuste, se preciso, com justificativa.
5. **Confirmar e gerar senha** → imprima o comprovante e entregue ao paciente.

### Médico

1. Entre com e-mail, senha e código. Clique em **Ficar disponível** (o login começa indisponível).
2. **Chamar próximo**: o sistema escolhe o paciente e a senha aparece no painel dos consultórios.
3. Paciente chegou → **Compareceu**. Não chegou → depois de 30 s, **Repetir chamada** (até 3 vezes).
4. Para parar de receber pacientes, use **Pausar** ou **Ausente**.

### TV dos painéis

1. Abra `/painel/triagem` ou `/painel/medico` no navegador da TV e coloque em tela cheia (F11).
2. Toque uma vez em **Toque para ativar o som**.
3. Deixe só **uma** aba de cada painel aberta (veja "Reconectando…" abaixo).

## Perguntas frequentes e erros comuns

| Situação | Causa | O que fazer |
|---|---|---|
| O código de login não chegou | Atraso do e-mail ou caixa de spam | Confira o spam. "Reenviar" libera depois de 60 s |
| "Código inválido ou expirado" | Código errado, vencido ou já usado | Peça um novo com "Reenviar" ou volte ao login. Muitas tentativas erradas bloqueiam aquele código |
| "Usuário inativo. Procure o administrador." | O Administrador desativou o login | O Administrador reativa em Usuários |
| Voltei ao login com "Sua sessão foi encerrada por inatividade" | 1 hora sem uso | Entre de novo; o que estava salvo continua lá |
| "Sua sessão expirou. Faça login novamente." | Passaram 12 horas ou o perfil foi alterado | Entre de novo |
| Abri uma tela e voltei para a minha tela inicial | A tela é de outro perfil | Cada perfil só acessa as próprias telas |
| O médico não consegue chamar | Está em Pausa ou Ausente, sem plantão vigente, ou já tem uma ficha chamada | Clique em "Ficar disponível"; peça ao Administrador o plantão; finalize a ficha chamada |
| "Aguarde N segundos para repetir a chamada." | Intervalo mínimo entre chamadas | Espere o tempo indicado |
| A ficha não mostra cor | Falta um sinal vital, o paciente tem menos de 16 anos ou é gestante | Preencha o que falta ou defina a prioridade manualmente, com justificativa |
| "Menor de 16 anos ou idade não informada: defina a prioridade manualmente." | A tabela de sinais vitais vale só para adultos | Use "Ajustar prioridade" com justificativa |
| "Esta ficha já foi chamada ou encerrada e não pode mais ser alterada." | A ficha saiu de "aguardando" | Correções só antes da chamada do médico |
| "Limite de 10 sintomas não listados por ficha." | Limite da ficha | Use sintomas do catálogo ou a observação |
| A senha mudou depois de corrigir a ficha | A especialidade mudou | Reimprima o comprovante e entregue o novo ao paciente |
| O painel mostra "Reconectando…" | Falha de rede ou limite de requisições do Xano (plano gratuito: 10 a cada 20 s para o sistema todo) | O painel continua com a última informação e volta sozinho. Feche abas extras do painel |
| Telas da equipe com erro de conexão durante o plantão | Limite de requisições do Xano atingido | Feche abas de painel abertas à toa; espere alguns segundos e tente de novo |
| Paciente diz que já tem ficha | Existe ficha aberta para o CPF | Use "Abrir ficha atual" na identificação ou "Fichas do dia" |
| Ficha ou ticket esquecido aberto desde ontem | Registro parado | O Administrador usa "Dispensar todos" no Início (mais de 24 h parado) |
| Esqueci a senha | — | "Esqueci minha senha" no login: código por e-mail e nova senha |

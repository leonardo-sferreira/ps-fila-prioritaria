# Guia por perfil

O que cada tipo de usuário vê e consegue fazer em cada tela, os dados que insere e o tipo de cada campo. Os endereços são relativos ao site (em desenvolvimento, `http://localhost:3000`). As regras citadas estão explicadas no [glossário](glossario-e-regras.md).

O sistema tem quatro perfis. Três são da equipe, com login por e-mail, senha e código; o quarto é o público, sem login.

| Perfil | Tela inicial depois do login | Pode | Não pode |
|---|---|---|---|
| **Recepção/Triagem** | `/recepcao` | Chamar tickets da pré-triagem, identificar e cadastrar pacientes, preencher a ficha, classificar e gerar a senha | Chamar pacientes para o médico; acessar cadastros e auditoria |
| **Médico** | `/medico` | Informar o próprio status, chamar o próximo paciente, confirmar comparecimento ou registrar desistência, imprimir a ficha | Escolher qual paciente chamar; alterar a ficha; acessar cadastros |
| **Administrador** | `/admin` | Cadastrar usuários, médicos, especialidades, sintomas, salas, plantões e parâmetros; acompanhar a fila, a equipe e a auditoria; dispensar registros parados | Triar pacientes ou chamar fichas (acompanha só para leitura) |
| **Público (paciente)** | — | Retirar ticket no Totem e acompanhar os painéis | Acessar qualquer tela da equipe |

Abrir pela URL uma tela de outro perfil leva de volta à tela inicial do próprio perfil. A permissão também é conferida pelo backend em cada operação, então esconder um botão não é a única proteção.

---

## Público (sem login)

### Totem — `/totem`

O paciente toca em um dos três tipos e recebe um ticket na tela (não é impresso). Não digita nada e nenhum dado pessoal é pedido.

| Botão | Ticket | Para quem |
|---|---|---|
| Pediátrico | `C-001`, `C-002`… | Crianças até 11 anos |
| Preferencial | `P-001`… | 60 anos ou mais, gestantes e demais preferenciais |
| Normal | `N-001`… | Demais pacientes |

A numeração recomeça a cada dia e é independente por tipo. Depois de ver o ticket, o paciente toca em **Concluir** e aguarda o painel da triagem.

### Painéis de chamada — `/painel/triagem` e `/painel/medico`

Cada TV abre um dos dois; `/painel` mostra os dois endereços. Os painéis atualizam sozinhos a cada 5 segundos, destacam e tocam um aviso a cada chamada (o navegador exige um toque em "Toque para ativar o som" na primeira vez) e nunca mostram nome, CPF ou dado clínico.

| Painel | "Chamando agora" | Tabela abaixo |
|---|---|---|
| Triagem | Ticket chamado pela Recepção (ex.: `C-004`), "Dirija-se à Recepção/Triagem" e a tentativa (1ª, 2ª ou 3ª chamada) | Últimos 4 tickets chamados, com horário |
| Consultórios | Senha chamada pelo médico (ex.: `V-CAR-003`), "Dirija-se à {especialidade} · {Sala}" e a tentativa | Últimas 4 chamadas: senha, especialidade, Sala e horário |

No painel dos consultórios, `?especialidades=CLI,ORT` no endereço mostra só essas especialidades. Chamadas com mais de 2 horas saem da tela (parâmetro "Tempo que uma chamada fica no painel").

### Aviso de privacidade — `/privacidade`

Texto sobre os dados tratados, aberto pelo rodapé da tela de login.

---

## Acesso da equipe

| Tela | Campos | Tipo e regra |
|---|---|---|
| Login — `/login` | E-mail; Senha | E-mail (espaços e maiúsculas são ignorados); senha de 8 ou mais caracteres |
| Código — `/login/codigo` | Código | 6 dígitos, enviado por e-mail, válido por tempo limitado. "Reenviar" libera depois de 60 s. Errar o código várias vezes bloqueia esse código |
| Esqueci minha senha — `/senha`, `/senha/codigo`, `/senha/nova` | E-mail; código de 6 dígitos; nova senha e confirmação | A resposta é sempre a mesma, exista ou não o e-mail (não revela quem é cadastrado) |

A sessão vale 12 horas e termina depois de 1 hora sem uso, voltando ao login com "Sua sessão foi encerrada por inatividade". Usuário desativado pelo Administrador perde o acesso na hora.

---

## Recepção/Triagem

### Início — `/recepcao`

- **Meu status:** Disponível, Pausa ou Ausente (escolha manual; mostrado ao Administrador).
- Resumo do plantão do dia: senhas aguardando médico, por cor e especialidade.
- Menu: Início, Fila de pré-triagem, Identificar paciente e Fichas do dia.

### Fila de pré-triagem — `/recepcao/fila`

Lista dos tickets do Totem aguardando, com tipo, horário e contagem por tipo. A ordem é decidida pelo sistema (pediátrico antes de preferencial; ciclo de 2 prioritários para 1 normal).

| Ação | Quando aparece | Efeito |
|---|---|---|
| Chamar próximo | Nenhum ticket em chamada | Chama o próximo ticket da ordem; aparece no painel da triagem |
| Chamar novamente | 30 s depois da 1ª chamada, 10 s depois das seguintes, até a 3ª | Repete a chamada no painel |
| Não compareceu | Depois do mesmo intervalo | 1ª vez: o ticket volta ao fim da fila; 2ª vez: sai da fila |
| Marcar presente | Ticket chamado | Libera "Identificar paciente" para esse ticket |
| Desistência | Ticket chamado | Tira o ticket da fila |

Nada é automático: sem clique, o ticket fica parado.

### Identificar paciente — `/recepcao/pacientes`

| Campo | Tipo | Regra |
|---|---|---|
| CPF | Texto `000.000.000-00` | Obrigatório e válido (dígitos verificadores); é o identificador único |
| Nome completo | Texto | Obrigatório no cadastro |
| Data de nascimento | Data | Obrigatória; não pode ser futura |
| Telefone | Texto `(00) 00000-0000` | Opcional |

Fluxo: pesquisar o CPF → se não existir, cadastrar → **Continuar** abre a ficha. Se o paciente já tiver ficha aberta, a tela oferece "Abrir ficha atual" em vez de criar outra. Fora da busca, o CPF aparece mascarado (`***.456.789-**`).

### Ficha de atendimento — `/recepcao/ficha/{id}`

| Bloco | Campo | Tipo | Regra |
|---|---|---|---|
| Sintomas | Sintomas do catálogo | Seleção múltipla com busca | Cada sintoma vale 1 a 3 pontos |
| | Sintoma não listado | Texto + gravidade (1, 2 ou 3) | Até 10; não pode repetir um sintoma do catálogo |
| | Observação / queixa geral | Texto livre | Opcional se houver sintoma |
| Sinais vitais | PA sistólica | Inteiro, mmHg | 40 a 300 |
| | FC | Inteiro, bpm | 20 a 250 |
| | FR | Inteiro, irpm | 4 a 80 |
| | Temperatura | Decimal com 1 casa, °C | 25,0 a 45,0 |
| | SpO₂ | Inteiro, % | 50 a 100 |
| | Glicemia capilar | Inteiro, mg/dL, opcional | 10 a 1500; marcar "sinais de gravidade" quando houver |
| | Gestante | Sim/não | Gestante tem classificação manual |
| Classificação | Ajustar prioridade | Vermelha, Amarela ou Azul + justificativa | Justificativa obrigatória; o ajuste some se sintomas ou sinais mudarem |

A cor aparece calculada à medida que os dados são preenchidos (veja o [cálculo](glossario-e-regras.md#classificação-de-risco)). Faltando um sinal vital, a tela mostra a pendência. Menores de 16 anos e gestantes exigem classificação manual justificada.

**Confirmar e gerar senha** (exige cor definida): define a especialidade de destino, gera a senha `COR-ESP-NNN`, coloca a ficha na fila do médico e abre o comprovante.

### Comprovante — `/recepcao/comprovante/{id}`

Comprovante de 80 mm para imprimir: senha, prioridade, especialidade e horário de entrada. Sem nome, CPF, sintomas nem sinais vitais. "Reimprimir" mostra sempre a mesma senha.

### Fichas do dia — `/recepcao/fichas`

Fichas abertas e as finalizadas de hoje, com busca por nome ou senha. Uma ficha **aguardando** pode ser reaberta e corrigida: se a cor mudar, a letra da senha muda e o número é mantido; se a especialidade mudar, sai uma senha nova e a tela pede a reimpressão.

---

## Médico

### Fila de atendimento — `/medico`

| Área | O que mostra ou faz |
|---|---|
| Status | **Ficar disponível**, **Pausar** e **Ausente**. "Em atendimento" é automático, ao confirmar o comparecimento. O login começa indisponível: é preciso escolher "Disponível" para chamar |
| Filas de especialidade | Quantas fichas aguardam em cada fila, por cor |
| Chamar próximo | O sistema escolhe a ficha (o médico não escolhe). Fila vazia mostra aviso. Pausa ou Ausente impedem a chamada |
| Ficha sob sua responsabilidade | Senha, paciente, idade, prioridade, condição prioritária, escore, sinais vitais, sintomas, observação e histórico |
| Repetir chamada | Depois de 30 s; até 3 chamadas por oportunidade. Sem comparecimento, a ficha volta uma vez ao fim da fila; na segunda vez, vira desistência |
| Compareceu | Ficha atendida; libera a impressão |
| Registrar desistência | Pede confirmação e tira a ficha da fila |
| Imprimir ficha — `/medico/ficha/{id}/imprimir` | Só para o médico que chamou |
| Meus plantões | Plantões cadastrados pelo Administrador |

---

## Administrador

O menu do Administrador tem as abas abaixo. Nada com histórico é excluído: é **desativado**, e toda alteração vai para a auditoria.

| Tela | O que faz | Campos e tipos |
|---|---|---|
| **Início** — `/admin` | Plantão do dia, equipe com sessão ativa e o status de cada um, fichas e tickets parados há mais de 24 h com "Dispensar todos" | — |
| **Fila geral** — `/admin/fila-geral` | Fichas em triagem, aguardando (na ordem prevista) e chamadas, de todas as especialidades; atualiza a cada 10 s; só leitura | Filtros: especialidade, cor, status |
| **Detalhe da ficha** — `/admin/fichas/{id}` | Triagem, sintomas, senhas que a ficha teve, ajuste de cor com justificativa, chamadas e histórico; só leitura | — |
| **Auditoria** — `/admin/auditoria` | Alterações, chamadas e acessos (login/logout), do mais recente para o mais antigo, 50 por página; "Exportar CSV" | Filtros: período (até 31 dias), tipo, usuário |
| **Usuários** — `/admin/usuarios` | Criar, editar, trocar perfil, ativar e desativar. A senha não é redefinida pelo Administrador: cada pessoa usa "Esqueci minha senha" | Nome; e-mail de login; perfil; senha inicial (8+); CPF; para Médico: CRM (`12345-SP`), especialidades próprias e sala (opcional); para Recepção: especialidade de referência (opcional) |
| **Médicos** — `/admin/medicos` | Cadastro profissional do médico | Nome, CRM, especialidades próprias (uma ou mais), sala atual |
| **Recepção/Triagem** — `/admin/recepcao` | Cadastro da equipe de triagem | Nome, CPF, especialidade de referência |
| **Especialidades** — `/admin/especialidades` | Especialidades atendidas | Nome; sigla (3 letras, fixa depois de criada, usada na senha); descrição |
| **Sintomas** — `/admin/sintomas` | Catálogo de sintomas | Nome; grupo; pontuação (1, 2 ou 3); destinos (especialidades, em ordem de preferência) |
| **Salas** — `/admin/salas` | Salas de atendimento | Nome; descrição |
| **Plantões** — `/admin/disponibilidade` | Disponibilidade dos médicos por período | Médico; data; início e fim (hora); "Repetir em escala 12x36" até uma data |
| **Parâmetros** — `/admin/parametros` | Valores das regras (limiares, idades, intervalos, ciclos, prazos) e faixas de sinais vitais | Valor inteiro dentro do limite mostrado; faixas: mínimo, máximo e pontos (0 a 3) |

Não é possível desativar a si mesmo nem o último Administrador ativo.

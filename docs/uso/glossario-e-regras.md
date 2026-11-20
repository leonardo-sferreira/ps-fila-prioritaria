# Glossário e regras de negócio

Termos usados nas telas e as regras e cálculos que o sistema aplica. Os valores marcados com **(parâmetro)** podem ser mudados pelo Administrador em Parâmetros; os demais são fixos no código. Onde cada regra está implementada: [configuração e regras no código](../manutencao/configuracao-e-regras.md).

> Projeto acadêmico: as regras clínicas são uma modelagem de estudo e não substituem protocolos reais de triagem.

## Glossário

| Termo | Significado |
|---|---|
| **Ticket** | Código retirado no Totem antes da triagem: `C-NNN` (pediátrico), `P-NNN` (preferencial) ou `N-NNN` (normal). Não tem dado pessoal e recomeça a cada dia |
| **Fila de pré-triagem** | Fila dos tickets aguardando a Recepção/Triagem |
| **Ficha de atendimento** | Registro de uma visita do paciente: sintomas, sinais vitais, cor, especialidade e senha. Um paciente tem no máximo uma ficha aberta por vez |
| **Sintoma do catálogo** | Sintoma cadastrado pelo Administrador, com pontuação de 1 a 3 e especialidades de destino |
| **Sintoma não listado** | Sintoma digitado na triagem, com gravidade de 1 a 3 escolhida pela Recepção; entra no escore, mas não define especialidade |
| **Sinais vitais** | PA sistólica, FC, FR, temperatura e SpO₂ (obrigatórios para o cálculo automático) e glicemia capilar (opcional) |
| **Escore** | Soma dos pontos dos sintomas e dos sinais vitais |
| **Cor / prioridade** | Classificação de risco: **Vermelha** (alto), **Amarela** (moderado) e **Azul** (baixo) |
| **Condição prioritária** | Idoso, criança ou gestante: passa à frente **dentro da mesma cor**, sem mudar a cor |
| **Ajuste manual** | Troca da cor pela Recepção, com justificativa obrigatória e registro na auditoria |
| **Especialidade sugerida / atribuída** | A sugerida sai dos sintomas; a atribuída é a fila em que a ficha entra |
| **Senha** | Código da ficha na fila do médico: `COR-ESP-NNN`, por exemplo `V-CAR-003` (V = Vermelha, A = Amarela, B = Azul; sigla da especialidade; número do dia) |
| **Comprovante** | Papel de 80 mm com a senha, entregue ao paciente |
| **Oportunidade / tentativa** | Cada vez que a ficha (ou o ticket) está na vez é uma oportunidade; cada chamada dentro dela é uma tentativa (até 3) |
| **Reentrada** | Volta da ficha ou do ticket ao fim da fila depois de uma oportunidade sem comparecimento (só uma vez) |
| **Desistência** | Saída da fila: registrada pela equipe ou automática depois da segunda oportunidade sem comparecimento |
| **Especialidade própria** | Especialidade em que o médico está cadastrado; define a preferência dele, não uma restrição |
| **Fila coberta / descoberta** | Coberta: tem médico próprio de plantão e disponível. Descoberta: não tem |
| **Plantão** | Período de disponibilidade do médico cadastrado pelo Administrador (pode repetir em escala 12x36) |
| **Status operacional** | Disponível, Pausa, Ausente ou Em atendimento (este último automático, só para o médico) |
| **Sessão** | Período logado: dura até 12 h e termina com 1 h sem uso ou no logout |
| **Auditoria** | Registro imutável de alterações, chamadas e acessos, com usuário, data, valor anterior e novo. Cargas automáticas aparecem como "Sistema" |
| **Registro parado** | Ficha ou ticket sem andamento há mais de 24 h **(parâmetro)**, que o Administrador pode dispensar |

## Regras do dia a dia

### Fila de pré-triagem

1. Pediátrico vem antes de preferencial.
2. Prioritários (pediátrico e preferencial) e normais alternam em ciclo: **2 prioritários para 1 normal** **(parâmetro)**, para ninguém esperar indefinidamente.
3. Toda chamada é feita por uma pessoa. Depois da 1ª chamada, espera **30 s** **(parâmetro)**; depois da 2ª e da 3ª, **10 s** **(parâmetro)**. Só então "Chamar novamente" e "Não compareceu" ficam disponíveis.
4. Até **3 chamadas** por oportunidade **(parâmetro)**. O 1º "Não compareceu" devolve o ticket ao fim da fila; o 2º encerra.
5. O tipo do ticket não interfere na cor definida na triagem.

### Classificação de risco

O escore soma:

- os pontos de **todos** os sintomas selecionados (1 a 3 cada, do catálogo ou não listados);
- os pontos de cada sinal vital (0 a 3), pelas faixas abaixo **(parâmetro, editáveis em Parâmetros)**.

| Sinal vital | 3 pontos | 2 pontos | 1 ponto | 0 ponto | 1 ponto | 2 pontos | 3 pontos |
|---|---|---|---|---|---|---|---|
| PA sistólica (mmHg) | ≤ 90 | 91–100 | 101–110 | 111–219 | | | ≥ 220 |
| FC (bpm) | ≤ 40 | | 41–50 | 51–90 | 91–110 | 111–130 | ≥ 131 |
| FR (irpm) | ≤ 8 | | 9–11 | 12–20 | | 21–24 | ≥ 25 |

As faixas completas, incluindo temperatura, SpO₂ e glicemia, estão em [domain-model.md](../domain-model.md#faixas-de-sinais-vitais) e na tela Parâmetros.

| Resultado | Cor |
|---|---|
| Escore de 0 a 4 | **Azul** |
| Escore de 5 a 9 (limiar Amarela = 5 **(parâmetro)**) | **Amarela** |
| Escore 10 ou mais (limiar Vermelha = 10 **(parâmetro)**) | **Vermelha** |
| Qualquer item isolado com 3 pontos (sintoma ou sinal vital) | **Vermelha**, mesmo com escore baixo |

- O cálculo automático vale para pacientes com **16 anos ou mais** **(parâmetro)**, não gestantes e com os cinco sinais vitais informados. Nos outros casos, a Recepção classifica manualmente, com justificativa.
- **Condição prioritária:** idoso a partir de **60 anos** **(parâmetro)**, criança até **11 anos** **(parâmetro)** e gestante. Reordena dentro da cor; não soma pontos.
- **Exemplo:** dor no peito (2) + falta de ar (2) + FC 115 (2) = escore 6 → Amarela. Com SpO₂ 91 (3 pontos), vira Vermelha pela regra do item isolado.
- Se sintomas ou sinais vitais mudarem, a cor é recalculada e o ajuste manual anterior é descartado.

### Direcionamento e senha

1. Paciente com até 11 anos vai para **Pediatria**.
2. Nos demais, vence a especialidade do **sintoma de maior pontuação**; empate → maior soma de pontos por especialidade → menor fila → menor ID.
3. Sem sintoma do catálogo, vai para a especialidade padrão, **Clínica Geral** **(parâmetro)**.
4. A senha é `COR-ESP-NNN`, com número sequencial por especialidade e por dia, independente da cor.
5. Ficha aguardando corrigida: só a cor mudou → troca a letra e mantém o número; a especialidade mudou → senha nova e reimpressão.

### Fila do médico

1. Só fichas **aguardando** participam.
2. **Vermelhas** primeiro. Sem Vermelha, cada especialidade alterna **2 Amarelas para 1 Azul** **(parâmetro)**.
3. Dentro da cor, condição prioritária vem antes; depois, ordem de chegada na fila e menor ID.
4. Ao "Chamar próximo", o sistema escolhe primeiro entre as especialidades próprias do médico (Vermelha própria antes de tudo; rodízio entre as próprias). Uma fila **descoberta** passa à frente só com cor mais grave; sem ficha própria, o médico apoia primeiro uma fila descoberta e depois outra coberta.
5. Dois médicos nunca recebem a mesma ficha: a reserva é atômica. Cada médico tem no máximo uma ficha chamada por vez.
6. **30 s** entre chamadas da mesma senha **(parâmetro)**, até **3 tentativas** por oportunidade e uma reentrada ao fim da fila. Sem comparecimento na segunda oportunidade, vira desistência.
7. Médico em **Pausa** ou **Ausente** não recebe fichas novas. Ao confirmar o comparecimento, fica **Em atendimento** automaticamente.

### Painéis públicos

- Mostram só senha, ticket, cor, especialidade, Sala e horário.
- Chamadas ficam na tela por **2 horas** desde a chamada **(parâmetro)**, o que funciona com o PS aberto 24 horas.
- A Sala é a vinculada ao médico no cadastro.

### Segurança e privacidade

- A permissão de cada perfil é conferida no backend em toda operação.
- CPF mascarado (`***.456.789-**`) fora dos campos de digitação.
- Código de 6 dígitos por e-mail no login e na redefinição de senha; tentativas limitadas.
- Sessão de 12 h; saída por inatividade em 1 h.
- Nada com histórico é apagado: é desativado. Toda alteração relevante vai para a auditoria.
- Fichas e tickets parados há mais de **24 h** **(parâmetro)** podem ser dispensados pelo Administrador como desistência, com registro em nome dele.

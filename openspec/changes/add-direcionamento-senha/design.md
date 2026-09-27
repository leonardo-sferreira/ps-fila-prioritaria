# Design técnico

## Contexto

Já existem: `medicos_disponiveis` (change 2), `especialidade_alternativa`, `sintoma_especialidade`, parâmetro `especialidade_padrao`, `ficha_atendimento` com classificação e `registrar_alteracao`. Esta change liga a ficha a uma fila e a uma senha. Também precisa acrescentar pontos de chamada em endpoints das changes 2 e 4 (disponibilidade e alteração de ficha).

## Objetivos / Fora dos objetivos

**Objetivos:**
- Uma única função `direcionar_ficha`, usada na confirmação, no redirecionamento automático e no redirecionamento sob demanda.
- Numeração de senha sem repetição com confirmações simultâneas.

**Fora dos objetivos:**
- Balancear a carga entre médicos da mesma especialidade (o médico que chama é decidido em `add-fila-chamada-medico`).

## Decisões

### D1. Fila por especialidade
A unidade de fila é a especialidade atribuída. Qualquer médico disponível dessa especialidade pode chamar a ficha.
- **Por quê:** a senha já identifica a especialidade (formato do documento formal), a previsão do painel por fila fica bem definida e um médico que sai não "prende" pacientes.
- **Alternativa:** fila por médico (leitura literal de RF18). Descartada porque obrigaria a escolher o médico na triagem e a redistribuir a cada troca de plantão. A divergência está registrada na proposta.

### D2. `direcionar_ficha(ficha, instante)`
1. Sugerida: entre os `ficha_sintoma` cujo sintoma tem a prioridade padrão mais grave, junta os `sintoma_especialidade` com especialidade ativa, ordena por (`ordem`, id do `ficha_sintoma`) e pega o primeiro; sem resultado, usa `obter_parametro('especialidade_padrao')`.
2. Candidatas = [sugerida] + alternativas ativas por `ordem`.
3. Atribuída = primeira candidata em que `medicos_disponiveis(instante, candidata)` não é vazio; se nenhuma tiver médico, devolve `sem_destino`.
Não grava nada; quem chama decide.

### D3. Contador de senha com linha por (data, especialidade)
Tabela `contador_senha` (`data`, `especialidade_id`, `ultimo_numero`) com índice único. `gerar_senha` faz upsert da linha e incremento condicional (`UPDATE ... SET ultimo_numero = ultimo_numero + 1 WHERE ultimo_numero = lido`), repetindo em caso de conflito, dentro da transação da confirmação.
- **Alternativa:** `max()+1` sobre as fichas, como no ticket. Descartada porque a senha muda quando a ficha é redirecionada, o que torna o `max` sobre fichas pouco confiável.

### D4. Confirmação em uma transação
`POST fichas/{id}/confirmar-triagem` com `{aceitar_sem_medico: bool}`: valida completude (reusa a validação da change 4), chama `direcionar_ficha`, decide (atribuída, recusa com aviso, ou sugerida marcada `sem_medico_no_direcionamento`), gera a senha, muda o status para AGUARDANDO e audita.

### D5. Ganchos de redirecionamento
- Em `PATCH fichas/{id}` e `ajustar-prioridade` (change 4): para ficha AGUARDANDO, depois de reclassificar, chama `direcionar_ficha`; se a atribuída ou a cor mudarem, gera nova senha e audita (tipo `REDIRECIONAMENTO` ou `SENHA_ALTERADA`).
- Nos endpoints de disponibilidade e de ativação de médico ou usuário (changes 1 e 2): depois da alteração, para cada especialidade do médico afetado que ficar sem médico disponível, chama `redirecionar_especialidade(esp)`, que percorre as fichas AGUARDANDO em ordem de `chegada_em` e aplica D2.
- `POST admin/redirecionar` (ADMINISTRADOR) chama `redirecionar_especialidade` sob demanda.

### D6. Comprovante como página imprimível
`GET fichas/{id}/comprovante` devolve só os campos permitidos (senha, cor, especialidade, chegada). O Reflex renderiza `/recepcao/comprovante/{id}` com CSS `@page { size: 80mm auto }` e chama `window.print()` ao abrir. A reimpressão reabre a mesma página.
- **Alternativa:** gerar PDF no backend. Descartada porque o Xano não é bom nisso e a impressão pelo navegador atende uma impressora térmica configurada no sistema operacional.

## Riscos / Compromissos

- [Mudança de senha confunde o paciente com um comprovante antigo] → A tela de triagem mostra "Senha alterada: reimprima o comprovante" sempre que a senha muda.
- [Redirecionar em massa causa muitas escritas] → Só roda para especialidades que perderam o último médico; o volume acadêmico é baixo.
- [Disponibilidade que termina pelo horário não dispara redirecionamento] → Existe o redirecionamento sob demanda; ver Questões em aberto.

## Plano de migração

Campos novos em `ficha_atendimento` (nulos em fichas EM_TRIAGEM) e uma tabela nova. Rollback: remover campos, tabela e endpoints, e voltar os endpoints das changes 2 e 4 à versão anterior.

## Questões em aberto

- Redirecionar automaticamente quando um período de disponibilidade termina (agendamento no Xano) pode ser acrescentado depois sem mudar a spec atual; por enquanto é sob demanda.

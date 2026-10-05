# Design técnico

## Contexto

Reutiliza `verificar_acesso`, `registrar_alteracao` e `FUSO_HORARIO` das changes anteriores. Tickets são emitidos pela change `add-totem`; esta change implementa a fila da Recepção/Triagem e o cadastro de pacientes.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Numeração diária sem buracos nem repetições, mesmo com emissões simultâneas.
- Chamada de ticket atômica entre várias estações de Recepção/Triagem.
- Validação de CPF no backend, sem depender do frontend.

**Fora dos objetivos:**
- Estimativa de tempo de espera na pré-triagem.

## Decisões

### D1. Tabelas
- `ticket_pre_triagem` emitido por `add-totem`: `data`, `numero`, `emitido_em`, `status` (`AGUARDANDO|CHAMADO|ATENDIDO|NAO_COMPARECEU|DESISTENCIA`), usuário/chamada, número da oportunidade, tentativas na oportunidade e `paciente_id` preenchido ao identificar; índice único (`data`, `numero`).
- `paciente`: `cpf` (11 dígitos, sem pontuação, único), `nome`, `data_nascimento`, `telefone`, `ativo`.

### D2. Emissão é responsabilidade da change `add-totem`
Esta change não expõe endpoint de criação de ticket nem implementa a tela pública do Totem. Consome registros já emitidos, preservando data, número e identidade.

### D3. Chamada atômica por atualização condicional
"Chamar próximo" seleciona o ticket AGUARDANDO mais antigo e o atualiza para CHAMADO com condição `status = AGUARDANDO`. Cada oportunidade admite até 3 chamadas com intervalo mínimo de 30 segundos entre chamadas da mesma senha. Esgotada a primeira oportunidade sem comparecimento, o mesmo ticket volta ao fim da fila uma vez; após a segunda oportunidade sem atendimento, recebe estado final `NAO_COMPARECEU`. Desistência explícita recebe estado final `DESISTENCIA`. Rechamar registra outra chamada no mesmo ticket e nunca emite um novo.

### D4. Autorização da Recepção/Triagem
Somente o perfil unificado RECEPCAO_TRIAGEM pode consultar e operar a fila. A autorização é verificada no backend; a interface Reflex não é controle de acesso. Emissão pública e segredo do Totem pertencem a `add-totem`.

### D5. CPF normalizado e validado no Xano
A função `normalizar_cpf` remove a pontuação, exige 11 dígitos, recusa sequências repetidas e confere os dois dígitos verificadores. Todos os endpoints de paciente a usam. O Reflex aplica máscara apenas por usabilidade.

### D6. Telas
- `/recepcao`: painel "Fila de Recepção/Triagem" (lista e botão "Chamar próximo"), cartão do ticket chamado com tentativas/oportunidade, Rechamar, Registrar desistência e busca por CPF. A ação "Paciente identificado" conclui o ticket; `add-triagem-classificacao` acrescenta "Abrir ficha" nesse mesmo ponto.
- `/admin/pacientes`: consulta somente leitura por CPF.

## Riscos / Compromissos

- [Várias estações chamando ao mesmo tempo] → Coberto por D3 e por um teste com chamadas paralelas.
- [Rechamar não aparece no painel ainda] → Nesta change, "Rechamar" só atualiza `chamado_em`; o painel vai exibir isso em `add-painel-publico`.

## Plano de migração

Cadastro de pacientes e operações de fila; emissão e registro base de tickets pertencem a `add-totem`. Compatibilidade entre as duas changes deve ser verificada antes da implementação.

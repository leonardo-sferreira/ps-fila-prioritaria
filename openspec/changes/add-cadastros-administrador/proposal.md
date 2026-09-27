# Proposta

## Por quê

A classificação, o direcionamento e a chamada de pacientes dependem de dados que só o Administrador mantém: especialidades e suas alternativas, sintomas com prioridade padrão, relação sintoma → especialidade, médicos com suas especialidades, disponibilidade diária e parâmetros das regras. Sem esses cadastros, nenhuma das próximas fatias (triagem, direcionamento, fila) pode ser testada. Esta change também cria a trilha de auditoria, que todas as próximas changes vão usar.

## O que muda

- **Especialidades:** cadastro (nome, descrição, sigla de 3 letras usada na senha, situação) e lista ordenada de especialidades alternativas (RF13, RN17).
- **Sintomas:** cadastro (nome, descrição, grupo, prioridade padrão Vermelha/Amarela/Azul, situação) e relação ordenada sintoma → especialidades (RF16, RN06, RN14).
- **Médicos:** cadastro vinculado a um usuário com perfil Médico, com registro profissional e uma ou mais especialidades (RF14).
- **Disponibilidade:** o Administrador registra, altera e remove períodos (data, hora inicial, hora final) de cada médico; o médico não altera a própria disponibilidade (RF15, RN15, RN16, UC06).
- **Parâmetros de regra:** tela para consultar e alterar os parâmetros operacionais (limites de idade, ciclo de chamada, tentativas, tamanho da previsão, especialidade padrão), com valores iniciais (RNF09, seção 22.1 do documento formal).
- **Auditoria:** registro imutável de alterações relevantes (tipo, registro afetado, valor anterior, valor novo, usuário, data/hora, justificativa). Nesta change ele passa a registrar alterações de disponibilidade, sintomas, especialidades e parâmetros (RF37, RNF07).
- Carga inicial de dados de exemplo (especialidades e sintomas da seção 6 do documento formal) para permitir testes.

### Fora do escopo

- Faixas de pontuação dos sinais vitais e limiares de risco: ficam em `add-triagem-classificacao`, junto com o cálculo que os usa.
- Redistribuição de pacientes quando um médico fica indisponível: fica em `add-direcionamento-senha`.
- Tela de consulta da auditoria pelo Administrador: fica em `add-acompanhamento-administrador`. Nesta change a auditoria só é gravada e verificada por testes.
- Exclusão física de registros: cadastros são desativados, nunca excluídos.
- Qualquer funcionalidade de paciente, ficha ou fila.

## Capacidades

### Novas capacidades
- `especialidades`: cadastro de especialidades, siglas e alternativas ordenadas.
- `sintomas`: cadastro de sintomas, prioridade padrão e relação ordenada com especialidades.
- `medicos-disponibilidade`: cadastro de médicos, vínculo com especialidades e disponibilidade por período.
- `parametros-regras`: parâmetros operacionais configuráveis pelo Administrador.
- `auditoria`: registro imutável de alterações relevantes.

### Capacidades modificadas
_Nenhuma._

## Impacto

- **Xano:** tabelas `especialidade`, `especialidade_alternativa`, `sintoma`, `sintoma_especialidade`, `medico`, `medico_especialidade`, `disponibilidade_medico`, `parametro` e `historico_alteracao`; endpoints CRUD protegidos para ADMINISTRADOR (com leitura liberada aos outros perfis onde as próximas changes precisarem); funções reutilizáveis `registrar_alteracao` e `obter_parametro`.
- **Reflex:** telas em `/admin/especialidades`, `/admin/sintomas`, `/admin/medicos`, `/admin/disponibilidade` e `/admin/parametros`.
- **Testes:** `tests/api/test_cadastros.py`, `test_disponibilidade.py`, `test_parametros.py` e `test_auditoria.py`.
- **Depende de:** `add-autenticacao-perfis` (usuários, perfis e `verificar_acesso`).
- **Divergência com o documento formal:** o modelo formal (seção 17) tem `Médico.especialidade_id` (uma especialidade); o contexto do PO fala em "suas especialidades". Esta change adota N:N (Médico_Especialidade), que também atende o caso de uma única especialidade.

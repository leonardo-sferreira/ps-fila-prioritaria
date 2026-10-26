# Proposta: Integração de segurança e auditoria de Pacientes

| Campo | Valor |
|---|---|
| Change | `integrar-seguranca-auditoria-pacientes` |
| Sprint e entrega | A definir pelo PO |
| Card no Trello | A criar para a integração pendente de Pacientes |
| Depende de | `add-autenticacao-perfis` (`verificar_acesso` e token) e `add-base-compartilhada` (`registrar_alteracao` atômico) |
| Situação | Proposta para revisão |
| Rastreabilidade | RF03, RF04, RF05, RN01, RN02 e CA01, conforme as especificações disponíveis no repositório |

## Why

Os endpoints de Paciente hoje retornam e alteram dados pessoais sem aplicar token, perfil ou auditoria, embora a tela já tenha guarda visual. Esta change conclui a integração originalmente deferida, impedindo exposição de CPF e cadastro fora dos perfis autorizados e tornando cadastros e alterações reais rastreáveis.

## What Changes

- Proteger no Xano `GET /pacientes`, `POST /pacientes` e `PATCH /pacientes/{id}` com autenticação nativa e `auth/verificar_acesso`: Recepção/Triagem pesquisa, cadastra e altera; Administrador apenas pesquisa; Médico recebe 403; ausência, invalidez ou desativação do usuário retorna 401 sem dados ou alteração.
- Usar `registrar_alteracao` dentro da mesma transação das escritas: cadastro registra `CADASTRO`; PATCH só registra alteração quando os valores resultantes diferem dos persistidos. No-op continua retornando `alterado: false`, sem escrita e sem auditoria.
- Fazer busca, cadastro e atualização na tela de Pacientes usarem o cliente HTTP compartilhado com o token da sessão e tratar 401 como sessão expirada, 403 como acesso negado e os erros de validação sem expor detalhes internos.
- Formalizar no requisito de Pacientes que `Continuar` abre a Ficha do fluxo de triagem, substituindo a decisão temporária arquivada de confirmação exclusivamente visual. A abertura de Ficha e suas regras permanecem na capability `ficha-atendimento`.
- Cobrir a matriz de permissão, token real, todos os erros do PATCH, auditoria atômica, no-op e CA01 em testes automatizados e roteiro ponta a ponta.

### Fora do escopo

- Criar ou alterar schema de Paciente, Usuário, Sessão ou Histórico de Alteração.
- Concluir itens de gestão de usuários, redefinição de senha, parâmetros, carga inicial ou cadastros administrativos não necessários a esta integração.
- Alterar regras de abertura, preenchimento clínico, sintomas, classificação, ticket, fila, chamada ou painel público.
- Exibir, editar ou administrar registros de auditoria por uma nova API.

## Capacidades

### Novas capacidades

_Nenhuma._

### Capacidades modificadas

- `pacientes`: autorização efetiva no backend, auditoria atômica de escritas e continuidade da identificação para a Ficha já especificada.

## Impacto

- **Xano:** endpoints e função existentes de Paciente passam a reutilizar `auth/verificar_acesso` e `registrar_alteracao`, sem infraestrutura paralela.
- **Reflex:** `PacienteState` deixa de fazer chamadas HTTP diretas para usar o cliente autenticado já existente e passa a reagir consistentemente a 401/403.
- **Testes:** adiciona cobertura de autorização, PATCH parcial e inspeção de auditoria; os testes de integração usam credenciais de teste já previstas no `.env`, sem versionar segredos.
- **Documentação:** atualiza a spec principal de `pacientes`; a divergência com a confirmação visual da change arquivada fica explicitamente substituída pelo fluxo consolidado de abertura de Ficha.

## Perguntas em aberto

- [ ] O card e a sprint desta integração ainda precisam ser vinculados pelo PO no Trello.

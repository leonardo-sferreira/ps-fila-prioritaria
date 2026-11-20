# Mapa: tela → estado → API

> Arquivo gerado por `python scripts/gerar_docs.py`. Não edite à mão: altere o código e gere de novo.

Cada tela (rota do Reflex) é desenhada por uma função em `frontend/ps_fila_prioritaria/paginas/` e usa um ou mais estados em `estados/`, que chamam a API do Xano por `api.requisitar` (`frontend/ps_fila_prioritaria/api.py`). A lista de endpoints de cada estado é obtida pelos caminhos citados no código e conferida com os endpoints existentes; quando um estado chama vários verbos no mesmo caminho, todos aparecem.

## Telas

| Rota | Perfil | Página (função) | Estados usados |
|---|---|---|---|
| `/` | público | `paginas/autenticacao.py` → `index` | `autenticacao` |
| `/admin` | ADMINISTRADOR | `paginas/painel_admin.py` → `area_admin` | `equipe`, `plantao` |
| `/admin/auditoria` | ADMINISTRADOR | `paginas/auditoria.py` → `pagina_auditoria` | `auditoria` |
| `/admin/disponibilidade` | ADMINISTRADOR | `paginas/cadastros.py` → `pagina_plantoes` | `cadastros` |
| `/admin/especialidades` | ADMINISTRADOR | `paginas/cadastros.py` → `pagina_especialidades` | `cadastros` |
| `/admin/fichas/[id]` | ADMINISTRADOR | `paginas/acompanhamento.py` → `pagina_ficha_admin` | `acompanhamento` |
| `/admin/fila-geral` | ADMINISTRADOR | `paginas/acompanhamento.py` → `pagina_fila_geral` | `acompanhamento` |
| `/admin/medicos` | ADMINISTRADOR | `paginas/cadastros.py` → `pagina_medicos` | `cadastros` |
| `/admin/parametros` | ADMINISTRADOR | `paginas/cadastros.py` → `pagina_parametros` | `cadastros` |
| `/admin/recepcao` | ADMINISTRADOR | `paginas/cadastros.py` → `pagina_recepcao` | `cadastros` |
| `/admin/salas` | ADMINISTRADOR | `paginas/cadastros.py` → `pagina_salas` | `cadastros` |
| `/admin/sintomas` | ADMINISTRADOR | `paginas/cadastros.py` → `pagina_sintomas` | `cadastros` |
| `/admin/usuarios` | ADMINISTRADOR | `paginas/usuarios.py` → `pagina_usuarios` | `usuarios` |
| `/login` | público | `paginas/autenticacao.py` → `login` | `autenticacao` |
| `/login/codigo` | público | `paginas/autenticacao.py` → `login_codigo` | `autenticacao` |
| `/medico` | MEDICO | `paginas/medico.py` → `area_medico` | `cadastros`, `medico` |
| `/medico/ficha/[id]/imprimir` | MEDICO | `paginas/medico.py` → `pagina_impressao_medico` | `cadastros`, `medico` |
| `/painel` | público | `paginas/painel.py` → `painel_escolha` | `painel` |
| `/painel/medico` | público | `paginas/painel.py` → `painel_medico` | `painel` |
| `/painel/triagem` | público | `paginas/painel.py` → `painel_triagem` | `painel` |
| `/privacidade` | público | `paginas/privacidade.py` → `privacidade` | — |
| `/recepcao` | RECEPCAO_TRIAGEM | `paginas/plantao.py` → `area_recepcao` | `autenticacao`, `plantao`, `status_equipe` |
| `/recepcao/comprovante/[id]` | RECEPCAO_TRIAGEM | `paginas/comprovante.py` → `pagina_comprovante` | `comprovante` |
| `/recepcao/ficha/[id]` | RECEPCAO_TRIAGEM | `paginas/ficha.py` → `pagina_recepcao_ficha` | `ficha` |
| `/recepcao/fichas` | RECEPCAO_TRIAGEM | `paginas/fichas_do_dia.py` → `pagina_fichas_do_dia` | `fichas_do_dia` |
| `/recepcao/fila` | RECEPCAO_TRIAGEM | `paginas/fila_pre_triagem.py` → `pagina_fila_tickets` | `fila_pre_triagem` |
| `/recepcao/pacientes` | RECEPCAO_TRIAGEM | `paginas/pacientes.py` → `pagina_recepcao_pacientes` | `pacientes` |
| `/sair/inatividade` | público | `carregando` | — |
| `/senha` | público | `paginas/autenticacao.py` → `senha_email` | `autenticacao` |
| `/senha/codigo` | público | `paginas/autenticacao.py` → `senha_codigo` | `autenticacao` |
| `/senha/nova` | público | `paginas/autenticacao.py` → `senha_nova` | `autenticacao` |
| `/senha/sucesso` | público | `paginas/autenticacao.py` → `senha_sucesso` | `autenticacao` |
| `/totem` | público | `paginas/totem.py` → `totem` | `totem` |

## Estados e endpoints que chamam

| Estado (`estados/`) | Endpoints |
|---|---|
| `acompanhamento.py` | `GET /admin/fichas/{ficha_id}` (Cadastros)<br>`GET /admin/fila-geral` (Cadastros)<br>`GET /especialidades` (Cadastros) |
| `auditoria.py` | `GET /admin/auditoria` (Cadastros)<br>`GET /usuarios` (Cadastros) |
| `autenticacao.py` | `POST /auth/login` (Autenticacao)<br>`POST /auth/login/reenviar` (Autenticacao)<br>`POST /auth/login/verificar` (Autenticacao)<br>`POST /auth/logout` (Autenticacao)<br>`GET /auth/me` (Autenticacao)<br>`POST /auth/senha/redefinir` (Autenticacao)<br>`POST /auth/senha/solicitar` (Autenticacao)<br>`POST /auth/senha/verificar` (Autenticacao)<br>`GET /recepcao` (Cadastros)<br>`POST /recepcao` (Cadastros) |
| `cadastros.py` | `GET /disponibilidade` (Cadastros)<br>`POST /disponibilidade` (Cadastros)<br>`DELETE /disponibilidade/{disponibilidade_id}` (Cadastros)<br>`PATCH /disponibilidade/{disponibilidade_id}` (Cadastros)<br>`GET /especialidades` (Cadastros)<br>`GET /faixas` (Cadastros)<br>`PATCH /faixas/{faixa_id}` (Cadastros)<br>`GET /medicos` (Cadastros)<br>`GET /medicos/me/disponibilidade` (Cadastros)<br>`GET /parametros` (Cadastros)<br>`PATCH /parametros/{chave}` (Cadastros)<br>`GET /recepcao` (Cadastros)<br>`POST /recepcao` (Cadastros)<br>`GET /salas` (Cadastros)<br>`GET /sintomas` (Cadastros)<br>`GET /sintomas` (Triagem)<br>`POST /sintomas` (Cadastros) |
| `comprovante.py` | `GET /fichas/{ficha_id}/comprovante` (Triagem) |
| `equipe.py` | `GET /admin/equipe` (Cadastros) |
| `expiracao.py` | `GET /expiracao` (Triagem)<br>`POST /expiracao` (Triagem) |
| `ficha.py` | `GET /fichas/{ficha_id}` (Triagem)<br>`PATCH /fichas/{ficha_id}` (Triagem)<br>`POST /fichas/{ficha_id}/confirmar-triagem` (Triagem)<br>`POST /fichas/{ficha_id}/prioridade` (Triagem)<br>`GET /sintomas` (Cadastros)<br>`GET /sintomas` (Triagem) |
| `fichas_do_dia.py` | `GET /fichas` (Triagem) |
| `fila_pre_triagem.py` | `GET /tickets` (Triagem)<br>`POST /tickets/proximo` (Triagem)<br>`POST /tickets/{ticket_id}/acao` (Triagem) |
| `medico.py` | `GET /fichas/{ficha_id}/impressao` (Fila)<br>`PATCH /me/status` (Autenticacao)<br>`POST /medico/chamar-proximo` (Fila)<br>`POST /medico/fichas/{ficha_id}/acao` (Fila)<br>`GET /medico/filas` (Fila) |
| `pacientes.py` | `POST /fichas` (Triagem)<br>`GET /pacientes` (Pacientes)<br>`POST /pacientes` (Pacientes)<br>`PATCH /pacientes/{paciente_id}` (Pacientes) |
| `painel.py` | `GET /painel` (Fila) |
| `plantao.py` | `GET /fichas` (Triagem)<br>`POST /fichas` (Triagem)<br>`GET /tickets` (Triagem) |
| `status_equipe.py` | `GET /me/status` (Autenticacao)<br>`PATCH /me/status` (Autenticacao) |
| `totem.py` | `POST /totem/tickets` (Triagem) |
| `usuarios.py` | `GET /salas` (Cadastros)<br>`GET /usuarios` (Cadastros)<br>`POST /usuarios` (Cadastros) |

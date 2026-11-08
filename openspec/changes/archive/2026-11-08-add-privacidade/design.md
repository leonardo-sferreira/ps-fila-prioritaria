# Design técnico

## Contexto

O frontend é um módulo Reflex único (`frontend/ps_fila_prioritaria/ps_fila_prioritaria.py`), com as telas de acesso montadas sobre `cartao_acesso()` e as páginas internas protegidas por `protegido()` e pelo `on_load` `AuthState.verificar_sessao`, que chama `GET auth/me` a cada página interna aberta. O CPF de paciente só aparece inteiro hoje no cabeçalho da ficha (`recepcao_ficha`, `FichaState.paciente["cpf"]`). Não há página pública fora das telas de acesso. O token vale 12 h (`TOKEN_TTL_SEGUNDOS`) e o "Sair" chama `auth/logout`, que preenche `logout_em` na sessão aberta.

## Objetivos / Fora dos objetivos

**Objetivos:**
- Um único texto de aviso, versionado no repositório, mostrado pela página sem cópia manual.
- Máscara de CPF numa função só, usada onde o CPF é exibido.
- Encerramento por inatividade que reaproveite o "Sair" existente e leia o tempo do Xano.

**Fora dos objetivos:**
- Fazer o Xano recusar token por inatividade (exigiria guardar a última atividade e mudar a validação do token em todos os endpoints).
- Componente genérico de exibição de dados pessoais para telas que ainda não existem (YAGNI).

## Decisões

### D1. Aviso em Markdown versionado, exibido com `rx.markdown`
O texto fica em `docs/aviso-de-privacidade.md`. A página `/privacidade` lê o arquivo ao montar a página e o exibe com `rx.markdown`, dentro de um cartão no padrão visual das telas de acesso (mais largo, para leitura), com "Voltar ao login" no fim.
- **Por quê:** o mesmo arquivo serve de documentação e de tela, como no ConectaRH, e o PO revisa o texto no repositório sem mexer em código.
- **Alternativa:** texto escrito direto no componente. Descartada porque duplicaria o texto e faria o PO editar Python.

### D2. Link do aviso no rodapé de `cartao_acesso()`
O rodapé "Acesso restrito a profissionais autorizados do PS" passa a ter, ao lado, o link "Aviso de privacidade" para `/privacidade`. Como login, código e redefinição de senha usam `cartao_acesso()`, o link aparece em todas de uma vez.
- **Por quê:** reaproveita o componente existente; nenhuma tela precisa ser alterada uma a uma.

### D3. Máscara de CPF em função pura, exposta como `rx.var` no estado da ficha
Uma função `mascarar_cpf(valor) -> str` tira tudo que não é dígito; com 11 dígitos, devolve `***.DDD.DDD-**`; senão, devolve "—". O `FichaState` ganha o `rx.var` `cpf_exibido`, e o cabeçalho da ficha passa a usá-lo no lugar de `paciente["cpf"]`.
- **Por quê:** é regra de exibição, então fica no Reflex; função pura é fácil de testar nos valores-limite (10, 11 e 12 dígitos, com e sem pontuação).
- **Alternativa:** mascarar no Xano. Descartada nesta change porque a Recepção/Triagem precisa do CPF completo para conferir e atualizar o cadastro; ver Riscos.

### D4. Tempo de inatividade no Xano, entregue pelo `auth/me`
Nova variável de ambiente `INATIVIDADE_SEGUNDOS=3600` (1 hora, decisão do PO). O `auth/me` passa a responder `{id, nome, email, perfil, inatividade_segundos}`. O `AuthState` guarda o valor ao validar a sessão.
- **Por quê:** o `auth/me` já é chamado em toda página interna; o parâmetro fica junto dos outros tempos (`TOKEN_TTL_SEGUNDOS`, `CODIGO_*`) e muda sem publicar o frontend.
- **Alternativa:** variável no `.env` do Reflex. Descartada para não espalhar parâmetros de sessão entre dois lugares.

### D5. Contagem no navegador com um script pequeno; encerramento pela rota `/sair/inatividade`
`protegido()` passa a incluir um marcador oculto com o tempo (`data-inatividade-ms`, ligado a `AuthState.inatividade_segundos`) e um `rx.script` que: (1) instala uma única vez os ouvintes de `mousemove`, `mousedown`, `keydown`, `scroll` e `touchstart`, que reiniciam a contagem; (2) a cada segundo confere se o marcador está na página e se o tempo sem interação passou do limite; (3) ao passar, navega para `/sair/inatividade`. A página `/sair/inatividade` tem `on_load` `AuthState.sair_por_inatividade`, que faz o mesmo que `sair()` (chama `auth/logout` e descarta token, nome e perfil) e deixa a mensagem "Sua sessão foi encerrada por inatividade." para a tela de login.
- **Por quê:** o Reflex não tem detecção de inatividade, e mandar um evento ao servidor a cada tecla seria custoso. Como o marcador só existe nas páginas protegidas, as telas públicas não contam inatividade, mesmo que o script continue carregado depois da navegação.
- **Alternativa:** evento em segundo plano do Reflex com `asyncio.sleep`. Descartada porque o servidor não sabe quando o usuário mexe no mouse sem receber esses eventos.

## Riscos / Compromissos

- [A inatividade é medida só no navegador] → Quem tiver o token pode usá-lo pela API até as 12 h de validade. Aceito nesta change (fora do escopo); o logout é registrado na sessão, o que já serve de rastro.
- [Abas diferentes contam separadamente] → Duas abas abertas: a aba parada encerra a sessão e a outra cai no login na próxima ação. Aceito: é o comportamento mais seguro.
- [A API continua devolvendo o CPF completo] → A máscara reduz a exposição visual, não a técnica. A spec `pacientes` já exige autenticação nesses endpoints, e o fato de não exigirem hoje está registrado nas perguntas em aberto da proposta.
- [Aviso desatualizado] → O texto é a fonte única; ao mudar dado tratado, prazo ou fornecedor, atualizar `docs/aviso-de-privacidade.md` na mesma change.

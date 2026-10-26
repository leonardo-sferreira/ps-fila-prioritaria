# Tarefas

## 1. Aviso de privacidade (D1, D2)

- [x] 1.1 [Docs] Escrever `docs/aviso-de-privacidade.md` com as seções exigidas pela spec, separando equipe e pacientes: dados tratados (equipe: nome, e-mail, perfil, horários de sessão e códigos de verificação guardados só como hash; pacientes: nome, CPF, data de nascimento, telefone e dados da triagem, que são dados de saúde), finalidade, compartilhamento (Xano como banco e Brevo para os e-mails de código), prazo de guarda, direitos do titular e como exercê-los. Os prazos de guarda ficam como "a definir pelo PO" (a seção de controlador e encarregado foi retirada por decisão do PO em 26/10/2026); verificar que todas as seções do cenário "Conteúdo obrigatório" estão presentes
  - Evidência (26/10/2026): `docs/aviso-de-privacidade.md` v1.0 com dados da equipe e dos pacientes conferidos nas tabelas do repositório; seções obrigatórias conferidas por `test_privacidade.py`.
- [x] 1.2 [Reflex] Criar a página pública `/privacidade`, que lê `docs/aviso-de-privacidade.md` e o exibe com `rx.markdown` num cartão no padrão das telas de acesso, com "Voltar ao login"; usada pelo link da 1.3. Verificar com teste que o conteúdo exibido é o do arquivo e manualmente que abre sem login e com sessão aberta (sem derrubar a sessão)
  - Evidência (26/10/2026): `/privacidade` aberta sem login no navegador (captura de tela), com o texto completo do arquivo e "Voltar ao login"; teste confere que o texto exibido é o do arquivo. A página não chama `auth/me` nem mexe na sessão.
- [x] 1.3 [Reflex] Refatorar o rodapé de `cartao_acesso()` para incluir o link "Aviso de privacidade" ao lado de "Acesso restrito a profissionais autorizados do PS"; verificar por captura de tela que o link aparece no login, no código do login e nas telas A1 a A4
  - Evidência: rodapé "Acesso restrito a profissionais autorizados do PS · Aviso de privacidade" conferido por captura no login, na A1 e no próprio aviso; o código do login e as telas A2 a A4 usam o mesmo `cartao_acesso()`.

## 2. CPF mascarado (D3)

- [x] 2.1 [Reflex] Criar a função `mascarar_cpf` e testá-la em `frontend/tests/test_privacidade.py` com os valores-limite: 11 dígitos com e sem pontuação (`***.456.789-**`), 10 e 12 dígitos, vazio e `None` ("—"); usada pela 2.2
  - Evidência: `mascarar_cpf` com 11 dígitos com e sem pontuação, 10, 12, vazio, `None` e texto, em `test_privacidade.py`.
- [x] 2.2 [Reflex] Refatorar o cabeçalho de `recepcao_ficha` para exibir `FichaState.cpf_exibido` (novo `rx.var` que usa `mascarar_cpf`) no lugar de `paciente["cpf"]`; verificar com teste do estado e manualmente que o campo de busca de CPF continua mostrando o valor digitado
  - Evidência: `FichaState.cpf_exibido` usado no cabeçalho da ficha, testado com e sem paciente; o campo de busca (`PacienteState.cpf_busca`) não foi alterado.

## 3. Saída por inatividade (D4, D5)

- [ ] 3.1 [Xano] Criar a variável de ambiente `INATIVIDADE_SEGUNDOS=3600` e fazer o `auth/me` devolver `inatividade_segundos`; publicar com dry-run antes, exportar o `.xs` e verificar com teste ao vivo em `test_api_autenticacao.py` (campo presente e maior que zero; sem token continua 401)
  - Parcial: `INATIVIDADE_SEGUNDOS=3600` confirmada por `workspace pull --env`; `auth/me` publicado (dry-run antes) e exportado; teste ao vivo sem token continua 401. O campo só aparece com token válido, que exige o código por e-mail: conferir no roteiro manual da 3.3.
- [x] 3.2 [Reflex] Guardar `inatividade_segundos` no `AuthState` ao validar a sessão e criar `sair_por_inatividade` (reaproveita `sair()` e deixa a mensagem "Sua sessão foi encerrada por inatividade."), com a página `/sair/inatividade`; atualizar `test_auth_state.py` (valor guardado, logout chamado, token descartado e mensagem)
  - Evidência: `inatividade_segundos` guardado pela guarda de rota; `sair_por_inatividade` reaproveita `_sair()` (extraído do `sair()`), com a página `/sair/inatividade`; 2 testes novos em `test_auth_state.py`.
- [ ] 3.3 [Reflex] Refatorar `protegido()` para incluir o marcador oculto com o tempo e o `rx.script` de contagem (D5); verificar manualmente com `INATIVIDADE_SEGUNDOS` reduzido para 60 no Xano: 59 s parado mantém a página, 60 s leva ao login com a mensagem, mexer o mouse aos 50 s reinicia a contagem, "voltar" depois do encerramento cai no login e o login aberto por mais de 60 s não é afetado; restaurar 3600 ao final
  - Parcial: marcador `#ps-inatividade` e script em `protegido()`; conferido no código gerado que `data-inatividade-ms` vem do estado; a rota `/sair/inatividade` leva ao login com a mensagem (captura de tela). Falta o roteiro manual logado, que depende do código por e-mail.

## 4. Documentação e fechamento

- [x] 4.1 [Docs] Atualizar `docs/project-overview.md` (funcionalidades e regras globais: aviso de privacidade, CPF mascarado nas telas internas e saída por inatividade) e o README (variável `INATIVIDADE_SEGUNDOS`); verificar que não contradizem a spec `privacidade`
  - Evidência: `project-overview.md` (funcionalidade e regra global de privacidade) e README (variáveis de tempo do Xano e arquivo do aviso).
- [ ] 4.2 Rodar a suíte completa (`pytest` em `frontend/`) e `reflex compile`; verificar que tudo passa e restaurar `frontend/reflex.lock` antes do commit
  - Parcial: 109 testes unitários passando, `reflex compile` sem erros e app aberto no navegador; `frontend/reflex.lock` restaurado antes do commit. Falta repetir a suíte depois do roteiro manual da 3.3.

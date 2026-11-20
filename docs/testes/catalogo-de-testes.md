# Catálogo de testes

> Arquivo gerado por `python scripts/gerar_docs.py`. Não edite à mão: altere o código e gere de novo.

Fonte: `tests/catalogo_testes.json`. Cada caso tem um ID permanente; o CI recusa teste sem registro no catálogo. Como rodar e como ler as evidências: [estrategia-de-testes.md](estrategia-de-testes.md).

| Suíte | Casos | Onde roda |
|---|---|---|
| Autotestes da infraestrutura de evidências | 41 | CI e local |
| Integração ao vivo (escrita isolada na v1) | 33 | Local, com autorização |
| E2E público (navegador) | 2 | CI |
| Reflex (estado das telas, API simulada) | 297 | CI e local |
| Xano funções puras (testes nativos remotos) | 97 | CI (CLI do Xano) |
| Xano estático (contratos lidos do código) | 13 | CI e local |
| **Total** | **483** | |

Colunas: **Entrada** = o que o teste prepara ou envia (resumo do objetivo); **Saída esperada** = o resultado que precisa acontecer para o teste passar.

## Autotestes da infraestrutura de evidências

| ID | Teste | Tipo | Entrada | Saída esperada | Código |
|---|---|---|---|---|---|
| CT-FERRAMENTA-0001 | Timeout transitorio do CLI Xano repete sem mudar o caso | INTEGRACAO | — | Timeout transitorio do CLI Xano repete sem mudar o caso. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0002 | Resultado json tem texto legivel sem alterar rastreabilidade | UNITARIO | — | Resultado json tem texto legivel sem alterar rastreabilidade. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0003 | Junit representa falha erro e não execucao | UNITARIO | — | Junit representa falha erro e não execucao. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0004 | Resumo mantem status e redige segredos | UNITARIO | — | Resumo mantem status e redige segredos. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0005 | Coleta falha não gera pass | UNITARIO | — | Coleta falha não gera pass. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0006 | Coleta resultado playwright com sufixo navegador | UNITARIO | — | Coleta resultado playwright com sufixo navegador. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0007 | Coleta distingue nomes iguais em modulos diferentes | UNITARIO | — | Coleta distingue nomes iguais em modulos diferentes. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0008 | Funcao Xano repete apos limite temporario | INTEGRACAO | — | Funcao Xano repete apos limite temporario. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0009 | Guardiao recusa host de producao e sem confirmacao | INTEGRACAO | — | Guardiao recusa host de producao e sem confirmacao. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0010 | HTTP registra somente rota status e campos | UNITARIO | — | HTTP registra somente rota status e campos. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0011 | Execucao bloqueada ou parcial não e aprovada | UNITARIO | — | Execucao bloqueada ou parcial não e aprovada. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0012 | Resumo actions e curto e mostra resultado | UNITARIO | — | Resumo actions e curto e mostra resultado. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0013 | Catalogo tem somente os seis roteiros abertos sem ponta a ponta | UNITARIO | — | Catalogo tem somente os seis roteiros abertos sem ponta a ponta. | `tests/test_roteiros_sprint5.py` |
| CT-FERRAMENTA-0014 | Todos os seletores disponiveis apontam para casos reais | UNITARIO | — | Todos os seletores disponiveis apontam para casos reais. | `tests/test_roteiros_sprint5.py` |
| CT-FERRAMENTA-0015 | Resultado tecnico propagado sem aprovar execucao parcial | UNITARIO | — | Resultado tecnico propagado sem aprovar execucao parcial. | `tests/test_roteiros_sprint5.py` |
| CT-FERRAMENTA-0016 | Caso e2e não conta como evidencia deste relatorio | UNITARIO | — | Caso e2e não conta como evidencia deste relatorio. | `tests/test_roteiros_sprint5.py` |
| CT-FERRAMENTA-0017 | Markdown e legivel e não contem dados de entrada | INTEGRACAO | — | Markdown e legivel e não contem dados de entrada. | `tests/test_roteiros_sprint5.py` |
| CT-FERRAMENTA-0018 | Projecoes seis estados sem casos infra ficticios | UNITARIO | — | Projecoes seis estados sem casos infra ficticios. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0019 | Merge ausencias corrupcao e fontes confiaveis | UNITARIO | — | Merge ausencias corrupcao e fontes confiaveis. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0020 | Merge rejeita commits run attempt duplicacao e tampering | UNITARIO | — | Merge rejeita commits run attempt duplicacao e tampering. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0021 | Merge leitura legada somente local explicita sem alterar origem | UNITARIO | — | Merge leitura legada somente local explicita sem alterar origem. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0022 | Merge recusa destino preserva histórico e sem roteiro fixo | UNITARIO | — | Merge recusa destino preserva histórico e sem roteiro fixo. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0023 | Codigos reais merge sucesso falha erro parcial ignorado bloqueado | UNITARIO | — | Codigos reais merge sucesso falha erro parcial ignorado bloqueado. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0024 | Runner codigos e publicacao apos falha instalacao e zero | UNITARIO | — | Runner codigos e publicacao apos falha instalacao e zero. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0025 | Runner process code sem xml e xml parcial nunca aprova | UNITARIO | — | Runner process code sem xml e xml parcial nunca aprova. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0026 | Nativo sucesso assertion timeout json ausente e credencial | UNITARIO | — | Nativo sucesso assertion timeout json ausente e credencial. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0027 | Minimizacao canarios em todos formatos e logs | UNITARIO | — | Minimizacao canarios em todos formatos e logs. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0028 | Muitos casos agrupa motivos sem tabela bruta | UNITARIO | — | Muitos casos agrupa motivos sem tabela bruta. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0029 | Needs failure não substituido por publicacao e roteiro explicito | UNITARIO | — | Needs failure não substituido por publicacao e roteiro explicito. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0030 | Seis estados eixos e gate | UNITARIO | — | Seis estados eixos e gate. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0031 | Catalogo identidade renomeacao duplicacao e divergencia | UNITARIO | — | Catalogo identidade renomeacao duplicacao e divergencia. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0032 | Xml identidades modulo classe variante setup teardown e erro call | UNITARIO | — | Xml identidades modulo classe variante setup teardown e erro call. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0033 | Destino exclusivo timeout e metadados ci | UNITARIO | — | Destino exclusivo timeout e metadados ci. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0034 | Guardiao funcoes python bloqueia antes do CLI | UNITARIO | — | Guardiao funcoes python bloqueia antes do CLI. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0035 | Helper CLI separa erros e preserva assertions | UNITARIO | — | Helper CLI separa erros e preserva assertions. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0036 | Guardiao controlado nega cada precondicao sem escrita | UNITARIO | — | Guardiao controlado nega cada precondicao sem escrita. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0037 | Estatica seleciona oito sem rede ou CLI | UNITARIO | — | Estatica seleciona oito sem rede ou CLI. | `tests/test_evidence_runner.py` |
| CT-FERRAMENTA-0038 | Ciclo temporario reutiliza ids e adaptador CLI | UNITARIO | — | Ciclo temporario reutiliza ids e adaptador CLI. | `tests/test_roteiros_sprint5.py` |
| CT-FERRAMENTA-0039 | E2e destino inicializacao e timeout sem logs sensiveis | UNITARIO | — | E2e destino inicializacao e timeout sem logs sensiveis. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0040 | Workflow topologia publicacao e gates preservados | UNITARIO | — | Workflow topologia publicacao e gates preservados. | `tests/test_evidence_pipeline.py` |
| CT-FERRAMENTA-0041 | Fixtures isolam Actions sem apagar contexto do runner | UNITARIO | Verificar que as fixtures sintéticas não herdam identidade nem publicam no Summary externo, preservando o contexto da execução intencional. | Os seis cenários antes reprovados passam sob ambiente CI; o Summary sentinela permanece intacto e o runner intencional mantém SHA, run, tentativa e job. | `tests/test_evidence_pipeline.py` |

## Integração ao vivo (escrita isolada na v1)

| ID | Teste | Tipo | Entrada | Saída esperada | Código |
|---|---|---|---|---|---|
| CT-XANO-0098 | Senha correta envia o código e ainda não devolve token[ADMINISTRADOR] | INTEGRACAO | Senha correta envia o código e ainda não devolve token | Senha correta envia o código e ainda não devolve token. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0099 | Email com maiusculas e espacos tambem entra | INTEGRACAO | — | Email com maiusculas e espacos tambem entra. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0100 | Senha errada usa a mesma mensagem generica | INTEGRACAO | — | Senha errada usa a mesma mensagem generica. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0101 | Campos ausentes sao recusados sem token | INTEGRACAO | — | Campos ausentes sao recusados sem token. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0102 | Código errado e tentativas esgotadas sao recusados sem token | INTEGRACAO | — | Código errado e tentativas esgotadas sao recusados sem token. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0103 | Reenvio antes do intervalo informa quanto falta | INTEGRACAO | — | Reenvio antes do intervalo informa quanto falta. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0104 | Reenvio sem login pendente pede novo login | INTEGRACAO | — | Reenvio sem login pendente pede novo login. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0105 | Verificar sem código e recusado | INTEGRACAO | — | Verificar sem código e recusado. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0106 | Me recusa requisicao sem token ou com token adulterado | INTEGRACAO | — | Me recusa requisicao sem token ou com token adulterado. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0107 | Resposta igual para email inexistente e campo obrigatorio | INTEGRACAO | — | Resposta igual para email inexistente e campo obrigatorio. | `frontend/tests/test_api_redefinicao_senha.py` |
| CT-XANO-0108 | Solicitacao valida responde igual e bloqueia reenvio imediato | INTEGRACAO | — | Solicitacao valida responde igual e bloqueia reenvio imediato. | `frontend/tests/test_api_redefinicao_senha.py` |
| CT-XANO-0109 | Código errado e tentativas esgotadas sao recusados | INTEGRACAO | — | Código errado e tentativas esgotadas sao recusados. | `frontend/tests/test_api_redefinicao_senha.py` |
| CT-XANO-0110 | Senha curta e código errado não trocam a senha | INTEGRACAO | — | Senha curta e código errado não trocam a senha. | `frontend/tests/test_api_redefinicao_senha.py` |
| CT-XANO-0111 | Emissao de cada tipo usa o prefixo e so dados operacionais[PEDIATRICO] | INTEGRACAO | Emissao de cada tipo usa o prefixo e so dados operacionais | Emissao de cada tipo usa o prefixo e so dados operacionais. | `frontend/tests/test_api_totem.py` |
| CT-XANO-0112 | Sequencia do tipo avanca sem mexer nos outros tipos | INTEGRACAO | — | Sequencia do tipo avanca sem mexer nos outros tipos. | `frontend/tests/test_api_totem.py` |
| CT-XANO-0113 | Chave ausente ou errada não emite | INTEGRACAO | — | Chave ausente ou errada não emite. | `frontend/tests/test_api_totem.py` |
| CT-XANO-0114 | Tipo ausente ou inválido não emite | INTEGRACAO | — | Tipo ausente ou inválido não emite. | `frontend/tests/test_api_totem.py` |
| CT-XANO-0115 | Emissoes simultaneas do mesmo tipo não repetem número | INTEGRACAO | — | Emissoes simultaneas do mesmo tipo não repetem número. | `frontend/tests/test_api_totem.py` |
| CT-XANO-0116 | Catalogo sintomas 46 ativos | INTEGRACAO | Valida que GET /sintomas retorna exatamente 46 sintomas ativos com campos obrigatórios. | Valida que GET /sintomas retorna exatamente 46 sintomas ativos com campos obrigatórios. | `frontend/tests/test_xano_api_integration.py` |
| CT-XANO-0117 | Rf06 abertura de ficha | INTEGRACAO | RF06: Paciente válido cria ficha em EM TRIAGEM com chegada em gerado pelo backend. | RF06: Paciente válido cria ficha em EM TRIAGEM com chegada em gerado pelo backend. | `frontend/tests/test_xano_api_integration.py` |
| CT-XANO-0118 | Rn03 bloqueio segunda ficha ativa | INTEGRACAO | RN03: Bloqueia abertura de segunda ficha quando já existe ficha em EM TRIAGEM. | RN03: Bloqueia abertura de segunda ficha quando já existe ficha em EM TRIAGEM. | `frontend/tests/test_xano_api_integration.py` |
| CT-XANO-0119 | Rf07 e rn04 fluxo completo ficha | INTEGRACAO | RF07 e RN04: - Sintomas, observação, ambos; - Edição posterior com coleção final; - Recarga por GET /fichas/{ID}; - Validação de RN04 (aceite e recusa no estado resultante). | RF07 e RN04: - Sintomas, observação, ambos; - Edição posterior com coleção final; - Recarga por GET /fichas/{ID}; - Validação de RN04 (aceite e recusa no estado resultante). | `frontend/tests/test_xano_api_integration.py` |
| CT-XANO-0120 | Fluxo concorrente e oportunidades | INTEGRACAO | — | Fluxo concorrente e oportunidades. | `tests/api/test_chamada.py` |
| CT-XANO-0121 | Fluxo | INTEGRACAO | — | Fluxo. | `tests/api/test_recuperacao_sessao_medico.py` |
| CT-XANO-0130 | Parametros sem token e com token adulterado | INTEGRACAO | — | Parametros sem token e com token adulterado. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0134 | Código errado não cria sessão e código certo cria | INTEGRACAO | Código de login errado não abre sessão; o código certo devolve o token e abre exatamente uma sessão. | Código de login errado não abre sessão; o código certo devolve o token e abre exatamente uma sessão. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0135 | Usuário desativado com token válido perde o acesso | INTEGRACAO | Com a sessão ainda aberta, desativar o login faz auth/me responder 401 na próxima requisição. | Com a sessão ainda aberta, desativar o login faz auth/me responder 401 na próxima requisição. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0136 | Usuário inativo não consegue entrar | INTEGRACAO | Login de usuário inativo é recusado sem enviar código, sem token e sem sessão. | Login de usuário inativo é recusado sem enviar código, sem token e sem sessão. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0140 | Consultas do Administrador | INTEGRACAO | Fila geral, detalhe da ficha, equipe e auditoria só para o Administrador; fila geral com as fichas do cenário na ordem da regra e filtros de cor e status. | Fila geral, detalhe da ficha, equipe e auditoria só para o Administrador; fila geral com as fichas do cenário na ordem da regra e filtros de cor e status. | `tests/api/test_acompanhamento.py` |
| CT-XANO-0141 | Fluxo reflete no acompanhamento | INTEGRACAO | me/status da própria sessão; detalhe com ajuste de cor e justificativa; ficha chamada duas vezes com médico e tentativa; sessão encerrada fora da equipe e na auditoria; auditoria ordenada, paginada e filtrada por origem, usuário e período. | me/status da própria sessão; detalhe com ajuste de cor e justificativa; ficha chamada duas vezes com médico e tentativa; sessão encerrada fora da equipe e na auditoria; auditoria ordenada, paginada e filtrada por origem, usuário e período. | `tests/api/test_acompanhamento.py` |
| CT-XANO-0142 | Mesmo código ao mesmo tempo abre uma sessão | INTEGRACAO | Duas verificações simultâneas do mesmo código: só uma entra (200), a outra é recusada (401) e só uma sessão é criada. | Duas verificações simultâneas do mesmo código: só uma entra (200), a outra é recusada (401) e só uma sessão é criada. | `frontend/tests/test_api_autenticacao.py` |
| CT-XANO-0143 | Painel público | INTEGRACAO | Painel sem token e sem dado pessoal; filtro por especialidade; Vermelha antes da Amarela; chamada igual à primeira prevista (CA11) e vira a atual; repetição como 2ª chamada; desistência sai da previsão. | Painel sem token e sem dado pessoal; filtro por especialidade; Vermelha antes da Amarela; chamada igual à primeira prevista (CA11) e vira a atual; repetição como 2ª chamada; desistência sai da previsão. | `tests/api/test_painel.py` |
| CT-XANO-0144 | Tamanho da previsão e ticket da triagem | INTEGRACAO | Com 3 aguardando, a previsão mostra só 3; com 8, exatamente 5; ticket chamado na triagem aparece e a rechamada volta como 2ª chamada (pacientes e ticket fictícios, apagados no fim). | Com 3 aguardando, a previsão mostra só 3; com 8, exatamente 5; ticket chamado na triagem aparece e a rechamada volta como 2ª chamada (pacientes e ticket fictícios, apagados no fim). | `tests/api/test_painel.py` |

## E2E público (navegador)

| ID | Teste | Tipo | Entrada | Saída esperada | Código |
|---|---|---|---|---|---|
| CT-REFLEX-0250 | Login abre aviso e volta | E2E | O link de privacidade abre o aviso público e o retorno mostra o login. | O link de privacidade abre o aviso público e o retorno mostra o login. | `tests/e2e/test_publico.py` |
| CT-REFLEX-0251 | Área interna sem sessão redireciona | E2E | Uma rota médica sem sessão não exibe a área protegida. | Uma rota médica sem sessão não exibe a área protegida. | `tests/e2e/test_publico.py` |

## Reflex (estado das telas, API simulada)

| ID | Teste | Tipo | Entrada | Saída esperada | Código |
|---|---|---|---|---|---|
| CT-REFLEX-0001 | Senha correta vai para o código sem token e sem guardar a senha | INTEGRACAO | — | Senha correta vai para o código sem token e sem guardar a senha. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0002 | Login recusado mostra mensagem da API e não guarda token | INTEGRACAO | — | Login recusado mostra mensagem da API e não guarda token. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0003 | Código correto guarda token e vai para a área do perfil | INTEGRACAO | — | Código correto guarda token e vai para a área do perfil. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0004 | Código recusado mostra mensagem e não guarda token | INTEGRACAO | — | Código recusado mostra mensagem e não guarda token. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0005 | Reenvio aceito avisa e reinicia o contador | INTEGRACAO | — | Reenvio aceito avisa e reinicia o contador. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0006 | Reenvio cedo demais mostra o tempo que falta | INTEGRACAO | — | Reenvio cedo demais mostra o tempo que falta. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0007 | Reenvio sem login pendente volta ao login | INTEGRACAO | — | Reenvio sem login pendente volta ao login. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0008 | Tela do código sem primeira etapa volta ao login | INTEGRACAO | — | Tela do código sem primeira etapa volta ao login. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0009 | Login sem configuracao avisa e não chama API | INTEGRACAO | — | Login sem configuracao avisa e não chama API. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0010 | Guarda sem token vai para o login sem chamar API | INTEGRACAO | — | Guarda sem token vai para o login sem chamar API. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0011 | Guarda com token expirado limpa sessão e avisa | INTEGRACAO | — | Guarda com token expirado limpa sessão e avisa. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0012 | Guarda com perfil errado redireciona para a propria área | INTEGRACAO | — | Guarda com perfil errado redireciona para a propria área. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0013 | Guarda com perfil certo libera a página | INTEGRACAO | — | Guarda com perfil certo libera a página. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0014 | Guarda guarda o tempo de inatividade vindo do auth me | INTEGRACAO | — | Guarda guarda o tempo de inatividade vindo do auth me. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0015 | Saída por inatividade encerra a sessão e avisa no login | INTEGRACAO | — | Saída por inatividade encerra a sessão e avisa no login. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0016 | Raiz leva usuário logado para a sua área | INTEGRACAO | — | Raiz leva usuário logado para a sua área. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0017 | Sair encerra sessão na API e descarta token | INTEGRACAO | — | Sair encerra sessão na API e descarta token. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0018 | Sair descarta token mesmo sem conexão | INTEGRACAO | — | Sair descarta token mesmo sem conexão. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0019 | Senha correta | INTEGRACAO | — | Senha correta. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0020 | Código correto | INTEGRACAO | — | Código correto. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0021 | Código recusado | INTEGRACAO | — | Código recusado. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0022 | Reenvio aceito | INTEGRACAO | — | Reenvio aceito. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0023 | Reenvio cedo | INTEGRACAO | — | Reenvio cedo. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0024 | Reenvio sem pendente | INTEGRACAO | — | Reenvio sem pendente. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0025 | Tela do código | INTEGRACAO | — | Tela do código. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0026 | Login recusado | INTEGRACAO | — | Login recusado. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0027 | Login sem configuracao | INTEGRACAO | — | Login sem configuracao. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0028 | Guarda sem token | INTEGRACAO | — | Guarda sem token. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0029 | Guarda token expirado | INTEGRACAO | — | Guarda token expirado. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0030 | Guarda perfil errado | INTEGRACAO | — | Guarda perfil errado. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0031 | Guarda perfil certo | INTEGRACAO | — | Guarda perfil certo. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0032 | Tempo de inatividade | INTEGRACAO | — | Tempo de inatividade. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0033 | Saída por inatividade | INTEGRACAO | — | Saída por inatividade. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0034 | Raiz | INTEGRACAO | — | Raiz. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0035 | Sair | INTEGRACAO | — | Sair. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0036 | Sair sem conexão | INTEGRACAO | — | Sair sem conexão. | `frontend/tests/test_auth_state.py` |
| CT-REFLEX-0037 | Especialidade nova envia sigla em maiusculas e edicao não envia sigla | UNITARIO | — | Especialidade nova envia sigla em maiusculas e edicao não envia sigla. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0038 | Médico novo envia senha e edicao não | UNITARIO | — | Médico novo envia senha e edicao não. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0039 | Recepção especialidade de referencia opcional | UNITARIO | — | Recepção especialidade de referencia opcional. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0040 | Sintoma converte pontuacao e mantem ordem dos destinos | UNITARIO | — | Sintoma converte pontuacao e mantem ordem dos destinos. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0041 | Marcar e desmarcar especialidade preserva a ordem | UNITARIO | — | Marcar e desmarcar especialidade preserva a ordem. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0042 | Ordem dos destinos em texto | UNITARIO | — | Ordem dos destinos em texto. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0043 | Filtro de situacao e busca sem acento | UNITARIO | — | Filtro de situacao e busca sem acento. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0044 | Salvar novo usa post e edicao usa patch no caminho do item | INTEGRACAO | — | Salvar novo usa post e edicao usa patch no caminho do item. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0045 | Erro ao salvar fica no dialogo | INTEGRACAO | — | Erro ao salvar fica no dialogo. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0046 | Desativar com código traduzido | INTEGRACAO | — | Desativar com código traduzido. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0047 | Sem conexão e sessão expirada | INTEGRACAO | — | Sem conexão e sessão expirada. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0048 | Linha de plantao diurno e noturno | UNITARIO | — | Linha de plantao diurno e noturno. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0049 | Novo plantao exige médico | UNITARIO | — | Novo plantao exige médico. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0050 | Plantao sobreposto mostra a mensagem | INTEGRACAO | — | Plantao sobreposto mostra a mensagem. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0051 | Escala 12x36 exige data final | UNITARIO | — | Escala 12x36 exige data final. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0052 | Escala 12x36 envia data final | INTEGRACAO | — | Escala 12x36 envia data final. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0053 | Plantao unico não envia data final | INTEGRACAO | — | Plantao unico não envia data final. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0054 | Linha de parametro com limites | UNITARIO | — | Linha de parametro com limites. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0055 | Parametro não numerico nem chama a API | INTEGRACAO | — | Parametro não numerico nem chama a API. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0056 | Set valor muda so a linha do parametro | UNITARIO | — | Set valor muda so a linha do parametro. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0057 | Linha de faixa | UNITARIO | — | Linha de faixa. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0058 | Faixa com limite não numerico | INTEGRACAO | — | Faixa com limite não numerico. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0059 | Faixa envia limite vazio como extremo aberto | INTEGRACAO | — | Faixa envia limite vazio como extremo aberto. | `frontend/tests/test_cadastros_state.py` |
| CT-REFLEX-0060 | Primeira chamada espera 30 segundos | INTEGRACAO | — | Primeira chamada espera 30 segundos. | `frontend/tests/test_chamada_manual.py` |
| CT-REFLEX-0061 | Segunda e terceira chamada esperam 10 segundos | INTEGRACAO | — | Segunda e terceira chamada esperam 10 segundos. | `frontend/tests/test_chamada_manual.py` |
| CT-REFLEX-0062 | Chamar novamente some na terceira chamada | INTEGRACAO | — | Chamar novamente some na terceira chamada. | `frontend/tests/test_chamada_manual.py` |
| CT-REFLEX-0063 | Sem parametros a tela não bloqueia e o Xano decide | INTEGRACAO | — | Sem parametros a tela não bloqueia e o Xano decide. | `frontend/tests/test_chamada_manual.py` |
| CT-REFLEX-0064 | Chamar novamente envia repetir | UNITARIO | — | Chamar novamente envia repetir. | `frontend/tests/test_chamada_manual.py` |
| CT-REFLEX-0065 | Não compareceu envia ausencia | UNITARIO | — | Não compareceu envia ausencia. | `frontend/tests/test_chamada_manual.py` |
| CT-REFLEX-0066 | Tela nunca avanca sozinha | UNITARIO | — | Tela nunca avanca sozinha. | `frontend/tests/test_chamada_manual.py` |
| CT-REFLEX-0067 | Datas Xano sao convertidas | UNITARIO | — | Datas Xano sao convertidas. | `frontend/tests/test_chamada_manual.py` |
| CT-REFLEX-0068 | Previa prepara fichas e tickets | INTEGRACAO | — | Previa prepara fichas e tickets. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0069 | Previa vazia | INTEGRACAO | — | Previa vazia. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0070 | Dispensar envia post e recarrega a previa | INTEGRACAO | — | Dispensar envia post e recarrega a previa. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0071 | Parametro inválido mostra o motivo sem recarregar | INTEGRACAO | — | Parametro inválido mostra o motivo sem recarregar. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0072 | Erro da API mantem a previa | INTEGRACAO | — | Erro da API mantem a previa. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0073 | Sem conexão | INTEGRACAO | — | Sem conexão. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0074 | Sessão expirada | INTEGRACAO | — | Sessão expirada. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0075 | Perfil recusado não altera nada | INTEGRACAO | — | Perfil recusado não altera nada. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0076 | Paginacao limites de 10 | UNITARIO | — | Paginacao limites de 10. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0077 | Paginacao troca de tamanho | UNITARIO | — | Paginacao troca de tamanho. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0078 | Ordem maior e menor tempo | UNITARIO | — | Ordem maior e menor tempo. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0079 | Página fora do intervalo fica no limite | UNITARIO | — | Página fora do intervalo fica no limite. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0080 | Recarregar volta para a primeira página | INTEGRACAO | — | Recarregar volta para a primeira página. | `frontend/tests/test_expiracao_state.py` |
| CT-REFLEX-0081 | Apenas ficha ativa do mesmo paciente bloqueia nova abertura | ESTATICO | Finais não entram no filtro; os três estados ativos continuam bloqueando. | Finais não entram no filtro; os três estados ativos continuam bloqueando. | `frontend/tests/test_ficha_abertura_contract.py` |
| CT-REFLEX-0082 | Carrega ficha catalogo sinais e classificação com token | INTEGRACAO | — | Carrega ficha catalogo sinais e classificação com token. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0083 | Sessão expirada encerra a sessão | INTEGRACAO | — | Sessão expirada encerra a sessão. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0084 | Erro de conexão | INTEGRACAO | — | Erro de conexão. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0085 | Seleção não duplica e desmarcacao remove | UNITARIO | — | Seleção não duplica e desmarcacao remove. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0086 | Disponiveis excluem selecionados e respeitam busca | UNITARIO | — | Disponiveis excluem selecionados e respeitam busca. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0087 | Adiciona e remove sintoma digitado | UNITARIO | — | Adiciona e remove sintoma digitado. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0088 | Sintoma digitado inválido e recusado na tela | UNITARIO | — | Sintoma digitado inválido e recusado na tela. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0089 | Limite de dez sintomas digitados | UNITARIO | — | Limite de dez sintomas digitados. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0090 | Rn04 recusada antes da requisicao | INTEGRACAO | — | Rn04 recusada antes da requisicao. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0091 | Sintoma digitado atende a rn04 | INTEGRACAO | — | Sintoma digitado atende a rn04. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0092 | Salvar entrega loading antes do patch | INTEGRACAO | — | Salvar entrega loading antes do patch. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0093 | Segunda invocacao e ignorada | INTEGRACAO | — | Segunda invocacao e ignorada. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0094 | Somente sintomas envia patch parcial e recarrega | INTEGRACAO | — | Somente sintomas envia patch parcial e recarrega. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0095 | Sintomas e observacao vazia preservam colecao final | INTEGRACAO | — | Sintomas e observacao vazia preservam colecao final. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0096 | Sinais vitais enviados como conjunto final | INTEGRACAO | — | Sinais vitais enviados como conjunto final. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0097 | Sinal vital não numerico e recusado na tela | INTEGRACAO | — | Sinal vital não numerico e recusado na tela. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0098 | Pendencias da classificação sao lidas | INTEGRACAO | — | Pendencias da classificação sao lidas. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0099 | Erro do backend libera loading | INTEGRACAO | — | Erro do backend libera loading. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0100 | Ajuste envia cor e justificativa e recarrega | INTEGRACAO | — | Ajuste envia cor e justificativa e recarrega. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0101 | Justificativa vazia e bloqueada na tela | INTEGRACAO | — | Justificativa vazia e bloqueada na tela. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0102 | Cor igual a calculada e bloqueada | INTEGRACAO | — | Cor igual a calculada e bloqueada. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0103 | Alteração não salva bloqueia o ajuste | INTEGRACAO | — | Alteração não salva bloqueia o ajuste. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0104 | Erro do backend fica no dialogo | INTEGRACAO | — | Erro do backend fica no dialogo. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0105 | Le o destino previsto | UNITARIO | — | Le o destino previsto. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0106 | Confirmacao envia post e abre o comprovante | INTEGRACAO | — | Confirmacao envia post e abre o comprovante. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0107 | Sem cor não confirma | INTEGRACAO | — | Sem cor não confirma. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0108 | Alteração não salva não confirma | INTEGRACAO | — | Alteração não salva não confirma. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0109 | Recusa do backend fica na ficha | INTEGRACAO | — | Recusa do backend fica na ficha. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0110 | Reimprimir abre o comprovante | UNITARIO | — | Reimprimir abre o comprovante. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0111 | Salvar com troca de senha mostra aviso | INTEGRACAO | — | Salvar com troca de senha mostra aviso. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0112 | Salvar sem troca de senha não mostra aviso | INTEGRACAO | — | Salvar sem troca de senha não mostra aviso. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0113 | Recusa sem cor abre o ajuste e envia tudo junto | INTEGRACAO | — | Recusa sem cor abre o ajuste e envia tudo junto. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0114 | Ajuste sem alteracoes usa o endpoint de prioridade e avisa a senha | INTEGRACAO | — | Ajuste sem alteracoes usa o endpoint de prioridade e avisa a senha. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0115 | Ficha chamada e recusada pelo backend | INTEGRACAO | — | Ficha chamada e recusada pelo backend. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0116 | Comprovante renderizado não expoe dados pessoais ou clinicos | UNITARIO | — | Comprovante renderizado não expoe dados pessoais ou clinicos. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0117 | Carrega so os campos do comprovante | INTEGRACAO | — | Carrega so os campos do comprovante. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0118 | Ficha sem senha ativa mostra mensagem | INTEGRACAO | — | Ficha sem senha ativa mostra mensagem. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0119 | Referencias vem das faixas de zero ponto | UNITARIO | — | Referencias vem das faixas de zero ponto. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0120 | Sem faixas todos os campos ficam sem referencia | UNITARIO | — | Sem faixas todos os campos ficam sem referencia. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0121 | Carregar guarda valores salvos e referencias | INTEGRACAO | — | Carregar guarda valores salvos e referencias. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0122 | Situacao vazio alterado e salvo | UNITARIO | — | Situacao vazio alterado e salvo. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0123 | Aviso de gestante e uma linha so | UNITARIO | — | Aviso de gestante e uma linha so. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0124 | Zero do servidor vira campo vazio e valor medido continua | INTEGRACAO | — | Zero do servidor vira campo vazio e valor medido continua. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0125 | Valor medido não e afetado | INTEGRACAO | — | Valor medido não e afetado. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0126 | Digitar no campo vazio tira o aviso | UNITARIO | — | Digitar no campo vazio tira o aviso. | `frontend/tests/test_ficha_state.py` |
| CT-REFLEX-0127 | Carregar prepara as linhas | INTEGRACAO | — | Carregar prepara as linhas. | `frontend/tests/test_fichas_do_dia_state.py` |
| CT-REFLEX-0128 | Cada filtro e finais agrupadas | INTEGRACAO | — | Cada filtro e finais agrupadas. | `frontend/tests/test_fichas_do_dia_state.py` |
| CT-REFLEX-0129 | Busca sem acento e maiusculas por nome e senha | INTEGRACAO | — | Busca sem acento e maiusculas por nome e senha. | `frontend/tests/test_fichas_do_dia_state.py` |
| CT-REFLEX-0130 | Filtro sem resultado devolve lista vazia | INTEGRACAO | — | Filtro sem resultado devolve lista vazia. | `frontend/tests/test_fichas_do_dia_state.py` |
| CT-REFLEX-0131 | Erro da API mantem a ultima lista | INTEGRACAO | — | Erro da API mantem a ultima lista. | `frontend/tests/test_fichas_do_dia_state.py` |
| CT-REFLEX-0132 | Sem conexão mantem a ultima lista | INTEGRACAO | — | Sem conexão mantem a ultima lista. | `frontend/tests/test_fichas_do_dia_state.py` |
| CT-REFLEX-0133 | Sessão expirada encerra a sessão | INTEGRACAO | — | Sessão expirada encerra a sessão. | `frontend/tests/test_fichas_do_dia_state.py` |
| CT-REFLEX-0134 | Chamada atualiza lista com senha e token | INTEGRACAO | — | Chamada atualiza lista com senha e token. | `frontend/tests/test_fila_tickets_state.py` |
| CT-REFLEX-0135 | Desistencia envia acao e recarrega | INTEGRACAO | — | Desistencia envia acao e recarrega. | `frontend/tests/test_fila_tickets_state.py` |
| CT-REFLEX-0136 | Identificacao preserva ticket | UNITARIO | — | Identificacao preserva ticket. | `frontend/tests/test_fila_tickets_state.py` |
| CT-REFLEX-0137 | Marcar presente envia acao e atualiza ticket | INTEGRACAO | — | Marcar presente envia acao e atualiza ticket. | `frontend/tests/test_fila_tickets_state.py` |
| CT-REFLEX-0138 | Resumo conta somente aguardando por tipo | UNITARIO | — | Resumo conta somente aguardando por tipo. | `frontend/tests/test_fila_tickets_state.py` |
| CT-REFLEX-0139 | Ticket do totem ganha tipo cor e hora de brasilia | INTEGRACAO | — | Ticket do totem ganha tipo cor e hora de brasilia. | `frontend/tests/test_fila_tickets_state.py` |
| CT-REFLEX-0140 | Tipo desconhecido não quebra a tela | INTEGRACAO | — | Tipo desconhecido não quebra a tela. | `frontend/tests/test_fila_tickets_state.py` |
| CT-REFLEX-0141 | Chamar não envia ID de ficha e mostra fila vazia | INTEGRACAO | — | Chamar não envia ID de ficha e mostra fila vazia. | `frontend/tests/test_medico_state.py` |
| CT-REFLEX-0142 | Repetir usa apenas ficha atribuida | INTEGRACAO | — | Repetir usa apenas ficha atribuida. | `frontend/tests/test_medico_state.py` |
| CT-REFLEX-0143 | Ocupado bloqueia requisicao repetida | INTEGRACAO | — | Ocupado bloqueia requisicao repetida. | `frontend/tests/test_medico_state.py` |
| CT-REFLEX-0144 | Carregar mostra estado do plantao | INTEGRACAO | — | Carregar mostra estado do plantao. | `frontend/tests/test_medico_state.py` |
| CT-REFLEX-0145 | Ativacao explicita envia status e recarrega cobertura | INTEGRACAO | — | Ativacao explicita envia status e recarrega cobertura. | `frontend/tests/test_medico_state.py` |
| CT-REFLEX-0146 | Intervalo retorna mensagem sem nova chamada | INTEGRACAO | — | Intervalo retorna mensagem sem nova chamada. | `frontend/tests/test_medico_state.py` |
| CT-REFLEX-0147 | Desistencia exige confirmacao antes de enviar | INTEGRACAO | — | Desistencia exige confirmacao antes de enviar. | `frontend/tests/test_medico_state.py` |
| CT-REFLEX-0148 | Comparecimento envia acao da ficha atribuida | INTEGRACAO | — | Comparecimento envia acao da ficha atribuida. | `frontend/tests/test_medico_state.py` |
| CT-REFLEX-0149 | Rota usa ID da ficha e carrega dados proprios | INTEGRACAO | — | Rota usa ID da ficha e carrega dados proprios. | `frontend/tests/test_medico_state.py` |
| CT-REFLEX-0150 | Ficha alheia e ID inválido não exibem dados | INTEGRACAO | — | Ficha alheia e ID inválido não exibem dados. | `frontend/tests/test_medico_state.py` |
| CT-REFLEX-0151 | Limite do Xano vira mensagem em portugues | UNITARIO | — | Limite do Xano vira mensagem em portugues. | `frontend/tests/test_mensagem_erro.py` |
| CT-REFLEX-0152 | 429 do nosso backend continua igual | UNITARIO | — | 429 do nosso backend continua igual. | `frontend/tests/test_mensagem_erro.py` |
| CT-REFLEX-0153 | Ficha ja na fila tem mensagem clara | UNITARIO | — | Ficha ja na fila tem mensagem clara. | `frontend/tests/test_mensagem_erro.py` |
| CT-REFLEX-0154 | Sinal vital inválido cita o campo | UNITARIO | — | Sinal vital inválido cita o campo. | `frontend/tests/test_mensagem_erro.py` |
| CT-REFLEX-0155 | Código desconhecido continua aparecendo | UNITARIO | — | Código desconhecido continua aparecendo. | `frontend/tests/test_mensagem_erro.py` |
| CT-REFLEX-0156 | Extrai o ID do caminho | UNITARIO | — | Extrai o ID do caminho. | `frontend/tests/test_mensagem_erro.py` |
| CT-REFLEX-0157 | Buscas sequenciais não reaproveitam dados do paciente anterior | INTEGRACAO | — | Buscas sequenciais não reaproveitam dados do paciente anterior. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0158 | CPF inválido descarta o paciente carregado | INTEGRACAO | — | CPF inválido descarta o paciente carregado. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0159 | Atualizar envia telefone vazio so quando usuário apaga | INTEGRACAO | — | Atualizar envia telefone vazio so quando usuário apaga. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0160 | Continuar cria ficha para paciente identificado | INTEGRACAO | — | Continuar cria ficha para paciente identificado. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0161 | Continuar reabre ficha em triagem existente | INTEGRACAO | — | Continuar reabre ficha em triagem existente. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0162 | Paciente ja na fila mostra aviso e atalho sem redirecionar[AGUARDANDO] | INTEGRACAO | Paciente ja na fila mostra aviso e atalho sem redirecionar | Paciente ja na fila mostra aviso e atalho sem redirecionar. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0163 | Abrir ficha atual sem ficha não redireciona | UNITARIO | — | Abrir ficha atual sem ficha não redireciona. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0164 | Nova busca descarta o atalho da ficha anterior | UNITARIO | — | Nova busca descarta o atalho da ficha anterior. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0165 | Continuar exibe erro de configuracao na tela de pacientes | INTEGRACAO | — | Continuar exibe erro de configuracao na tela de pacientes. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0166 | Cancelar limpa pesquisa e formulario sem chamar API | INTEGRACAO | — | Cancelar limpa pesquisa e formulario sem chamar API. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0167 | Operacoes de paciente enviam token e tratam 401 e 403 | INTEGRACAO | — | Operacoes de paciente enviam token e tratam 401 e 403. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0168 | Erros publicos de paciente sao preservados | INTEGRACAO | — | Erros publicos de paciente sao preservados. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0169 | Carregamento de env usa o arquivo do frontend | INTEGRACAO | — | Carregamento de env usa o arquivo do frontend. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0170 | Buscas sequenciais | INTEGRACAO | — | Buscas sequenciais. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0171 | CPF inválido | INTEGRACAO | — | CPF inválido. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0172 | Telefone vazio | INTEGRACAO | — | Telefone vazio. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0173 | Continuar | INTEGRACAO | — | Continuar. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0174 | Erro configuracao triagem | INTEGRACAO | — | Erro configuracao triagem. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0175 | Cancelar | INTEGRACAO | — | Cancelar. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0176 | Token e acesso | INTEGRACAO | — | Token e acesso. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0177 | Erros publicos | INTEGRACAO | — | Erros publicos. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0178 | Arquivo env | INTEGRACAO | — | Arquivo env. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0179 | Ticket associado | INTEGRACAO | — | Ticket associado. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0180 | Continuar encaminha ticket e limpa contexto apos sucesso | INTEGRACAO | — | Continuar encaminha ticket e limpa contexto apos sucesso. | `frontend/tests/test_paciente_state.py` |
| CT-REFLEX-0181 | Indicadores do dia | UNITARIO | — | Indicadores do dia. | `frontend/tests/test_painel_admin.py` |
| CT-REFLEX-0182 | Indicadores com fila vazia e cancelada | UNITARIO | — | Indicadores com fila vazia e cancelada. | `frontend/tests/test_painel_admin.py` |
| CT-REFLEX-0183 | Espera media abaixo de uma hora | UNITARIO | — | Espera media abaixo de uma hora. | `frontend/tests/test_painel_admin.py` |
| CT-REFLEX-0184 | Equipe medicos primeiro e por nome | UNITARIO | — | Equipe medicos primeiro e por nome. | `frontend/tests/test_painel_admin.py` |
| CT-REFLEX-0185 | Equipe conta medicos por status | UNITARIO | — | Equipe conta medicos por status. | `frontend/tests/test_painel_admin.py` |
| CT-REFLEX-0186 | Equipe vazia | UNITARIO | — | Equipe vazia. | `frontend/tests/test_painel_admin.py` |
| CT-REFLEX-0187 | Carregar busca a equipe | INTEGRACAO | — | Carregar busca a equipe. | `frontend/tests/test_painel_admin.py` |
| CT-REFLEX-0188 | Carregar mostra erro e mantem os dados | INTEGRACAO | — | Carregar mostra erro e mantem os dados. | `frontend/tests/test_painel_admin.py` |
| CT-REFLEX-0189 | Na espera soma pre triagem e fila medica | UNITARIO | — | Na espera soma pre triagem e fila medica. | `frontend/tests/test_plantao_state.py` |
| CT-REFLEX-0190 | Barra por cor soma 100 e rotula so o que cabe | UNITARIO | — | Barra por cor soma 100 e rotula so o que cabe. | `frontend/tests/test_plantao_state.py` |
| CT-REFLEX-0191 | Cor sem ficha não aparece e bloco estreito fica sem rotulo | UNITARIO | — | Cor sem ficha não aparece e bloco estreito fica sem rotulo. | `frontend/tests/test_plantao_state.py` |
| CT-REFLEX-0192 | Espera mais longa em minutos e horas | UNITARIO | — | Espera mais longa em minutos e horas. | `frontend/tests/test_plantao_state.py` |
| CT-REFLEX-0193 | Percurso do dia | UNITARIO | — | Percurso do dia. | `frontend/tests/test_plantao_state.py` |
| CT-REFLEX-0194 | Fila por especialidade ordenada e relativa a maior | UNITARIO | — | Fila por especialidade ordenada e relativa a maior. | `frontend/tests/test_plantao_state.py` |
| CT-REFLEX-0195 | Chegadas por hora ultimas 12 horas com a atual em destaque | UNITARIO | — | Chegadas por hora ultimas 12 horas com a atual em destaque. | `frontend/tests/test_plantao_state.py` |
| CT-REFLEX-0196 | Dia vazio | UNITARIO | — | Dia vazio. | `frontend/tests/test_plantao_state.py` |
| CT-REFLEX-0197 | Carregar busca fichas e tickets | INTEGRACAO | — | Carregar busca fichas e tickets. | `frontend/tests/test_plantao_state.py` |
| CT-REFLEX-0198 | Falha mantem os ultimos dados | INTEGRACAO | — | Falha mantem os ultimos dados. | `frontend/tests/test_plantao_state.py` |
| CT-REFLEX-0199 | Sessão expirada | INTEGRACAO | — | Sessão expirada. | `frontend/tests/test_plantao_state.py` |
| CT-REFLEX-0200 | CPF com 11 digitos mostra so do 4o ao 9o | UNITARIO | — | CPF com 11 digitos mostra so do 4o ao 9o. | `frontend/tests/test_privacidade.py` |
| CT-REFLEX-0201 | CPF ausente ou sem 11 digitos não aparece em parte | UNITARIO | — | CPF ausente ou sem 11 digitos não aparece em parte. | `frontend/tests/test_privacidade.py` |
| CT-REFLEX-0202 | Cabecalho da ficha usa o CPF mascarado | UNITARIO | — | Cabecalho da ficha usa o CPF mascarado. | `frontend/tests/test_privacidade.py` |
| CT-REFLEX-0203 | Página mostra o texto do arquivo do aviso | UNITARIO | — | Página mostra o texto do arquivo do aviso. | `frontend/tests/test_privacidade.py` |
| CT-REFLEX-0204 | Aviso tem as secoes obrigatorias para equipe e pacientes | UNITARIO | — | Aviso tem as secoes obrigatorias para equipe e pacientes. | `frontend/tests/test_privacidade.py` |
| CT-REFLEX-0205 | CPF 11 digitos | UNITARIO | — | CPF 11 digitos. | `frontend/tests/test_privacidade.py` |
| CT-REFLEX-0206 | CPF inválido | UNITARIO | — | CPF inválido. | `frontend/tests/test_privacidade.py` |
| CT-REFLEX-0207 | Cabecalho ficha | UNITARIO | — | Cabecalho ficha. | `frontend/tests/test_privacidade.py` |
| CT-REFLEX-0208 | Texto do aviso | UNITARIO | — | Texto do aviso. | `frontend/tests/test_privacidade.py` |
| CT-REFLEX-0209 | Secoes do aviso | UNITARIO | — | Secoes do aviso. | `frontend/tests/test_privacidade.py` |
| CT-REFLEX-0210 | Solicitar guarda o email e vai para o código | INTEGRACAO | — | Solicitar guarda o email e vai para o código. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0211 | Solicitar cedo demais fica na tela com a mensagem | INTEGRACAO | — | Solicitar cedo demais fica na tela com a mensagem. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0212 | Reenvio avisa e reinicia o contador | INTEGRACAO | — | Reenvio avisa e reinicia o contador. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0213 | Código correto guarda o código e vai para a nova senha | INTEGRACAO | — | Código correto guarda o código e vai para a nova senha. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0214 | Código inválido mostra a mensagem da tela a2b | INTEGRACAO | — | Código inválido mostra a mensagem da tela a2b. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0215 | Senhas diferentes sao recusadas sem chamar a API | INTEGRACAO | — | Senhas diferentes sao recusadas sem chamar a API. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0216 | Nova senha valida limpa o fluxo e mostra o sucesso | INTEGRACAO | — | Nova senha valida limpa o fluxo e mostra o sucesso. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0217 | Nova senha curta mostra a mensagem da API e mantem o código | INTEGRACAO | — | Nova senha curta mostra a mensagem da API e mantem o código. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0218 | Guardas das telas voltam para o inicio do fluxo | INTEGRACAO | — | Guardas das telas voltam para o inicio do fluxo. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0219 | Solicitar | INTEGRACAO | — | Solicitar. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0220 | Solicitar cedo | INTEGRACAO | — | Solicitar cedo. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0221 | Reenvio | INTEGRACAO | — | Reenvio. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0222 | Código correto | INTEGRACAO | — | Código correto. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0223 | Código inválido | INTEGRACAO | — | Código inválido. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0224 | Senhas diferentes | INTEGRACAO | — | Senhas diferentes. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0225 | Nova senha valida | INTEGRACAO | — | Nova senha valida. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0226 | Nova senha curta | INTEGRACAO | — | Nova senha curta. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0227 | Guardas | INTEGRACAO | — | Guardas. | `frontend/tests/test_senha_state.py` |
| CT-REFLEX-0228 | Emissao mostra o código e manda a chave so ao backend | INTEGRACAO | — | Emissao mostra o código e manda a chave so ao backend. | `frontend/tests/test_totem_state.py` |
| CT-REFLEX-0229 | Falha da API mostra erro sem tentar de novo | INTEGRACAO | — | Falha da API mostra erro sem tentar de novo. | `frontend/tests/test_totem_state.py` |
| CT-REFLEX-0230 | Sem conexão mostra erro sem tentar de novo | INTEGRACAO | — | Sem conexão mostra erro sem tentar de novo. | `frontend/tests/test_totem_state.py` |
| CT-REFLEX-0231 | Concluir volta para a escolha | UNITARIO | — | Concluir volta para a escolha. | `frontend/tests/test_totem_state.py` |
| CT-REFLEX-0232 | Emissao | INTEGRACAO | — | Emissao. | `frontend/tests/test_totem_state.py` |
| CT-REFLEX-0233 | Falha | INTEGRACAO | — | Falha. | `frontend/tests/test_totem_state.py` |
| CT-REFLEX-0234 | Sem conexão | INTEGRACAO | — | Sem conexão. | `frontend/tests/test_totem_state.py` |
| CT-REFLEX-0235 | Concluir | UNITARIO | — | Concluir. | `frontend/tests/test_totem_state.py` |
| CT-REFLEX-0236 | Linha usuário marca admin e cadastro incompleto | UNITARIO | — | Linha usuário marca admin e cadastro incompleto. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0237 | Filtro por perfil situacao e busca | UNITARIO | — | Filtro por perfil situacao e busca. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0238 | Corpo troca para médico leva crm especialidades e sala | UNITARIO | — | Corpo troca para médico leva crm especialidades e sala. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0239 | Corpo troca para recepção leva CPF e referencia opcional | UNITARIO | — | Corpo troca para recepção leva CPF e referencia opcional. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0240 | Corpo troca para admin leva so o perfil | UNITARIO | — | Corpo troca para admin leva so o perfil. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0241 | Criar admin envia senha e perfil e edicao não | UNITARIO | — | Criar admin envia senha e perfil e edicao não. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0242 | Criar recepção leva CPF e referencia | UNITARIO | — | Criar recepção leva CPF e referencia. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0243 | Editar médico leva crm especialidades e sala sem senha nem perfil | UNITARIO | — | Editar médico leva crm especialidades e sala sem senha nem perfil. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0244 | Novo usuário comeca como recepção | UNITARIO | — | Novo usuário comeca como recepção. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0245 | Troca oferece administrador para quem não e | UNITARIO | — | Troca oferece administrador para quem não e. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0246 | Abrir troca escolhe outro perfil e limpa dados | UNITARIO | — | Abrir troca escolhe outro perfil e limpa dados. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0247 | Trocar perfil envia patch e fecha | INTEGRACAO | — | Trocar perfil envia patch e fecha. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0248 | Trocar perfil mostra erro do ultimo admin e mantem dialogo | INTEGRACAO | — | Trocar perfil mostra erro do ultimo admin e mantem dialogo. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0249 | Mensagens das regras existem | UNITARIO | — | Mensagens das regras existem. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0252 | Alteração do admin mostra evento, alvo e valores | UNITARIO | A linha de auditoria mostra data/hora de Brasília, evento, registro e valores anterior e novo. | A linha de auditoria mostra data/hora de Brasília, evento, registro e valores anterior e novo. | `frontend/tests/test_auditoria_state.py` |
| CT-REFLEX-0253 | Carga automática aparece como Sistema | UNITARIO | Registro sem usuário da carga inicial aparece com responsável "Sistema". | Registro sem usuário da carga inicial aparece com responsável "Sistema". | `frontend/tests/test_auditoria_state.py` |
| CT-REFLEX-0254 | Login e chamada traduzidos | UNITARIO | Eventos de acesso e de chamada aparecem com texto legível. | Eventos de acesso e de chamada aparecem com texto legível. | `frontend/tests/test_auditoria_state.py` |
| CT-REFLEX-0255 | Parâmetros só levam filtros preenchidos | UNITARIO | A consulta envia só os filtros preenchidos e a página mínima 1. | A consulta envia só os filtros preenchidos e a página mínima 1. | `frontend/tests/test_auditoria_state.py` |
| CT-REFLEX-0256 | Filtro volta para a primeira página e consulta | UNITARIO | Trocar um filtro consulta de novo a partir da página 1. | Trocar um filtro consulta de novo a partir da página 1. | `frontend/tests/test_auditoria_state.py` |
| CT-REFLEX-0257 | CSV tem cabeçalho, ponto e vírgula e BOM | UNITARIO | O CSV exportado abre no Excel em português: BOM, separador ; e cabeçalho fixo. | O CSV exportado abre no Excel em português: BOM, separador ; e cabeçalho fixo. | `frontend/tests/test_auditoria_state.py` |
| CT-REFLEX-0258 | Exportar busca todas as páginas | UNITARIO | A exportação reúne todas as páginas do filtro atual, não só a aberta. | A exportação reúne todas as páginas do filtro atual, não só a aberta. | `frontend/tests/test_auditoria_state.py` |
| CT-REFLEX-0259 | Troca para Recepção sem CPF avisa sem chamar a API | UNITARIO | Trocar para Recepção/Triagem sem CPF mostra "Informe o CPF." e não chama a API. | Trocar para Recepção/Triagem sem CPF mostra "Informe o CPF." e não chama a API. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0260 | Dados obrigatórios por perfil | UNITARIO | Médico exige CRM e especialidade; Recepção exige CPF; Administrador não exige dados extras. | Médico exige CRM e especialidade; Recepção exige CPF; Administrador não exige dados extras. | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0261 | Missing param do Xano vira mensagem em português | UNITARIO | "Missing param: cpf" do Xano aparece como "Preencha o campo CPF." | "Missing param: cpf" do Xano aparece como "Preencha o campo CPF." | `frontend/tests/test_usuarios_state.py` |
| CT-REFLEX-0266 | Espera em minutos e horas | UNITARIO | O tempo de espera desde a chegada aparece em minutos ou em horas e minutos. | O tempo de espera desde a chegada aparece em minutos ou em horas e minutos. | `frontend/tests/test_acompanhamento_state.py` |
| CT-REFLEX-0267 | Linha mostra médico, tentativa e posição | UNITARIO | Chamada mostra médico e tentativa; aguardando mostra a posição prevista na fila. | Chamada mostra médico e tentativa; aguardando mostra a posição prevista na fila. | `frontend/tests/test_acompanhamento_state.py` |
| CT-REFLEX-0268 | Ordem da fila geral | UNITARIO | Chamadas primeiro, depois aguardando por especialidade e posição prevista, depois em triagem. | Chamadas primeiro, depois aguardando por especialidade e posição prevista, depois em triagem. | `frontend/tests/test_acompanhamento_state.py` |
| CT-REFLEX-0269 | Filtros vazios não vão para a API | UNITARIO | A consulta envia só os filtros escolhidos. | A consulta envia só os filtros escolhidos. | `frontend/tests/test_acompanhamento_state.py` |
| CT-REFLEX-0270 | Detalhe mostra ajuste, chamadas e histórico | UNITARIO | O detalhe mostra o ajuste com justificativa, as tentativas de chamada e o histórico. | O detalhe mostra o ajuste com justificativa, as tentativas de chamada e o histórico. | `frontend/tests/test_acompanhamento_state.py` |
| CT-REFLEX-0271 | Trocar filtro consulta de novo | UNITARIO | Trocar um filtro da fila geral consulta o backend com o filtro novo. | Trocar um filtro da fila geral consulta o backend com o filtro novo. | `frontend/tests/test_acompanhamento_state.py` |
| CT-REFLEX-0272 | Destino com e sem Sala | UNITARIO | Mostra 'Especialidade · Sala N' quando o médico tem Sala e só a especialidade quando não tem. | Mostra 'Especialidade · Sala N' quando o médico tem Sala e só a especialidade quando não tem. | `frontend/tests/test_painel_state.py` |
| CT-REFLEX-0273 | Indicação da tentativa | UNITARIO | A chamada atual sempre indica a tentativa: 1ª, 2ª ou 3ª chamada. | A chamada atual sempre indica a tentativa: 1ª, 2ª ou 3ª chamada. | `frontend/tests/test_painel_state.py` |
| CT-REFLEX-0274 | Formatação do painel para a TV | UNITARIO | Senha, destino, cor, ticket da triagem e no máximo 4 últimas chamadas, com especialidade e Sala em colunas; sem previsão. | Senha, destino, cor, ticket da triagem e no máximo 4 últimas chamadas, com especialidade e Sala em colunas; sem previsão. | `frontend/tests/test_painel_state.py` |
| CT-REFLEX-0275 | Painel sem chamadas | UNITARIO | Sem chamada atual, ticket ou previsão, o painel monta vazio sem erro. | Sem chamada atual, ticket ou previsão, o painel monta vazio sem erro. | `frontend/tests/test_painel_state.py` |
| CT-REFLEX-0276 | Detecção de chamada nova | UNITARIO | No painel dos médicos só a chamada médica nova ou repetida dispara destaque e som; no da triagem, só o ticket chamado ou rechamado. | No painel dos médicos só a chamada médica nova ou repetida dispara destaque e som; no da triagem, só o ticket chamado ou rechamado. | `frontend/tests/test_painel_state.py` |
| CT-REFLEX-0277 | Filtro de especialidades pelo endereço | UNITARIO | ?especialidades=car, ort vira CAR,ORT; vazio exibe todas. | ?especialidades=car, ort vira CAR,ORT; vazio exibe todas. | `frontend/tests/test_painel_state.py` |
| CT-REFLEX-0278 | Tela do painel pela rota | UNITARIO | /painel/triagem abre o painel da triagem; /painel/medico, o dos consultórios. | /painel/triagem abre o painel da triagem; /painel/medico, o dos consultórios. | `frontend/tests/test_painel_state.py` |
| CT-STATUS-S4-001 | Consulta status real da api sem escrita | INTEGRACAO | — | Consulta status real da api sem escrita. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-002 | Altera tres estados manuais somente apos confirmacao | INTEGRACAO | — | Altera tres estados manuais somente apos confirmacao. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-003 | Estado manual invalido inclusive em atendimento nao envia | INTEGRACAO | — | Estado manual invalido inclusive em atendimento nao envia. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-004 | Ausencia de token redireciona sem http | INTEGRACAO | — | Ausencia de token redireciona sem http. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-005 | Outros perfis nao consultam nem alteram status da recepcao | INTEGRACAO | — | Outros perfis nao consultam nem alteram status da recepcao. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-006 | 401 encerra sessao e redireciona | INTEGRACAO | — | 401 encerra sessao e redireciona. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-007 | 403 preserva status anterior sem confirmar mudanca | INTEGRACAO | — | 403 preserva status anterior sem confirmar mudanca. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-008 | Get nao publicado mostra indisponibilidade sem status ficticio | INTEGRACAO | — | Get nao publicado mostra indisponibilidade sem status ficticio. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-009 | Erro publico do servidor nao confirma | INTEGRACAO | — | Erro publico do servidor nao confirma. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-010 | Timeout nao repete e nao presume status anterior | INTEGRACAO | — | Timeout nao repete e nao presume status anterior. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-011 | Falha de rede nao repete | INTEGRACAO | — | Falha de rede nao repete. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-012 | Respostas inesperadas nao confirmam nem repetem | INTEGRACAO | — | Respostas inesperadas nao confirmam nem repetem. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-013 | Ambiente ausente nao chama http | INTEGRACAO | — | Ambiente ausente nao chama http. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-014 | Processamento bloqueia reentrada de consulta e alteracao | INTEGRACAO | — | Processamento bloqueia reentrada de consulta e alteracao. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-015 | Guardiao ja esta ativo durante requisicao | INTEGRACAO | — | Guardiao ja esta ativo durante requisicao. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-016 | Consulta invalida nao reutiliza status de sessao anterior | INTEGRACAO | — | Consulta invalida nao reutiliza status de sessao anterior. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-017 | Seletor nao oferece em atendimento e nao envia ao renderizar | INTEGRACAO | — | Seletor nao oferece em atendimento e nao envia ao renderizar. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-018 | Pagina recepcao preserva protecao de perfil | INTEGRACAO | — | Pagina recepcao preserva protecao de perfil. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-019 | Contrato get status e apenas leitura da propria sessao | ESTATICO | — | Contrato get status e apenas leitura da propria sessao. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-020 | Contrato status manual recusa admin e estado automatico | ESTATICO | — | Contrato status manual recusa admin e estado automatico. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-021 | Contrato medico inicia indisponivel recepcao disponivel | ESTATICO | — | Contrato medico inicia indisponivel recepcao disponivel. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-022 | Contrato chamada e comparecimento preservam status automatico | ESTATICO | — | Contrato chamada e comparecimento preservam status automatico. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-023 | Medico em pausa recusado sem sucesso ou repeticao | INTEGRACAO | — | Medico em pausa recusado sem sucesso ou repeticao. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-024 | Comparecimento em pausa atualiza status pelo retorno do servidor | INTEGRACAO | — | Comparecimento em pausa atualiza status pelo retorno do servidor. | `frontend/tests/test_status_equipe.py` |
| CT-STATUS-S4-025 | Proxima chamada confirmada restaura disponivel | INTEGRACAO | — | Proxima chamada confirmada restaura disponivel. | `frontend/tests/test_status_equipe.py` |

## Xano funções puras (testes nativos remotos)

| ID | Teste | Tipo | Entrada | Saída esperada | Código |
|---|---|---|---|---|---|
| CT-XANO-0001 | Vermelha tardia e ciclo preservado | UNITARIO | — | Vermelha tardia e ciclo preservado. | `tests/api/test_ordenacao.py` |
| CT-XANO-0002 | Ciclo amarela amarela azul | UNITARIO | — | Ciclo amarela amarela azul. | `tests/api/test_ordenacao.py` |
| CT-XANO-0003 | Ciclo respeita quantidades configuradas | UNITARIO | — | Ciclo respeita quantidades configuradas. | `tests/api/test_ordenacao.py` |
| CT-XANO-0004 | Vermelha intercalada não avanca | UNITARIO | — | Vermelha intercalada não avanca. | `tests/api/test_ordenacao.py` |
| CT-XANO-0005 | Cor alternativa não avanca | UNITARIO | — | Cor alternativa não avanca. | `tests/api/test_ordenacao.py` |
| CT-XANO-0006 | Prioritarios dentro da cor sem precedencia entre tipos | UNITARIO | — | Prioritarios dentro da cor sem precedencia entre tipos. | `tests/api/test_ordenacao.py` |
| CT-XANO-0007 | Condicao prioritaria não ultrapassa cor | UNITARIO | — | Condicao prioritaria não ultrapassa cor. | `tests/api/test_ordenacao.py` |
| CT-XANO-0008 | Empate de chegada por ID | UNITARIO | — | Empate de chegada por ID. | `tests/api/test_ordenacao.py` |
| CT-XANO-0009 | Reentrada vai ao fim sem mudar chegada | UNITARIO | — | Reentrada vai ao fim sem mudar chegada. | `tests/api/test_ordenacao.py` |
| CT-XANO-0010 | Estados fora da fila sao excluidos | UNITARIO | — | Estados fora da fila sao excluidos. | `tests/api/test_ordenacao.py` |
| CT-XANO-0011 | Previsao tres e sete e nova vermelha | UNITARIO | — | Previsao tres e sete e nova vermelha. | `tests/api/test_ordenacao.py` |
| CT-XANO-0012 | Previsao não retorna dados pessoais | UNITARIO | — | Previsao não retorna dados pessoais. | `tests/api/test_ordenacao.py` |
| CT-XANO-0013 | Cobertura exclui pausa ausencia e inativos | UNITARIO | — | Cobertura exclui pausa ausencia e inativos. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0014 | Cobertura exige plantao sessão e usuário ativos | UNITARIO | — | Cobertura exige plantao sessão e usuário ativos. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0015 | Matriz cor propria contra descoberta | UNITARIO | — | Matriz cor propria contra descoberta. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0016 | Desempate entre descobertas por ordem efetiva e ID | UNITARIO | — | Desempate entre descobertas por ordem efetiva e ID. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0017 | Vermelha propria mais antiga e menor ID | UNITARIO | — | Vermelha propria mais antiga e menor ID. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0018 | Rodizio proprio e salto de fila vazia | UNITARIO | — | Rodizio proprio e salto de fila vazia. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0019 | Rodizio preserva ciclo interno de cada fila | UNITARIO | — | Rodizio preserva ciclo interno de cada fila. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0020 | Descoberta mais grave supera propria | UNITARIO | — | Descoberta mais grave supera propria. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0021 | Empate de cor favorece propria | UNITARIO | — | Empate de cor favorece propria. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0022 | Sem propria prioriza descoberta mesmo com coberta mais grave | UNITARIO | — | Sem propria prioriza descoberta mesmo com coberta mais grave. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0023 | Fallback coberta e desempates descoberta | UNITARIO | — | Fallback coberta e desempates descoberta. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0024 | Fila vazia | UNITARIO | — | Fila vazia. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0025 | Politica completa com duas proprias e terceira fila | UNITARIO | — | Politica completa com duas proprias e terceira fila. | `tests/api/test_selecao_entre_filas.py` |
| CT-XANO-0026 | Bordas 1: PA 90, FC 90, FR 8, T 35.0, SpO2 91 | UNITARIO | — | Bordas 1: PA 90, FC 90, FR 8, T 35.0, SpO2 91. Valores esperados: PA sistólica = 3; FC = 0; FR = 3; Temperatura = 3; SpO2 = 3. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0027 | Bordas 2: PA 91, FC 91, FR 9, T 35.1, SpO2 92 | UNITARIO | — | Bordas 2: PA 91, FC 91, FR 9, T 35.1, SpO2 92. Valores esperados: PA sistólica = 2; FC = 1; FR = 1; Temperatura = 1; SpO2 = 2. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0028 | Bordas 3: PA 100, FC 110, FR 11, T 36.0, SpO2 93 | UNITARIO | — | Bordas 3: PA 100, FC 110, FR 11, T 36.0, SpO2 93. Valores esperados: PA sistólica = 2; FC = 1; FR = 1; Temperatura = 1; SpO2 = 2. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0029 | Bordas 4: PA 101, FC 111, FR 12, T 36.1, SpO2 94 | UNITARIO | — | Bordas 4: PA 101, FC 111, FR 12, T 36.1, SpO2 94. Valores esperados: PA sistólica = 1; FC = 2; FR = 0; Temperatura = 0; SpO2 = 1. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0030 | Bordas 5: PA 110, FC 130, FR 20, T 38.0, SpO2 95 | UNITARIO | — | Bordas 5: PA 110, FC 130, FR 20, T 38.0, SpO2 95. Valores esperados: PA sistólica = 1; FC = 2; FR = 0; Temperatura = 0; SpO2 = 1. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0031 | Bordas 6: PA 111, FC 131, FR 21, T 38.1, SpO2 96 | UNITARIO | — | Bordas 6: PA 111, FC 131, FR 21, T 38.1, SpO2 96. Valores esperados: PA sistólica = 0; FC = 3; FR = 2; Temperatura = 1; SpO2 = 0. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0032 | Bordas 7: PA 219, FC 51, FR 24, T 39.0 | UNITARIO | — | Bordas 7: PA 219, FC 51, FR 24, T 39.0. Valores esperados: PA sistólica = 0; FC = 0; FR = 2; Temperatura = 1; SpO2 = 0. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0033 | Bordas 8: PA 220, FC 50, FR 25, T 39.1 | UNITARIO | — | Bordas 8: PA 220, FC 50, FR 25, T 39.1. Valores esperados: PA sistólica = 3; FC = 1; FR = 3; Temperatura = 2; SpO2 = 0. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0034 | Bordas 9: FC 41 | UNITARIO | — | Bordas 9: FC 41. Valores esperados: FC = 1. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0035 | Bordas 10: FC 40 | UNITARIO | — | Bordas 10: FC 40. Valores esperados: FC = 3. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0036 | Glicemia 53 sem gravidade soma 2 e fica Azul | UNITARIO | — | Glicemia 53 sem gravidade soma 2 e fica Azul. Valores esperados: Glicemia = 2; escore total = 4; item crítico = falso; prioridade calculada = "AZUL". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0037 | Glicemia 53 com gravidade gera Vermelha | UNITARIO | — | Glicemia 53 com gravidade gera Vermelha. Valores esperados: Glicemia = 3; item crítico = verdadeiro; prioridade calculada = "VERMELHA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0038 | Glicemia 54 com gravidade soma 2 | UNITARIO | — | Glicemia 54 com gravidade soma 2. Valores esperados: Glicemia = 2. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0039 | Glicemia 59 sem gravidade soma 1 | UNITARIO | — | Glicemia 59 sem gravidade soma 1. Valores esperados: Glicemia = 1. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0040 | Glicemia 60 soma 0 | UNITARIO | — | Glicemia 60 soma 0. Valores esperados: Glicemia = 0. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0041 | Glicemia não medida não bloqueia | UNITARIO | — | Glicemia não medida não bloqueia. Valores esperados: Glicemia = nulo; prioridade calculada = "AZUL". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0042 | Escore 4 sem item 3 é Azul | UNITARIO | — | Escore 4 sem item 3 é Azul. Valores esperados: escore total = 4; prioridade calculada = "AZUL". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0043 | Escore 5 sem item 3 é Amarela | UNITARIO | — | Escore 5 sem item 3 é Amarela. Valores esperados: escore total = 5; prioridade calculada = "AMARELA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0044 | Escore 9 sem item 3 é Amarela | UNITARIO | — | Escore 9 sem item 3 é Amarela. Valores esperados: escore total = 9; prioridade calculada = "AMARELA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0045 | Escore 10 sem item 3 é Vermelha | UNITARIO | — | Escore 10 sem item 3 é Vermelha. Valores esperados: escore total = 10; item crítico = falso; prioridade calculada = "VERMELHA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0046 | 5.4 febre 1 + mal-estar 1 = 2 Azul | UNITARIO | — | 5.4 febre 1 + mal-estar 1 = 2 Azul. Valores esperados: escore total = 2; prioridade calculada = "AZUL". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0047 | 5.4 sintomas 2+2+2 e sinais 2 = 8 Amarela | UNITARIO | — | 5.4 sintomas 2+2+2 e sinais 2 = 8 Amarela. Valores esperados: escore sintomas = 6; escore sinais = 2; escore total = 8; prioridade calculada = "AMARELA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0048 | 5.4 sintomas 2+2+2+2 e sinais 2 = 10 Vermelha | UNITARIO | — | 5.4 sintomas 2+2+2+2 e sinais 2 = 10 Vermelha. Valores esperados: escore total = 10; prioridade calculada = "VERMELHA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0049 | Convulsão isolada de 3 pontos é Vermelha pela exceção | UNITARIO | — | Convulsão isolada de 3 pontos é Vermelha pela exceção. Valores esperados: escore total = 3; item crítico = verdadeiro; prioridade calculada = "VERMELHA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0050 | Sintoma digitado de 2 pontos soma ao escore | UNITARIO | — | Sintoma digitado de 2 pontos soma ao escore. Valores esperados: escore total = 3; prioridade calculada = "AZUL". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0051 | Sintoma digitado de 3 pontos é Vermelha | UNITARIO | — | Sintoma digitado de 3 pontos é Vermelha. Valores esperados: item crítico = verdadeiro; prioridade calculada = "VERMELHA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0052 | SpO2 91 é Vermelha pela exceção | UNITARIO | — | SpO2 91 é Vermelha pela exceção. Valores esperados: item crítico = verdadeiro; prioridade calculada = "VERMELHA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0053 | Temperatura 39.1 não gera Vermelha sozinha | UNITARIO | — | Temperatura 39.1 não gera Vermelha sozinha. Valores esperados: escore total = 3; item crítico = falso; prioridade calculada = "AZUL". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0054 | SpO2 ausente bloqueia o cálculo | UNITARIO | — | SpO2 ausente bloqueia o cálculo. Valores esperados: prioridade calculada = nulo; escore total = nulo. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0055 | Paciente de 10 anos exige classificação manual | UNITARIO | — | Paciente de 10 anos exige classificação manual. Valores esperados: prioridade calculada = nulo; tabela adulta = falso; condicao prioritaria = "CRIANCA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0056 | Paciente de 16 anos é calculado | UNITARIO | — | Paciente de 16 anos é calculado. Valores esperados: tabela adulta = verdadeiro; prioridade calculada = "AZUL"; condicao prioritaria = "NENHUMA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0057 | Gestante exige classificação manual | UNITARIO | — | Gestante exige classificação manual. Valores esperados: prioridade calculada = nulo; condicao prioritaria = "GESTANTE". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0058 | Gestante de 60 anos registra GESTANTE | UNITARIO | — | Gestante de 60 anos registra GESTANTE. Valores esperados: condicao prioritaria = "GESTANTE". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0059 | Idoso de 68 anos mantém a cor do escore | UNITARIO | — | Idoso de 68 anos mantém a cor do escore. Valores esperados: condicao prioritaria = "IDOSO"; prioridade calculada = "AZUL". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0060 | 12 anos não é criança | UNITARIO | — | 12 anos não é criança. Valores esperados: condicao prioritaria = "NENHUMA"; tabela adulta = falso. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0061 | 11 anos é criança | UNITARIO | — | 11 anos é criança. Valores esperados: condicao prioritaria = "CRIANCA". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0062 | Sem faixas configuradas bloqueia | UNITARIO | — | Sem faixas configuradas bloqueia. Valores esperados: prioridade calculada = nulo. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0063 | Sem sintoma nem observação bloqueia | UNITARIO | — | Sem sintoma nem observação bloqueia. Valores esperados: prioridade calculada = nulo. | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0064 | Só observação é aceita | UNITARIO | — | Só observação é aceita. Valores esperados: escore total = 0; prioridade calculada = "AZUL". | `backend/xano/function/classificacao/pontuar.xs` |
| CT-XANO-0065 | Tem as 30 faixas | UNITARIO | — | Tem as 30 faixas. Valores esperados: total = 30. | `backend/xano/function/classificacao/faixas_padrao.xs` |
| CT-XANO-0066 | Um sintoma de Cardiologia | UNITARIO | — | Um sintoma de Cardiologia. Valores esperados: especialidade id = 1; motivo = "SINTOMAS". | `backend/xano/function/direcionamento/escolher_destino.xs` |
| CT-XANO-0067 | Maior pontuação individual vence (Neurologia 3 contra Cardiologia 2) | UNITARIO | — | Maior pontuação individual vence (Neurologia 3 contra Cardiologia 2). Valores esperados: especialidade id = 3. | `backend/xano/function/direcionamento/escolher_destino.xs` |
| CT-XANO-0068 | Empate na maior decidido pela soma (Cardiologia 2+2 contra Clínica 2) | UNITARIO | — | Empate na maior decidido pela soma (Cardiologia 2+2 contra Clínica 2). Valores esperados: especialidade id = 1. | `backend/xano/function/direcionamento/escolher_destino.xs` |
| CT-XANO-0069 | Empate decidido pela fila menor | UNITARIO | — | Empate decidido pela fila menor. Valores esperados: especialidade id = 3. | `backend/xano/function/direcionamento/escolher_destino.xs` |
| CT-XANO-0070 | Empate total decidido pelo menor ID | UNITARIO | — | Empate total decidido pelo menor ID. Valores esperados: especialidade id = 3. | `backend/xano/function/direcionamento/escolher_destino.xs` |
| CT-XANO-0071 | 11 anos vai para Pediatria | UNITARIO | — | 11 anos vai para Pediatria. Valores esperados: especialidade id = 5; motivo = "PEDIATRIA". | `backend/xano/function/direcionamento/escolher_destino.xs` |
| CT-XANO-0072 | 12 anos segue os sintomas | UNITARIO | — | 12 anos segue os sintomas. Valores esperados: especialidade id = 3. | `backend/xano/function/direcionamento/escolher_destino.xs` |
| CT-XANO-0073 | Sem sintoma do catálogo vai para a especialidade padrão | UNITARIO | — | Sem sintoma do catálogo vai para a especialidade padrão. Valores esperados: especialidade id = 2; motivo = "PADRAO". | `backend/xano/function/direcionamento/escolher_destino.xs` |
| CT-XANO-0074 | Sem especialidade padrão configurada | UNITARIO | — | Sem especialidade padrão configurada. Valores esperados: especialidade id = nulo; motivo = "PADRAO_NAO_CONFIGURADO". | `backend/xano/function/direcionamento/escolher_destino.xs` |
| CT-XANO-0075 | Primeira Vermelha de Clínica Geral | UNITARIO | — | Primeira Vermelha de Clínica Geral. | `backend/xano/function/direcionamento/formatar_senha.xs` |
| CT-XANO-0076 | Amarela de Cardiologia número 42 | UNITARIO | — | Amarela de Cardiologia número 42. | `backend/xano/function/direcionamento/formatar_senha.xs` |
| CT-XANO-0077 | Azul acima de 999 | UNITARIO | — | Azul acima de 999. | `backend/xano/function/direcionamento/formatar_senha.xs` |
| CT-XANO-0078 | Nada muda mantém a senha | UNITARIO | — | Nada muda mantém a senha. Valores esperados: acao = "MANTER"; senha = "[REDACTED]". | `backend/xano/function/direcionamento/senha_reavaliada.xs` |
| CT-XANO-0079 | Só a cor muda troca a letra e mantém o número | UNITARIO | — | Só a cor muda troca a letra e mantém o número. Valores esperados: acao = "TROCAR_COR"; senha = "[REDACTED]". | `backend/xano/function/direcionamento/senha_reavaliada.xs` |
| CT-XANO-0080 | Especialidade muda pede número novo | UNITARIO | — | Especialidade muda pede número novo. Valores esperados: acao = "NOVO_NUMERO"; senha = [REDACTED] | `backend/xano/function/direcionamento/senha_reavaliada.xs` |
| CT-XANO-0081 | Especialidade e cor mudam pede número novo | UNITARIO | — | Especialidade e cor mudam pede número novo. Valores esperados: acao = "NOVO_NUMERO". | `backend/xano/function/direcionamento/senha_reavaliada.xs` |
| CT-XANO-0082 | Normaliza CPF válido com pontuação | UNITARIO | — | Normaliza CPF válido com pontuação. | `backend/xano/function/pacientes/normalizar_cpf.xs` |
| CT-XANO-0083 | Aceita CPF válido sem pontuação | UNITARIO | — | Aceita CPF válido sem pontuação. | `backend/xano/function/pacientes/normalizar_cpf.xs` |
| CT-XANO-0084 | Recusa sequência repetida | UNITARIO | — | Recusa sequência repetida. | `backend/xano/function/pacientes/normalizar_cpf.xs` |
| CT-XANO-0085 | Recusa tamanho inválido | UNITARIO | — | Recusa tamanho inválido. | `backend/xano/function/pacientes/normalizar_cpf.xs` |
| CT-XANO-0086 | Recusa dígitos verificadores inválidos | UNITARIO | — | Recusa dígitos verificadores inválidos. | `backend/xano/function/pacientes/normalizar_cpf.xs` |
| CT-XANO-0087 | Limpa telefone com null | UNITARIO | — | Limpa telefone com null. Valores esperados: valor = nulo; alterado = verdadeiro. | `backend/xano/function/pacientes/normalizar_telefone.xs` |
| CT-XANO-0088 | Limpa telefone com texto vazio | UNITARIO | — | Limpa telefone com texto vazio. Valores esperados: valor = nulo; alterado = verdadeiro. | `backend/xano/function/pacientes/normalizar_telefone.xs` |
| CT-XANO-0089 | Telefone vazio já está ausente | UNITARIO | — | Telefone vazio já está ausente. Valores esperados: valor = nulo; alterado = falso. | `backend/xano/function/pacientes/normalizar_telefone.xs` |
| CT-XANO-0090 | Mesmo telefone não é alteração | UNITARIO | — | Mesmo telefone não é alteração. Valores esperados: alterado = falso. | `backend/xano/function/pacientes/normalizar_telefone.xs` |
| CT-XANO-0091 | Telefone novo é alteração | UNITARIO | — | Telefone novo é alteração. Valores esperados: alterado = verdadeiro. | `backend/xano/function/pacientes/normalizar_telefone.xs` |
| CT-XANO-0092 | Vermelha tardia precede amarela sem avançar ciclo | UNITARIO | — | Vermelha tardia precede amarela sem avançar ciclo. Valores esperados: id = 2; próxima posição = 2. | `backend/xano/function/fila/proxima_ficha.xs` |
| CT-XANO-0093 | Cor alternativa não avança ciclo | UNITARIO | — | Cor alternativa não avança ciclo. Valores esperados: id = 1; próxima posição = 1. | `backend/xano/function/fila/proxima_ficha.xs` |
| CT-XANO-0094 | Condição prioritária vence chegada dentro da cor | UNITARIO | — | Condição prioritária vence chegada dentro da cor. Valores esperados: id = 2. | `backend/xano/function/fila/proxima_ficha.xs` |
| CT-XANO-0095 | Reentrada usa ordem efetiva | UNITARIO | — | Reentrada usa ordem efetiva. Valores esperados: id = 2. | `backend/xano/function/fila/proxima_ficha.xs` |
| CT-XANO-0096 | Três fichas retornam três senhas sem dados pessoais | UNITARIO | — | Três fichas retornam três senhas sem dados pessoais. | `backend/xano/function/fila/prever_fila.xs` |
| CT-XANO-0097 | Pausa e ausência não cobrem; atendimento cobre | UNITARIO | — | Pausa e ausência não cobrem; atendimento cobre. | `backend/xano/function/fila/avaliar_cobertura.xs` |

## Xano estático (contratos lidos do código)

| ID | Teste | Tipo | Entrada | Saída esperada | Código |
|---|---|---|---|---|---|
| CT-XANO-0122 | Nenhum endpoint grava no histórico diretamente | ESTATICO | — | Nenhum endpoint grava no histórico diretamente. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0123 | So a funcao de auditoria grava no histórico | ESTATICO | — | So a funcao de auditoria grava no histórico. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0124 | Auditoria dos endpoints fica dentro da transacao | ESTATICO | — | Auditoria dos endpoints fica dentro da transacao. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0125 | Responsável vem da sessão | ESTATICO | O usuário auditado é sempre o autenticado, nunca um valor vindo do corpo da requisição. | O usuário auditado é sempre o autenticado, nunca um valor vindo do corpo da requisição. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0126 | Valores iniciais da baseline | ESTATICO | — | Valores iniciais da baseline. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0127 | Todo parametro inicial tem regra e respeita os limites | ESTATICO | — | Todo parametro inicial tem regra e respeita os limites. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0128 | Fuso não e parametro | ESTATICO | — | Fuso não e parametro. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0129 | Fuso fixo em sao paulo | ESTATICO | — | Fuso fixo em sao paulo. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0131 | Endpoint nunca audita como Sistema | ESTATICO | Nenhum endpoint chama registrar_alteracao com sistema: true. | Nenhum endpoint chama registrar_alteracao com sistema: true. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0132 | Carga automática audita cada inserção | ESTATICO | Cada inserção das funções inicializar_* é auditada como Sistema. | Cada inserção das funções inicializar_* é auditada como Sistema. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0137 | Administrador não tem status | ESTATICO | PATCH me/status aceita só Médico e Recepção/Triagem. | PATCH me/status aceita só Médico e Recepção/Triagem. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0138 | Em atendimento não é escolhido à mão | ESTATICO | PATCH me/status aceita só DISPONIVEL, PAUSA e AUSENTE. | PATCH me/status aceita só DISPONIVEL, PAUSA e AUSENTE. | `tests/api/test_base_compartilhada.py` |
| CT-XANO-0139 | Comparecimento põe Em atendimento | ESTATICO | fila/agir_chamada grava EM_ATENDIMENTO na sessão do médico ao confirmar o comparecimento. | fila/agir_chamada grava EM_ATENDIMENTO na sessão do médico ao confirmar o comparecimento. | `tests/api/test_base_compartilhada.py` |


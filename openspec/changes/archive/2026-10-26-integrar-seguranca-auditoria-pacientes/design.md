# Design técnico

## Contexto

Ver `proposal.md` para a motivação. Os três endpoints do grupo Pacientes existem, mas ainda não têm autenticação nem chamam a infraestrutura de auditoria. `auth/verificar_acesso` e o cliente HTTP do Reflex já existem; `registrar_alteracao` é responsabilidade da change `add-base-compartilhada` e ainda não está disponível. A rota `/recepcao/pacientes` já valida a sessão para usabilidade, mas seus handlers fazem chamadas HTTP diretas, sem o token.

## Objetivos / Fora dos objetivos

**Objetivos:**

- Aplicar a matriz de perfil de Pacientes no Xano em toda requisição.
- Registrar cadastro e alteração real de forma atômica, sem auditar recusas ou no-op.
- Reaproveitar a sessão e o cliente HTTP existentes para que a tela envie o token e reaja a 401/403.
- Alinhar a spec de Pacientes ao fluxo consolidado que abre a Ficha após a identificação.

**Fora dos objetivos:**

- Criar mecanismo de autenticação, auditoria ou transporte HTTP paralelo.
- Alterar schema, contratos de CPF ou os contratos de Ficha além da continuidade já implementada.
- Resolver a autorização e auditoria dos demais endpoints de Triagem.

## Decisões

### D1. Proteger cada endpoint de Pacientes no backend

`GET /pacientes` passa a exigir autenticação nativa do Xano e chama `auth/verificar_acesso` com `RECEPCAO_TRIAGEM` e `ADMINISTRADOR`. `POST /pacientes` e `PATCH /pacientes/{id}` usam o mesmo mecanismo, somente com `RECEPCAO_TRIAGEM`. A verificação ocorre antes de consulta ou escrita e usa o usuário retornado para a auditoria.

- **Por quê:** a permissão precisa valer fora do navegador, recarregar o usuário ativo a cada requisição e impedir vazamento de dados pessoais.
- **Alternativa descartada:** confiar apenas na guarda de rota ou no perfil armazenado no token. A primeira é contornável e a segunda não faz desativação valer imediatamente.

### D2. Escrita e auditoria usam uma única transação

Após a autorização, POST e PATCH real executam a escrita e `registrar_alteracao` no mesmo `db.transaction`. O cadastro envia `CADASTRO`, sem valor anterior; PATCH envia somente os campos efetivamente alterados, com valores anterior e novo. PATCH no-op retorna o registro já carregado com `alterado: false`, fora de qualquer escrita ou auditoria.

- **Por quê:** atende a atomicidade da capability Auditoria e evita históricos de mudanças que não ocorreram.
- **Alternativa descartada:** auditar como último passo fora de transação. Uma falha deixaria o Paciente e o histórico divergentes.

### D3. A infraestrutura compartilhada é pré-requisito, não cópia local

Antes de aplicar esta change, `add-base-compartilhada` deve disponibilizar e validar `registrar_alteracao` em transação. A integração usa sua assinatura e tabela publicadas; não cria função, endpoint ou tabela substitutos. A matriz 401/403 de `auth/verificar_acesso` também deve estar verificada na change de autenticação.

- **Por quê:** evita duas implementações de infraestrutura transversal e preserva a auditoria como fonte única.
- **Alternativa descartada:** implementar uma auditoria específica de Pacientes enquanto a base não está pronta. Isso duplicaria regra, dados e testes.

### D4. A tela usa o cliente autenticado existente

`PacienteState` passa a usar `api.requisitar` com `XANO_API_URL` e o token da sessão já mantido em `AuthState` para busca, cadastro e atualização. A resposta 401 encerra a sessão local e direciona para `/login`, no mesmo padrão da guarda de rota; 403 mantém a sessão e mostra acesso negado. CPF inválido, duplicado, não encontrado e demais 400 preservam as mensagens públicas atuais.

- **Por quê:** centraliza a montagem de URL, o header `Authorization`, timeout e TLS, sem criar outro cliente.
- **Alternativa descartada:** acrescentar headers manualmente em cada `httpx.get/post/patch`; repetiria a lógica de autenticação e aumentaria o risco de algum endpoint ficar sem token.

### D5. `Continuar` é continuidade do fluxo, não nova regra de Ficha

A change atualiza apenas a requirement de Pacientes que ainda descreve a confirmação visual da Sprint antiga. O comportamento passa a referenciar a capability `ficha-atendimento`: após a identificação, a interface solicita a abertura e direciona à edição da Ficha. Erros, ficha não finalizada e demais regras continuam sob o contrato de Ficha.

- **Por quê:** a visão consolidada do projeto já define identificação seguida de abertura da Ficha, e o código atual já segue esse fluxo.
- **Alternativa descartada:** voltar o botão para confirmação sem efeito. Isso reintroduziria uma regra temporária da change arquivada e quebraria o fluxo de triagem existente.

A autorização e a auditoria de `POST /fichas` NÃO fazem parte desta change: a integração da Ficha continua pendente na capability `ficha-atendimento`. Esta change não deve apresentar a abertura da Ficha como protegida por suas alterações de Paciente.

## Riscos / Compromissos

- [`registrar_alteracao` ainda não publicado] → concluir a task 1.2 e sua verificação 1.4 de `add-base-compartilhada` antes de publicar os endpoints de Pacientes.
- [Uma chamada sem token em algum handler de Paciente] → concentrar todas as três operações no cliente existente e cobrir o header/token nos testes de estado e integração.
- [Dados pessoais em valores de auditoria] → manter a trilha sem endpoint público de escrita, edição ou exclusão e limitar sua consulta ao fluxo administrativo já previsto.
- [`POST /fichas` permanece sem autorização e auditoria nesta base] → registrar essa integração como pendência separada de `ficha-atendimento`; não a considerar entregue por esta change.
- [Testes remotos alteram dados] → usar usuários e Pacientes de teste, com CPF gerado, e limpar ou desativar os dados conforme o roteiro de testes existente.

## Plano de migração

1. Confirmar a publicação e os testes de `registrar_alteracao` e de `verificar_acesso`.
2. Publicar no Xano a função e os três endpoints de Pacientes atualizados na mesma versão, exportando os XanoScripts para o repositório.
3. Publicar o frontend que envia o token somente após os endpoints aceitarem autenticação.
4. Executar testes automatizados, o roteiro de perfis e CA01 antes do aceite.

Rollback: NÃO restaurar endpoints públicos de Pacientes. Em falha, manter a autenticação e restaurar somente uma versão previamente validada que preserve `auth = "usuario"` e `verificar_acesso`; se ela não existir, manter as escritas indisponíveis até a correção, sem expor dados. Reverter o frontend somente para uma versão compatível com esses endpoints autenticados. Não remover a infraestrutura compartilhada nem registros de auditoria já confirmados.

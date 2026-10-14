# Tarefas

## 1. Xano — CPF

- [x] 1.1 [Xano] Validar o uso da tabela `paciente` existente e implementar função reutilizável de normalização/validação de CPF.
- [x] 1.2 [Xano] Cobrir CPF válido com e sem pontuação, tamanho inválido, sequência repetida e dígitos verificadores inválidos.

## 2. Xano — API de Paciente

- [x] 2.1 [Xano] Implementar `GET /pacientes?cpf=` e `POST /pacientes` com normalização, unicidade, validação e erros previstos.
- [x] 2.2 [Xano] Implementar `PATCH /pacientes/{id}` parcial, sem CPF, com 400 para corpo vazio/inválido, 404 para inexistente e retorno `alterado` para no-op ou alteração real.

## 3. Reflex — Recepção/Triagem

- [x] 3.2 [Reflex] Exibir Paciente encontrado, formulário condicional de cadastro e edição de nome, nascimento e telefone sem edição de CPF.
- [x] 3.4 [Reflex] Disponibilizar `Continuar` somente como confirmação visual, sem Ficha, ticket, classificação ou persistência de seleção.

## 4. Integração e testes/aceite

- [x] 4.2 [Testes] Cobrir busca com CPF existente/inexistente e formatos equivalentes; cadastro válido, duplicidade 400 com `CPF_DUPLICADO`, campos obrigatórios e regras de data.
- [x] 4.4 [Aceite] Verificar CA01: CPF existente recupera o mesmo Paciente sem duplicar cadastro.

## Pendências deferidas após o fechamento

A fatia funcional de identificação, cadastro e atualização cadastral de pacientes foi concluída, validada e aceita.

As tarefas abaixo permanecem abertas intencionalmente porque dependem de capacidades que ainda não foram implementadas no projeto:

- autenticação/autorização por perfil;
- verificar_acesso;
- tratamento real de 401/403;
- registrar_alteracao;
- auditoria.

Essas tarefas não representam falha ou implementação incompleta da fatia entregue nesta change.

Quando as changes responsáveis por autenticação e base compartilhada forem implementadas (`add-autenticacao-perfis` e `add-base-compartilhada`), estas pendências DEVEM ser reavaliadas e a integração com Paciente deverá ser executada e validada.

O fechamento desta change não equivale à dispensa dessas tarefas.

- [ ] 2.3 [Xano] Integrar `verificar_acesso` e `registrar_alteracao` conforme as changes de autenticação e base compartilhada, sem duplicar infraestrutura.
- [ ] 3.1 [Reflex] Criar área protegida de Recepção/Triagem para entrada e busca de CPF.
- [ ] 3.3 [Reflex] Exibir mensagens de CPF inválido, duplicado, não encontrado quando aplicável, erro de validação, 401 e 403.
- [ ] 4.1 [Integração] Integrar token real, comunicação Reflex → Xano, 401/403 e busca após cadastro.
- [ ] 4.3 [Testes] Cobrir PATCH parcial, 404, 400 para corpo vazio/CPF no payload/dados inválidos, no-op sem auditoria e alteração real com auditoria.

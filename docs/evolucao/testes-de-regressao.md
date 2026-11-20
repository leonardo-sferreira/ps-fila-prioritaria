# Testes de regressão e atualização

Como garantir que uma atualização (de biblioteca, do Reflex, do Xano ou de uma regra) não quebrou o que já funciona.

## A suíte de regressão

A regressão é a soma das suítes automatizadas descritas em [estratégia de testes](../testes/estrategia-de-testes.md). Elas rodam no CI em **todo push e Pull Request**, então qualquer mudança que quebre um comportamento coberto aparece antes do merge.

| Camada protegida | Suíte | Cobre |
|---|---|---|
| Telas e lógica do frontend | `reflex` | Todos os estados: login, triagem, ficha, médico, cadastros, auditoria, painéis |
| Contratos do backend | `xano-static` | Autorização, auditoria e parâmetros lidos do código |
| Regras de negócio | `xano-safe` | Pontuação, faixas, ordem da fila, senha, destino, prazos |
| Fluxos reais | `controlled` | Concorrência de chamada e de login, painel, acompanhamento |
| Navegação pública | `e2e` | Login, aviso de privacidade e guarda de rota |

## Roteiro para atualizar uma dependência

1. **Branch própria:** `chore/atualiza-<biblioteca>`.
2. **Atualizar** a versão em `frontend/requirements.txt` (sempre fixada com `==`) e instalar: `pip install -r requirements.txt`.
3. **Compilar:** `reflex compile --dry` em `frontend/`. Atualizações do Reflex podem mudar componentes e exigir ajustes nas telas.
4. **Rodar a regressão local:** `reflex`, `xano-static` e `autotestes`. Os três precisam continuar com o mesmo número de casos aprovados.
5. **Conferir as telas principais** manualmente: login, ficha, médico, painéis e Administrador.
6. **Pull Request:** o CI roda também `xano-safe` e `e2e`.
7. **Atualizar o inventário:** `python scripts/gerar_docs.py` regenera [dependencias.md](dependencias.md).

### Cuidados conhecidos

| Componente | Cuidado |
|---|---|
| Reflex | Mudanças de API entre versões (por exemplo, `router.page.params` foi substituído; o projeto usa `router.url`). Conferir o changelog do Reflex antes de subir de versão menor |
| Python | O CI usa 3.12; o desenvolvimento local também roda em 3.14. Testar nas duas antes de mudar |
| Xano CLI | O formato do `pull` muda a formatação dos `.xs`. Não substitua os arquivos do repositório pelos baixados sem revisar |
| Xano (plataforma) | Atualizações da plataforma não são controladas pela equipe; a suíte `xano-safe` no CI detecta mudança de comportamento das funções |

## Mudança de regra de negócio

1. Atualize a change do OpenSpec (spec e design) antes do código.
2. Escreva ou ajuste o teste que descreve a regra nova (função pura: teste nativo no `.xs`; estado: `frontend/tests`).
3. Implemente e rode a regressão. Testes antigos que falharem por causa da regra nova são atualizados no mesmo PR, com o motivo na descrição.
4. Mudanças só de valor (limiar, intervalo, ciclo) não precisam de código: são parâmetros ([configuração](../manutencao/configuracao-e-regras.md#parâmetros-editáveis-pelo-administrador)).

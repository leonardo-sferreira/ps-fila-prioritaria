# Inventário de dependências (SBOM)

> Arquivo gerado por `python scripts/gerar_docs.py`. Não edite à mão: altere o código e gere de novo.

## Plataformas

| Componente | Versão | Onde é definida | Observação |
|---|---|---|---|
| Python (CI) | 3.12 | `.github/workflows/ci.yml` | O ambiente local também roda em 3.14 |
| Reflex | ver tabela abaixo | `frontend/requirements.txt` | Gera o frontend em React/Next.js e um backend em Python (Starlette/Granian) |
| Bun / Node | gerido pelo Reflex | `frontend/reflex.lock/` | Instalado pelo Reflex na primeira execução |
| Xano | plano gratuito, branch `v1` | workspace 147348 | Banco, endpoints e funções; limite de 10 requisições a cada 20 s |
| Xano CLI | 1.3.4 | instalação global (`npm`) | Publicação (`xano workspace push`) e testes por função |
| Brevo | API de e-mail | `$env.BREVO_API_KEY` no Xano | Envio dos códigos de login e de redefinição de senha |
| OpenSpec | CLI | instalação global | Especificações e changes em `openspec/` |

## Bibliotecas Python do frontend

Todas fixadas com `==` em `frontend/requirements.txt`. **Direta** = importada pelo código do projeto; as demais vêm como dependência do Reflex.

| Biblioteca | Versão | Uso |
|---|---|---|
| anyio | 4.15.1 | transitiva |
| bidict | 0.24.1 | transitiva |
| certifi | 2026.7.22 | transitiva |
| click | 8.5.0 | transitiva |
| granian | 2.8.4 | transitiva |
| h11 | 0.16.0 | transitiva |
| httpcore | 1.0.9 | transitiva |
| httpx | 0.28.1 | **direta** |
| idna | 3.20 | transitiva |
| markdown-it-py | 4.2.0 | transitiva |
| mdurl | 0.1.2 | transitiva |
| packaging | 26.3 | transitiva |
| platformdirs | 4.13.0 | transitiva |
| Pygments | 2.21.0 | transitiva |
| python-engineio | 4.14.0 | transitiva |
| python-dotenv | 1.2.2 | **direta** |
| python-multipart | 0.0.32 | transitiva |
| python-socketio | 5.17.0 | transitiva |
| redis | 7.4.1 | transitiva |
| reflex | 0.10.0 | **direta** |
| reflex-base | 0.10.0 | transitiva |
| reflex-build-sdk | 0.1.0 | transitiva |
| reflex-components-code | 0.10.0 | transitiva |
| reflex-components-core | 0.10.0 | transitiva |
| reflex-components-dataeditor | 0.10.0 | transitiva |
| reflex-components-gridjs | 0.10.0 | transitiva |
| reflex-components-lucide | 1.1.0 | transitiva |
| reflex-components-markdown | 0.10.0 | transitiva |
| reflex-components-moment | 0.10.0 | transitiva |
| reflex-components-plotly | 0.10.0 | transitiva |
| reflex-components-radix | 0.10.0 | transitiva |
| reflex-components-react-player | 0.10.0 | transitiva |
| reflex-components-recharts | 0.10.0 | transitiva |
| reflex-components-sonner | 0.10.0 | transitiva |
| reflex-hosting-cli | 0.2.0 | transitiva |
| rich | 15.0.0 | transitiva |
| simple-websocket | 1.1.0 | transitiva |
| starlette | 1.7.0 | transitiva |
| typing_extensions | 4.16.0 | transitiva |
| watchfiles | 1.3.0 | transitiva |
| wrapt | 2.5.0 | transitiva |
| wsproto | 1.3.2 | transitiva |

## Ferramentas de teste

| Ferramenta | Uso |
|---|---|
| pytest | Todas as suítes (`scripts/run_test_evidence.py`) |
| Playwright (Chromium) | Suíte E2E pública (`tests/e2e/`) |
| GitHub Actions | CI em todo push e PR (`.github/workflows/ci.yml`) |


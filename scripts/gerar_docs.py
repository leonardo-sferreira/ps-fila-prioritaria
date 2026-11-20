"""Gera as partes da documentação que saem direto do código, para não divergirem dele.

Uso (na raiz do repositório):  python scripts/gerar_docs.py

Lê backend/xano (endpoints, tabelas e funções), frontend/requirements.txt e tests/catalogo_testes.json e
reescreve os arquivos marcados como gerados em docs/. Os demais documentos são escritos à mão.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
XANO = RAIZ / "backend" / "xano"
DOCS = RAIZ / "docs"
AVISO = "> Arquivo gerado por `python scripts/gerar_docs.py`. Não edite à mão: altere o código e gere de novo.\n"

GRUPO_URL = {"Autenticacao": "XANO_AUTH_API_URL", "Cadastros": "XANO_CADASTROS_API_URL", "Fila": "XANO_FILA_API_URL",
             "Pacientes": "XANO_API_URL", "Triagem": "XANO_TRIAGEM_API_URL"}


def ler(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")


def comentario_inicial(texto: str) -> str:
    linhas = []
    for linha in texto.splitlines():
        if linha.startswith("//"):
            linhas.append(linha[2:].strip())
        elif linhas or linha.strip():
            break
    return " ".join(linhas)


def bloco(texto: str, inicio: int) -> str:
    """Conteúdo entre a chave que abre em `inicio` e a que fecha."""
    profundidade, i = 0, inicio
    while i < len(texto):
        if texto[i] == "{":
            profundidade += 1
        elif texto[i] == "}":
            profundidade -= 1
            if profundidade == 0:
                return texto[inicio + 1:i]
        i += 1
    return texto[inicio + 1:]


def secao(texto: str, nome: str) -> str | None:
    m = re.search(rf"^\s{{2}}{nome}\s*(=\s*)?\{{", texto, re.M)
    if not m:
        return None
    return bloco(texto, texto.index("{", m.start()))


def campos_input(corpo: str | None) -> list[tuple[str, str, bool, str]]:
    if not corpo:
        return []
    campos = []
    for linha in corpo.splitlines():
        linha = linha.strip()
        m = re.match(r"^(\w+)(\??)\s+(\w+)(\??)(?:\s*=\s*([^\s{]+))?(?:\s+filters=(\S+))?", linha)
        if m and m.group(1) not in ("values", "table", "sensitive", "description"):
            tipo, opcional = m.group(1) + ("[]" if "[]" in linha.split()[0] else ""), bool(m.group(2) or m.group(4))
            extras = []
            if m.group(5):
                extras.append(f"padrão {m.group(5)}")
            if m.group(6):
                extras.append("filtros: " + ", ".join(m.group(6).split("|")))
            campos.append((m.group(3), tipo, opcional, ", ".join(extras)))
    return campos


def endpoints() -> list[dict]:
    lista = []
    for arq in sorted((XANO / "api").rglob("*.xs")):
        if arq.name == "api_group.xs":
            continue
        t = ler(arq)
        m = re.search(r'^query\s+"?([^"\s]+)"?\s+verb=(\w+)', t, re.M)
        if not m:
            continue
        grupo = re.search(r'api_group\s*=\s*"?([^"\n]+?)"?\s*$', t, re.M)
        perfis = re.search(r"perfis_permitidos\s*:\s*\[([^\]]*)\]", t)
        resp = re.search(r"^\s{2}response\s*=\s*", t, re.M)
        resposta = ""
        if resp:
            resto = t[resp.end():]
            resposta = bloco(resto, 0).strip() if resto.startswith("{") else resto.splitlines()[0].strip()
            resposta = "{\n  " + "\n  ".join(l.strip() for l in resposta.splitlines() if l.strip()) + "\n}" if resto.startswith("{") else resposta
        erros = sorted(set(re.findall(r'error\s*=\s*"([^"]+)"', t)))
        lista.append({
            "arquivo": arq.relative_to(RAIZ).as_posix(), "caminho": "/" + m.group(1), "verbo": m.group(2),
            "grupo": grupo.group(1).strip('"') if grupo else "?", "auth": 'auth = "usuario"' in t,
            "perfis": [p.strip().strip('"') for p in perfis.group(1).split(",")] if perfis else [],
            "descricao": comentario_inicial(t) or (re.search(r'description\s*=\s*"([^"]+)"', t) or [None, ""])[1],
            "entrada": campos_input(secao(t, "input")), "resposta": resposta, "erros": erros,
        })
    return lista


def gerar_contratos(lista: list[dict]) -> str:
    por_grupo = defaultdict(list)
    for e in lista:
        por_grupo[e["grupo"]].append(e)
    out = ["# Contratos de API (Xano)\n", AVISO,
           "Todos os endpoints ficam no Xano, divididos em grupos de API. Cada grupo tem uma URL base própria, configurada "
           "no `frontend/.env` (coluna \"Variável\"). As chamadas usam JSON; endpoints com **login** exigem o cabeçalho "
           "`Authorization: Bearer <token>` (o token vem de `POST /auth/login/verificar`). Erros seguem o formato do Xano: "
           "`{\"code\": \"ERROR_CODE_...\", \"message\": \"...\"}` com status 400 (entrada), 401 (sessão), 403 (perfil), "
           "404 (não encontrado) ou 429 (limite de requisições do plano).\n",
           "| Grupo | Variável da URL base | Endpoints |", "|---|---|---|"]
    for g in sorted(por_grupo):
        out.append(f"| {g} | `{GRUPO_URL.get(g, '?')}` | {len(por_grupo[g])} |")
    for g in sorted(por_grupo):
        out.append(f"\n## Grupo {g}\n")
        for e in sorted(por_grupo[g], key=lambda x: (x["caminho"], x["verbo"])):
            acesso = ("login: " + ", ".join(e["perfis"])) if e["perfis"] else ("login" if e["auth"] else "público (sem login)")
            out.append(f"### `{e['verbo']} {e['caminho']}`\n")
            if e["descricao"]:
                out.append(e["descricao"] + "\n")
            out.append(f"- **Acesso:** {acesso}")
            out.append(f"- **Código:** `{e['arquivo']}`")
            if e["entrada"]:
                out.append("- **Entrada:**\n\n  | Campo | Tipo | Obrigatório | Observação |\n  |---|---|---|---|")
                for nome, tipo, opcional, extra in e["entrada"]:
                    out.append(f"  | `{nome}` | {tipo} | {'não' if opcional else 'sim'} | {extra} |")
            else:
                out.append("- **Entrada:** nenhuma")
            if e["resposta"]:
                out.append("- **Resposta (200):**\n\n  ```\n  " + e["resposta"].replace("\n", "\n  ") + "\n  ```")
            if e["erros"]:
                out.append("- **Mensagens de erro:** " + "; ".join(f"`{x}`" for x in e["erros"]))
            out.append("")
    return "\n".join(out) + "\n"


def tabelas() -> list[dict]:
    lista = []
    for arq in sorted((XANO / "table").glob("*.xs")):
        t = ler(arq)
        nome = re.search(r"^table\s+\"?(\w+)", t, re.M).group(1)
        corpo = secao(t, "schema") or ""
        campos, i = [], 0
        linhas = corpo.splitlines()
        comentario = ""
        while i < len(linhas):
            l = linhas[i].strip()
            if l.startswith("//"):
                comentario = (comentario + " " + l[2:].strip()).strip()
                i += 1
                continue
            m = re.match(r"^(\w+)(\??)\s+(\w+)(\??)(?:=(\S+))?", l)
            if m:
                ref, valores = None, None
                if l.endswith("{"):
                    j, sub = i + 1, []
                    while j < len(linhas) and linhas[j].strip() != "}":
                        sub.append(linhas[j].strip())
                        j += 1
                    joined = " ".join(sub)
                    r = re.search(r'table\s*=\s*"(\w+)"', joined)
                    v = re.search(r"values\s*=\s*\[([^\]]*)\]", joined)
                    ref = r.group(1) if r else None
                    valores = re.findall(r'"([^"]+)"', v.group(1)) if v else None
                    i = j
                campos.append({"nome": m.group(3), "tipo": m.group(1), "opcional": bool(m.group(2) or m.group(4)),
                               "padrao": m.group(5), "ref": ref, "valores": valores, "nota": comentario})
                comentario = ""
            i += 1
        lista.append({"nome": nome, "descricao": comentario_inicial(t), "campos": campos, "arquivo": arq.relative_to(RAIZ).as_posix()})
    return lista


TIPO_MERMAID = {"int": "int", "text": "string", "email": "string", "password": "string", "timestamp": "timestamp",
                "date": "date", "bool": "boolean", "enum": "enum", "json": "json", "decimal": "decimal"}


def gerar_dados(lista: list[dict]) -> str:
    out = ["# Dicionário de dados e DER\n", AVISO,
           "Tabelas do banco do Xano (`backend/xano/table/`). O diagrama mostra as chaves estrangeiras declaradas "
           "(`campo { table = \"...\" }`). O caminho funcional dos dados está em [modelo-de-dados.md](modelo-de-dados.md).\n",
           "## Diagrama entidade-relacionamento\n", "```mermaid", "erDiagram"]
    for t in lista:
        for c in t["campos"]:
            if c["ref"]:
                out.append(f"    {c['ref']} ||--o{{ {t['nome']} : \"{c['nome']}\"")
    for t in lista:
        out.append(f"    {t['nome']} {{")
        for c in t["campos"]:
            chave = " PK" if c["nome"] == "id" else (" FK" if c["ref"] else "")
            out.append(f"        {TIPO_MERMAID.get(c['tipo'], 'string')} {c['nome']}{chave}")
        out.append("    }")
    out.append("```\n")
    out.append("## Tabelas\n")
    for t in lista:
        out.append(f"### `{t['nome']}`\n")
        if t["descricao"]:
            out.append(t["descricao"] + "\n")
        out.append(f"Código: `{t['arquivo']}`\n")
        out.append("| Campo | Tipo | Obrigatório | Detalhe |\n|---|---|---|---|")
        for c in t["campos"]:
            det = []
            if c["ref"]:
                det.append(f"→ `{c['ref']}.id`")
            if c["valores"]:
                det.append("valores: " + ", ".join(f"`{v}`" for v in c["valores"]))
            if c["padrao"]:
                det.append(f"padrão `{c['padrao']}`")
            if c["nota"]:
                det.append(c["nota"])
            out.append(f"| `{c['nome']}` | {c['tipo']} | {'não' if c['opcional'] else 'sim'} | {'; '.join(det)} |")
        out.append("")
    return "\n".join(out) + "\n"


def funcoes() -> list[dict]:
    lista = []
    for arq in sorted((XANO / "function").rglob("*.xs")):
        t = ler(arq)
        m = re.search(r'^function\s+"?([^"\s{]+)"?', t, re.M)
        if not m:
            continue
        desc = comentario_inicial(t) or (re.search(r'description\s*=\s*"([^"]+)"', t) or [None, ""])[1]
        lista.append({"nome": m.group(1), "descricao": desc, "arquivo": arq.relative_to(RAIZ).as_posix(),
                      "testes": len(re.findall(r'^\s{2}test\s+"', t, re.M)), "so_teste": "/teste_" in m.group(1) or m.group(1).startswith("teste")})
    return lista


def gerar_funcoes(lista: list[dict]) -> str:
    out = ["# Funções do Xano (regras de negócio no código)\n", AVISO,
           "Funções reutilizadas pelos endpoints (`backend/xano/function/`). Funções puras têm testes nativos do Xano "
           "(coluna \"Testes nativos\"), que rodam na suíte `xano-safe` do CI. As funções `teste_*` existem só para os "
           "testes de integração e não têm endpoint público.\n"]
    por_pasta = defaultdict(list)
    for f in lista:
        por_pasta[f["nome"].split("/")[0] if "/" in f["nome"] else "(raiz)"].append(f)
    for pasta in sorted(por_pasta):
        out.append(f"## {pasta}\n\n| Função | O que faz | Testes nativos |\n|---|---|---|")
        for f in sorted(por_pasta[pasta], key=lambda x: x["nome"]):
            nome = f"`{f['nome']}`" + (" *(só teste)*" if f["so_teste"] else "")
            out.append(f"| {nome} | {f['descricao'] or '—'} | {f['testes'] or '—'} |")
        out.append("")
    return "\n".join(out) + "\n"


def gerar_dependencias() -> str:
    reqs = [l.strip() for l in ler(RAIZ / "frontend" / "requirements.txt").splitlines() if l.strip() and not l.startswith("#")]
    diretas = {"reflex", "httpx", "python-dotenv"}
    out = ["# Inventário de dependências (SBOM)\n", AVISO,
           "## Plataformas\n",
           "| Componente | Versão | Onde é definida | Observação |", "|---|---|---|---|",
           "| Python (CI) | 3.12 | `.github/workflows/ci.yml` | O ambiente local também roda em 3.14 |",
           "| Reflex | ver tabela abaixo | `frontend/requirements.txt` | Gera o frontend em React/Next.js e um backend em Python (Starlette/Granian) |",
           "| Bun / Node | gerido pelo Reflex | `frontend/reflex.lock/` | Instalado pelo Reflex na primeira execução |",
           "| Xano | plano gratuito, branch `v1` | workspace 147348 | Banco, endpoints e funções; limite de 10 requisições a cada 20 s |",
           "| Xano CLI | 1.3.4 | instalação global (`npm`) | Publicação (`xano workspace push`) e testes por função |",
           "| Brevo | API de e-mail | `$env.BREVO_API_KEY` no Xano | Envio dos códigos de login e de redefinição de senha |",
           "| OpenSpec | CLI | instalação global | Especificações e changes em `openspec/` |",
           "\n## Bibliotecas Python do frontend\n",
           "Todas fixadas com `==` em `frontend/requirements.txt`. **Direta** = importada pelo código do projeto; as demais vêm "
           "como dependência do Reflex.\n", "| Biblioteca | Versão | Uso |", "|---|---|---|"]
    for r in reqs:
        nome, _, versao = r.partition("==")
        out.append(f"| {nome} | {versao or '—'} | {'**direta**' if nome.lower() in diretas else 'transitiva'} |")
    out.append("\n## Ferramentas de teste\n\n| Ferramenta | Uso |\n|---|---|\n| pytest | Todas as suítes (`scripts/run_test_evidence.py`) |\n"
               "| Playwright (Chromium) | Suíte E2E pública (`tests/e2e/`) |\n| GitHub Actions | CI em todo push e PR (`.github/workflows/ci.yml`) |\n")
    return "\n".join(out) + "\n"


SUITE_NOME = {"reflex": "Reflex (estado das telas, API simulada)", "xano-static": "Xano estático (contratos lidos do código)",
              "xano-safe": "Xano funções puras (testes nativos remotos)", "controlled": "Integração ao vivo (escrita isolada na v1)",
              "e2e": "E2E público (navegador)", "autotestes": "Autotestes da infraestrutura de evidências"}


def gerar_testes() -> str:
    dados = json.loads(ler(RAIZ / "tests" / "catalogo_testes.json"))
    casos = dados["casos"]
    por_suite = defaultdict(list)
    for c in casos:
        por_suite[c.get("suite", "?")].append(c)
    out = ["# Catálogo de testes\n", AVISO,
           "Fonte: `tests/catalogo_testes.json`. Cada caso tem um ID permanente; o CI recusa teste sem registro no catálogo. "
           "Como rodar e como ler as evidências: [estrategia-de-testes.md](estrategia-de-testes.md).\n",
           "| Suíte | Casos | Onde roda |", "|---|---|---|"]
    onde = {"reflex": "CI e local", "xano-static": "CI e local", "xano-safe": "CI (CLI do Xano)", "controlled": "Local, com autorização",
            "e2e": "CI", "autotestes": "CI e local"}
    for s in sorted(por_suite):
        out.append(f"| {SUITE_NOME.get(s, s)} | {len(por_suite[s])} | {onde.get(s, '—')} |")
    out.append(f"| **Total** | **{len(casos)}** | |\n")
    out.append("Colunas: **Entrada** = o que o teste prepara ou envia (resumo do objetivo); **Saída esperada** = o resultado "
               "que precisa acontecer para o teste passar.\n")
    for s in sorted(por_suite):
        out.append(f"## {SUITE_NOME.get(s, s)}\n\n| ID | Teste | Tipo | Entrada | Saída esperada | Código |\n|---|---|---|---|---|---|")
        for c in sorted(por_suite[s], key=lambda x: x["id"]):
            seletor = c.get("seletor", "").split("::")[0]
            limpar = lambda x: str(x or "—").replace("|", "\\|").replace("\n", " ")
            objetivo = c.get("objetivo") or ""
            entrada = "—" if objetivo.strip(". ").lower() == str(c.get("nome") or "").strip(". ").lower() else objetivo
            out.append(f"| {c['id']} | {limpar(c.get('nome'))} | {c.get('tipo', '—')} | {limpar(entrada)} | "
                       f"{limpar(c.get('resultado_esperado'))} | `{seletor}` |")
        out.append("")
    return "\n".join(out) + "\n"


FRONT = RAIZ / "frontend" / "ps_fila_prioritaria"


def normalizar(caminho: str) -> str:
    return re.sub(r"\{[^}]*\}", "{}", caminho.rstrip("/"))


def gerar_mapa(lista: list[dict]) -> str:
    por_caminho = defaultdict(list)
    for e in lista:
        por_caminho[normalizar(e["caminho"])].append(e)
    app = ler(FRONT / "ps_fila_prioritaria.py")
    # Rotas: chamadas app.add_page(funcao, route="...", ...) e a tabela do laço dos cadastros do Administrador.
    rotas = []
    for m in re.finditer(r'app\.add_page\(\s*(\w+),\s*route="([^"]+)"(.*?)\)\n', app, re.S):
        perfil = re.search(r'verificar_sessao\("(\w+)"\)', m.group(3))
        rotas.append((m.group(1), m.group(2), perfil.group(1) if perfil else "público"))
    for m in re.finditer(r'\((\w+),\s*"(/[^"]+)",\s*"[^"]*",\s*\w+\)', app):
        rotas.append((m.group(1), m.group(2), "ADMINISTRADOR"))
    rotas = [r for r in rotas if r[0] != "_pagina"]
    # Função de página → módulo, pelos imports do app (evita confundir funções de mesmo nome em módulos diferentes).
    paginas_por_funcao = {}
    for m in re.finditer(r"from ps_fila_prioritaria\.paginas\.(\w+) import (\([^)]*\)|[^\n]+)", app):
        for nome in re.findall(r"\w+", m.group(2)):
            paginas_por_funcao[nome] = FRONT / "paginas" / f"{m.group(1)}.py"
    estados_usados = {}
    for arq in (FRONT / "paginas").glob("*.py"):
        estados_usados[arq] = sorted(set(re.findall(r"from ps_fila_prioritaria\.estados\.(\w+) import", ler(arq))))
    chamadas = {}
    verbo_re = r'"(GET|POST|PATCH|PUT|DELETE)"\s*,\s*(?:"XANO_\w+"\s*,\s*|VARIAVEL_API\s*,\s*)?(f?"[^"]*"|self\.CAMINHO|f"\{self\.CAMINHO\}[^"]*")'
    for arq in sorted((FRONT / "estados").glob("*.py")):
        t = ler(arq)
        caminhos_base = re.findall(r'CAMINHO\s*=\s*"(/[^"]*)"', t)
        pares = set()
        for verbo, alvo in re.findall(verbo_re, t):
            if "CAMINHO" in alvo:
                sufixo = re.sub(r'^f?"\{self\.CAMINHO\}', "", alvo).rstrip('"') if alvo.startswith('f"') else ""
                for base in caminhos_base:
                    pares.add((verbo, normalizar(base + sufixo)))
            else:
                pares.add((verbo, normalizar(alvo.lstrip("f").strip('"'))))
        com_verbo = {c for _, c in pares}
        # Caminho citado sem o verbo ao lado (verbo em variável): lista os verbos que existem para ele.
        for lit in re.findall(r'f?"(/[A-Za-z0-9_./{}\-]*)"', t):
            chave = normalizar(lit)
            if chave not in com_verbo:
                for e in por_caminho.get(chave, []):
                    pares.add((e["verbo"], chave))
        achados = []
        for verbo, chave in sorted(pares, key=lambda x: (x[1], x[0])):
            for e in por_caminho.get(chave, []):
                if e["verbo"] == verbo:
                    achados.append(f"`{verbo} {e['caminho']}` ({e['grupo']})")
        chamadas[arq.stem] = achados
    out = ["# Mapa: tela → estado → API\n", AVISO,
           "Cada tela (rota do Reflex) é desenhada por uma função em `frontend/ps_fila_prioritaria/paginas/` e usa um ou mais "
           "estados em `estados/`, que chamam a API do Xano por `api.requisitar` (`frontend/ps_fila_prioritaria/api.py`). "
           "A lista de endpoints de cada estado é obtida pelos caminhos citados no código e conferida com os endpoints existentes; "
           "quando um estado chama vários verbos no mesmo caminho, todos aparecem.\n",
           "## Telas\n", "| Rota | Perfil | Página (função) | Estados usados |", "|---|---|---|---|"]
    for funcao, rota, perfil in sorted(rotas, key=lambda r: r[1]):
        arq = paginas_por_funcao.get(funcao)
        estados = ", ".join(f"`{x}`" for x in estados_usados.get(arq, [])) if arq else "—"
        origem = f"`paginas/{arq.name}` → `{funcao}`" if arq else f"`{funcao}`"
        out.append(f"| `{rota}` | {perfil} | {origem} | {estados or '—'} |")
    out.append("\n## Estados e endpoints que chamam\n\n| Estado (`estados/`) | Endpoints |\n|---|---|")
    for nome, achados in sorted(chamadas.items()):
        if nome != "__init__":
            out.append(f"| `{nome}.py` | {'<br>'.join(achados) if achados else '— (sem chamada direta à API)'} |")
    return "\n".join(out) + "\n"


SPRINTS = [("2026-10-12", "Sprint 1 — Base, documentação e identificação do paciente"),
           ("2026-10-26", "Sprint 2 — Ficha, sintomas e prioridade na triagem"),
           ("2026-11-09", "Sprint 3 — Administrador, direcionamento e senha"),
           ("2026-11-16", "Sprint 4 — Fila do médico, chamada e acompanhamento"),
           ("2026-12-31", "Sprint 5 — Painel público, testes e apresentação")]


def gerar_changelog() -> str:
    arquivo = RAIZ / "openspec" / "changes" / "archive"
    entradas = []
    for pasta in sorted(arquivo.iterdir()):
        proposta = pasta / "proposal.md"
        if not proposta.exists():
            continue
        t = ler(proposta)
        data, nome = pasta.name[:10], pasta.name[11:]
        m = re.search(r"^## Why\s*\n+(.+?)(?:\n\n|\n## )", t, re.S | re.M)
        resumo = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        entradas.append((data, nome, resumo, pasta.relative_to(RAIZ).as_posix()))
    out = ["# Changelog\n", AVISO,
           "Histórico do que foi entregue, montado a partir das changes arquivadas do OpenSpec "
           "(`openspec/changes/archive/<data>-<nome>/`). Cada change tem proposta, design, tarefas e o delta de "
           "especificação que foi incorporado a `openspec/specs/`. Versões publicadas no GitHub: `v0.1.0` "
           "(25/10/2026, identificação do paciente e ficha). Os PRs de cada entrega estão no histórico do GitHub.\n"]
    for limite, titulo in SPRINTS:
        do_sprint = [e for e in entradas if e[0] <= limite and all(e[0] > l for l, _ in SPRINTS[:SPRINTS.index((limite, titulo))])]
        if not do_sprint:
            continue
        out.append(f"## {titulo}\n")
        for data, nome, resumo, caminho in do_sprint:
            d = f"{data[8:10]}/{data[5:7]}/{data[:4]}"
            out.append(f"- **{d} — `{nome}`**" + (f": {resumo}" if resumo else "") + f" ([change]({'../../' + caminho}))")
        out.append("")
    return "\n".join(out) + "\n"


def main() -> None:
    (DOCS / "manutencao").mkdir(parents=True, exist_ok=True)
    (DOCS / "evolucao").mkdir(parents=True, exist_ok=True)
    (DOCS / "testes").mkdir(parents=True, exist_ok=True)
    arquivos = {
        DOCS / "manutencao" / "contratos-api.md": gerar_contratos(endpoints()),
        DOCS / "manutencao" / "mapa-telas-api.md": gerar_mapa(endpoints()),
        DOCS / "manutencao" / "dicionario-de-dados.md": gerar_dados(tabelas()),
        DOCS / "manutencao" / "funcoes-xano.md": gerar_funcoes(funcoes()),
        DOCS / "evolucao" / "dependencias.md": gerar_dependencias(),
        DOCS / "evolucao" / "changelog.md": gerar_changelog(),
        DOCS / "testes" / "catalogo-de-testes.md": gerar_testes(),
    }
    for caminho, texto in arquivos.items():
        caminho.write_text(texto, encoding="utf-8", newline="\n")
        print(f"gerado {caminho.relative_to(RAIZ).as_posix()} ({texto.count(chr(10))} linhas)")


if __name__ == "__main__":
    main()

"""Executa suites permitidas e produz evidências sem registrar dados sensíveis.

Uso: python scripts/run_test_evidence.py --suite reflex|xano-safe|controlled|e2e
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
REMOTE_FILES = {
    "test_api_autenticacao.py": ("autenticacao", "escrita operacional: códigos, tentativas e bloqueios"),
    "test_api_redefinicao_senha.py": ("autenticacao", "escrita operacional: códigos e limites de tentativa"),
    "test_api_totem.py": ("totem", "escrita: criação de tickets na fila"),
    "test_xano_api_integration.py": ("ficha-atendimento", "escrita: pacientes e fichas sem limpeza garantida"),
    "test_chamada.py": ("chamada-paciente", "escrita: cenário, chamadas, sessões e limpeza remota"),
    "test_recuperacao_sessao_medico.py": ("chamada-paciente", "escrita: sessões e estado operacional"),
}
SPEC_BY_FILE = {
    "test_auth_state.py": "autenticacao",
    "test_chamada_manual.py": "fila-pre-triagem",
    "test_ficha_abertura_contract.py": "ficha-atendimento",
    "test_ficha_state.py": "ficha-atendimento",
    "test_fila_tickets_state.py": "fila-pre-triagem",
    "test_medico_state.py": "chamada-paciente",
    "test_mensagem_erro.py": "ficha-atendimento",
    "test_paciente_state.py": "pacientes",
    "test_privacidade.py": "privacidade",
    "test_senha_state.py": "autenticacao",
    "test_totem_state.py": "totem",
    "test_ordenacao.py": "fila-priorizada",
    "test_selecao_entre_filas.py": "fila-priorizada",
    "test_publico.py": "privacidade",
}
SPEC_CHANGE = {"autenticacao": "add-autenticacao-perfis"}
NATIVE_PURE = (
    "classificacao/pontuar", "classificacao/faixas_padrao",
    "direcionamento/escolher_destino", "direcionamento/formatar_senha",
    "direcionamento/senha_reavaliada", "pacientes/normalizar_cpf",
    "pacientes/normalizar_telefone", "fila/proxima_ficha",
    "fila/prever_fila", "fila/selecionar_entre_filas", "fila/avaliar_cobertura",
)
SENSITIVE = [
    (re.compile(r"(?i)(bearer\s+)[^\s\"']+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(token|senha|password|secret|chave_dispositivo)([\"']?\s*(?::|=(?!=))\s*[\"']?)[^\s,}\"']+"), r"\1\2[REDACTED]"),
    (re.compile(r"(?i)((?:token|senha|password|secret|chave_dispositivo)\s*==\s*['\"])[^'\"]+(['\"])"), r"\1[REDACTED]\2"),
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF REDACTED]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[EMAIL REDACTED]"),
    (re.compile(r"https?://[^\s\"'<>]+"), "[URL REDACTED]"),
]


def clean(value: object, limit: int = 700) -> str:
    result = str(value)
    for pattern, replacement in SENSITIVE:
        result = pattern.sub(replacement, result)
    return result[:limit]


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else "indisponível"


def identifier(node: str, component: str) -> str:
    prefix = "REFLEX" if component == "Reflex" else "XANO"
    return f"CT-{prefix}-{hashlib.sha256(node.encode()).hexdigest()[:10].upper()}"


def http_metadata(func: ast.AST, filename: str, helpers: dict[str, ast.AST]) -> tuple[list[str], list[str], list[int], list[str]]:
    methods, routes, statuses, fields = set(), set(), set(), []
    if filename == "test_api_totem.py":
        methods.add("POST")
        routes.add("/totem/tickets")
    nodes = list(ast.walk(func))
    seen_helpers = set()
    for item in list(nodes):
        if isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id in helpers and item.func.id not in seen_helpers:
            seen_helpers.add(item.func.id)
            nodes.extend(ast.walk(helpers[item.func.id]))
    for item in nodes:
        if isinstance(item, ast.Call):
            name = item.func.attr if isinstance(item.func, ast.Attribute) else item.func.id if isinstance(item.func, ast.Name) else ""
            if name in {"_req", "_chamar", "requisitar", "_protegida"}:
                offset = 1 if name == "_req" else 0
                if len(item.args) > offset and isinstance(item.args[offset], ast.Constant) and str(item.args[offset].value).upper() in {"GET", "POST", "PATCH", "PUT", "DELETE"}:
                    methods.add(str(item.args[offset].value).upper())
                if name == "_chamar" and filename == "test_api_redefinicao_senha.py":
                    methods.add("POST")
                    route_index = 0
                else:
                    route_index = offset + (2 if name == "_protegida" else 1)
                if len(item.args) > route_index:
                    value = item.args[route_index]
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        routes.add(value.value)
                    elif isinstance(value, ast.JoinedStr):
                        routes.add("".join(part.value if isinstance(part, ast.Constant) else "{id}" for part in value.values))
            if name == "_verificar" and filename == "test_recuperacao_sessao_medico.py":
                methods.add("POST")
                routes.add("/auth/login/verificar")
            if name in {"json", "get"} and isinstance(item.func, ast.Attribute):
                fields.append(clean(ast.unparse(item), 120))
        if isinstance(item, ast.Compare) and any(isinstance(op, ast.Eq) for op in item.ops):
            for part in item.comparators:
                if isinstance(part, ast.Constant) and isinstance(part.value, int) and 100 <= part.value <= 599:
                    statuses.add(part.value)
    return sorted(methods), sorted(routes), sorted(statuses), fields[:8]


def source_cases(path: Path, component: str, kind: str, external: bool, blocked: str = "") -> list[dict]:
    relative = str(path.relative_to(ROOT))
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
    helpers = {item.name: item for item in tree.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}
    cases = []
    for top in tree.body:
        if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)) and top.name.startswith("test_"):
            members = [(top.name, top)]
        elif isinstance(top, ast.ClassDef):
            members = [(f"{top.name}.{item.name}", item) for item in top.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_")]
        else:
            continue
        for name, func in members:
            full = f"{relative}::{name}"
            assertions = []
            for item in ast.walk(func):
                if isinstance(item, ast.Assert):
                    assertions.append(ast.unparse(item.test))
                elif isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and item.func.attr.startswith("assert"):
                    assertions.append(ast.unparse(item))
            assertions = [clean(a, 180) for a in assertions[:12]]
            if not assertions:
                for call in ast.walk(func):
                    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id in helpers:
                        for item in ast.walk(helpers[call.func.id]):
                            if isinstance(item, ast.Assert):
                                assertions.append(clean(ast.unparse(item.test), 180))
                            elif isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and item.func.attr.startswith("assert"):
                                assertions.append(clean(ast.unparse(item), 180))
                    if assertions:
                        break
            methods, routes, statuses, fields = http_metadata(func, path.name, helpers) if kind == "integracao_api_real" else ([], [], [], [])
            spec = SPEC_BY_FILE.get(path.name) or REMOTE_FILES.get(path.name, (None,))[0]
            spec_path = f"openspec/specs/{spec}/spec.md" if spec and (ROOT / "openspec/specs" / spec / "spec.md").exists() else None
            if spec and not spec_path and spec in SPEC_CHANGE:
                candidate = f"openspec/changes/{SPEC_CHANGE[spec]}/specs/{spec}/spec.md"
                spec_path = candidate if (ROOT / candidate).exists() else None
            cases.append({
                "id": identifier(full, component), "node": full, "nome": name.replace("test_", "").replace("_", " "),
                "objetivo": clean(ast.get_docstring(func) or name.replace("test_", "").replace("_", " ")),
                "tipo": kind, "componente": component, "requisito": spec_path,
                "rastreabilidade_formal": "não verificada no Confluence" if spec_path else "não identificada",
                "precondicoes": "ambiente isolado comprovado e autorização explícita" if blocked else ("perfil CLI Xano autenticado; funções puras" if external else "dependências Python instaladas; mocks locais quando usados"),
                "entradas": f"Definidas no código em {relative}:{func.lineno}",
                "resultado_esperado": clean(ast.get_docstring(func) or "; ".join(assertions[:3]) or "As assertions do caso devem passar"),
                "assertions": assertions,
                "dependencia_externa": external, "classe_seguranca": "escrita_isolada" if blocked else "nao_mutavel",
                "motivo_bloqueio": blocked,
                "metodo_http": methods or None, "endpoint": routes or None, "status_http_esperado": statuses or None, "status_http_real": None,
                "exemplo_resposta_sanitizada": None, "assertions_resposta": fields,
            })
            for decorator in func.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute) or decorator.func.attr != "parametrize" or len(decorator.args) < 2:
                    continue
                try:
                    parameter = ast.literal_eval(decorator.args[0])
                    values = ast.literal_eval(decorator.args[1])
                except (ValueError, TypeError, SyntaxError):
                    continue
                template = cases.pop()
                for value in values:
                    variant = dict(template)
                    suffix = f"[{value}]"
                    variant["node"] = full + suffix
                    variant["id"] = identifier(variant["node"], component)
                    variant["nome"] = template["nome"] + suffix
                    variant["entradas"] = template["entradas"] + f"; {parameter}={value}"
                    cases.append(variant)
                break
    return cases


def native_cases() -> list[dict]:
    cases = []
    for function in NATIVE_PURE:
        path = ROOT / "backend/xano/function" / (function + ".xs")
        source = path.read_text(encoding="utf-8")
        # A revisão estática é parte do guardião: novos acessos a dados retiram a função da suite.
        if re.search(r"\b(?:db|api|redis)\.", source):
            raise RuntimeError(f"Função deixou de ser pura: {function}")
        callees = re.findall(r'function\.run\s+"([^"]+)"', source)
        if any(callee not in NATIVE_PURE for callee in callees):
            raise RuntimeError(f"Função chama dependência não revisada: {function}")
        for match in re.finditer(r'(?m)^\s*test "([^"]+)"\s*\{', source):
            name = match.group(1)
            start = match.end() - 1
            depth, end = 0, start
            for pos in range(start, len(source)):
                if source[pos] == "{":
                    depth += 1
                elif source[pos] == "}":
                    depth -= 1
                    if depth == 0:
                        end = pos + 1
                        break
            block = source[start:end]
            checks = []
            for check in re.finditer(r"expect\.[A-Za-z_]+\s*(?:\([^)]*\))?", block):
                following = block[check.end():]
                value = re.match(r"\s*\{\s*value\s*=\s*([^\n}]+)", following)
                checks.append(clean(check.group(0) + (" = " + value.group(1).strip() if value else ""), 180))
            input_line = next((line.strip() for line in block.splitlines() if line.strip().startswith("input =")), "input definido no XanoScript")
            spec = function.split("/")[0]
            spec = {"classificacao": "classificacao-prioridade", "fila": "fila-priorizada", "pacientes": "pacientes", "direcionamento": "direcionamento"}.get(spec)
            relative = str(path.relative_to(ROOT))
            node = f"{relative}::{name}"
            cases.append({
                "id": identifier(node, "Xano"), "node": node, "nome": name, "objetivo": name,
                "tipo": "unitario_nativo", "componente": "Xano", "requisito": f"openspec/specs/{spec}/spec.md" if spec else None,
                "rastreabilidade_formal": "não verificada no Confluence", "precondicoes": "Unit test nativo publicado na branch v1; função pura revisada localmente",
                "entradas": clean(input_line, 500), "resultado_esperado": f"{name}; expectativas nativas: {', '.join(checks)}",
                "assertions": [clean(check, 180) for check in checks],
                "dependencia_externa": True, "classe_seguranca": "nao_mutavel", "motivo_bloqueio": "",
                "metodo_http": None, "endpoint": None, "status_http_esperado": None, "status_http_real": None,
                "exemplo_resposta_sanitizada": None, "assertions_resposta": [], "native_function": function,
                "native_name": name,
            })
    return cases


def catalog(suite: str) -> list[dict]:
    if suite == "reflex":
        return [case for path in sorted((FRONTEND / "tests").glob("test_*.py")) if path.name not in REMOTE_FILES for case in source_cases(path, "Reflex", "integracao_mock" if "patch(" in path.read_text(encoding="utf-8") or "contract" in path.name else "unitario", False)]
    if suite == "xano-safe":
        return [case for path in (ROOT / "tests/api/test_ordenacao.py", ROOT / "tests/api/test_selecao_entre_filas.py") for case in source_cases(path, "Xano", "integracao_funcao_pura", True)] + native_cases()
    if suite == "controlled":
        paths = [FRONTEND / "tests" / name for name in REMOTE_FILES if (FRONTEND / "tests" / name).exists()]
        paths += [ROOT / "tests/api" / name for name in REMOTE_FILES if (ROOT / "tests/api" / name).exists()]
        cases = [case for path in paths for case in source_cases(path, "Xano", "integracao_api_real", True, REMOTE_FILES[path.name][1])]
        for case in cases:
            if case["node"].endswith("test_catalogo_sintomas_46_ativos") or case["node"].endswith("test_me_recusa_requisicao_sem_token_ou_com_token_adulterado"):
                case["classe_seguranca"] = "nao_mutavel"
                case["motivo_bloqueio"] = "Consulta HTTP sem escrita; dependência de URL e/ou token de teste não configurada nesta execução"
                case["precondicoes"] = "URL Xano válida; token de leitura quando exigido"
        return cases
    if suite == "e2e":
        return source_cases(ROOT / "tests/e2e/test_publico.py", "Reflex", "e2e", True)
    raise ValueError(suite)


def junit_write(cases: list[dict], path: Path, suite: str) -> None:
    counts = Counter(c["status"] for c in cases)
    testsuite = ET.Element("testsuite", name=suite, tests=str(len(cases)), failures=str(counts["FAIL"]), errors=str(counts["ERROR"]), skipped=str(counts["SKIPPED"] + counts["NOT_RUN"]), time=str(round(sum(c["duracao_segundos"] for c in cases), 3)))
    for case in cases:
        node = ET.SubElement(testsuite, "testcase", name=case["id"] + " " + case["nome"], classname=case["componente"] + "." + case["tipo"], time=str(case["duracao_segundos"]))
        if case["status"] in ("FAIL", "ERROR"):
            ET.SubElement(node, "failure" if case["status"] == "FAIL" else "error", message=case["motivo"] or case["resultado_obtido"]).text = case["motivo"] or case["resultado_obtido"]
        elif case["status"] in ("SKIPPED", "NOT_RUN"):
            ET.SubElement(node, "skipped", message=case["motivo"] or case["status"])
    ET.ElementTree(testsuite).write(path, encoding="utf-8", xml_declaration=True)


def execution_status(cases: list[dict], infra: bool) -> str:
    counts = Counter(case["status"] for case in cases)
    if infra:
        return "ERRO_INFRAESTRUTURA"
    if counts["FAIL"] or counts["ERROR"]:
        return "REPROVADA"
    if counts["NOT_RUN"] or counts["SKIPPED"]:
        return "PARCIAL" if counts["PASS"] else "BLOQUEADA"
    return "APROVADA" if counts["PASS"] else "ERRO_INFRAESTRUTURA"


def markdown_write(data: dict, path: Path) -> None:
    cases = data["casos"]
    counts = Counter(c["status"] for c in cases)
    lines = ["# Evidência de execução de testes", "", f"Execução: `{data['execucao_id']}`", f"UTC: {data['data_utc']}", f"Commit: `{data['commit']}` · Branch: `{data['branch']}`", f"Suite: `{data['suite']}` · Ambiente: `{data['ambiente']}`", f"Resultado da execução: **{data.get('status_execucao', execution_status(cases, data.get('falha_infraestrutura', False)))}**", "", f"PASS: {counts['PASS']} · FAIL: {counts['FAIL']} · ERROR: {counts['ERROR']} · SKIPPED: {counts['SKIPPED']} · NOT_RUN: {counts['NOT_RUN']}", "", "| ID | Requisito | Resultado esperado | Resultado obtido | Status | Duração (s) |", "|---|---|---|---|---|---:|"]
    if data.get("alvo_xano"):
        lines.insert(7, f"Xano: branch `{data['alvo_xano']['branch']}`, datasource `{data['alvo_xano']['datasource']}` (funções puras)")
    def cell(value: object) -> str:
        return clean(value or "—", 160).replace("|", "\\|").replace("\n", " ")
    for c in cases:
        lines.append(f"| {c['id']} | {cell(c['requisito'])} | {cell(c['resultado_esperado'])} | {cell(c['resultado_obtido'])} | {c['status']} | {c['duracao_segundos']:.3f} |")
    failures = [c for c in cases if c["status"] in ("FAIL", "ERROR")]
    lines += ["", "## Falhas e erros", ""]
    lines += [f"- `{c['id']}`: {clean(c['motivo'])}" for c in failures] or ["- Nenhum nesta execução."]
    lines += ["", "## Limitações", ""]
    lines += [f"- {clean(x)}" for x in data["limitacoes"]] or ["- Nenhuma registrada."]
    lines += ["", "## Arquivos de evidência", "", "- `resultados.xml`: JUnit XML", "- `resultados.json`: casos, assertions e ambiente", "- `pytest.xml`: saída sanitizada do pytest, quando executado", "- `pytest.log`: saída sanitizada do pytest, quando executado", "- `ui/`: screenshots e traces de falhas de interface, quando disponíveis", ""]
    if (path.parent / "gerador.xml").exists():
        lines.insert(-1, "- `gerador.xml`: autotestes do mecanismo de evidências")
    path.write_text("\n".join(lines), encoding="utf-8")


def github_summary_write(data: dict, path: Path) -> None:
    """Publica um resumo curto no Actions; o inventário completo fica no artifact."""
    cases = data["casos"]
    counts = Counter(case["status"] for case in cases)
    lines = [
        f"## {data['suite']}: {data['status_execucao']}",
        "",
        "| PASS | FAIL | ERROR | SKIPPED | NOT_RUN |",
        "|---:|---:|---:|---:|---:|",
        f"| {counts['PASS']} | {counts['FAIL']} | {counts['ERROR']} | {counts['SKIPPED']} | {counts['NOT_RUN']} |",
        "",
    ]
    failures = [case for case in cases if case["status"] in ("FAIL", "ERROR")]
    if failures:
        lines += ["Falhas:", ""]
        lines += [f"- `{case['id']}`: {clean(case['motivo'], 200)}" for case in failures[:10]]
        if len(failures) > 10:
            lines.append(f"- Mais {len(failures) - 10} no artifact.")
        lines.append("")
    if data["limitacoes"]:
        lines += ["Limitações:", ""]
        lines += [f"- {clean(item, 200)}" for item in data["limitacoes"][:5]]
        lines.append("")
    lines += ["XML, JSON e relatório completo: artifact de evidências deste job.", ""]
    with path.open("a", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")


def run_pytest(suite: str, out: Path, cases: list[dict]) -> tuple[str | None, int | None]:
    if suite == "reflex":
        paths = ["tests/" + p.name for p in sorted((FRONTEND / "tests").glob("test_*.py")) if p.name not in REMOTE_FILES]
        cwd = FRONTEND
    elif suite == "xano-safe":
        paths, cwd = ["tests/api/test_ordenacao.py", "tests/api/test_selecao_entre_filas.py"], ROOT
    elif suite == "controlled":
        paths = ["tests/" + p.name for p in sorted((FRONTEND / "tests").glob("test_*.py")) if p.name in REMOTE_FILES]
        cwd = FRONTEND
    else:
        paths, cwd = ["tests/e2e/test_publico.py"], ROOT
    args = [sys.executable, "-m", "pytest", "-q", *paths, f"--junitxml={out / 'pytest.xml'}", "-o", "junit_family=xunit2"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + str(FRONTEND) + os.pathsep + env.get("PYTHONPATH", "")
    if suite == "controlled":
        env["EVIDENCE_HTTP_EVENTS"] = str(out / "http-events.jsonl")
        args += ["-p", "scripts.pytest_http_evidence"]
    with tempfile.TemporaryDirectory(prefix="xano-config-") as config_dir:
        if suite == "xano-safe" and os.getenv("XANO_CLI_CONFIG_YAML"):
            config = Path(config_dir) / "credentials.yaml"
            config.write_text(os.environ["XANO_CLI_CONFIG_YAML"], encoding="utf-8")
            config.chmod(0o600)
            env["XANO_CONFIG"] = str(config)
        if suite == "e2e":
            args += ["--screenshot=only-on-failure", f"--output={out / 'ui'}", "--tracing=retain-on-failure"]
        proc = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, timeout=600, check=False)
    log = clean(proc.stdout + "\n" + proc.stderr, 20000)
    (out / "pytest.log").write_text(log, encoding="utf-8")
    return (None if (out / "pytest.xml").exists() else "pytest não produziu XML; erro de infraestrutura/coleta", proc.returncode)


def collect_pytest_results(out: Path, cases: list[dict]) -> None:
    xml = out / "pytest.xml"
    if not xml.exists():
        return
    tree = ET.parse(xml)
    by_key = {c["node"].split("::")[-1]: c for c in cases}
    seen = set()
    for entry in tree.iter("testcase"):
        name = entry.get("name", "")
        cls = entry.get("classname", "").split(".")[-1]
        key = f"{cls}.{name}" if cls and (cls.startswith("Test") or cls.endswith("Test")) else name
        case = by_key.get(key) or by_key.get(name)
        if case is None and "[" in name:
            # pytest-playwright acrescenta o navegador ao nome do caso.
            base = name.split("[", 1)[0]
            case = by_key.get(f"{cls}.{base}") or by_key.get(base)
        if case is None:
            continue
        seen.add(case["id"])
        case["duracao_segundos"] = float(entry.get("time", "0"))
        if entry.find("failure") is not None:
            failure = entry.find("failure")
            case["status"], case["motivo"] = "FAIL", clean(failure.get("message", "assertion falhou"))
            case["resultado_obtido"] = "Assertion falhou"
        elif entry.find("error") is not None:
            error = entry.find("error")
            case["status"], case["motivo"] = "ERROR", clean(error.get("message", "erro"))
            case["resultado_obtido"] = "Erro durante o teste"
        elif entry.find("skipped") is not None:
            skipped = entry.find("skipped")
            case["status"], case["motivo"] = "SKIPPED", clean(skipped.get("message", "ignorado"))
            case["resultado_obtido"] = "Ignorado pelo pytest"
        else:
            case["status"] = "PASS"
            case["motivo"] = ""
            case["resultado_obtido"] = "Assertions executadas e satisfeitas pelo pytest"
    for case in cases:
        if case["id"] not in seen:
            case["motivo"] = "Não coletado pelo pytest; consulte pytest.log"
    for element in tree.iter():
        element.attrib.update({key: clean(value, 3000) for key, value in element.attrib.items()})
        if element.text:
            element.text = clean(element.text, 10000)
        if element.tail:
            element.tail = clean(element.tail, 10000)
    tree.write(xml, encoding="utf-8", xml_declaration=True)


def collect_http_results(out: Path, cases: list[dict]) -> None:
    path = out / "http-events.jsonl"
    if not path.exists():
        return
    by_key = {case["node"].split("::")[-1]: case for case in cases}
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        case = by_key.get(record["node"].split("::")[-1])
        if not case:
            continue
        events = record["eventos"]
        case["status_http_real"] = [event["status"] for event in events]
        case["exemplo_resposta_sanitizada"] = [event["resposta"] for event in events]
        case["metodo_http"] = [event["metodo"] for event in events]
        case["endpoint"] = [event["endpoint"] for event in events]
        if events:
            case["resultado_obtido"] += "; HTTP " + ", ".join(f"{event['metodo']} {event['endpoint']} → {event['status']}" for event in events)


def preflight_xano() -> str | None:
    if shutil.which("xano") is None:
        return "CLI Xano não instalado"
    if not (os.getenv("XANO_CLI_CONFIG_YAML") or os.getenv("XANO_CONFIG") or Path.home().joinpath(".xano/credentials.yaml").exists()):
        return "Credencial de CLI Xano ausente"
    env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="xano-preflight-") as tmp:
        if os.getenv("XANO_CLI_CONFIG_YAML"):
            config = Path(tmp) / "credentials.yaml"
            config.write_text(os.environ["XANO_CLI_CONFIG_YAML"], encoding="utf-8")
            config.chmod(0o600)
            env["XANO_CONFIG"] = str(config)
        try:
            proc = subprocess.run(["xano", "profile", "me", "-p", env.get("XANO_TEST_PROFILE") or "ps-impacta", "-o", "json"], env=env, text=True, capture_output=True, timeout=20, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return "CLI Xano indisponível ou sem resposta; funções não executadas"
    if proc.returncode:
        return "Autenticação/conectividade do CLI Xano indisponível; funções não executadas"
    return None


def run_native(cases: list[dict]) -> list[str]:
    native = [case for case in cases if case["tipo"] == "unitario_nativo"]
    if not native:
        return []
    env = os.environ.copy()
    profile = env.get("XANO_TEST_PROFILE") or "ps-impacta"
    with tempfile.TemporaryDirectory(prefix="xano-native-") as tmp:
        if env.get("XANO_CLI_CONFIG_YAML"):
            config = Path(tmp) / "credentials.yaml"
            config.write_text(env["XANO_CLI_CONFIG_YAML"], encoding="utf-8")
            config.chmod(0o600)
            env["XANO_CONFIG"] = str(config)
        try:
            listing = subprocess.run(["xano", "unit_test", "list", "-p", profile, "--branch", "v1", "--per_page", "10000", "-o", "json"], env=env, text=True, capture_output=True, timeout=40, check=False)
            if listing.returncode:
                return ["Listagem dos unit tests nativos falhou; casos nativos permanecem NOT_RUN"]
            payload = json.loads(listing.stdout)
            if payload.get("nextPage"):
                return ["Listagem dos unit tests nativos foi paginada; execução incompleta evitada"]
            published = {(item.get("obj_name"), item.get("name")): item for item in payload.get("items", [])}
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return ["Listagem dos unit tests nativos indisponível; casos nativos permanecem NOT_RUN"]
        limitations = []
        for index, case in enumerate(native, 1):
            record = published.get((case["native_function"], case["native_name"]))
            if not record:
                case["motivo"] = "Unit test nativo não encontrado na branch v1 publicada"
                limitations.append(f"{case['id']}: unit test nativo ausente no servidor")
                continue
            started = time.perf_counter()
            time.sleep(2.5)
            try:
                proc = subprocess.run(["xano", "unit_test", "run", str(record["id"]), "-p", profile, "--branch", "v1", "-o", "json"], env=env, text=True, capture_output=True, timeout=50, check=False)
                output = json.loads(proc.stdout)
                statuses = [str(item.get("status", "")).lower() for item in output.get("results", [])]
                case["duracao_segundos"] = round(time.perf_counter() - started, 3)
                if proc.returncode == 0 and output.get("status") == "ok" and statuses and all(status == "pass" for status in statuses):
                    case["status"] = "PASS"
                    case["resultado_obtido"] = f"{len(statuses)} resultado(s) nativo(s) PASS"
                elif any(status in {"fail", "failed"} for status in statuses):
                    case["status"] = "FAIL"
                    case["resultado_obtido"] = f"Status nativo: {statuses}"
                    case["motivo"] = clean(output.get("message") or "Expectativa nativa não satisfeita")
                else:
                    case["status"] = "ERROR"
                    case["resultado_obtido"] = "CLI não retornou status de assertion confiável"
                    case["motivo"] = clean(output.get("message") or "Resposta nativa inválida")
            except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
                case["status"] = "ERROR"
                case["duracao_segundos"] = round(time.perf_counter() - started, 3)
                case["resultado_obtido"] = "Falha de infraestrutura do CLI"
                case["motivo"] = type(exc).__name__
            if index % 10 == 0 or index == len(native):
                print(f"Unit tests nativos Xano: {index}/{len(native)} processados", flush=True)
        return limitations


def controlled_gate() -> str | None:
    if os.getenv("XANO_ISOLATED_CONFIRMATION") != "CONFIRMO_WORKSPACE_DESCARTAVEL":
        return "Confirmação explícita do workspace descartável ausente"
    host = os.getenv("XANO_ISOLATED_API_HOST", "").strip().lower()
    if not host or "/" in host or ":" in host:
        return "XANO_ISOLATED_API_HOST inválido ou ausente"
    for key in ("XANO_AUTH_API_URL", "XANO_TRIAGEM_API_URL", "XANO_API_URL"):
        url = os.getenv(key, "")
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != host or parsed.username or parsed.password:
            return f"{key} não aponta para o host isolado confirmado"
    needed = ("TEST_RECEPCAO_TOKEN", "TOTEM_CHAVE", "TEST_ADMIN_EMAIL", "TEST_ADMIN_SENHA", "TEST_RECEPCAO_EMAIL", "TEST_RECEPCAO_SENHA", "TEST_MEDICO_EMAIL", "TEST_MEDICO_SENHA")
    missing = [key for key in needed if not os.getenv(key)]
    if missing:
        return "Credenciais de teste ausentes: " + ", ".join(missing)
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=["reflex", "xano-safe", "controlled", "e2e"], required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--require-execution", action="store_true", help="Falha se nenhum teste da suite for executado")
    parser.add_argument("--execute-controlled", action="store_true", help="Exige confirmação e host isolado; executa só testes HTTP do frontend")
    args = parser.parse_args()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    execution_id = os.getenv("GITHUB_RUN_ID", "local") + "-" + uuid.uuid4().hex[:12]
    out = args.output or ROOT / "test-evidence" / execution_id / args.suite
    if not out.is_absolute():
        out = ROOT / out
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    catalog_error = None
    try:
        cases = catalog(args.suite)
    except (OSError, SyntaxError, RuntimeError) as exc:
        cases = []
        catalog_error = clean(f"Catálogo de testes indisponível: {type(exc).__name__}: {exc}")
    for case in cases:
        case.update(status="NOT_RUN", resultado_obtido="Não executado", duracao_segundos=0.0, motivo=case["motivo_bloqueio"])
    limitations = []
    infra = False
    blocked = catalog_error
    if args.suite == "xano-safe":
        limitations.append("Pureza verificada nos XanoScripts versionados; equivalência integral do código remoto da branch v1 não foi comparada nesta execução.")
    if catalog_error:
        infra = True
    if catalog_error:
        limitations.append(catalog_error)
    elif args.suite == "controlled":
        if args.execute_controlled:
            blocked = controlled_gate()
            if blocked:
                limitations.append("Execução de escrita recusada pelo guardião de isolamento.")
            else:
                for case in cases:
                    if case["node"].startswith("tests/api/"):
                        case["motivo"] = "Teste CLI fixa branch v1; não habilitado nesta suite HTTP isolada"
                limitations.append("Cenários CLI com branch v1 fixa permanecem NOT_RUN; workspace descartável deve ser limpo após a execução HTTP.")
        else:
            blocked = "Suite de escrita não executada: isolamento do workspace e dos endpoints não comprovado; autorização explícita necessária."
    elif args.suite == "e2e" and not os.getenv("REFLEX_E2E_BASE_URL"):
        blocked = "REFLEX_E2E_BASE_URL ausente; servidor Reflex e navegador Playwright não disponíveis nesta execução."
    elif args.suite == "xano-safe":
        blocked = preflight_xano()
        if blocked and (args.require_execution or ("ausente" not in blocked and "não instalado" not in blocked)):
            infra = True
    if blocked:
        limitations.append(blocked)
        for case in cases:
            case["motivo"] = blocked if not case["motivo"] else case["motivo"] + "; " + blocked
    if not blocked:
        try:
            problem, code = run_pytest(args.suite, out, cases)
            collect_pytest_results(out, cases)
            if args.suite == "controlled":
                collect_http_results(out, cases)
            if args.suite == "xano-safe":
                native_limitations = run_native(cases)
                limitations.extend(native_limitations)
                infra = infra or bool(native_limitations)
            if problem:
                limitations.append(problem)
                infra = True
            if code and not any(c["status"] in ("FAIL", "ERROR") for c in cases):
                limitations.append(f"pytest terminou com código {code}; verifique coleta/infraestrutura em pytest.log")
                infra = True
        except Exception as exc:
            limitations.append(f"Falha de infraestrutura/coleta: {type(exc).__name__}")
            infra = True
    if any(c["status"] == "NOT_RUN" for c in cases):
        limitations.append("Casos NOT_RUN não constituem aprovação nem cobertura executada.")
    if infra:
        cases.append({
            "id": "CT-INFRA-" + args.suite.upper().replace("-", "_"),
            "node": "infraestrutura::" + args.suite,
            "nome": "Disponibilidade da infraestrutura de testes",
            "objetivo": "Verificar que a suite pode ser executada e que o resultado foi coletado",
            "tipo": "infraestrutura", "componente": "CLI Xano" if args.suite == "xano-safe" else "pytest",
            "requisito": None, "rastreabilidade_formal": "não aplicável",
            "precondicoes": "ferramentas e conectividade disponíveis", "entradas": "configuração local/CI",
            "resultado_esperado": "Suite iniciada e relatório JUnit gerado",
            "assertions": ["Processo retorna resultado coletável"],
            "dependencia_externa": True, "classe_seguranca": "nao_mutavel",
            "motivo_bloqueio": "", "metodo_http": None, "endpoint": None,
            "status_http_esperado": None, "status_http_real": None,
            "exemplo_resposta_sanitizada": None, "assertions_resposta": [],
            "status": "ERROR", "resultado_obtido": "Suite não executada ou coleta incompleta",
            "duracao_segundos": 0.0, "motivo": "; ".join(limitations),
        })
    for case in cases:
        case["evidencias"] = ["resultados.xml", "resultados.json", "resumo.md"]
        if (out / "pytest.xml").exists():
            case["evidencias"].extend(["pytest.xml", "pytest.log"])
        if (out / "http-events.jsonl").exists():
            case["evidencias"].append("http-events.jsonl")
        if args.suite == "e2e" and case["status"] in ("FAIL", "ERROR"):
            case["evidencias"].append("ui/")
    if not cases:
        limitations.append("Nenhum caso encontrado no catálogo; verifique descoberta.")
        infra = True
    working_tree_clean = not bool(git("status", "--porcelain"))
    if not working_tree_clean:
        limitations.append("Árvore de trabalho com alterações locais: o commit SHA identifica a base, não todo o código desta execução.")
    try:
        reflex_version = importlib.metadata.version("reflex")
    except importlib.metadata.PackageNotFoundError:
        reflex_version = "não instalado"
    data = {
        "execucao_id": execution_id, "data_utc": timestamp, "commit": git("rev-parse", "HEAD"),
        "branch": os.getenv("GITHUB_REF_NAME") or git("branch", "--show-current"),
        "suite": args.suite, "ambiente": os.getenv("GITHUB_ACTIONS") and "GitHub Actions" or "local",
        "alvo_xano": {"branch": "v1", "datasource": "live", "observacao": "Somente funções puras com dados sintéticos"} if args.suite == "xano-safe" else None,
        "ferramentas": {"python": platform.python_version(), "pytest": importlib.metadata.version("pytest") if importlib.util.find_spec("pytest") else "não instalado", "reflex": reflex_version, "xano_cli": clean(subprocess.run(["xano", "--version"], text=True, capture_output=True).stdout.strip()) if shutil.which("xano") else "não instalado"},
        "github_run_id": os.getenv("GITHUB_RUN_ID"), "github_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "arvore_trabalho_limpa": working_tree_clean,
        "limitacoes": limitations, "falha_infraestrutura": infra, "casos": cases,
    }
    data["status_execucao"] = execution_status(cases, infra)
    junit_write(cases, out / "resultados.xml", args.suite)
    (out / "resultados.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_write(data, out / "resumo.md")
    counts = Counter(c["status"] for c in cases)
    print(f"{args.suite}: " + " ".join(f"{status}={counts[status]}" for status in ("PASS", "FAIL", "ERROR", "SKIPPED", "NOT_RUN")))
    print(f"Evidências: {out}")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        github_summary_write(data, Path(os.environ["GITHUB_STEP_SUMMARY"]))
    return 1 if counts["FAIL"] or counts["ERROR"] or infra or (args.require_execution and not counts["PASS"]) else 0


if __name__ == "__main__":
    sys.exit(main())

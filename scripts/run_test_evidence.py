"""Executa suites permitidas e produz evidências sem registrar dados sensíveis.

Uso: python scripts/run_test_evidence.py --suite reflex|xano-safe|controlled|e2e
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
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
    "test_acompanhamento.py": ("acompanhamento-administrador", "escrita: cenário sintético de fila com limpeza remota"),
    "test_painel.py": ("painel-publico", "escrita: cenário sintético de fila com chamadas e limpeza remota"),
}
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


def source_cases(path: Path) -> list[dict]:
    """Descobre vínculos técnicos; metadados funcionais pertencem só ao catálogo."""
    relative = path.relative_to(ROOT).as_posix()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
    cases = []
    for top in tree.body:
        if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)) and top.name.startswith("test_"):
            members = [(top.name, top)]
        elif isinstance(top, ast.ClassDef):
            members = [(f"{top.name}.{f.name}", f) for f in top.body if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and f.name.startswith("test_")]
        else:
            continue
        for name, func in members:
            selectors = [f"{relative}::{name}"]
            for decorator in func.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute) or decorator.func.attr != "parametrize":
                    continue
                # Somente literais estáveis ou IDs explícitos; nunca repr de objetos.
                try:
                    values = ast.literal_eval(decorator.args[1])
                    ids = next((ast.literal_eval(k.value) for k in decorator.keywords if k.arg == "ids"), None)
                    if ids is None:
                        if not all(isinstance(v, (str, int, bool)) for v in values):
                            raise ValueError()
                        ids = [str(v) for v in values]
                    if len(ids) != len(values) or len(set(ids)) != len(ids):
                        raise ValueError()
                    selectors = [f"{selector}[{key}]" for selector in selectors for key in ids]
                except (ValueError, TypeError, SyntaxError, IndexError):
                    raise ValueError("Parametrização sem identidade estável reconhecível") from None
            cases.extend({"node": selector} for selector in selectors)
    return cases


def native_cases() -> list[dict]:
    cases = []
    for function in NATIVE_PURE:
        path = ROOT / "backend/xano/function" / (function + ".xs")
        source = path.read_text(encoding="utf-8")
        for name in re.findall(r'(?m)^\s*test "([^"]+)"\s*\{', source):
            cases.append({"node": f"{path.relative_to(ROOT).as_posix()}::{name}", "native_function": function, "native_name": name})
    return cases


CATALOG_PATH = ROOT / 'tests/catalogo_testes.json'
SUITES = ('autotestes', 'reflex', 'xano-static', 'xano-safe', 'controlled', 'e2e')
STATES = ('PASSED', 'FAILED', 'ERROR', 'SKIPPED', 'NOT_RUN', 'BLOCKED')
UNEXECUTED = {'SKIPPED', 'NOT_RUN', 'BLOCKED'}
FORMAT_VERSION = 2
PUBLIC_FILES = ('resultados.json', 'resultados.xml', 'resumo.md', 'pytest.xml', 'pytest.log', 'http-events.jsonl', 'servidor.log')


def state(value: str) -> str:
    value = {'PASS': 'PASSED', 'FAIL': 'FAILED'}.get(value, value)
    if value not in STATES:
        raise ValueError('Estado de caso desconhecido')
    return value


def case_key(case: dict) -> tuple:
    return case['id'], case.get('variante', '')


def diagnostic(code: str, message: str, **context) -> dict:
    return {'codigo': code, 'mensagem': message, **context}


def discover(suite: str) -> list[dict]:
    """Descoberta sem importar testes ou carregar .env; nunca inicia rede."""
    if suite == 'reflex':
        paths = [p for p in sorted((FRONTEND / 'tests').glob('test_*.py')) if p.name not in REMOTE_FILES]
    elif suite == 'xano-safe':
        paths = [ROOT / 'tests/api/test_ordenacao.py', ROOT / 'tests/api/test_selecao_entre_filas.py']
    elif suite in ('xano-static', 'controlled'):
        paths = [ROOT / 'tests/api/test_base_compartilhada.py']
        if suite == 'controlled':
            paths += [p for base in (FRONTEND / 'tests', ROOT / 'tests/api') for p in sorted(base.glob('test_*.py')) if p.name in REMOTE_FILES]
    elif suite == 'autotestes':
        paths = sorted((ROOT / 'tests').glob('test_*.py'))
    elif suite == 'e2e':
        paths = [ROOT / 'tests/e2e/test_publico.py']
    else:
        raise ValueError('Suíte desconhecida')
    cases = [c for p in paths for c in source_cases(p)]
    if suite == 'xano-static':
        cases = [c for c in cases if any('::' + cls + '.' in c['node'] for cls in ('AuditoriaTest', 'ParametrosTest', 'StatusEquipeTest'))]
    if suite == 'controlled':
        cases = [c for c in cases if 'test_base_compartilhada.py' not in c['node'] or '::ConsultaSemTokenTest.' in c['node']]
    return cases + (native_cases() if suite == 'xano-safe' else [])


def load_catalog(path: Path = CATALOG_PATH) -> list[dict]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if payload.get('versao') != 1:
        raise ValueError('Versão de catálogo inválida')
    ids, selectors, aliases, expanded = set(), set(), set(), []
    spec_texts = {}
    for record in payload['casos']:
        if record['id'] in ids:
            raise ValueError('ID duplicado no catálogo')
        ids.add(record['id'])
        for ref in record['referencias']['openspec']:
            ref_path = (ROOT / ref['arquivo']).resolve()
            if not ref_path.is_relative_to(ROOT / 'openspec'):
                raise ValueError('Referência fora do OpenSpec')
            if ref['arquivo'] not in spec_texts:
                spec_texts[ref['arquivo']] = ref_path.read_text(encoding='utf-8')
            if ref.get('cenario') and f"#### Scenario: {ref['cenario']}\n" not in spec_texts[ref['arquivo']]:
                raise ValueError('Cenário OpenSpec inexistente')
        if any(ref.get('estado') != 'PENDENTE' for ref in record['referencias']['formais']):
            raise ValueError('Referência formal não conferida nesta change')

        if record['tipo'] not in {'UNITARIO','INTEGRACAO','E2E','ESTATICO'} or record['modo_dependencia'] not in {'LOCAL','MOCK','REAL'} or record['suite'] not in SUITES:
            raise ValueError('Classificação de caso inválida')
        variants = record.get('variantes') or [{'chave': '', 'seletor': record['seletor'], 'aliases_historicos': record.get('aliases_historicos', [])}]
        keys = set()
        for variant in variants:
            selector, key = variant['seletor'], variant['chave']
            if selector in selectors or key in keys or (record.get('variantes') and not key):
                raise ValueError('Seletor ou variante ambígua no catálogo')
            selectors.add(selector); keys.add(key)
            for alias in variant.get('aliases_historicos', []):
                if alias in aliases:
                    raise ValueError('Alias histórico ambíguo')
                aliases.add(alias)
            case = {k:v for k,v in record.items() if k != 'variantes'}
            case.update(node=selector, variante=key, aliases_historicos=variant.get('aliases_historicos', []), dependencia_externa=record['modo_dependencia']=='REAL')
            expanded.append(case)
    return expanded


def catalog(suite: str, path: Path = CATALOG_PATH) -> list[dict]:
    cases = [c for c in load_catalog(path) if c['suite'] == suite]
    if suite in {'reflex', 'xano-static', 'autotestes'} and any(c['modo_dependencia'] == 'REAL' or c['classe_seguranca'] != 'nao_mutavel' for c in cases):
        raise ValueError('Dependência real ou escrita recusada em suíte local')
    actual = [c['node'] for c in discover(suite)]
    registered = [c['node'] for c in cases]
    if len(actual) != len(set(actual)) or set(actual) != set(registered):
        raise ValueError('Divergência descoberta/catálogo: sem registro=%d; removidos=%d' % (len(set(actual)-set(registered)), len(set(registered)-set(actual))))
    return cases


def axes(cases: list[dict], diagnostics=(), obligations=()) -> tuple[str, str]:
    counts = Counter(state(c['status']) for c in cases)
    technical = 'ERROR' if diagnostics or counts['ERROR'] else 'FAILED' if counts['FAILED'] else 'PASSED'
    useful = counts['PASSED'] + counts['FAILED']
    pending = any(counts[s] for s in UNEXECUTED | {'ERROR'}) or bool(diagnostics) or bool(obligations)
    if useful:
        level = 'PARCIAL' if pending else 'COMPLETA'
    else:
        level = 'BLOQUEADA' if counts['BLOCKED'] or counts['ERROR'] or diagnostics else 'NAO_EXECUTADA'
    return technical, level


def execution_status(cases: list[dict], infra: bool = False) -> str:
    """Compatibilidade de leitura; os eixos canônicos são calculados por axes."""
    technical, level = axes(cases, [True] if infra else [])
    if technical == 'ERROR': return 'ERRO_INFRAESTRUTURA'
    if technical == 'FAILED': return 'REPROVADA'
    return 'APROVADA' if level == 'COMPLETA' else level


def gate(data: dict, require_execution=False, require_complete=False) -> int:
    if data['status_tecnico'] != 'PASSED': return 1
    if require_execution and not any(c['status'] in {'PASSED','FAILED','ERROR'} for c in data['casos']): return 1
    if require_complete and data['nivel_validacao'] != 'COMPLETA': return 1
    return 0


def new_output(path: Path) -> Path:
    path = path.resolve()
    if path.exists() and any(path.iterdir()):
        raise FileExistsError('Destino não vazio: use outro diretório; histórico preservado')
    path.mkdir(parents=True, exist_ok=True)
    return path


def public_url(value: str | None) -> str | None:
    if not value: return None
    try:
        parsed = urlparse(value)
    except ValueError:
        return None
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.query or parsed.fragment:
        return None
    if parsed.hostname == 'github.com' and re.fullmatch(r'/[\w.-]+/[\w.-]+/actions/runs/\d+(?:/attempts/\d+|/artifacts/\d+)?', parsed.path):
        return value
    if parsed.hostname == 'trello.com' and re.fullmatch(r'/c/[\w-]+(?:/[\w%.-]+)?', parsed.path):
        return value
    return None


def metadata(suite: str, started: datetime) -> dict:
    observed = git('rev-parse','HEAD')
    run = os.getenv('GITHUB_RUN_ID'); attempt = os.getenv('GITHUB_RUN_ATTEMPT')
    repo = os.getenv('GITHUB_REPOSITORY','')
    link = public_url(f'https://github.com/{repo}/actions/runs/{run}') if run else None
    return {
        'versao_formato': FORMAT_VERSION, 'execucao_id': f'{run or "local"}-{uuid.uuid4().hex[:12]}',
        'suite': suite, 'escopo_validacao': f'Casos automatizados selecionados: {suite}; aceite integrado/manual fora deste escopo.',
        'inicio_utc': started.isoformat(), 'data_utc': started.isoformat(),
        'commit': observed, 'sha_esperado': os.getenv('GITHUB_SHA'), 'sha_observado': observed,
        'branch': clean(os.getenv('GITHUB_REF_NAME') or git('branch','--show-current'),120),
        'arvore_trabalho_limpa': not bool(git('status','--porcelain')),
        'ambiente': 'GitHub Actions' if os.getenv('GITHUB_ACTIONS') else 'local',
        'github_run_id': run, 'github_run_attempt': attempt,
        'github_job': os.getenv('GITHUB_JOB'), 'github_url': link,
        'ferramentas': {'python': platform.python_version(), **{p: package_version(p) for p in ('pytest','reflex','playwright')}},
        'dependencias': [], 'origens': [], 'diagnosticos': [], 'obrigacoes_pendentes': [], 'limitacoes': [], 'casos': [],
    }


def package_version(name: str) -> str:
    try: return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError: return 'não instalado'


def finalize(data: dict) -> dict:
    for case in data['casos']:
        case['status'] = state(case['status'])
        if case['status'] in UNEXECUTED and not case.get('motivo'):
            raise ValueError('Estado sem execução exige motivo')
        if not isinstance(case.get('duracao_segundos', 0), (int,float)) or case.get('duracao_segundos', 0) < 0:
            raise ValueError('Duração inválida')
    data['status_tecnico'], data['nivel_validacao'] = axes(data['casos'], data.get('diagnosticos'), data.get('obrigacoes_pendentes'))
    data['aprovacao_integral'] = data['status_tecnico'] == 'PASSED' and data['nivel_validacao'] == 'COMPLETA'
    data['totais'] = {s: sum(c['status']==s for c in data['casos']) for s in STATES}
    data['totais_por_tipo'] = dict(Counter(c['tipo'] for c in data['casos']))
    data['totais_por_componente'] = dict(Counter(c['componente'] for c in data['casos']))
    data['totais_por_dependencia'] = dict(Counter(c['modo_dependencia'] for c in data['casos']))
    data['total_casos'] = len(data['casos'])
    data['fim_utc'] = datetime.now(timezone.utc).isoformat()
    data['duracao_segundos'] = round((datetime.fromisoformat(data['fim_utc'])-datetime.fromisoformat(data['inicio_utc'])).total_seconds(),3)
    data['status_execucao'] = execution_status(data['casos'], bool(data.get('diagnosticos')))
    data['falha_infraestrutura'] = bool(data.get('diagnosticos'))
    if not data.get('arvore_trabalho_limpa'):
        limitation = 'Árvore de trabalho com alterações locais: SHA identifica apenas a base.'
        if limitation not in data['limitacoes']: data['limitacoes'].append(limitation)
    return data


def junit_write(cases: list[dict], path: Path, suite: str, data: dict | None = None) -> None:
    counts = Counter(state(c['status']) for c in cases)
    root = ET.Element('testsuite', name=suite, tests=str(len(cases)), failures=str(counts['FAILED']), errors=str(counts['ERROR']), skipped=str(sum(counts[s] for s in UNEXECUTED)), time=str(sum(c.get('duracao_segundos',0) for c in cases)))
    props = ET.SubElement(root,'properties')
    for key in ('versao_formato','execucao_id','commit','github_run_id','github_run_attempt','status_tecnico','nivel_validacao','inicio_utc','fim_utc','duracao_segundos'):
        if data and data.get(key) is not None: ET.SubElement(props,'property',name=key,value=str(data[key]))
    if data:
        ET.SubElement(props,'property', name='diagnosticos', value=json.dumps(data.get('diagnosticos',[]),ensure_ascii=False))
    for c in cases:
        status = state(c['status']); name=c['id'] + (f"[{c['variante']}]" if c.get('variante') else '')
        if c.get('origem_suite'): name = c['origem_suite'] + '::' + name
        entry=ET.SubElement(root,'testcase',name=name,classname=f"{c.get('componente','')}.{c.get('tipo','')}",time=str(c.get('duracao_segundos',0)))
        if status != 'PASSED':
            tag='failure' if status=='FAILED' else 'error' if status=='ERROR' else 'skipped'
            ET.SubElement(entry,tag,type=status,message=c.get('motivo') or status)
    ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)


def markdown_write(data: dict, path: Path) -> None:
    # Nenhuma assertion, resposta, entrada ou mensagem livre de executor é publicada.
    counts=Counter(state(c['status']) for c in data['casos'])
    technical,level=axes(data['casos'],data.get('diagnosticos',()),data.get('obrigacoes_pendentes',()))
    lines=[f"# Evidências: {data['suite']}",'',f"Execução: `{data.get('execucao_id','indisponível')}` · Commit: `{data.get('commit','indisponível')}`",'',
           f"Escopo: {data.get('escopo_validacao','Casos selecionados; aceite integrado não demonstrado.')}",'',
           f"Resultado técnico: **{technical}** · Nível de validação: **{level}** · Aprovação integral do escopo: **{'sim' if technical=='PASSED' and level=='COMPLETA' else 'não'}**",'',
           f"Ambiente: {data.get('ambiente','indisponível')} · Início: {data.get('inicio_utc','indisponível')} · Fim: {data.get('fim_utc','indisponível')} · Duração: {data.get('duracao_segundos',0):.3f} s",'',
           ' | '.join(f'{s}: {counts[s]}' for s in STATES),'', 'Tipos: '+', '.join(f'{k}: {v}' for k,v in Counter(c.get('tipo','não informado') for c in data['casos']).items()),'',
           '## Critérios e rastreabilidade','',
           'Assertions dos casos selecionados são o critério técnico. Cenários, referências OpenSpec, aliases e origem de cada caso estão em `resultados.json`. Referências formais permanecem pendentes de conferência no Confluence; autotestes não são cobertura do produto.','']
    refs=sorted({r['arquivo'] for c in data['casos'] for r in c.get('referencias',{}).get('openspec',[])})
    lines += ['Componentes: ' + ', '.join(f"{k}: {v}" for k, v in Counter(c.get('componente', 'não informado') for c in data['casos']).items()), '']
    lines += [f'- `{r}`' for r in refs]
    scenarios = {(r['arquivo'], r['cenario']) for c in data['casos'] for r in c.get('referencias', {}).get('openspec', []) if r.get('cenario')}
    lines += [f'Cenários OpenSpec identificados: {len(scenarios)}; associações formais não conferidas.']
    lines += ['', '## Falhas e pendências', '']
    groups={}
    for c in data['casos']:
        if state(c['status']) != 'PASSED': groups.setdefault((state(c['status']),c.get('motivo') or 'Motivo indisponível'),[]).append(c.get('id','indisponível'))
    for (s,reason),ids in groups.items():
        lines.append(f"- {s}: {len(ids)} caso(s). {reason}. IDs: {', '.join(ids[:6])}" + ('; demais no JSON.' if len(ids)>6 else '.'))
    lines += [f"- Diagnóstico `{d['codigo']}`: {d['mensagem']}" for d in data.get('diagnosticos',[])]
    lines += [f'- Obrigação pendente: {o}' for o in data.get('obrigacoes_pendentes',[])]
    if not groups and not data.get('diagnosticos') and not data.get('obrigacoes_pendentes'): lines.append('- Nenhuma no escopo automatizado selecionado.')
    lines += ['', '## Limites e evidências', '']+[f'- {x}' for x in data.get('limitacoes',[])]
    lines += ['- `resultados.json`: registro canônico; `resultados.xml`: projeção JUnit; `resumo.md`: síntese.', '- `pytest.xml` e `pytest.log`, quando presentes: auxiliares minimizados, nunca somar como outra execução.', '- Roteiros/ciclos e suas etapas manuais são avaliados somente quando selecionados explicitamente.']
    if data.get('github_url'):
        lines.append(f"- [Run e artifacts]({data['github_url']})")
        artifacts = {'autotestes':'evidencias-autotestes','reflex':'evidencias-reflex','xano-static':'evidencias-xano-static','e2e':'evidencias-e2e','xano-safe':'evidencias-xano','consolidado':'evidencias-consolidadas'}
        if data['suite'] in artifacts: lines.append(f"- Artifact previsto para esta suíte: `{artifacts[data['suite']]}`.")
    if data.get('roteiro'): lines.append(f"- Ciclo: {data['roteiro']['ciclo']}; validação funcional: {data['roteiro']['nivel_validacao']}; detalhes em `{data['roteiro']['arquivo']}`.")
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def github_summary_write(data: dict, path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report=Path(tmp)/'summary.md';markdown_write(data,report)
        with path.open('a',encoding='utf-8') as f: f.write(report.read_text()+'\n')


def write_reports(data: dict, out: Path) -> None:
    finalize(data)
    (out/'resultados.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    junit_write(data['casos'],out/'resultados.xml',data['suite'],data)
    markdown_write(data,out/'resumo.md')
    if os.getenv('GITHUB_STEP_SUMMARY'): github_summary_write(data,Path(os.environ['GITHUB_STEP_SUMMARY']))


def pytest_selector(case: dict, cwd: Path) -> str:
    file, member=case['node'].split('::',1)
    return str((ROOT/file).relative_to(cwd))+'::'+member.replace('.', '::', 1) if '.' in member.split('[',1)[0] else str((ROOT/file).relative_to(cwd))+'::'+member


def run_pytest(suite: str, out: Path, cases: list[dict]) -> tuple[str | None, int | None]:
    cwd = FRONTEND if suite=='reflex' else ROOT
    selected=[c for c in cases if not c.get('native_function') and c['status'] != 'BLOCKED']
    if not selected: return None,None
    args=[sys.executable,'-m','pytest','-q',*[pytest_selector(c,cwd) for c in selected],f'--junitxml={out/"pytest.xml"}', '-o','junit_family=xunit2']
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT)+os.pathsep+str(FRONTEND)+os.pathsep+env.get('PYTHONPATH','')
    if suite=='controlled':
        env['EVIDENCE_HTTP_EVENTS']=str(out/'http-events.jsonl');args+=['-p','scripts.pytest_http_evidence']
    # Sem screenshots/traces automáticos: apenas os arquivos minimizados entram no upload.
    with tempfile.TemporaryDirectory(prefix='xano-config-') as tmp:
        if suite=='xano-safe' and env.get('XANO_CLI_CONFIG_YAML'):
            cfg=Path(tmp)/'credentials.yaml';cfg.write_text(env['XANO_CLI_CONFIG_YAML']);cfg.chmod(0o600);env['XANO_CONFIG']=str(cfg)
        try:
            proc=subprocess.run(args,cwd=cwd,env=env,text=True,capture_output=True,timeout=600,check=False)
            code=proc.returncode;problem=None if (out/'pytest.xml').exists() else 'pytest não produziu XML'
        except subprocess.TimeoutExpired:
            code=124;problem='Timeout do pytest; resultados disponíveis preservados'
        except OSError:
            code=127;problem='Não foi possível iniciar pytest'
    # Saída livre pode conter nomes/senhas de fixtures: publicar somente campos permitidos.
    (out/'pytest.log').write_text(f'Executor: pytest\nSuíte: {suite}\nCódigo: {code}\nSaída livre omitida por minimização.\n',encoding='utf-8')
    return problem,code


def junit_key(case: dict) -> tuple[str,str]:
    file,member=case['node'].split('::',1)
    module=Path(file).with_suffix('').as_posix().replace('/','.')
    if '.' in member.split('[',1)[0]:
        cls,name=member.split('.',1);return module+'.'+cls,name
    return module,member


def collect_pytest_results(out: Path, cases: list[dict]) -> list[dict]:
    xml=out/'pytest.xml';diagnostics=[]
    if not xml.exists(): return [diagnostic('XML_AUSENTE','pytest não produziu resultado coletável')]
    try: tree=ET.parse(xml)
    except (ET.ParseError,OSError):
        xml.write_text('<?xml version="1.0"?><testsuite tests="0"/>',encoding='utf-8')
        return [diagnostic('XML_INVALIDO','XML do executor inválido; nenhum resultado inferido')]
    seen=set();aux=ET.Element('testsuite',name='pytest-auxiliar')
    for entry in tree.iter('testcase'):
        name=entry.get('name','');cls=entry.get('classname','')
        matches=[]
        for c in cases:
            expected_cls,expected_name=junit_key(c)
            class_match=expected_cls==cls or (expected_cls.startswith('frontend.') and expected_cls[len('frontend.'):] == cls)
            name_match=expected_name==name or (c.get('tipo')=='E2E' and name==expected_name+'[chromium]')
            if class_match and name_match: matches.append(c)
        if len(matches)!=1:
            diagnostics.append(diagnostic('RESULTADO_SEM_ASSOCIACAO','Resultado não corresponde inequivocamente ao catálogo'));continue
        case=matches[0];key=case_key(case)
        if case.get('status')=='BLOCKED':
            diagnostics.append(diagnostic('EXECUCAO_BLOQUEADA','Executor retornou caso impedido pelo guardião'));continue
        failure=entry.find('failure');error=entry.find('error');skip=entry.find('skipped')
        # pytest representa exceções de call em failure: só AssertionError é reprovação funcional.
        if error is not None: status='ERROR';reason='Erro de preparação ou finalização do pytest'
        elif failure is not None:
            assertion='AssertionError' in (failure.get('message','')+' '+(failure.text or '')) or failure.get('type','')=='AssertionError'
            status='FAILED' if assertion else 'ERROR';reason='Expectativa funcional não satisfeita' if assertion else 'Erro durante a execução do pytest'
        elif skip is not None: status='SKIPPED';reason='Omissão intencional informada pelo pytest; conteúdo livre omitido'
        else: status='PASSED';reason=''
        if key in seen:
            # xUnit2 pode produzir call e teardown separados. Preservar o erro, sem duplicar caso.
            diagnostics.append(diagnostic('RESULTADO_REPETIDO','Mais de um resultado do executor para o mesmo caso'))
            if case['status']=='ERROR': status='ERROR';reason=case['motivo']
            elif case['status']=='FAILED' and status not in {'ERROR'}: status='FAILED';reason=case['motivo']
        seen.add(key)
        try: duration=float(entry.get('time','0'));assert duration>=0 and duration<float('inf')
        except (ValueError,AssertionError): duration=0;diagnostics.append(diagnostic('DURACAO_INVALIDA','Duração do executor inválida'))
        case.update(status=status,motivo=reason,duracao_segundos=case.get('duracao_segundos',0)+duration,resultado_obtido={'PASSED':'Assertions aprovadas','FAILED':'Assertion reprovada','ERROR':'Resultado funcional inconclusivo','SKIPPED':'Ignorado pelo executor'}[status])
        safe=ET.SubElement(aux,'testcase',classname=junit_key(case)[0],name=junit_key(case)[1],time=str(duration))
        if status!='PASSED': ET.SubElement(safe,'failure' if status=='FAILED' else 'error' if status=='ERROR' else 'skipped',message=reason,type=status)
    for case in cases:
        if not case.get('native_function') and case.get('status')!='BLOCKED' and case_key(case) not in seen:
            case.update(status='NOT_RUN',motivo='Caso esperado não coletado pelo pytest')
    # Reescrever o auxiliar corrente somente com identidades e mensagens permitidas.
    ET.ElementTree(aux).write(xml,encoding='utf-8',xml_declaration=True)
    return diagnostics


def collect_http_results(out: Path, cases: list[dict]) -> list[dict]:
    path=out/'http-events.jsonl';diagnostics=[]
    if not path.exists(): return diagnostics
    safe=[]
    try:
        from .pytest_http_evidence import _route
    except ImportError:
        from pytest_http_evidence import _route
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            record=json.loads(line)
            matches=[c for c in cases if c['node']==record['node'] or c['node'].removeprefix('frontend/')==record['node']]
            if len(matches)!=1: raise ValueError()
            events=[{'metodo':e['metodo'] if e.get('metodo') in {'GET','POST','PATCH','PUT','DELETE'} else 'OUTRO','endpoint':_route(e.get('endpoint','')),'status':int(e['status']),'resposta':{'tipo':'conteúdo omitido'}} for e in record['eventos']]
            case=matches[0];case['status_http_real']=[e['status'] for e in events]
            case['resultado_obtido']+='; HTTP '+', '.join(f"{e['metodo']} {e['endpoint']} → {e['status']}" for e in events)
            case['eventos_http']=events;safe.append({'node':case['node'],'eventos':events})
        except (ValueError,KeyError,TypeError): diagnostics.append(diagnostic('HTTP_INVALIDO','Evento HTTP sem associação ou formato válido'))
    path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in safe),encoding='utf-8')
    return diagnostics


def pure_guard(functions=NATIVE_PURE, root: Path = ROOT) -> str | None:
    """Lista explicitamente revisada; negar recursos e dependências não revisadas."""
    visited=set()
    def check(function):
        if function in visited:return None
        if function not in NATIVE_PURE:return 'Dependência Xano não revisada pelo guardião de pureza'
        visited.add(function)
        try: source=(root/'backend/xano/function'/f'{function}.xs').read_text(encoding='utf-8')
        except OSError:return 'XanoScript local não disponível para revisão de pureza'
        if re.search(r'\b(?:db|api|redis|external|storage|task|queue|http)\s*\.',source): return 'Recurso proibido encontrado pelo guardião de pureza'
        for callee in re.findall(r'function\.run\s+"([^"]+)"',source):
            problem=check(callee)
            if problem:return problem
        return None
    for function in functions:
        problem=check(function)
        if problem:return problem
    return None


def preflight_xano() -> str | None:
    if shutil.which('xano') is None:return 'CLI Xano não instalado'
    if not (os.getenv('XANO_CLI_CONFIG_YAML') or os.getenv('XANO_CONFIG') or Path.home().joinpath('.xano/credentials.yaml').exists()):return 'Credencial de CLI Xano ausente'
    with tempfile.TemporaryDirectory(prefix='xano-preflight-') as tmp:
        env=xano_env(Path(tmp))
        try: proc=subprocess.run(['xano','profile','me','-p',env.get('XANO_TEST_PROFILE') or 'ps-impacta','-o','json'],env=env,text=True,capture_output=True,timeout=20,check=False)
        except (OSError,subprocess.TimeoutExpired):return 'CLI Xano indisponível ou sem resposta'
    return 'Autenticação/conectividade do CLI Xano indisponível' if proc.returncode else None


def xano_env(tmp: Path) -> dict:
    env=os.environ.copy()
    if env.get('XANO_CLI_CONFIG_YAML'):
        cfg=tmp/'credentials.yaml';cfg.write_text(env['XANO_CLI_CONFIG_YAML']);cfg.chmod(0o600);env['XANO_CONFIG']=str(cfg)
    return env


def executar_teste_nativo(record_id: str, profile: str, env: dict) -> tuple:
    # Tempo esgotado: repete uma vez, com prazo maior. Resposta fora de JSON (recusa pelo limite do plano, de 10
    # requisições a cada 20 s, ou saída truncada sob carga): espera a janela seguinte e repete até duas vezes.
    prazos,esperas_json=[50,90],2
    while True:
        try:
            proc=subprocess.run(['xano','unit_test','run',record_id,'-p',profile,'--branch','v1','-o','json'],env=env,text=True,capture_output=True,timeout=prazos[0],check=False)
        except subprocess.TimeoutExpired:
            if len(prazos)==1:raise
            prazos.pop(0);time.sleep(2.5);continue
        try:
            return proc,json.loads(proc.stdout)
        except json.JSONDecodeError:
            if not esperas_json:raise
            esperas_json-=1;time.sleep(21)


def run_native(cases: list[dict]) -> list[dict]:
    native=[c for c in cases if c.get('native_function')];diags=[]
    if not native:return diags
    problem=pure_guard([c['native_function'] for c in native])
    if problem:
        for c in native:c.update(status='BLOCKED',motivo=problem)
        return diags
    with tempfile.TemporaryDirectory(prefix='xano-native-') as tmp:
        env=xano_env(Path(tmp));profile=env.get('XANO_TEST_PROFILE') or 'ps-impacta'
        try:
            proc=subprocess.run(['xano','unit_test','list','-p',profile,'--branch','v1','--per_page','10000','-o','json'],env=env,text=True,capture_output=True,timeout=40,check=False)
            if proc.returncode:raise ValueError()
            listing=json.loads(proc.stdout)
            if listing.get('nextPage'):raise ValueError()
            pairs=[(i['obj_name'],i['name']) for i in listing['items']]
            if len(pairs)!=len(set(pairs)):raise ValueError()
            published={pair:i for pair,i in zip(pairs,listing['items'])}
        except (OSError,subprocess.TimeoutExpired,ValueError,KeyError,TypeError):
            for c in native:c.update(status='ERROR',motivo='Listagem nativa indisponível ou inválida')
            return [diagnostic('LISTAGEM_XANO','Não foi possível obter listagem nativa confiável')]
        for c in native:
            record=published.get((c['native_function'],c['native_name']))
            if not record:
                c.update(status='BLOCKED',motivo='Teste nativo ausente na branch v1 publicada');continue
            started=time.monotonic();time.sleep(2.5)
            try:
                proc,result=executar_teste_nativo(str(record['id']),profile,env)
                statuses=[str(i.get('status','')).lower() for i in result.get('results',[])]
                if proc.returncode not in (0,1) or result.get('status')!='ok':status='ERROR'
                elif proc.returncode==0 and statuses and all(s=='pass' for s in statuses):status='PASSED'
                elif statuses and all(s in {'pass','fail','failed'} for s in statuses) and any(s in {'fail','failed'} for s in statuses):status='FAILED'
                else:status='ERROR'
                c.update(status=status,motivo='' if status=='PASSED' else 'Expectativa nativa não satisfeita' if status=='FAILED' else 'Resposta CLI nativa inconclusiva',resultado_obtido='Assertions nativas aprovadas' if status=='PASSED' else 'Resultado nativo sem aprovação')
            except (OSError,subprocess.TimeoutExpired,ValueError,AttributeError,TypeError):c.update(status='ERROR',motivo='Erro de transporte ou formato do CLI nativo')
            c['duracao_segundos']=round(time.monotonic()-started,3)
    return diags


def controlled_gate() -> str | None:
    if os.getenv('XANO_ISOLATED_CONFIRMATION')!='CONFIRMO_WORKSPACE_DESCARTAVEL':return 'Confirmação explícita do workspace descartável ausente'
    host=os.getenv('XANO_ISOLATED_API_HOST','').strip().lower()
    if not host or '/' in host or ':' in host:return 'XANO_ISOLATED_API_HOST inválido ou ausente'
    for key in ('XANO_AUTH_API_URL','XANO_TRIAGEM_API_URL','XANO_API_URL','XANO_CADASTROS_API_URL'):
        url=urlparse(os.getenv(key,''))
        if url.scheme!='https' or url.hostname!=host or url.username or url.password:return f'{key} não aponta para o host isolado confirmado'
    needed=('TEST_RECEPCAO_TOKEN','TOTEM_CHAVE','TEST_ADMIN_EMAIL','TEST_ADMIN_SENHA','TEST_RECEPCAO_EMAIL','TEST_RECEPCAO_SENHA','TEST_MEDICO_EMAIL','TEST_MEDICO_SENHA')
    if any(not os.getenv(k) for k in needed):return 'Credenciais de teste ausentes'
    return None


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=SUITES,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--require-execution',action='store_true')
    parser.add_argument('--require-complete',action='store_true')
    parser.add_argument('--execute-controlled',action='store_true')
    parser.add_argument('--blocked-reason',choices=['instalacao','servidor','navegador','dependencia'])
    args=parser.parse_args(argv);started=datetime.now(timezone.utc)
    data=metadata(args.suite,started)
    try:out=new_output(args.output or ROOT/'test-evidence'/data['execucao_id']/args.suite)
    except (OSError,FileExistsError) as exc:
        print(str(exc),file=sys.stderr);return 2
    try:cases=catalog(args.suite)
    except (OSError,ValueError,SyntaxError,KeyError) as exc:
        causes = {'ID duplicado no catálogo':'ID_DUPLICADO', 'Seletor ou variante ambígua no catálogo':'SELETOR_VARIANTE', 'Alias histórico ambíguo':'ALIAS', 'Dependência real ou escrita recusada em suíte local':'DEPENDENCIA_REAL', 'Parametrização sem identidade estável reconhecível':'PARAMETRIZACAO'}
        cause = causes.get(str(exc),'DESCOBERTA_DIVERGENTE' if str(exc).startswith('Divergência descoberta/catálogo:') else 'FORMATO_INVALIDO')
        cases=[];data['diagnosticos'].append(diagnostic('CATALOGO_INVALIDO','Catálogo indisponível ou divergente da descoberta',causa=cause))
    data['casos']=cases
    for c in cases:c.update(status='NOT_RUN',motivo='Caso ainda não iniciado',resultado_obtido='Não executado',duracao_segundos=0.0,origem_execucao=data['execucao_id'],origem_suite=args.suite,evidencias=['resultados.json','resultados.xml','resumo.md'])
    blocked=None
    if args.blocked_reason:
        blocked={'instalacao':'Instalação das dependências falhou','servidor':'Servidor público indisponível','navegador':'Navegador indisponível','dependencia':'Dependência obrigatória indisponível'}[args.blocked_reason]
        data['diagnosticos'].append(diagnostic('PREPARACAO_FALHOU',blocked))
    elif args.suite=='controlled':
        blocked=controlled_gate() if args.execute_controlled else 'Escrita não autorizada; isolamento e autorização explícita obrigatórios'
        if not blocked:
            for c in cases:
                if c['node'].startswith('tests/api/') and 'test_base_compartilhada.py' not in c['node']:c.update(status='BLOCKED',motivo='Cenário CLI fixa v1; escrita recusada nesta suíte HTTP isolada')
    elif args.suite=='xano-safe':
        blocked=pure_guard() or preflight_xano()
        data['alvo_xano']={'branch':'v1','datasource':'live'}
        data['limitacoes'].append('Pureza verificada no Git; equivalência integral do código remoto da branch v1 não foi comparada. Funções puras com dados sintéticos não comprovam persistência.')
    elif args.suite=='e2e':
        base=urlparse(os.getenv('REFLEX_E2E_BASE_URL',''))
        if base.scheme!='http' or base.hostname not in {'127.0.0.1','localhost'} or base.username or base.password or base.query or base.fragment:blocked='Servidor E2E público controlado local indisponível'
        elif not importlib.util.find_spec('playwright'):blocked='Playwright/navegador indisponível'
        data['limitacoes'].append('E2E público verifica navegação e redirecionamento; não comprova fluxo clínico completo ou painel de chamadas.')
    if blocked:
        for c in cases:c.update(status='BLOCKED',motivo=blocked)
        data['dependencias'].append({'nome':args.suite,'disponivel':False,'motivo':blocked})
    elif cases:
        data['dependencias'].append({'nome':args.suite,'disponivel':True})
        try:
            problem,code=run_pytest(args.suite,out,cases)
            if code is not None:
                data['diagnosticos']+=collect_pytest_results(out,[c for c in cases if not c.get('native_function')])
                if code not in (0,1) or code==1 and not any(c['status'] in {'FAILED','ERROR'} for c in cases):data['diagnosticos'].append(diagnostic('PYTEST_PROCESSO','pytest retornou código não zero sem resultado funcional suficiente',codigo_saida=code))
            if problem:data['diagnosticos'].append(diagnostic('PYTEST_INFRA',problem))
            if args.suite=='controlled':data['diagnosticos']+=collect_http_results(out,cases)
            if args.suite=='xano-safe':data['diagnosticos']+=run_native(cases)
        except Exception:
            data['diagnosticos'].append(diagnostic('EXECUTOR_ERRO','Falha tratável do executor; resultados disponíveis preservados'))
            if (out/'pytest.xml').exists():data['diagnosticos']+=collect_pytest_results(out,[c for c in cases if not c.get('native_function')])
    if not cases:data['diagnosticos'].append(diagnostic('ZERO_CASOS','Nenhum caso confiável disponível'))
    if data.get('sha_esperado') and data['sha_esperado']!=data['commit']:data['diagnosticos'].append(diagnostic('SHA_DIVERGENTE','SHA esperado difere do checkout testado'))
    for c in cases:
        c['evidencias'] += [f for f in ('pytest.xml','pytest.log','http-events.jsonl') if (out/f).exists()]
    write_reports(data,out)
    print(f"{args.suite}: técnico={data['status_tecnico']} validação={data['nivel_validacao']} {data['totais']}")
    print(f'Evidências: {out}')
    return gate(data,args.require_execution,args.require_complete)


if __name__=='__main__':sys.exit(main())

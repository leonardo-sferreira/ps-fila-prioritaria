"""Cenários sintéticos da infraestrutura, sempre em diretórios temporários."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
import xml.etree.ElementTree as ET
import pytest
from scripts import run_test_evidence as ev, merge_test_evidence as merge



@pytest.fixture(autouse=True)
def contexto_local_das_fixtures(monkeypatch):
    """Separa as simulações do run e do Summary reais do processo executor."""
    for key in tuple(os.environ):
        if key.startswith('GITHUB_'):
            monkeypatch.delenv(key)


def fixture_source(path, suite='xano-static', status='PASSED', commit=None, run=None, attempt=None):
    data=ev.metadata(suite,datetime.now(timezone.utc));data.update(commit=commit or ev.git('rev-parse','HEAD'),github_run_id=run,github_run_attempt=attempt)
    data['casos']=[dict(c,status=status,duracao_segundos=.01,motivo='' if status=='PASSED' else 'Motivo sintético',resultado_obtido='Resultado sintético') for c in ev.catalog(suite)]
    ev.new_output(path);ev.write_reports(data,path);return data


# Casos da suíte estática no catálogo; cresce quando um teste estático novo é registrado.
N_ESTATICA=len(ev.catalog('xano-static'))


def run_merge(tmp, inputs, *args, suites=('xano-static',), output='out'):
    cmd=[sys.executable,str(ev.ROOT/'scripts/merge_test_evidence.py'),'--output',str(tmp/output)]
    for suite in suites:cmd+=['--expected-suite',suite]
    for path in inputs:cmd+=['--input',str(path)]
    result=subprocess.run([*cmd,*args],capture_output=True,text=True)
    data=json.loads((tmp/output/'resultados.json').read_text()) if (tmp/output/'resultados.json').exists() else None
    return result.returncode,data


def assert_formats(path):
    data=json.loads((path/'resultados.json').read_text());root=ET.parse(path/'resultados.xml').getroot();md=(path/'resumo.md').read_text()
    assert int(root.get('tests'))==len(data['casos'])==data['total_casos']
    assert int(root.get('failures'))==data['totais']['FAILED']
    assert int(root.get('errors'))==data['totais']['ERROR']
    assert int(root.get('skipped'))==sum(data['totais'][s] for s in ev.UNEXECUTED)
    for status,n in data['totais'].items():assert f'{status}: {n}' in md
    assert data['status_tecnico'] in md and data['nivel_validacao'] in md
    assert float(root.get('time'))==pytest.approx(sum(c['duracao_segundos'] for c in data['casos']))
    assert len({c.get('name') for c in root.findall('testcase')})==len(data['casos'])


def test_projecoes_seis_estados_sem_casos_infra_ficticios(tmp_path):
    data=fixture_source(tmp_path/'source')
    for case,status in zip(data['casos'],ev.STATES):case.update(status=status,motivo='' if status=='PASSED' else 'Motivo sintético')
    data['diagnosticos']=[ev.diagnostic('FIXTURE','Diagnóstico sintético da ferramenta')]
    ev.write_reports(data,tmp_path/'source');assert_formats(tmp_path/'source')
    assert data['total_casos']==N_ESTATICA and data['status_tecnico']=='ERROR' and data['nivel_validacao']=='PARCIAL'
    skips=ET.parse(tmp_path/'source/resultados.xml').getroot().findall('testcase/skipped')
    assert {s.get('type') for s in skips}==ev.UNEXECUTED


def test_merge_ausencias_corrupcao_e_fontes_confiaveis(tmp_path):
    fixture_source(tmp_path/'valid')
    (tmp_path/'broken').mkdir();(tmp_path/'broken/resultados.json').write_text('{quebrado')
    code,data=run_merge(tmp_path,[tmp_path/'valid',tmp_path/'broken',tmp_path/'missing'],suites=('xano-static','e2e'))
    assert code==1 and data['totais']['PASSED']==N_ESTATICA and data['nivel_validacao']=='PARCIAL'
    assert data['obrigacoes_pendentes']==['e2e'];assert_formats(tmp_path/'out')
    code,data=run_merge(tmp_path,[],output='empty')
    assert code==1 and data['casos']==[] and data['nivel_validacao']=='BLOQUEADA'
    assert_formats(tmp_path/'empty')


def test_merge_rejeita_commits_run_attempt_duplicacao_e_tampering(tmp_path):
    commit=ev.git('rev-parse','HEAD')
    fixture_source(tmp_path/'valid')
    variants=[('commit',{'commit':'f'*40},[]),('run',{'run':'41'},[]),('attempt',{'run':'42','attempt':'2'},['--expected-run-id','42','--expected-attempt','1'])]
    for name,changes,args in variants:
        fixture_source(tmp_path/name,**changes)
        code,data=run_merge(tmp_path,[tmp_path/name],*args,output='out-'+name)
        assert code==1 and data['totais']['PASSED']==0
    code,data=run_merge(tmp_path,[tmp_path/'valid',tmp_path/'valid'],output='duplicate')
    assert code==1 and data['totais']['PASSED']==0
    source=json.loads((tmp_path/'valid/resultados.json').read_text())
    for name,change in [('case',lambda d:d['casos'].append(d['casos'][0])),('count',lambda d:d['totais'].update(PASSED=99)),('state',lambda d:d['casos'][0].update(status='MISTERIO')),('omit',lambda d:d['casos'].pop())]:
        copy=json.loads(json.dumps(source));change(copy);path=tmp_path/name;path.mkdir();(path/'resultados.json').write_text(json.dumps(copy))
        code,data=run_merge(tmp_path,[path],output='out-'+name)
        assert code==1 and data['total_casos']==0


def test_merge_leitura_legada_somente_local_explicita_sem_alterar_origem(tmp_path):
    data=fixture_source(tmp_path/'legacy');data.pop('versao_formato')
    # Casos registrados depois do formato legado não têm alias: mantêm o ID permanente.
    for c in data['casos']:c.update(id=(c['aliases_historicos'] or [c['id']])[0],status='PASS')
    path=tmp_path/'legacy/resultados.json';path.write_text(json.dumps(data));before=path.read_bytes()
    code,result=run_merge(tmp_path,[path.parent],output='denied');assert code==1
    code,result=run_merge(tmp_path,[path.parent],'--allow-legacy-local',output='allowed')
    assert code==0 and result['totais']['PASSED']==N_ESTATICA and result['limitacoes']
    assert path.read_bytes()==before
    with patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}):
        with pytest.raises(ValueError):merge.validate_source(data,data['commit'],None,None,True)


def test_merge_recusa_destino_preserva_historico_e_sem_roteiro_fixo(tmp_path):
    fixture_source(tmp_path/'valid');code,data=run_merge(tmp_path,[tmp_path/'valid']);assert code==0
    before={p.name:p.read_bytes() for p in (tmp_path/'out').iterdir()}
    code,_=run_merge(tmp_path,[tmp_path/'valid']);assert code==2
    assert before=={p.name:p.read_bytes() for p in (tmp_path/'out').iterdir()}
    assert not (tmp_path/'out/roteiros-sprint5.md').exists()


def test_codigos_reais_merge_sucesso_falha_erro_parcial_ignorado_bloqueado(tmp_path):
    for index,(status,strict,expected) in enumerate([('PASSED',False,0),('FAILED',False,1),('ERROR',False,1),('SKIPPED',False,0),('SKIPPED',True,1),('BLOCKED',False,0),('BLOCKED',True,1),('NOT_RUN',True,1)]):
        path=tmp_path/f's{index}';fixture_source(path,status=status)
        code,data=run_merge(tmp_path,[path],*(['--require-complete'] if strict else []),output=f'o{index}')
        assert code==expected;assert_formats(tmp_path/f'o{index}')
    code,data=run_merge(tmp_path,[tmp_path/'s3'],'--require-execution',output='require-execution');assert code==1
    source=tmp_path/'partial';data=fixture_source(source);data['casos'][0].update(status='NOT_RUN',motivo='Não iniciado');ev.write_reports(data,source)
    code,result=run_merge(tmp_path,[source],output='partial-ok');assert code==0 and result['nivel_validacao']=='PARCIAL'
    code,result=run_merge(tmp_path,[source],'--require-complete',output='partial-denied');assert code==1


def test_runner_codigos_e_publicacao_apos_falha_instalacao_e_zero(tmp_path):
    cases=ev.catalog('xano-static')
    scenarios=[('pass','',0,0),('failure','<failure message="AssertionError: esperado"/>',1,1),('error','<error message="setup"/>',1,1),('partial','',0,0),('skip','<skipped message="deliberado"/>',0,0)]
    for name,inner,code,expected in scenarios:
        def executor(suite,out,selected):
            chosen=selected[:1] if name=='partial' else selected
            entries=''.join(f'<testcase classname="{ev.junit_key(c)[0]}" name="{ev.junit_key(c)[1]}">{inner}</testcase>' for c in chosen)
            (out/'pytest.xml').write_text('<testsuite>'+entries+'</testsuite>');return None,code
        with patch.object(ev,'run_pytest',side_effect=executor):
            result=ev.main(['--suite','xano-static','--output',str(tmp_path/name)])
            assert result==expected;assert_formats(tmp_path/name)
        if name in ('partial','skip'):
            with patch.object(ev,'run_pytest',side_effect=executor):assert ev.main(['--suite','xano-static','--output',str(tmp_path/(name+'strict')),'--require-complete'])==1
    with patch.object(ev,'run_pytest') as executor:
        assert ev.main(['--suite','xano-static','--output',str(tmp_path/'installation'),'--blocked-reason','instalacao'])==1
        executor.assert_not_called();assert_formats(tmp_path/'installation')
    with patch.object(ev,'controlled_gate',return_value=None),patch.object(ev,'run_pytest',return_value=(None,None)) as executor:
        assert ev.main(['--suite','controlled','--execute-controlled','--output',str(tmp_path/'isolated-inventory'),'--require-complete'])==1
        data=json.loads((tmp_path/'isolated-inventory/resultados.json').read_text())
        fixed=[c for c in data['casos'] if c['status']=='BLOCKED']
        assert len(fixed)==2 and all(c['node'].startswith('tests/api/') and 'v1' in c['motivo'] for c in fixed)
    with patch.object(ev,'catalog',return_value=[]):
        assert ev.main(['--suite','xano-static','--output',str(tmp_path/'zero')])==1
        assert_formats(tmp_path/'zero')


def test_runner_process_code_sem_xml_e_xml_parcial_nunca_aprova(tmp_path):
    case=ev.catalog('xano-static')[0]
    partial=f'<testsuite><testcase classname="{ev.junit_key(case)[0]}" name="{ev.junit_key(case)[1]}"/></testsuite>'
    for index,xml in enumerate([None,'<testsuite/>','<quebrado',partial]):
        def executor(suite,out,cases):
            if xml:(out/'pytest.xml').write_text(xml)
            return 'Processo interrompido',124
        with patch.object(ev,'run_pytest',side_effect=executor):
            assert ev.main(['--suite','xano-static','--output',str(tmp_path/str(index))])==1
        data=json.loads((tmp_path/str(index)/'resultados.json').read_text())
        assert data['totais']['PASSED']==(1 if index==3 else 0) and data['diagnosticos']


def test_nativo_sucesso_assertion_timeout_json_ausente_e_credencial(tmp_path):
    from types import SimpleNamespace
    cases=[dict(c,status='NOT_RUN',motivo='Não iniciado',duracao_segundos=0) for c in ev.catalog('xano-safe') if c.get('native_function')][:1]
    listing=SimpleNamespace(returncode=0,stdout=json.dumps({'items':[{'id':1,'obj_name':cases[0]['native_function'],'name':cases[0]['native_name']}]}))
    for statuses,code,expected in [(['pass'],0,'PASSED'),(['fail'],0,'FAILED'),(['fail'],1,'FAILED'),(['pass'],2,'ERROR'),(['estranho'],0,'ERROR'),([],0,'ERROR')]:
        with patch.object(ev.subprocess,'run',return_value=listing),patch.object(ev,'executar_teste_nativo',return_value=(SimpleNamespace(returncode=code),{'status':'ok','results':[{'status':s} for s in statuses]})),patch.object(ev.time,'sleep'):
            ev.run_native(cases);assert cases[0]['status']==expected
    for error in (subprocess.TimeoutExpired('xano',50),json.JSONDecodeError('fixture','',0)):
        with patch.object(ev.subprocess,'run',return_value=listing),patch.object(ev,'executar_teste_nativo',side_effect=error),patch.object(ev.time,'sleep'):
            ev.run_native(cases);assert cases[0]['status']=='ERROR'
    with patch.object(ev.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='{"items":[]}')):
        ev.run_native(cases);assert cases[0]['status']=='BLOCKED'
    with patch.object(ev.shutil,'which',return_value='/fixture/xano'),patch.dict(os.environ,{},clear=True),patch.object(Path,'home',return_value=tmp_path),patch.object(ev.subprocess,'run') as cli:
        assert 'ausente' in ev.preflight_xano();cli.assert_not_called()


def test_minimizacao_canarios_em_todos_formatos_e_logs(tmp_path):
    # Canários sintéticos não devem sobreviver a nenhuma projeção publicável.
    canary='Pessoa CanarioPrivado cpf=529.982.247-25 email=canario@example.test token=SegredoCanario codigo=123456 credencial_custom=ChaveCanario https://privado.example.test'
    def executor(suite,out,cases):
        c=cases[0]
        import html
        (out/'pytest.xml').write_text(f'<testsuite><testcase classname="{ev.junit_key(c)[0]}" name="{ev.junit_key(c)[1]}"><failure message="AssertionError: {html.escape(canary,quote=True)}">{html.escape(canary)}</failure></testcase></testsuite>')
        return None,1
    with patch.object(ev,'run_pytest',side_effect=executor):
        assert ev.main(['--suite','xano-static','--output',str(tmp_path/'out')])==1
    for p in (tmp_path/'out').iterdir():
        for secret in ('CanarioPrivado','529.982.247-25','canario@example.test','SegredoCanario','123456','ChaveCanario','privado.example.test'):assert secret not in p.read_text()
    case=dict(ev.catalog('xano-static')[0],status='NOT_RUN')
    with patch.object(ev.subprocess,'run',return_value=type('Process',(),{'returncode':1,'stdout':canary,'stderr':canary})()):ev.run_pytest('xano-static',tmp_path,[case])
    assert 'Canario' not in (tmp_path/'pytest.log').read_text()
    source=fixture_source(tmp_path/'metadata')
    source.update(github_url='https://privado.example.test',github_job=[canary],dependencias=[{'nome':canary,'motivo':canary}],ferramentas={'python':canary},alvo_xano={'observacao':canary})
    (tmp_path/'metadata/resultados.json').write_text(json.dumps(source))
    code,result=run_merge(tmp_path,[tmp_path/'metadata'],output='metadata-out')
    assert code==0
    for published in (tmp_path/'metadata-out').iterdir():
        assert 'Canario' not in published.read_text() and 'privado.example.test' not in published.read_text()
    from scripts.pytest_http_evidence import _route,_example
    assert 'Canario' not in _route('https://privado.example.test/PessoaCanario?token=x')
    assert 'Canario' not in str(_example(type('Response',(),{'json':lambda self:{'ChaveCanario':'segredo'}})()))
    assert ev.public_url('https://github.com/owner/repo/actions/runs/123')


def test_muitos_casos_agrupa_motivos_sem_tabela_bruta(tmp_path):
    cases=[dict(c,status='BLOCKED',motivo='Dependência obrigatória ausente',duracao_segundos=0) for c in ev.catalog('reflex')]
    data=ev.metadata('reflex',datetime.now(timezone.utc));data['casos']=cases;ev.finalize(data)
    ev.markdown_write(data,tmp_path/'resumo.md');text=(tmp_path/'resumo.md').read_text()
    assert len(text.splitlines())<60 and f'{len(cases)} caso(s)' in text
    assert cases[-1]['id'] not in text


def test_needs_failure_nao_substituido_por_publicacao_e_roteiro_explicito(tmp_path):
    fixture_source(tmp_path/'valid')
    code,data=run_merge(tmp_path,[tmp_path/'valid'],'--needs-result','xano-static=failure',output='needs')
    assert code==1 and data['diagnosticos'];assert_formats(tmp_path/'needs')
    code,data=run_merge(tmp_path,[tmp_path/'valid'],'--roteiro',str(ev.ROOT/'tests/roteiros/sprint5.json'),output='roteiro')
    assert code==0 and data['nivel_validacao']=='PARCIAL' and not data['aprovacao_integral']
    assert (tmp_path/'roteiro/roteiros-sprint5.md').exists()


def test_e2e_destino_inicializacao_e_timeout_sem_logs_sensiveis(tmp_path):
    import importlib.util
    from scripts import run_reflex_e2e_ci as helper
    from types import ModuleType
    from unittest.mock import MagicMock
    package=ModuleType('playwright');sync=ModuleType('playwright.sync_api')
    sync.sync_playwright=MagicMock()
    old=tmp_path/'old';old.mkdir();(old/'pytest.xml').write_text('histórico')
    with patch.object(helper,'run_evidence') as runner:
        assert helper.main(['--output',str(old)])==2;runner.assert_not_called()
        assert (old/'pytest.xml').read_text()=='histórico'
    for name,side_effect in [('init',OSError('CanarioPrivado')),('timeout',None)]:
        proc=type('Process',(),{'pid':99999999,'poll':lambda self:None,'wait':lambda self,timeout=None:0})()
        with patch.object(helper.shutil,'which',return_value='/fixture/reflex'),patch.dict(sys.modules,{'playwright':package,'playwright.sync_api':sync}),patch.object(helper.importlib.util,'find_spec',return_value=True),patch.object(helper.Path,'exists',autospec=True,side_effect=lambda path: path.is_file() or path.is_dir() or 'chrome' in str(path)),patch.object(helper.subprocess,'Popen',side_effect=side_effect,return_value=proc),patch.object(helper.time,'monotonic',side_effect=[0,301]),patch.object(helper.os,'killpg'),patch.object(helper,'run_evidence',return_value=1) as runner:
            sync.sync_playwright.return_value.__enter__.return_value.chromium.executable_path='/fixture/chrome'
            assert helper.main(['--output',str(tmp_path/name)])==1
            assert runner.call_args.args[0] is None and runner.call_args.args[2]=='servidor'
        assert 'CanarioPrivado' not in (tmp_path/name/'servidor.log').read_text()


def test_workflow_topologia_publicacao_e_gates_preservados(tmp_path):
    # Estrutura e contratos do YAML; parse completo também é feito na validação local.
    text=(ev.ROOT/'.github/workflows/ci.yml').read_text()
    import re
    jobs=re.findall(r'^  ([a-z0-9]+):\n    name:',text,re.M)
    assert jobs==['autotestes','reflex','estatico','e2e','xano','consolidado']
    assert 'needs: [autotestes, reflex, estatico, e2e, xano]' in text
    assert 'continue-on-error' not in text and '--execute-controlled' not in text
    assert text.count('if-no-files-found: error')==6
    assert text.count('uses: actions/download-artifact@v4')==5
    assert text.count('--require-execution --require-complete')==10
    for artifact in ('evidencias-reflex','evidencias-e2e','evidencias-xano','evidencias-consolidadas'):assert f'name: {artifact}' in text
    for suite in ('autotestes','reflex','xano-static','xano-safe','e2e'):assert f'--expected-suite {suite}' in text
    assert 'contents: read' in text and 'workflow_dispatch:' in text and 'pull_request:' in text
    assert '--expected-run-id "$GITHUB_RUN_ID" --expected-attempt "$GITHUB_RUN_ATTEMPT"' in text
    fake = tmp_path / 'python'
    fake.write_text('#!/bin/bash\nexit "${FIXTURE_RC:-0}"\n');fake.chmod(0o700)
    environment = dict(os.environ, PATH=str(tmp_path)+os.pathsep+os.environ.get('PATH',''))
    first_job = text.split('  reflex:')[0]
    install = re.search(r'        run: \|\n(.*?)      - name:', first_job, re.S).group(1)
    execute = re.search(r'      - name: Executar e produzir evidências.*?        run: \|\n(.*?)      - name:', first_job, re.S).group(1)
    for index, (script,rc) in enumerate(((install,13),(execute,7),(execute,0))):
        output=tmp_path/f'output-{index}';environment.update(GITHUB_OUTPUT=str(output),FIXTURE_RC=str(rc),INSTALL_CODE='0')
        captured=subprocess.run(['bash','-c',script],env=environment)
        assert captured.returncode==0 and output.read_text().strip()==f'code={rc}'
        # Mesmo após publicação bem sucedida, o gate real conserva o retorno original.
        environment['TEST_CODE']=str(rc)
        result=subprocess.run(['bash','-c','test "$INSTALL_CODE" = "0" && test "$TEST_CODE" = "0"'],env=environment)
        assert result.returncode==(0 if rc==0 else 1)

    # Cada download e cada publicação depende apenas de always, não do sucesso anterior.
    for block in text.split('      - ')[1:]:
        if 'uses: actions/download-artifact' in block or 'uses: actions/upload-artifact' in block:assert 'if: always()' in block


def test_fixtures_isolam_actions_sem_apagar_contexto_do_runner(tmp_path):
    summary = tmp_path / 'summary-externo.md'
    sentinel = 'Resumo externo preservado.\n'
    summary.write_text(sentinel)
    commit = ev.git('rev-parse', 'HEAD')
    # Contexto sintético exclusivo desta regressão; nenhuma chamada remota.
    env = dict(os.environ, GITHUB_ACTIONS='true', GITHUB_SHA=commit,
               GITHUB_RUN_ID='123456789', GITHUB_RUN_ATTEMPT='3',
               GITHUB_JOB='autotestes', GITHUB_REPOSITORY='owner/repo',
               GITHUB_STEP_SUMMARY=str(summary))
    selected = (
        'test_merge_ausencias_corrupcao_e_fontes_confiaveis',
        'test_merge_leitura_legada_somente_local_explicita_sem_alterar_origem',
        'test_merge_recusa_destino_preserva_historico_e_sem_roteiro_fixo',
        'test_codigos_reais_merge_sucesso_falha_erro_parcial_ignorado_bloqueado',
        'test_minimizacao_canarios_em_todos_formatos_e_logs',
        'test_needs_failure_nao_substituido_por_publicacao_e_roteiro_explicito',
    )
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '-q', *[f'{__file__}::{name}' for name in selected]],
        cwd=ev.ROOT, env=env, text=True, capture_output=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout[-3000:]
    assert summary.read_text() == sentinel
    output = tmp_path / 'runner-intencional'
    result = subprocess.run(
        [sys.executable, str(ev.ROOT / 'scripts/run_test_evidence.py'),
         '--suite', 'xano-static', '--output', str(output),
         '--blocked-reason', 'dependencia', '--require-complete'],
        cwd=ev.ROOT, env=env, text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 1
    data = json.loads((output / 'resultados.json').read_text())
    assert data['commit'] == data['sha_esperado'] == commit
    assert (data['github_run_id'], data['github_run_attempt'], data['github_job']) == ('123456789', '3', 'autotestes')
    assert data['ambiente'] == 'GitHub Actions' and data['totais']['BLOCKED'] == N_ESTATICA
    assert_formats(output)
    assert summary.read_text().startswith(sentinel + '# Evidências: xano-static')

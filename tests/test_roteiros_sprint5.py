"""Autotestes dos roteiros: nenhum dado sintético constitui teste de produto."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from scripts import roteiros_sprint5, roteiros_testes, run_test_evidence as ev


def _caso(case, status):
    return {**case, 'status':status, 'duracao_segundos':0, 'motivo':'Omissão de fixture' if status in ev.UNEXECUTED else ''}


def test_catalogo_tem_somente_os_seis_roteiros_abertos_sem_ponta_a_ponta():
    assert [r['numero'] for r in roteiros_sprint5.ROTEIROS]==[101,102,103,104,105,106]
    assert sum(len(r['verificacoes']) for r in roteiros_sprint5.ROTEIROS)==22
    assert all('ponta-a-ponta' not in r['url'] for r in roteiros_sprint5.ROTEIROS)
    assert sum(not v['casos'] for r in roteiros_sprint5.ROTEIROS for v in r['verificacoes'])==3


def test_todos_os_seletores_disponiveis_apontam_para_casos_reais():
    config=roteiros_testes.load_config(roteiros_sprint5.CONFIG)
    ids={c['id'] for c in ev.catalog('reflex')+ev.catalog('xano-safe')}
    assert all(set(v['casos'])<=ids for r in config['roteiros'] for v in r['verificacoes'])
    assert all('seletores' not in v for r in config['roteiros'] for v in r['verificacoes'])
    assert all('resultado_esperado' not in v for r in config['roteiros'] for v in r['verificacoes'])


def test_resultado_tecnico_propagado_sem_aprovar_execucao_parcial():
    cases=ev.catalog('reflex')[:2];item={'casos':[c['id'] for c in cases],'pendencia':'Manual'}
    passed=[_caso(c,'PASS') for c in cases]
    assert roteiros_testes.avaliar(item,passed)[0]=='PASS técnico'
    assert roteiros_testes.avaliar(item,passed[:1])[0]=='SEM EVIDÊNCIA'
    for status in ('NOT_RUN','SKIPPED','BLOCKED'):
        assert roteiros_testes.avaliar(item,[passed[0],_caso(cases[1],status)])[0]=='NÃO EXECUTADO'
    for status in ('FAIL','FAILED','ERROR','DESCONHECIDO'):
        assert roteiros_testes.avaliar(item,[passed[0],_caso(cases[1],status)])[0]=='FALHOU'


def test_caso_e2e_nao_conta_como_evidencia_deste_relatorio():
    case=ev.catalog('reflex')[0];case=_caso(case,'PASSED');case['tipo']='E2E'
    assert roteiros_testes.avaliar({'casos':[case['id']]},[case])[0]=='SEM EVIDÊNCIA'
    assert roteiros_testes.avaliar({'casos':[]},[])[0]=='PENDENTE'


def test_markdown_e_legivel_e_nao_contem_dados_de_entrada():
    cases=[_caso(c,'PASSED') for c in ev.catalog('reflex')+ev.catalog('xano-safe')]
    data={'commit':'abc','execucao_id':'local','casos':cases,'arvore_trabalho_limpa':False}
    text=roteiros_sprint5.gerar_relatorio(data)
    assert text.count('## 101 —')==1 and text.count('## 106 —')==1
    assert 'PASS técnico: 19' in text and 'PENDENTE: 3' in text
    assert 'nenhum roteiro é considerado aprovado por inteiro' in text
    assert 'SHA acima identifica apenas o commit de base' in text
    result=roteiros_testes.resultado_roteiro(data,roteiros_testes.load_config(roteiros_sprint5.CONFIG))
    assert result['nivel_validacao']=='PARCIAL' and not result['aprovacao_integral']
    assert result['pendencias_manuais']==22


def test_ciclo_temporario_reutiliza_ids_e_adaptador_cli():
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);config=roteiros_testes.load_config(roteiros_sprint5.CONFIG)
        config.update(ciclo='Fixture temporária',titulo='Fixture de reutilização',arquivo='fixture.md')
        path=tmp/'config.json';path.write_text(json.dumps(config));data=tmp/'data.json';data.write_text('{"casos":[]}')
        for script,args in [('roteiros_testes.py',['--config',str(path)]),('roteiros_sprint5.py',[])]:
            out=tmp/script
            proc=subprocess.run([sys.executable,str(ev.ROOT/'scripts'/script),'--input',str(data),'--output',str(out),*args],capture_output=True)
            assert proc.returncode==0
            assert 'PENDENTE' in out.read_text()
        assert [v['casos'] for r in config['roteiros'] for v in r['verificacoes']]==[v['casos'] for r in roteiros_sprint5.ROTEIROS for v in r['verificacoes']]
        # A execução completa pode reprovar; erro e ausência continuam incompletos.
        config['roteiros'] = [{'verificacoes': [{'casos': [ev.catalog('reflex')[0]['id']], 'pendencia': ''}]}]
        case = ev.catalog('reflex')[0]
        for status, technical, level in [('FAILED','FAILED','COMPLETA'), ('ERROR','ERROR','BLOQUEADA'), ('PASSED','PASSED','COMPLETA'), ('BLOCKED','PASSED','BLOQUEADA')]:
            result = roteiros_testes.resultado_roteiro({'casos': [_caso(case,status)]}, config)
            assert result['status_tecnico'] == technical and result['nivel_validacao'] == level
            assert result['aprovacao_integral'] == (status == 'PASSED')

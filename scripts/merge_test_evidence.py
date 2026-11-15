"""Consolida fontes compatíveis, publicando diagnóstico também sem artifacts."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import hashlib
import re
import os
from pathlib import Path
import sys
try:
    from . import run_test_evidence as evidence
    from . import roteiros_testes
except ImportError:
    import run_test_evidence as evidence
    import roteiros_testes


SAFE_REASONS = {
    'Navegador indisponível', 'Servidor público indisponível',
    'Dependência obrigatória indisponível', 'Instalação das dependências falhou',
    'Credencial de CLI Xano ausente', 'CLI Xano não instalado',
    'Autenticação/conectividade do CLI Xano indisponível',
    'Escrita não autorizada; isolamento e autorização explícita obrigatórios',
}


def safe_origin(source: dict, normalized: dict) -> dict:
    """Origem também é entrada externa: não republicar objetos ou texto livre."""
    result = {'suite': source['suite'], 'execucao_id': normalized['execucao_id'], 'commit': source['commit'],
              'github_run_id': source.get('github_run_id'), 'github_run_attempt': source.get('github_run_attempt'),
              'github_job': source.get('github_job') if isinstance(source.get('github_job'),str) and source.get('github_job') in {'autotestes','reflex','estatico','e2e','xano'} else None,
              'github_url': evidence.public_url(source.get('github_url')) if isinstance(source.get('github_url'),str) else None,
              'arvore_trabalho_limpa': source.get('arvore_trabalho_limpa') if isinstance(source.get('arvore_trabalho_limpa'),bool) else None}
    for key in ('inicio_utc', 'fim_utc'):
        try: result[key] = datetime.fromisoformat(source[key]).isoformat()
        except (ValueError,KeyError,TypeError): result[key] = None
    duration = source.get('duracao_segundos')
    result['duracao_segundos'] = duration if isinstance(duration,(int,float)) and 0 <= duration < float('inf') else None
    result['alvo_xano'] = {'branch':'v1','datasource':'live'} if source['suite']=='xano-safe' else None
    result['dependencias'] = [{'nome':source['suite'], 'disponivel':True if normalized['casos'] and all(c['status'] in {'PASSED','FAILED'} for c in normalized['casos']) else None,
                              'motivos':sorted({c['motivo'] for c in normalized['casos'] if c['status']=='BLOCKED'})}]
    tools = source.get('ferramentas')
    result['ferramentas'] = {key: value if isinstance(value,str) and re.fullmatch(r'[0-9][0-9A-Za-z.+-]{0,40}',value) else 'indisponível'
                            for key,value in tools.items() if key in {'python','pytest','reflex','playwright','xano_cli'}} if isinstance(tools,dict) else {}
    return result


def validate_source(source: dict, commit: str, run, attempt, allow_legacy: bool) -> dict:
    """Fonte atual deve conferir contagens e eixos; legado exige opção local."""
    legacy=source.get('versao_formato') is None
    if legacy and (not allow_legacy or os.getenv('GITHUB_ACTIONS')):raise ValueError('Legado requer leitura local explícita')
    if not legacy and source.get('versao_formato')!=evidence.FORMAT_VERSION:raise ValueError('Versão inválida')
    if not legacy and source.get('sha_observado') != source.get('commit'):raise ValueError('SHA observado divergente')
    if source['commit']!=commit:raise ValueError('Commit incompatível')
    if not re.fullmatch(r'[0-9a-f]{40,64}',source['commit']):raise ValueError('Commit inválido')
    for key in ('github_run_id','github_run_attempt'):
        if source.get(key) is not None and not re.fullmatch(r'[0-9]+',str(source[key])):raise ValueError('Contexto GitHub inválido')
    if not legacy and (source.get('github_run_id')!=run or source.get('github_run_attempt')!=attempt):raise ValueError('Run/tentativa incompatíveis')
    if source['suite'] not in evidence.SUITES or not source.get('execucao_id'):raise ValueError('Origem inválida')
    origin = 'legado-' + hashlib.sha256(str(source['execucao_id']).encode()).hexdigest()[:12] if legacy else source['execucao_id']
    if not legacy and not re.fullmatch(r'(?:local|[0-9]+)-[0-9a-f]{12}',origin):raise ValueError('ID de execução inválido')
    cases=source['casos'];keys=[evidence.case_key(c) for c in cases]
    if len(keys)!=len(set(keys)):raise ValueError('Casos duplicados na origem')
    catalog=evidence.load_catalog();by_key={evidence.case_key(c):c for c in catalog if c['suite']==source['suite']}
    by_alias={a:evidence.case_key(c) for c in catalog if c['suite']==source['suite'] for a in c.get('aliases_historicos',[])}
    normalized=[];used=set()
    for raw in cases:
        key=evidence.case_key(raw)
        if legacy and raw['id'] in by_alias:key=by_alias[raw['id']]
        if key not in by_key or key in used:raise ValueError('Caso desconhecido ou repetido')
        used.add(key);status=evidence.state(raw['status'])
        if status in evidence.UNEXECUTED and not raw.get('motivo'):raise ValueError('Ausência sem motivo')
        duration=raw.get('duracao_segundos',0)
        if not isinstance(duration,(int,float)) or not 0<=duration<float('inf'):raise ValueError('Duração inválida')
        # Metadados de teste vêm do catálogo; saída livre das fontes não é republicada.
        case=dict(by_key[key]);case.update(status=status,duracao_segundos=duration,
            motivo='' if status=='PASSED' else raw['motivo'] if status=='BLOCKED' and raw.get('motivo') in SAFE_REASONS else {'FAILED':'Expectativa funcional não satisfeita','ERROR':'Erro de execução na fonte','BLOCKED':'Dependência ou autorização ausente na fonte','NOT_RUN':'Caso não iniciado na fonte','SKIPPED':'Omissão intencional na fonte'}[status],
            resultado_obtido='Assertions aprovadas' if status=='PASSED' else 'Sem aprovação técnica',origem_execucao=origin,origem_suite=source['suite'],evidencias=['resultados.json','resultados.xml','resumo.md'])
        normalized.append(case)
    # Fonte que omite caso não pode se apresentar completa.
    missing=set(by_key)-used
    if missing and not legacy:raise ValueError('Fonte omite casos esperados do catálogo')
    if not legacy:
        if source.get('total_casos')!=len(cases) or source.get('totais')!={s:sum(evidence.state(c['status'])==s for c in cases) for s in evidence.STATES}:raise ValueError('Contagens divergentes')
        technical,level=evidence.axes(cases,source.get('diagnosticos',[]),source.get('obrigacoes_pendentes',[]))
        if (source.get('status_tecnico'),source.get('nivel_validacao'))!=(technical,level):raise ValueError('Conclusão divergente')
        for name in ('inicio_utc','fim_utc'):
            if datetime.fromisoformat(source[name]).tzinfo is None:raise ValueError('Horário sem fuso')
    return {'casos':normalized,'legacy':legacy,'incompleta':bool(missing),'execucao_id':origin}


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,action='append',default=[])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expected-suite',choices=evidence.SUITES,action='append',required=True)
    parser.add_argument('--expected-commit',default=os.getenv('GITHUB_SHA') or evidence.git('rev-parse','HEAD'))
    parser.add_argument('--expected-run-id',default=os.getenv('GITHUB_RUN_ID'))
    parser.add_argument('--expected-attempt',default=os.getenv('GITHUB_RUN_ATTEMPT'))
    parser.add_argument('--needs-result',action='append',default=[])
    parser.add_argument('--allow-legacy-local',action='store_true')
    parser.add_argument('--require-execution',action='store_true')
    parser.add_argument('--require-complete',action='store_true')
    parser.add_argument('--roteiro',type=Path)
    args=parser.parse_args(argv)
    try:out=evidence.new_output(args.output)
    except OSError as exc:print(str(exc),file=sys.stderr);return 2
    data=evidence.metadata('consolidado',datetime.now(timezone.utc));data['commit']=args.expected_commit
    data['github_run_id']=args.expected_run_id;data['github_run_attempt']=args.expected_attempt
    expected=set(args.expected_suite);data['suites_esperadas']=sorted(expected)
    accepted={};seen_suites=set();seen_origins=set();invalid_suites=set()
    for input_index,path in enumerate(args.input,1):
        suite=None
        try:
            source=json.loads((path/'resultados.json' if path.is_dir() or path.suffix!='.json' else path).read_text(encoding='utf-8'))
            suite=source['suite'];origin=source['execucao_id']
            if suite in seen_suites or origin in seen_origins:
                invalid_suites.add(suite);accepted.pop(suite,None)
                for s,(prev,_) in list(accepted.items()):
                    if prev['execucao_id']==origin:accepted.pop(s);invalid_suites.add(s)
                raise ValueError('Origem ou suíte repetida')
            seen_suites.add(suite);seen_origins.add(origin)
            if suite not in expected or suite in invalid_suites:raise ValueError('Suíte não esperada ou repetida')
            normalized=validate_source(source,args.expected_commit,args.expected_run_id,args.expected_attempt,args.allow_legacy_local)
            accepted[suite]=(source,normalized)
        except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
            causes = {'Commit incompatível':'COMMIT', 'Run/tentativa incompatíveis':'RUN_ATTEMPT', 'Origem ou suíte repetida':'DUPLICACAO', 'Casos duplicados na origem':'CASOS_DUPLICADOS', 'Estado de caso desconhecido':'ESTADO', 'Contagens divergentes':'CONTAGENS', 'Conclusão divergente':'CONCLUSAO', 'Fonte omite casos esperados do catálogo':'CASOS_AUSENTES', 'Versão inválida':'VERSAO', 'SHA observado divergente':'SHA_OBSERVADO', 'Legado requer leitura local explícita':'LEGADO_NAO_AUTORIZADO'}
            cause = 'JSON_AUSENTE' if isinstance(exc,OSError) else 'JSON_INVALIDO' if isinstance(exc,json.JSONDecodeError) else causes.get(str(exc),'FORMATO_INVALIDO')
            data['diagnosticos'].append(evidence.diagnostic('FONTE_REJEITADA','Fonte ausente, inválida, duplicada ou com identidade incompatível',entrada=input_index,suite=suite if suite in evidence.SUITES else None,causa=cause))
    for suite in sorted(expected-set(accepted)):
        data['diagnosticos'].append(evidence.diagnostic('SUITE_AUSENTE','Suíte obrigatória sem fonte confiável',suite=suite))
        data['obrigacoes_pendentes'].append(suite)
    for suite,(source,normalized) in accepted.items():
        data['casos']+=normalized['casos']
        data['origens'].append(safe_origin(source,normalized))
        if source.get('diagnosticos') or source.get('falha_infraestrutura'):data['diagnosticos'].append(evidence.diagnostic('ERRO_FONTE','Fonte registra diagnóstico de infraestrutura',suite=suite))
        data['obrigacoes_pendentes'] += [suite+': obrigação pendente da fonte'] if source.get('obrigacoes_pendentes') else []
        if normalized['incompleta']:data['obrigacoes_pendentes'].append(suite+': catálogo atual não totalmente representado na fonte legada')
        if normalized['legacy']:data['limitacoes'].append(f'{suite}: leitura legada local; identidade run/tentativa não comprovada; arquivo original preservado.')
        if suite=='xano-safe':data['limitacoes'].append('Xano: equivalência integral do código remoto com o Git não demonstrada.')
    for item in args.needs_result:
        try:
            suite,result=item.split('=',1)
            if suite not in expected or result not in {'success','failure','cancelled','skipped'}:raise ValueError()
            if result!='success':data['diagnosticos'].append(evidence.diagnostic('JOB_NAO_APROVADO','Job obrigatório sem sucesso no Actions',suite=suite,resultado=result))
        except ValueError:data['diagnosticos'].append(evidence.diagnostic('NEEDS_INVALIDO','Contexto needs inválido'))
    if args.roteiro:
        try:
            config=roteiros_testes.load_config(args.roteiro);data['roteiro']=roteiros_testes.resultado_roteiro(data,config)
            (out/config['arquivo']).write_text(roteiros_testes.gerar_relatorio(data,config),encoding='utf-8')
            if not data['roteiro']['aprovacao_integral']:data['obrigacoes_pendentes'].append('Roteiro funcional selecionado com verificações ou etapas manuais pendentes')
        except (OSError,ValueError,KeyError):data['diagnosticos'].append(evidence.diagnostic('ROTEIRO_INVALIDO','Configuração de roteiro inválida'))
    evidence.write_reports(data,out)
    print(f"Consolidado: técnico={data['status_tecnico']} validação={data['nivel_validacao']} {data['totais']}")
    return evidence.gate(data,args.require_execution,args.require_complete)

if __name__=='__main__':sys.exit(main())

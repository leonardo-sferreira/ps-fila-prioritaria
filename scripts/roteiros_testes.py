"""Avalia roteiros configuráveis por IDs; lê evidências sem executar testes."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path

try:
    from .run_test_evidence import ROOT, load_catalog, public_url, state
except ImportError:
    from run_test_evidence import ROOT, load_catalog, public_url, state


def load_config(path: Path) -> dict:
    config=json.loads(path.read_text(encoding='utf-8'))
    if config.get('versao')!=1 or Path(config['arquivo']).name!=config['arquivo'] or not config['arquivo'].endswith('.md'):
        raise ValueError('Configuração de roteiro inválida')
    ids={c['id'] for c in load_catalog()}
    for card in config['roteiros']:
        if card.get('url') and not public_url(card['url']):raise ValueError('Link de atividade inválido')
        for check in card['verificacoes']:
            if set(check['casos'])-ids:raise ValueError('Roteiro referencia caso inexistente')
    return config


def avaliar(item: dict, cases: list[dict]) -> tuple[str,list[dict]]:
    ids=item['casos']
    if not ids:return 'PENDENTE',[]
    # Cada ID parametrizado exige todas as variantes catalogadas.
    expected={ (c['id'],c.get('variante','')) for c in load_catalog() if c['id'] in ids }
    aliases={a:(c['id'],c.get('variante','')) for c in load_catalog() for a in c.get('aliases_historicos',[])}
    found=[];keys=set();states=[]
    for c in cases:
        key=(c.get('id'),c.get('variante',''))
        if c.get('id') in aliases:key=aliases[c['id']]
        if key not in expected or c.get('tipo') in {'E2E','e2e'}:continue
        found.append(c);keys.add(key)
        try:states.append(state(c['status']))
        except ValueError:states.append('ERROR')
    if set(states)&{'FAILED','ERROR'}:return 'FALHOU',found
    if keys!=expected:return 'SEM EVIDÊNCIA',found
    if set(states)&{'SKIPPED','NOT_RUN','BLOCKED'}:return 'NÃO EXECUTADO',found
    return ('PASS técnico' if states and set(states)=={'PASSED'} else 'SEM EVIDÊNCIA'),found


def resultado_roteiro(data: dict, config: dict) -> dict:
    catalog = load_catalog()
    aliases = {a: (c['id'], c.get('variante', '')) for c in catalog for a in c.get('aliases_historicos', [])}
    checks = []
    states = []
    pending = False
    for roteiro in config['roteiros']:
        for item in roteiro['verificacoes']:
            result, found = avaliar(item, data.get('casos', []))
            expected = {(c['id'], c.get('variante', '')) for c in catalog if c['id'] in item['casos']}
            observed = {aliases.get(c.get('id'), (c.get('id'), c.get('variante', ''))) for c in found}
            current = []
            for case in found:
                try:
                    current.append(state(case['status']))
                except ValueError:
                    current.append('ERROR')
            states.extend(current)
            pending |= bool(item['pendencia']) or not expected or expected != observed or bool(set(current) & {'ERROR', 'SKIPPED', 'NOT_RUN', 'BLOCKED'})
            checks.append({'resultado': result, 'pendencia': item['pendencia']})
    useful = bool(set(states) & {'PASSED', 'FAILED'})
    technical = 'ERROR' if 'ERROR' in states else 'FAILED' if 'FAILED' in states else 'PASSED'
    level = ('PARCIAL' if pending else 'COMPLETA') if useful else 'BLOQUEADA' if set(states) & {'BLOCKED', 'ERROR'} else 'NAO_EXECUTADA'
    return {'ciclo': config['ciclo'], 'arquivo': config['arquivo'], 'status_tecnico': technical, 'nivel_validacao': level,
            'aprovacao_integral': technical == 'PASSED' and level == 'COMPLETA',
            'totais': dict(Counter(c['resultado'] for c in checks)), 'pendencias_manuais': sum(bool(c['pendencia']) for c in checks)}


def gerar_relatorio(data: dict, config: dict) -> str:
    result=resultado_roteiro(data,config)
    lines=[f"# {config['titulo']}",'',f"Ciclo: {config['ciclo']} · Commit: `{data.get('commit','indisponível')}` · Execução: `{data.get('execucao_id','indisponível')}`",'', config.get('descricao',''),'',
           f"Resultado técnico: **{result['status_tecnico']}** · Validação funcional: **{result['nivel_validacao']}** · Aprovação integral: **{'sim' if result['aprovacao_integral'] else 'não'}**",'',
           '**PASS técnico** confirma apenas os testes citados; nenhum roteiro é considerado aprovado por inteiro sem executar seus passos pendentes.','',
           'IDs, variantes, nomes, requisitos e resultados esperados estão no catálogo e em `resultados.json`; nenhuma pendência cria caso fictício.','']
    if not data.get('arvore_trabalho_limpa',True) or any('Árvore de trabalho com alterações locais' in l for l in data.get('limitacoes',[])):
        lines+=['O SHA acima identifica apenas o commit de base; arquivos locais alterados participaram da coleta.','']
    if any('equivalência integral do código remoto' in l for l in data.get('limitacoes',[])):
        lines+=['A equivalência integral do Xano remoto com o Git não foi demonstrada.','']
    lines += [' · '.join(f'{s}: {n}' for s,n in result['totais'].items()),'']
    for card in config['roteiros']:
        title=f"[{card['titulo']}]({card['url']})" if card.get('url') else card['titulo']
        lines += [f"## {card['numero']} — {title}",'','| Verificação | Resultado técnico | IDs | Pendência obrigatória |','|---|---|---|---|']
        for item in card['verificacoes']:
            status,_=avaliar(item,data.get('casos',[]))
            cells=(item['titulo'],status,', '.join(item['casos']) or '—',item['pendencia'])
            lines.append('| '+' | '.join(str(c).replace('|','\\|').replace('\n',' ') for c in cells)+' |')
        lines.append('')
    return '\n'.join(lines)


def main(argv=None, default_config: Path | None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--config',type=Path,default=default_config,required=default_config is None)
    args=parser.parse_args(argv)
    if args.output.exists():raise FileExistsError('Relatório histórico preservado; escolha outra saída')
    config=load_config(args.config);data=json.loads(args.input.read_text())
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(gerar_relatorio(data,config),encoding='utf-8')
    return 0

if __name__=='__main__':raise SystemExit(main())

"""Adaptador histórico da Sprint 5; implementação comum em roteiros_testes."""
from pathlib import Path
try:
    from . import roteiros_testes as generic
except ImportError:
    import roteiros_testes as generic

CONFIG = Path(__file__).resolve().parents[1] / 'tests/roteiros/sprint5.json'
ROTEIROS = generic.load_config(CONFIG)['roteiros']
avaliar = generic.avaliar

def gerar_relatorio(dados: dict) -> str:
    return generic.gerar_relatorio(dados, generic.load_config(CONFIG))

def main() -> int:
    return generic.main(default_config=CONFIG)

if __name__=='__main__':raise SystemExit(main())

"""Inicia servidor de produção próprio, coleta E2E público e preserva histórico."""
from __future__ import annotations
import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen
try:
    from .run_test_evidence import ROOT, new_output
except ImportError:
    from run_test_evidence import ROOT, new_output

FRONTEND = ROOT / 'frontend'
OUTPUT = ROOT / 'test-evidence/e2e'


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));return sock.getsockname()[1]


def run_evidence(base_url: str | None, output: Path = OUTPUT, reason: str | None=None) -> int:
    env=os.environ.copy();env.pop('REFLEX_E2E_BASE_URL',None)
    if base_url:env['REFLEX_E2E_BASE_URL']=base_url
    args=[sys.executable,str(ROOT/'scripts/run_test_evidence.py'),'--suite','e2e','--output',str(output),'--require-execution','--require-complete']
    if reason:args+=['--blocked-reason',reason]
    return subprocess.run(args,env=env,check=False).returncode


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUTPUT)
    args=parser.parse_args(argv)
    try:out=new_output(args.output)
    except OSError as exc:print(str(exc),file=sys.stderr);return 2
    process=None;server_status='não iniciado';ready=False
    try:
        reflex=shutil.which('reflex')
        if not reflex or not importlib.util.find_spec('playwright'):return run_evidence(None,out,'dependencia')
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            if not Path(playwright.chromium.executable_path).exists():return run_evidence(None,out,'navegador')
        env=os.environ.copy();env['CI']='1';port=free_port();base=f'http://127.0.0.1:{port}'
        # Log livre temporário privado: nunca incluído nos artifacts.
        with tempfile.TemporaryFile(mode='w+') as stream:
            try:
                process=subprocess.Popen([reflex,'run','--env','prod','--single-port','--frontend-port',str(port)],cwd=FRONTEND,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            except OSError:
                server_status='falha ao iniciar';return run_evidence(None,out,'servidor')
            deadline=time.monotonic()+300
            while time.monotonic()<deadline and process.poll() is None:
                try:
                    with urlopen(base+'/login',timeout=2) as response:ready=response.status==200
                except (OSError,URLError):pass
                if ready:break
                time.sleep(2)
            server_status='pronto' if ready else 'não ficou pronto dentro do prazo'
            return run_evidence(base if ready else None,out,None if ready else 'servidor')
    finally:
        if process is not None and process.poll() is None:
            try:os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait()
        (out/'servidor.log').write_text(f'Servidor público controlado: {server_status}.\nSaída livre omitida por minimização.\n',encoding='utf-8')

if __name__=='__main__':sys.exit(main())

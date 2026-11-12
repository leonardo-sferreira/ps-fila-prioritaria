"""Sobe o Reflex no CI, executa o E2E público e encerra o servidor."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen

from run_test_evidence import ROOT, clean


FRONTEND = ROOT / "frontend"
OUTPUT = ROOT / "test-evidence" / "e2e"
BASE_URL = "http://127.0.0.1:3000"


def run_evidence(base_url: str | None) -> int:
    env = os.environ.copy()
    if base_url:
        env["REFLEX_E2E_BASE_URL"] = base_url
    else:
        env.pop("REFLEX_E2E_BASE_URL", None)
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_test_evidence.py"), "--suite", "e2e",
         "--output", str(OUTPUT), "--require-execution"],
        env=env, check=False,
    ).returncode


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    server_log = Path(tempfile.gettempdir()) / f"reflex-e2e-{os.getpid()}.log"
    reflex = shutil.which("reflex")
    if not reflex:
        (OUTPUT / "servidor.log").write_text("CLI Reflex não instalado.\n", encoding="utf-8")
        return run_evidence(None)

    env = os.environ.copy()
    env["CI"] = "1"
    process = None
    try:
        with server_log.open("w", encoding="utf-8") as stream:
            try:
                process = subprocess.Popen(
                    [reflex, "run", "--env", "prod", "--frontend-port", "3000"],
                    cwd=FRONTEND, env=env, stdout=stream, stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            except OSError as exc:
                print(f"Reflex não iniciou: {type(exc).__name__}", flush=True)
                return run_evidence(None)
            deadline = time.monotonic() + 300
            ready = False
            while time.monotonic() < deadline and process.poll() is None:
                try:
                    with urlopen(BASE_URL + "/login", timeout=2) as response:
                        ready = response.status == 200
                except (OSError, URLError):
                    pass
                if ready:
                    break
                time.sleep(2)
            if not ready:
                print("Reflex não ficou pronto; E2E registrado como NOT_RUN.", flush=True)
                return run_evidence(None)
            return run_evidence(BASE_URL)
    finally:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
        if server_log.exists():
            (OUTPUT / "servidor.log").write_text(
                clean(server_log.read_text(encoding="utf-8", errors="replace"), 20000) + "\n",
                encoding="utf-8",
            )
            server_log.unlink()


if __name__ == "__main__":
    sys.exit(main())

"""Consolida artefatos de jobs independentes sem alterar resultados de casos."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from run_test_evidence import execution_status, github_summary_write, junit_write, markdown_write


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_files = [path / "resultados.json" for path in args.input]
    if any(not path.exists() for path in source_files):
        missing = [str(path) for path in source_files if not path.exists()]
        print("Evidência ausente: " + ", ".join(missing), file=sys.stderr)
        return 2
    sources = [json.loads(path.read_text(encoding="utf-8")) for path in source_files]
    if len({source["commit"] for source in sources}) != 1:
        print("Commits divergentes entre os jobs", file=sys.stderr)
        return 2
    cases = []
    for source in sources:
        for case in source["casos"]:
            case = dict(case)
            case["origem_execucao"] = source["execucao_id"]
            cases.append(case)
    data = {
        "execucao_id": f"{os.getenv('GITHUB_RUN_ID', 'local')}-{os.getenv('GITHUB_RUN_ATTEMPT', '1')}",
        "data_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": sources[0]["commit"], "branch": sources[0]["branch"],
        "suite": "consolidado", "ambiente": sources[0]["ambiente"],
        "ferramentas": {source["suite"]: source["ferramentas"] for source in sources},
        "github_run_id": os.getenv("GITHUB_RUN_ID"), "github_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "limitacoes": [f"{source['suite']}: {item}" for source in sources for item in source["limitacoes"]],
        "falha_infraestrutura": any(source["falha_infraestrutura"] for source in sources),
        "casos": cases,
    }
    data["status_execucao"] = execution_status(cases, data["falha_infraestrutura"])
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "resultados.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    junit_write(cases, args.output / "resultados.xml", "consolidado")
    markdown_write(data, args.output / "resumo.md")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        github_summary_write(data, Path(os.environ["GITHUB_STEP_SUMMARY"]))
    counts = Counter(case["status"] for case in cases)
    print(f"Consolidado: {dict(counts)}")
    return 1 if counts["FAIL"] or counts["ERROR"] or data["falha_infraestrutura"] else 0


if __name__ == "__main__":
    sys.exit(main())

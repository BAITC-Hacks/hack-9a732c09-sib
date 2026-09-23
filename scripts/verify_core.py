"""Cross-platform judge/contract gate. Run from any working directory."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    command = [sys.executable, *args]
    print("RUN python " + " ".join(args), flush=True)
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=300,
                            env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1"))
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(args)}")
    if args[0] == "local_eval.py":
        if any(marker in result.stdout for marker in ("Агент упал", "отброшена", "не вернул ни одной")):
            raise RuntimeError("Evaluator silently rejected the agent/campaigns")
        if len(args) == 1 and "Пилотов проведено: 0" in result.stdout:
            raise RuntimeError("No pilots performed")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    manifest = json.loads((ROOT / "docs" / "organizer-manifest.json").read_text(encoding="utf-8-sig"))
    for relative, expected in manifest["sha256"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Organizer file changed: {relative}")
    print(f"PASS organizer integrity: {len(manifest['sha256'])} files", flush=True)
    run(["-m", "pytest", "-q", "tests/test_agent_contract.py", "tests/test_core_models.py", "tests/test_contract_fixtures.py"])
    run(["local_eval.py"])
    run(["local_eval.py", "--runs", "10"])
    run(["make_submission.py"])
    first = (ROOT / "submission.csv").read_bytes()
    run(["make_submission.py"])
    if first != (ROOT / "submission.csv").read_bytes():
        raise RuntimeError("Submission is not byte-for-byte reproducible")
    print("PASS submission SHA256: " + hashlib.sha256(first).hexdigest())
    print("PASS all core/contract/judge checks")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)

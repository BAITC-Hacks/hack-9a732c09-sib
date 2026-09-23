"""Cross-platform judge/contract gate. Run from any working directory."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    command = [sys.executable, *args]
    print("RUN python " + " ".join(args), flush=True)
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=300,
                            env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1",
                                     FP_LLM_PROVIDER="off"))
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


def verify_submission():
    path = ROOT / "submission.csv"
    original = path.read_bytes() if path.exists() else None
    try:
        run(["make_submission.py"])
        first = path.read_bytes()
        run(["make_submission.py"])
        if first != path.read_bytes():
            raise RuntimeError("Submission is not byte-for-byte reproducible")
        # The official pandas exporter uses native newlines; Git may store LF.
        if original is not None and original.replace(b"\r\n", b"\n") != first.replace(b"\r\n", b"\n"):
            raise RuntimeError("Existing submission differs from generated output; original preserved. Regenerate explicitly after review.")
        print("PASS submission SHA256: " + hashlib.sha256(first).hexdigest())
    finally:
        # Pre-flight must not destroy an existing human-edited artifact, even on failure.
        if original is not None:
            path.write_bytes(original)


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
    # A fresh temp root avoids stale Windows pytest permissions. Include runtime
    # and backend regressions, not only the original bootstrap test files.
    with TemporaryDirectory(prefix="false-positive-verify-") as temporary:
        run(["-m", "pytest", "-q", "-p", "no:cacheprovider",
             "--basetemp", str(Path(temporary) / "pytest")])
    run(["local_eval.py"])
    run(["local_eval.py", "--runs", "10"])
    verify_submission()
    print("PASS all core/runtime/backend/contract/judge checks (offline)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)

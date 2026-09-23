"""Pre-flight must preserve an existing artifact when generation fails/drifts."""

import pytest
from types import SimpleNamespace

from scripts import verify_core


def test_verifier_overrides_llm_mode_only_in_child_process(monkeypatch):
    monkeypatch.setenv("FP_LLM_PROVIDER", "openai")
    captured = {}
    def fake_run(command, **kwargs):
        captured.update(kwargs["env"])
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(verify_core.subprocess, "run", fake_run)
    verify_core.run(["make_submission.py"])
    assert captured["FP_LLM_PROVIDER"] == "off"
    assert verify_core.os.environ["FP_LLM_PROVIDER"] == "openai"


@pytest.mark.parametrize("failure", ["stale", "crash", "nondeterministic"])
def test_verifier_preserves_existing_submission_on_failure(tmp_path, monkeypatch, failure):
    path = tmp_path / "submission.csv"
    path.write_bytes(b"existing human content\n")
    monkeypatch.setattr(verify_core, "ROOT", tmp_path)
    calls = []

    def generator(args):
        calls.append(args)
        content = str(len(calls)).encode() if failure == "nondeterministic" else b"new content\n"
        path.write_bytes(content)
        if failure == "crash":
            raise RuntimeError("generator failed after opening file")

    monkeypatch.setattr(verify_core, "run", generator)
    with pytest.raises(RuntimeError):
        verify_core.verify_submission()
    assert path.read_bytes() == b"existing human content\n"


def test_verifier_can_generate_missing_submission(tmp_path, monkeypatch):
    monkeypatch.setattr(verify_core, "ROOT", tmp_path)
    path = tmp_path / "submission.csv"
    monkeypatch.setattr(verify_core, "run", lambda args: path.write_bytes(b"generated\n"))
    verify_core.verify_submission()
    assert path.read_bytes() == b"generated\n"


def test_existing_csv_from_another_platform_is_preserved(tmp_path, monkeypatch):
    path = tmp_path / "submission.csv"
    path.write_bytes(b"campaign,channel\nexample,push\n")
    monkeypatch.setattr(verify_core, "ROOT", tmp_path)
    monkeypatch.setattr(verify_core, "run", lambda args: path.write_bytes(b"campaign,channel\r\nexample,push\r\n"))
    verify_core.verify_submission()
    assert path.read_bytes() == b"campaign,channel\nexample,push\n"

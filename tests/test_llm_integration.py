import json

import pytest

from false_positive.domain.models import Campaign, Candidate
from runtime.configured import build_engine
from runtime.llm import LLMHypothesisAdvisor


CANDIDATES = [Candidate(Campaign("tariff_2", "push"), 100, 200000., 0.),
              Candidate(Campaign("tariff_3", "push"), 200, 400000., 0.)]


def test_provider_payload_and_validation_without_network(monkeypatch):
    calls = []
    def transport(self, url, payload):
        calls.append((url, payload))
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": '{"order":[1,0]}'}]}]}
    monkeypatch.setattr(LLMHypothesisAdvisor, "_request", transport)
    advisor = LLMHypothesisAdvisor("openai", "test-secret")
    assert advisor.prioritize(CANDIDATES, [], {}) == [1, 0]
    assert len(calls) == 1 and "ID_NUMBER" not in json.dumps(calls[0][1])
    assert "test-secret" not in repr(advisor) and "test-secret" not in json.dumps(calls[0][1])
    with pytest.raises(ValueError, match="budget"):
        advisor.prioritize(CANDIDATES, [], {})


@pytest.mark.parametrize("answer", ['{"order":[0,0]}', '{"order":[true,0]}', '{"order":[2,0]}',
                                    '{"order":[0]}', '{"order":[1,0],"campaign":{}}', 'invalid JSON'])
def test_malformed_model_output_rejected(monkeypatch, answer):
    monkeypatch.setattr(LLMHypothesisAdvisor, "_request", lambda *args: {
        "output": [{"type": "message", "content": [{"type": "output_text", "text": answer}]}]})
    with pytest.raises(ValueError):
        LLMHypothesisAdvisor("openai", "test-secret").prioritize(CANDIDATES, [], {})


def test_offline_mode_never_reads_env_file(monkeypatch):
    import runtime.configured as configured
    def forbidden():
        raise AssertionError("Offline mode read .env")
    monkeypatch.setattr(configured, "settings_from_env_file", forbidden)
    assert build_engine("off").hypothesis_advisor is None
    with pytest.raises(ValueError, match="off or openai"):
        build_engine("nvidia")


def test_key_alias_and_missing_key_are_controlled(monkeypatch):
    import runtime.configured as configured
    monkeypatch.setattr(configured, "settings_from_env_file", lambda: {"OPEN_AI_API_KEY": "test-secret"})
    assert build_engine("openai").hypothesis_advisor.api_key == "test-secret"
    monkeypatch.setattr(configured, "settings_from_env_file", lambda: {})
    advisor = build_engine("openai").hypothesis_advisor
    with pytest.raises(ValueError, match="configuration"):
        advisor.prioritize(CANDIDATES, [], {})


@pytest.mark.parametrize("error", [PermissionError("private path"),
                                  UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad encoding")])
def test_unreadable_settings_use_observable_fallback(monkeypatch, error):
    import runtime.configured as configured
    from tests.test_adaptive_strategy import ScenarioEnvironment
    def unreadable():
        raise error
    monkeypatch.setattr(configured, "settings_from_env_file", unreadable)
    result = build_engine("openai").run(ScenarioEnvironment(lambda *args: -0.3))
    assert result.campaigns
    assert "hypothesis_advisor_fallback:ValueError" in result.warnings

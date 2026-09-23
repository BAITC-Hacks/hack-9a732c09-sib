import json
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from false_positive.domain.models import Campaign, Candidate
from runtime.configured import build_engine
from runtime.llm import (
    LLMAuthenticationError, LLMCallLimitError, LLMConfigurationError,
    LLMHypothesisAdvisor, LLMIncompleteResponse, LLMInvalidJSON,
    LLMInvalidPriorities, LLMNetworkError, LLMProviderError, LLMRateLimitError,
    LLMRefusal, LLMResponseShapeError, LLMTimeoutError,
)


CANDIDATES = [Candidate(Campaign("tariff_2", "push"), 100, 200000., 0.),
              Candidate(Campaign("tariff_3", "push"), 200, 400000., 0.)]


def completed_response(answer):
    return {"status": "completed", "output": [{"type": "message", "content": [
        {"type": "output_text", "text": answer}]}]}


def test_provider_payload_and_validation_without_network(monkeypatch):
    calls = []
    def transport(self, url, payload):
        calls.append((url, payload))
        return completed_response('{"priorities":{"h0":20,"h1":90}}')
    monkeypatch.setattr(LLMHypothesisAdvisor, "_request", transport)
    advisor = LLMHypothesisAdvisor("openai", "test-secret")
    assert advisor.prioritize(CANDIDATES, [], {}) == [1, 0]
    assert len(calls) == 1 and "ID_NUMBER" not in json.dumps(calls[0][1])
    assert "test-secret" not in repr(advisor) and "test-secret" not in json.dumps(calls[0][1])
    schema = calls[0][1]["text"]["format"]["schema"]["properties"]["priorities"]
    assert set(schema["required"]) == {"h0", "h1"}
    assert schema["additionalProperties"] is False
    assert advisor.diagnostics["status"] == "accepted"
    assert "test-secret" not in json.dumps(advisor.diagnostics)
    with pytest.raises(LLMCallLimitError, match="budget"):
        advisor.prioritize(CANDIDATES, [], {})
    assert len(calls) == 1


@pytest.mark.parametrize("answer", [
    '{"priorities":{"h0":20}}',
    '{"priorities":{"h0":20,"h1":90,"h2":10}}',
    '{"priorities":{"h0":true,"h1":90}}',
    '{"priorities":{"h0":-1,"h1":90}}',
    '{"priorities":{"h0":20,"h1":101}}',
    '{"priorities":{"h0":"20","h1":90}}',
    '{"priorities":{"h0":20,"h1":90},"campaign":{}}',
    '{"order":[1,0]}',
])
def test_malformed_model_output_rejected(monkeypatch, answer):
    monkeypatch.setattr(LLMHypothesisAdvisor, "_request", lambda *args: completed_response(answer))
    advisor = LLMHypothesisAdvisor("openai", "test-secret")
    with pytest.raises(LLMInvalidPriorities):
        advisor.prioritize(CANDIDATES, [], {})
    assert advisor.diagnostics["status"] == "fallback"


@pytest.mark.parametrize("answer", [
    'invalid JSON', '{"priorities":{"h0":20,"h0":90,"h1":10}}',
])
def test_invalid_json_and_duplicate_keys_rejected(monkeypatch, answer):
    monkeypatch.setattr(LLMHypothesisAdvisor, "_request", lambda *args: completed_response(answer))
    with pytest.raises(LLMInvalidJSON):
        LLMHypothesisAdvisor("openai", "test-secret").prioritize(CANDIDATES, [], {})


def test_priority_ties_preserve_order_without_duplicate_hypotheses(monkeypatch):
    monkeypatch.setattr(LLMHypothesisAdvisor, "_request", lambda *args:
                        completed_response('{"priorities":{"h1":50,"h0":50}}'))
    assert LLMHypothesisAdvisor("openai", "test-secret").prioritize(CANDIDATES, [], {}) == [0, 1]


@pytest.mark.parametrize("response,category", [
    ({"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}}, LLMIncompleteResponse),
    ({"status": "completed", "output": [{"type": "message", "content": [
        {"type": "refusal", "refusal": "private provider text"}]}]}, LLMRefusal),
    ({"status": "completed", "output": []}, LLMResponseShapeError),
    ({"status": "failed"}, LLMResponseShapeError),
])
def test_unusable_responses_have_safe_error_categories(monkeypatch, response, category):
    monkeypatch.setattr(LLMHypothesisAdvisor, "_request", lambda *args: response)
    advisor = LLMHypothesisAdvisor("openai", "test-secret")
    with pytest.raises(category) as caught:
        advisor.prioritize(CANDIDATES, [], {})
    assert advisor.diagnostics["error_code"] == category.__name__
    assert "private provider text" not in str(caught.value) + json.dumps(advisor.diagnostics)


@pytest.mark.parametrize("status,category", [
    (401, LLMAuthenticationError), (429, LLMRateLimitError), (503, LLMProviderError),
])
def test_http_failures_do_not_expose_provider_body(monkeypatch, status, category):
    import runtime.llm as llm
    error = HTTPError("https://api.openai.com/v1/responses", status, "private message",
                      {}, BytesIO(b"private body"))
    class FailingOpener:
        def open(self, *args, **kwargs):
            raise error
    monkeypatch.setattr(llm, "build_opener", lambda *args: FailingOpener())
    advisor = LLMHypothesisAdvisor("openai", "test-secret")
    with pytest.raises(category) as caught:
        advisor.prioritize(CANDIDATES, [], {})
    assert advisor.diagnostics["http_status"] == status
    assert advisor.diagnostics["error_code"] == category.__name__
    assert error.fp.closed
    assert "private" not in str(caught.value) + json.dumps(advisor.diagnostics)
    assert "test-secret" not in str(caught.value) + json.dumps(advisor.diagnostics)


@pytest.mark.parametrize("error,category", [
    (TimeoutError("private timeout"), LLMTimeoutError),
    (URLError(TimeoutError("private timeout")), LLMTimeoutError),
    (URLError("private network"), LLMNetworkError),
])
def test_connection_failures_have_safe_error_categories(monkeypatch, error, category):
    import runtime.llm as llm
    class FailingOpener:
        def open(self, *args, **kwargs):
            raise error
    monkeypatch.setattr(llm, "build_opener", lambda *args: FailingOpener())
    advisor = LLMHypothesisAdvisor("openai", "test-secret")
    with pytest.raises(category) as caught:
        advisor.prioritize(CANDIDATES, [], {})
    assert advisor.diagnostics["error_code"] == category.__name__
    assert "private" not in str(caught.value) + json.dumps(advisor.diagnostics)


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
    with pytest.raises(LLMConfigurationError, match="configuration"):
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
    assert "hypothesis_advisor_fallback:LLMConfigurationError" in result.warnings

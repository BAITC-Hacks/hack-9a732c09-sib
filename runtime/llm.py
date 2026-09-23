"""One bounded LLM call prioritizes public hypotheses, never authorizes spending."""

import json
from socket import timeout as SocketTimeout
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ADVISOR_VERSION = "priorities-v2"


class LLMConfigurationError(ValueError): pass
class LLMCallLimitError(ValueError): pass
class LLMAuthenticationError(ValueError): pass
class LLMRateLimitError(ValueError): pass
class LLMProviderError(ValueError): pass
class LLMTimeoutError(ValueError): pass
class LLMNetworkError(ValueError): pass
class LLMResponseTooLarge(ValueError): pass
class LLMInvalidJSON(ValueError): pass
class LLMIncompleteResponse(ValueError): pass
class LLMRefusal(ValueError): pass
class LLMResponseShapeError(ValueError): pass
class LLMInvalidPriorities(ValueError): pass


def strict_json(raw):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise LLMInvalidJSON("Duplicate JSON key")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=unique_pairs)
    except (json.JSONDecodeError, UnicodeError, TypeError):
        raise LLMInvalidJSON("Invalid JSON response") from None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass
class LLMHypothesisAdvisor:
    provider: str
    api_key: str = field(repr=False)
    model: str = ""
    timeout: float = 15.0
    calls: int = field(default=0, init=False)
    diagnostics: dict = field(default_factory=dict, init=False)

    def _request(self, url, payload):
        request = Request(url, data=json.dumps(payload, allow_nan=False).encode("utf-8"),
                          headers={"Authorization": "Bearer " + self.api_key,
                                   "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with build_opener(NoRedirect()).open(request, timeout=self.timeout) as response:
                self.diagnostics["http_status"] = response.status
                raw = response.read(262145)
        except HTTPError as exc:
            status = exc.code
            self.diagnostics["http_status"] = status
            exc.close()
            category = (LLMAuthenticationError if status in (401, 403) else
                        LLMRateLimitError if status == 429 else LLMProviderError)
            raise category("Provider HTTP error") from None
        except (TimeoutError, SocketTimeout):
            raise LLMTimeoutError("Provider timeout") from None
        except URLError as exc:
            category = LLMTimeoutError if isinstance(exc.reason, TimeoutError) else LLMNetworkError
            raise category("Provider connection failed") from None
        except OSError:
            raise LLMNetworkError("Provider connection failed") from None
        if len(raw) > 262144:
            raise LLMResponseTooLarge("LLM response exceeds limit")
        return strict_json(raw)

    def prioritize(self, candidates, tariffs, channels):
        if self.calls >= 1:
            raise LLMCallLimitError("LLM call budget exhausted")
        self.calls += 1
        self.diagnostics = dict(advisor_version=ADVISOR_VERSION, model=self.model or "gpt-4.1-mini",
                                calls=self.calls, status="started")
        try:
            order = self._prioritize(candidates, tariffs, channels)
        except Exception as exc:
            self.diagnostics.update(status="fallback", error_code=type(exc).__name__)
            raise
        self.diagnostics.update(status="accepted", order=order)
        return order

    def _prioritize(self, candidates, tariffs, channels):
        if self.provider != "openai" or not self.api_key or not 0 < self.timeout <= 30:
            raise LLMConfigurationError("Invalid LLM configuration")
        ids = [f"h{i}" for i in range(len(candidates))]
        if not ids:
            return []
        context = dict(
            hypotheses=[dict(id=ids[i], campaign=c.campaign.to_dict(), audience_size=c.n_customers,
                             baseline_total_arpu=c.baseline_arpu, cost_per_contact=c.cost_per_contact)
                        for i, c in enumerate(candidates)],
            tariffs=tariffs, channels=channels,
        )
        instructions = (
            "You prioritize experiments for a synthetic telecom tariff campaign case. "
            "Return JSON with exactly one key priorities: an object assigning EVERY hypothesis ID "
            "an integer research priority from 0 to 100 (higher is explored first). Ties are allowed. "
            "Prioritize diverse, plausible tariff transitions with meaningful audience value "
            "and affordable communication. Prices do not prove revenue uplift. True effects "
            "are unknown and only later noisy pilots can justify final deployment. "
            "Priorities express research preference, NOT predicted profit or confidence. "
            "You cannot change hypotheses, budgets, or evidence thresholds. "
            "No explanations or other keys. Data follows:\n" + json.dumps(context, allow_nan=False)
        )
        priorities_schema = {"type": "object",
            "properties": {key: {"type": "integer", "minimum": 0, "maximum": 100} for key in ids},
            "required": ids, "additionalProperties": False}
        schema = {"type": "object", "properties": {"priorities": priorities_schema},
                  "required": ["priorities"], "additionalProperties": False}
        result = self._request("https://api.openai.com/v1/responses", {
            "model": self.model or "gpt-4.1-mini", "input": instructions, "store": False,
            "max_output_tokens": 1024,
            "text": {"format": {"type": "json_schema", "name": "hypothesis_priorities", "strict": True, "schema": schema}},
        })
        if not isinstance(result, dict):
            raise LLMResponseShapeError("Response must be an object")
        status = result.get("status")
        self.diagnostics["response_status"] = status if status in ("completed", "incomplete", "failed") else "unknown"
        if status == "incomplete":
            details = result.get("incomplete_details") or {}
            reason = details.get("reason") if isinstance(details, dict) else None
            self.diagnostics["incomplete_reason"] = reason if reason in ("max_output_tokens", "content_filter") else "unknown"
            raise LLMIncompleteResponse("Incomplete provider response")
        if status != "completed" or not isinstance(result.get("output"), list):
            raise LLMResponseShapeError("Expected a completed response")
        texts = []
        for item in result["output"]:
            if not isinstance(item, dict):
                raise LLMResponseShapeError("Invalid output item")
            if item.get("type") != "message":
                continue
            if not isinstance(item.get("content"), list):
                raise LLMResponseShapeError("Invalid message content")
            for content in item["content"]:
                if not isinstance(content, dict):
                    raise LLMResponseShapeError("Invalid content item")
                if content.get("type") == "refusal":
                    raise LLMRefusal("Provider refused the request")
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    texts.append(content["text"])
        if len(texts) != 1:
            raise LLMResponseShapeError("Expected one structured output")
        answer = strict_json(texts[0])
        if not isinstance(answer, dict) or set(answer) != {"priorities"}:
            raise LLMInvalidPriorities("Unexpected priority shape")
        priorities = answer["priorities"]
        if (not isinstance(priorities, dict) or set(priorities) != set(ids)
                or any(type(v) is not int or not 0 <= v <= 100 for v in priorities.values())):
            raise LLMInvalidPriorities("Expected one bounded priority per hypothesis")
        self.diagnostics["priorities"] = priorities
        # Completeness follows from fixed object keys; ties cannot duplicate IDs.
        return sorted(range(len(ids)), key=lambda i: (-priorities[ids[i]], i))

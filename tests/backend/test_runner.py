from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.runner import StrategyRunner
from backend.app.schemas import RunAccepted
from backend.app.service import RunService
from false_positive.strategy.engine import StrategyEngine
from local_eval import evaluate_agent
from tests.backend.test_api import poll, submit


def metadata():
    return RunAccepted(run_id=uuid4(), created_at=datetime.now(timezone.utc),
                       status="queued", source="mock_environment")


def test_core_called_once_and_mapping_uses_official_score():
    calls, scores = [], []

    class SpyEngine(StrategyEngine):
        def run(self, env):
            calls.append(env)
            return super().run(env)

    def evaluator(agent, **kwargs):
        score = evaluate_agent(agent, **kwargs)
        scores.append(score)
        return score

    result = StrategyRunner(SpyEngine, evaluator).run(metadata(), 42)
    assert len(calls) == len(scores) == 1
    score = scores[0]
    assert result.n_campaigns == score["n_campaigns"] - score["n_pilots"]
    for key in ("gross_arpu_lift", "net_arpu_gain", "baseline_total_arpu", "total_arpu_after",
                "growth_vs_baseline_pct", "unique_customers_targeted", "risk_score_pct", "coverage_pct"):
        assert getattr(result, key) == score[key]


def test_paid_final_budget_comes_from_scoring():
    class PaidFinalEngine(StrategyEngine):
        def run(self, env):
            result = super().run(env)
            result.campaigns = [replace(c, channel="sms") for c in result.campaigns]
            return result

    result = StrategyRunner(PaidFinalEngine).run(metadata(), 42)
    assert result.total_cost > 0
    assert result.total_cost == sum(d.cost for d in result.campaigns_detail)
    assert result.remaining_budget == 100000 - result.total_cost
    assert result.remaining_budget < result.pilots[-1].remaining_budget
    assert result.remaining_contacts < result.pilots[-1].remaining_contacts
    assert result.roi == pytest.approx(result.gross_arpu_lift / result.total_cost)


def test_negative_score_is_completed():
    result = StrategyRunner().run(metadata(), 1)
    assert result.net_arpu_gain < 0
    assert result.status == "completed" and result.error is None


@pytest.mark.parametrize("failure", ["exception_after_pilots", "missing_pilot", "invalid_campaign"])
def test_swallowed_core_errors_and_incomplete_trace_are_failed(failure):
    class BrokenEngine(StrategyEngine):
        def run(self, env):
            result = super().run(env)
            if failure == "exception_after_pilots":
                raise RuntimeError("Core failed after consuming pilot resources")
            if failure == "missing_pilot":
                result.pilots.pop()
            if failure == "invalid_campaign":
                result.campaigns = [replace(c, target_tariff="tariff_99999") for c in result.campaigns]
            return result

    with TestClient(create_app(RunService(StrategyRunner(BrokenEngine)))) as client:
        result = poll(client, submit(client)["run_id"])
        assert result["status"] == "failed"
        assert result["error"]["code"] == "INCOMPLETE_RUN"
        assert "net_arpu_gain" not in result


@pytest.mark.parametrize("failure", ["none", "nan", "wrong_detail", "wrong_total", "twice"])
def test_invalid_evaluator_result_is_never_completed(failure):
    def bad_evaluator(agent, **kwargs):
        score = evaluate_agent(agent, **kwargs)
        if failure == "none":
            return None
        if failure == "nan":
            score["risk_score_pct"] = float("nan")
        if failure == "wrong_detail":
            score["campaigns_detail"][0]["n_contacts"] -= 1
        if failure == "wrong_total":
            score["total_contacts"] += 1
        if failure == "twice":
            evaluate_agent(agent, **kwargs)
        return score

    with TestClient(create_app(RunService(StrategyRunner(evaluator=bad_evaluator)))) as client:
        assert poll(client, submit(client)["run_id"])["status"] == "failed"

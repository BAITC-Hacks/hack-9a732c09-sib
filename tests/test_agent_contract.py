import ast
import json
from pathlib import Path

import pandas as pd
import pytest

from agent import Agent
from false_positive.domain.constraints import FILTER_VALUES
from false_positive.strategy.engine import StrategyEngine
from tests.support import ControlledEnvironment

ROOT = Path(__file__).resolve().parents[1]


def assert_valid(campaigns, env):
    assert isinstance(campaigns, list) and 1 <= len(campaigns) <= 10
    for campaign in campaigns:
        assert isinstance(campaign, dict)
        assert campaign["target_tariff"] in set(env.tariffs["tariff_plan_code"])
        assert campaign["channel"] in env.channels
        for key, allowed in FILTER_VALUES.items():
            assert campaign.get(key) is None or campaign[key] in allowed
    from scoring_core import validate_strategy
    validate_strategy(pd.DataFrame(campaigns), env.tariffs)


def test_agent_public_boundary_and_trace():
    env = ControlledEnvironment()
    run = StrategyEngine().run(env)
    assert_valid([c.to_dict() for c in run.campaigns], env)
    assert len(run.pilots) == len(env.pilot_history) > 0
    assert run.resources_after_plan.remaining_contacts >= 0
    assert run.resources_after_plan.remaining_budget >= 0
    assert {event["event"] for event in run.trace} >= {"started", "pilot_observed", "completed"}
    json.dumps(run.to_dict(), allow_nan=False)
    assert_valid(Agent().act(ControlledEnvironment()), env)


def test_observations_change_actual_decisions():
    first = Agent().act(ControlledEnvironment({"tariff_1": .3, "tariff_2": -.2, "tariff_3": -.2}))
    second = Agent().act(ControlledEnvironment({"tariff_1": -.2, "tariff_2": .3, "tariff_3": -.2}))
    assert first[0]["filter_current_tariff"] == "tariff_1"
    assert second[0]["filter_current_tariff"] == "tariff_2"


@pytest.mark.parametrize("pilot_error", [False, True])
def test_negative_or_failed_pilots_still_produce_one_valid_fallback(pilot_error):
    env = ControlledEnvironment({"tariff_1": -.3, "tariff_2": -.2, "tariff_3": -.1}, pilot_error)
    run = StrategyEngine().run(env)
    assert len(run.campaigns) == 1
    assert any(w.startswith("fallback_used") for w in run.warnings)
    assert_valid([c.to_dict() for c in run.campaigns], env)


@pytest.mark.parametrize("answer", [None, [100], [0, 0, 0], [True, 1, 2]])
def test_invalid_advisor_has_deterministic_fallback(answer):
    class InvalidAdvisor:
        def rank(self, observations):
            return answer
    actual = StrategyEngine(InvalidAdvisor()).run(ControlledEnvironment())
    expected = StrategyEngine().run(ControlledEnvironment())
    assert actual.campaigns == expected.campaigns
    assert any(w.startswith("advisor_fallback") for w in actual.warnings)


def test_observer_and_advisor_exceptions_do_not_break_judge():
    class Broken:
        def rank(self, observations):
            raise TimeoutError("unavailable")
        def record(self, event, payload):
            raise RuntimeError("unavailable")
    run = StrategyEngine(Broken()).run(ControlledEnvironment(), observer=Broken())
    assert run.campaigns == StrategyEngine().run(ControlledEnvironment()).campaigns
    assert "observer_failed" in run.warnings


def test_low_resources_reserve_a_real_final_campaign():
    env = ControlledEnvironment()
    env.channels.pop("push")
    env.remaining_budget = 160
    env.remaining_contacts = 40
    run = StrategyEngine().run(env)
    assert run.pilots
    assert run.resources_after_plan.remaining_budget >= 0
    assert run.resources_after_plan.remaining_contacts >= 0


def test_same_seed_same_submission_and_immutable_public_tables():
    from mock_environment import make_mock_env
    from make_submission import build_submission
    env, _ = make_mock_env(seed=42)
    profile, tariffs = env.customer_profile.copy(deep=True), env.tariffs.copy(deep=True)
    assert_valid(Agent().act(env), env)
    pd.testing.assert_frame_equal(profile, env.customer_profile)
    pd.testing.assert_frame_equal(tariffs, env.tariffs)
    first, second = build_submission(Agent()), build_submission(Agent())
    pd.testing.assert_frame_equal(first, second)
    assert 1 <= len(first) <= 10


@pytest.mark.parametrize("seed", range(10))
def test_official_evaluator_has_no_invalid_campaigns_and_respects_limits(seed, capsys):
    from local_eval import evaluate_agent
    result = evaluate_agent(Agent(), seed=seed, verbose=False)
    output = capsys.readouterr().out
    assert "отброшена" not in output and "Агент упал" not in output
    assert result is not None and 1 <= result["n_pilots"] <= 20
    assert 1 <= result["n_campaigns"] - result["n_pilots"] <= 10
    assert 0 <= result["total_cost"] <= 100000
    assert 0 < result["total_contacts"] <= 15000
    assert all(detail["n_contacts"] <= 5000 for detail in result["campaigns_detail"])


def test_core_dependency_direction():
    forbidden = {"backend", "frontend", "fastapi", "pydantic", "requests", "httpx", "openai",
                 "mock_environment", "environment", "scoring_core", "local_eval"}
    for path in [ROOT / "agent.py", *sorted((ROOT / "false_positive").rglob("*.py"))]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [(node.module or "").split(".")[0]]
            else:
                continue
            assert not (set(modules) & forbidden), path

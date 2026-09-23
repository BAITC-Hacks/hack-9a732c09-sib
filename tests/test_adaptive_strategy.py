from dataclasses import replace

import pandas as pd
import pytest

from false_positive.domain.models import Campaign, Candidate, PilotObservation
from false_positive.strategy.engine import StrategyEngine
from false_positive.strategy.evidence import Evidence
from tests.support import ControlledEnvironment


def observation(ratio, n=200, number=1):
    return PilotObservation(f"pilot_{number}", "tariff_2", "push", n, 0.0, ratio,
                            ratio * n * 2000, 100000.0, 15000 - n)


def evidence(ratios, cost=0):
    candidate = Candidate(Campaign("tariff_2", "push"), 1000, 2000000.0, cost)
    return Evidence(candidate, [observation(r, number=i) for i, r in enumerate(ratios)])


@pytest.mark.parametrize("ratios", [[.9], [.9, .9], [.9, -.3, -.3], [.02, .02, .02]])
def test_one_spike_two_reports_and_small_identical_gains_cannot_authorize_scale(ratios):
    assert not evidence(ratios).confirmed()


def test_stable_strong_evidence_can_authorize_scale_but_expensive_channel_cannot():
    assert evidence([.4, .4, .4]).confirmed()
    assert not evidence([.4, .4, .4], cost=1000).confirmed()
    assert evidence([.4, .4, .4]).uncertainty > 0
    assert evidence([.4, .4, .4]).uncertainty < evidence([.4]).uncertainty


class ScenarioEnvironment(ControlledEnvironment):
    """Public double with independent scripted effects, never mock model effects."""
    def __init__(self, behavior):
        super().__init__()
        self.behavior = behavior
        self.calls = {}
        self.customer_profile = pd.DataFrame([
            dict(ID_NUMBER=offset+i, current_tariff=tariff, arpu_segment="MID", data_segment="LITE",
                 call_segment="MEDIUM", predicted_arpu=arpu)
            for tariff, count, offset, arpu in [("tariff_1", 800, 0, 2000.),
                                              ("tariff_2", 600, 1000, 2000.),
                                              ("tariff_3", 1, 3000, 100.)]
            for i in range(count)
        ])

    def run_pilot(self, target_tariff, channel, n_customers=100, **filters):
        profile = self.customer_profile
        for name, value in filters.items():
            if value is not None:
                column = "current_tariff" if name == "filter_current_tariff" else name.removeprefix("filter_")
                profile = profile[profile[column].isin(value.split(";"))]
        cost_per_contact = self.channels[channel]["cost_per_contact"]
        n = min(n_customers, len(profile), self.remaining_contacts)
        if cost_per_contact:
            n = min(n, int(self.remaining_budget // cost_per_contact))
        assert self.pilots_left > 0 and 10 <= n_customers <= 200 and n > 0
        key = (filters.get("filter_current_tariff"), target_tariff, channel)
        call = self.calls.get(key, 0)
        self.calls[key] = call + 1
        ratio = self.behavior(key, call)
        cost = n * cost_per_contact
        self.remaining_budget -= cost
        self.remaining_contacts -= n
        self.pilots_left -= 1
        result = dict(pilot=f"pilot_{len(self.pilot_history)+1}", target_tariff=target_tariff,
                      channel=channel, n_customers=n, cost=cost, observed_lift_ratio=ratio,
                      observed_lift_total=ratio*n*float(profile.predicted_arpu.mean()),
                      remaining_budget=self.remaining_budget, remaining_contacts=self.remaining_contacts)
        self.pilot_history.append(result)
        return result


def test_exploratory_spike_is_not_scaled_and_fallback_minimizes_exposure():
    env = ScenarioEnvironment(lambda key, call: .9 if call == 0 else -.4)
    run = StrategyEngine().run(env)
    assert len(run.campaigns) == 1
    assert run.campaigns[0].filter_current_tariff == "tariff_3"
    assert any(w.startswith("fallback_used") for w in run.warnings)


def test_confirmed_audience_is_deployed_once_after_repeats_and_resources_are_shared():
    env = ScenarioEnvironment(lambda key, call: .8 if key[0] == "tariff_1" else -.8)
    run = StrategyEngine().run(env)
    assert run.campaigns[0].filter_current_tariff == "tariff_1"
    assert len(run.pilots) <= 20 and any(count >= 3 for count in env.calls.values())
    # Different tariff/channel hypotheses of the same audience cannot overlap in final.
    audiences = [(c.filter_current_tariff, c.filter_arpu_segment, c.filter_data_segment, c.filter_call_segment)
                 for c in run.campaigns]
    assert len(audiences) == len(set(audiences))
    assert run.resources_after_plan.remaining_contacts >= 0
    assert run.resources_after_plan.remaining_budget >= 0
    assert sum(p.n_customers for p in run.pilots) <= 3000
    assert sum(p.cost for p in run.pilots) <= 15000


def test_failure_after_resource_consumption_keeps_actual_reserve():
    class Malformed(ScenarioEnvironment):
        def run_pilot(self, *args, **kwargs):
            result = super().run_pilot(*args, **kwargs)
            result["observed_lift_ratio"] = float("nan")
            return result
    env = Malformed(lambda key, call: -.2)
    run = StrategyEngine().run(env)
    assert not run.pilots and env.pilot_history
    assert run.resources_after_pilots.remaining_contacts == env.remaining_contacts
    assert run.resources_after_plan.remaining_contacts >= 0
    assert any(w.startswith("pilot_failed") for w in run.warnings)


@pytest.mark.parametrize("order", [None, [999], [True, False], [0, 0]])
def test_bad_external_advisor_falls_back_without_changing_plan(order):
    class BadAdvisor:
        def prioritize(self, candidates, tariffs, channels):
            return order
    actual = StrategyEngine(hypothesis_advisor=BadAdvisor()).run(ControlledEnvironment())
    expected = StrategyEngine().run(ControlledEnvironment())
    assert actual.campaigns == expected.campaigns
    assert any(w.startswith("hypothesis_advisor_fallback") for w in actual.warnings)


def test_external_advisor_can_prioritize_but_cannot_bypass_pilot_confirmation():
    class Advisor:
        def prioritize(self, candidates, tariffs, channels):
            return list(reversed(range(len(candidates))))
    run = StrategyEngine(hypothesis_advisor=Advisor()).run(ScenarioEnvironment(lambda key, call: -.8))
    assert run.campaigns[0].filter_current_tariff == "tariff_3"
    assert any(w.startswith("fallback_used") for w in run.warnings)

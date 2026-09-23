"""One core execution inside the official evaluator; no private environment access."""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from math import isclose
from time import perf_counter

from false_positive.strategy.engine import StrategyEngine
from local_eval import evaluate_agent

from .schemas import Campaign, RunAccepted, RunCompleted


class IncompleteRunError(ValueError):
    """The evaluator result cannot be reconciled with a successful core run."""


class CapturingAgent:
    def __init__(self, engine):
        self.engine = engine
        self.run = None
        self.calls = 0
        self.returned = False
        self.subscriber_count = 0

    def act(self, env):
        self.calls += 1
        if self.calls != 1:
            raise IncompleteRunError("Repeated agent invocation")
        self.subscriber_count = len(env.customer_profile)
        self.run = self.engine.run(env)
        campaigns = [campaign.to_dict() for campaign in self.run.campaigns]
        known_tariffs = set(env.tariffs["tariff_plan_code"])
        if not 1 <= len(campaigns) <= 10:
            raise IncompleteRunError("Final plan is empty or exceeds the limit")
        for campaign in campaigns:
            Campaign.model_validate(campaign)
            if campaign["target_tariff"] not in known_tariffs:
                raise IncompleteRunError("Unknown final tariff")
        self.returned = True
        return campaigns


def require(condition, message):
    if not condition:
        raise IncompleteRunError(message)


class StrategyRunner:
    def __init__(self, engine_factory=StrategyEngine, evaluator=evaluate_agent):
        self.engine_factory = engine_factory
        self.evaluator = evaluator

    def run(self, accepted: RunAccepted, seed: int) -> RunCompleted:
        started = perf_counter()
        agent = CapturingAgent(self.engine_factory())
        score = self.evaluator(agent, seed=seed, verbose=False)
        run = agent.run
        require(agent.calls == 1 and agent.returned and run is not None and score is not None,
                "Evaluator did not capture a successful strategy execution")
        pilots, campaigns = run.pilots, run.campaigns
        details = score["campaigns_detail"]
        require(score["n_pilots"] == len(pilots), "Incomplete pilot trace")
        require(score["n_campaigns"] == len(pilots) + len(campaigns) == len(details),
                "Evaluator changed the campaign plan")
        mapped_details = []
        for position, detail in enumerate(details):
            is_pilot = position < len(pilots)
            index = position if is_pilot else position - len(pilots)
            row = pilots[index] if is_pilot else campaigns[index]
            name = row.pilot if is_pilot else row.campaign_name
            require(detail["name"] == name and detail["channel"] == row.channel,
                    "Campaign detail does not match trace")
            if is_pilot:
                require(detail["n_contacts"] == row.n_customers and isclose(detail["cost"], row.cost),
                        "Pilot accounting does not match trace")
            require(detail["n_negative"] <= detail["n_contacts"], "Invalid negative contact count")
            mapped_details.append(dict(detail, kind="pilot" if is_pilot else "final", index=index))
        cost, contacts = score["total_cost"], score["total_contacts"]
        require(isclose(sum(d["cost"] for d in details), cost), "Inconsistent scored cost")
        require(sum(d["n_contacts"] for d in details) == contacts, "Inconsistent scored contacts")
        require(score["unique_customers_targeted"] <= min(agent.subscriber_count, contacts),
                "Invalid unique customer count")
        require(isclose(score["net_arpu_gain"], score["gross_arpu_lift"] - cost), "Inconsistent net gain")
        warnings = list(run.warnings)
        if cost == 0:
            warnings.append("roi_undefined:zero_total_cost")
        values = {key: score[key] for key in (
            "baseline_total_arpu", "gross_arpu_lift", "total_cost", "net_arpu_gain", "total_arpu_after",
            "growth_vs_baseline_pct", "total_contacts", "unique_customers_targeted", "coverage_pct",
            "risk_score_pct",
        )}
        result = RunCompleted(
            **dict(accepted.model_dump(), status="completed"), completed_at=datetime.now(timezone.utc),
            **values, n_pilots=len(pilots), n_campaigns=len(campaigns),
            roi=None if cost == 0 else score["roi"], remaining_budget=100000 - cost,
            remaining_contacts=15000 - contacts, pilots=[asdict(p) for p in pilots],
            campaigns=[c.to_dict() for c in campaigns], campaigns_detail=mapped_details,
            warnings=warnings, duration_ms=(perf_counter() - started) * 1000, error=None,
        )
        # Validate before publishing, including all nested values.
        json.dumps(result.model_dump(mode="json"), allow_nan=False)
        return result

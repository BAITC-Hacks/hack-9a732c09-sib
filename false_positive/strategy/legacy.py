"""Frozen pre-improvement baseline for controlled comparisons only."""

from dataclasses import asdict
from time import perf_counter

from false_positive.advisors.base import DecisionAdvisor, DeterministicAdvisor, estimated_net
from false_positive.domain.constraints import MAX_CAMPAIGNS, MIN_PILOT_CUSTOMERS
from false_positive.domain.models import PilotObservation, PilotRequest, ResourceState, StrategyRun
from false_positive.domain.protocols import AgentEnvironmentProtocol, StrategyObserver
from false_positive.observability.trace import TraceRecorder
from .baseline import generate_candidates
from .fallback import choose_fallback, fits, reserve


class LegacyStrategyEngine:
    def __init__(self, advisor: DecisionAdvisor | None = None):
        self.advisor = advisor if advisor is not None else DeterministicAdvisor()

    def run(self, env: AgentEnvironmentProtocol, observer: StrategyObserver | None = None) -> StrategyRun:
        started = perf_counter()
        before = ResourceState.from_env(env)
        warnings: list[str] = []
        recorder = TraceRecorder()

        def emit(event: str, payload: dict):
            recorder.record(event, payload)
            if observer is not None:
                try:
                    observer.record(event, payload.copy())
                except Exception:
                    if "observer_failed" not in warnings:
                        warnings.append("observer_failed")

        candidates = generate_candidates(env)
        # Keep an affordable final campaign in reserve before any pilot.
        safety = choose_fallback(sorted(candidates, key=lambda c: (c.n_customers, c.campaign.campaign_name)), before)
        observed = []
        emit("started", {"resources": asdict(before), "candidate_count": len(candidates)})
        attempts = 0
        for candidate in candidates:
            if attempts >= 3 or env.pilots_left <= 0:
                break
            resources = ResourceState.from_env(env)
            contacts = resources.remaining_contacts - safety.n_customers
            money = resources.remaining_budget - safety.n_customers * safety.cost_per_contact
            n = min(100, candidate.n_customers, contacts)
            if candidate.cost_per_contact > 0:
                n = min(n, int(money // candidate.cost_per_contact))
            if n < MIN_PILOT_CUSTOMERS or money < 0:
                continue
            attempts += 1
            request = PilotRequest(candidate.campaign, int(n))
            try:
                result = env.run_pilot(**request.to_kwargs())
                observation = PilotObservation.from_result(result, request)
            except Exception as exc:
                # Read actual env resources next time: a failed response may still cost resources.
                warnings.append(f"pilot_failed:{type(exc).__name__}")
                emit("pilot_failed", {"campaign": candidate.campaign.to_dict(), "error_type": type(exc).__name__})
                continue
            observed.append((candidate, observation))
            emit("pilot_observed", asdict(observation))

        after_pilots = ResourceState.from_env(env)
        try:
            order = self.advisor.rank(observed.copy())
            if (not isinstance(order, list) or any(type(i) is not int for i in order)
                    or sorted(order) != list(range(len(observed)))):
                raise ValueError("Advisor must return a permutation of observation indices")
        except Exception as exc:
            warnings.append(f"advisor_fallback:{type(exc).__name__}")
            order = DeterministicAdvisor().rank(observed)

        remaining = after_pilots
        selected = []
        for index in order:
            candidate, observation = observed[index]
            if estimated_net(candidate, observation) > 0 and fits(candidate, remaining):
                selected.append(candidate.campaign)
                remaining = reserve(candidate, remaining)
            if len(selected) == MAX_CAMPAIGNS:
                break
        if not selected:
            warnings.append("fallback_used:no_positive_affordable_observation")
            ranked = [observed[i][0] for i in order]
            candidate = choose_fallback(ranked + [safety] + candidates, remaining)
            selected = [candidate.campaign]
            remaining = reserve(candidate, remaining)
        emit("completed", {"campaigns": [c.to_dict() for c in selected], "resources_after_plan": asdict(remaining)})
        return StrategyRun(
            campaigns=selected, pilots=[item[1] for item in observed], resources_before=before,
            resources_after_pilots=after_pilots, resources_after_plan=remaining,
            warnings=warnings, trace=recorder.events, duration_ms=(perf_counter() - started) * 1000,
        )

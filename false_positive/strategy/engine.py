"""Adaptive public-interface strategy with repeated-pilot risk checks."""

from dataclasses import asdict, replace
from time import perf_counter

from false_positive.advisors.base import DecisionAdvisor, DeterministicAdvisor
from false_positive.domain.models import PilotObservation, PilotRequest, ResourceState, StrategyRun
from false_positive.domain.protocols import AgentEnvironmentProtocol, StrategyObserver
from false_positive.observability.trace import TraceRecorder
from .candidates import audience_key, channel_hypothesis, generate_hypotheses, small_fallbacks
from .evidence import Evidence
from .fallback import choose_fallback, fits, reserve


def permutation(order, size):
    return (isinstance(order, list) and all(type(i) is int for i in order)
            and sorted(order) == list(range(size)))


class StrategyEngine:
    def __init__(self, advisor: DecisionAdvisor | None = None, hypothesis_advisor=None):
        self.advisor = advisor if advisor is not None else DeterministicAdvisor()
        self.hypothesis_advisor = hypothesis_advisor

    def run(self, env: AgentEnvironmentProtocol, observer: StrategyObserver | None = None) -> StrategyRun:
        started = perf_counter()
        before = ResourceState.from_env(env)
        warnings, pilots = [], []
        recorder = TraceRecorder()

        def emit(event, payload):
            recorder.record(event, payload)
            if observer is not None:
                try:
                    observer.record(event, payload.copy())
                except Exception:
                    if "observer_failed" not in warnings:
                        warnings.append("observer_failed")

        candidates = generate_hypotheses(env)
        safety_candidates = small_fallbacks(env, candidates)
        safety = choose_fallback(safety_candidates, before)
        emit("started", {"resources": asdict(before), "candidate_count": len(candidates)})
        # Bound advisory payload/candidate pool. No subscriber records or private state.
        pool = candidates[:24]
        if self.hypothesis_advisor is not None and pool:
            try:
                order = self.hypothesis_advisor.prioritize(pool, env.tariffs.to_dict(orient="records"), env.channels)
                if not permutation(order, len(pool)):
                    raise ValueError("Hypothesis advisor must return a permutation")
                pool = [pool[i] for i in order]
                emit("hypotheses_prioritized", {"source": "external_advisor", "order": order})
            except Exception as exc:
                warnings.append(f"hypothesis_advisor_fallback:{type(exc).__name__}")
                emit("hypotheses_prioritized", {"source": "deterministic_fallback"})
        # Cover distinct current tariffs before spending the limited pilot budget
        # on alternative targets for the same audience.
        shortlist, seen = [], set()
        for c in pool:
            current = c.campaign.filter_current_tariff
            if current not in seen:
                shortlist.append(c)
                seen.add(current)
            if len(shortlist) == 6:
                break
        for c in pool:
            if len(shortlist) == 6:
                break
            if c not in shortlist:
                shortlist.append(c)
        evidence = [Evidence(c) for c in shortlist]
        promoted = set()
        attempts = 0
        # Reserve enough contacts for meaningful final deployment, plus a real
        # mandatory fallback. Paid reconnaissance is capped at 15% of cash.
        contact_cap = min(3000, max(0, before.remaining_contacts - safety.n_customers))
        minimum_probe_cost = min((10 * c.cost_per_contact for c in shortlist), default=0)
        money_cap = min(max(before.remaining_budget * .15, minimum_probe_cost),
                        max(0.0, before.remaining_budget - safety.n_customers * safety.cost_per_contact))

        def pilot_size(item):
            actual = ResourceState.from_env(env)
            spent_contacts = before.remaining_contacts - actual.remaining_contacts
            spent_money = before.remaining_budget - actual.remaining_budget
            count = min(80 if not item.observations else 200, item.candidate.n_customers,
                        contact_cap - spent_contacts, actual.remaining_contacts - safety.n_customers)
            cost = item.candidate.cost_per_contact
            if cost > 0:
                count = min(count, int(min(money_cap - spent_money,
                            actual.remaining_budget - safety.n_customers * safety.cost_per_contact) // cost))
            return max(0, int(count))

        while attempts < min(20, before.pilots_left) and env.pilots_left > 0:
            # An observed positive on a cheap channel may justify testing a paid
            # alternative. The alternative must pass its own repeated-pilot gate.
            for item in list(evidence):
                key = audience_key(item.candidate)
                if item.confirmed() and key not in promoted:
                    promoted.add(key)
                    alternative = channel_hypothesis(item, env)
                    if (alternative is not None and env.pilots_left >= 3
                            and 480 * alternative.cost_per_contact <= money_cap - (before.remaining_budget - env.remaining_budget)):
                        evidence.append(Evidence(alternative))
            feasible = [item for item in evidence if item.attempts < 4 and pilot_size(item) >= 10
                        and not item.confirmed()
                        and (not item.observations or item.upper_net() > 0)]
            if not feasible:
                break
            untested = [item for item in feasible if item.attempts == 0]
            item = untested[0] if untested else max(feasible, key=lambda e: (
                e.upper_net() / (1 + len(e.observations)), -e.attempts,
                e.candidate.campaign.campaign_name))
            request = PilotRequest(item.candidate.campaign, pilot_size(item))
            attempts += 1
            item.attempts += 1
            try:
                observation = PilotObservation.from_result(env.run_pilot(**request.to_kwargs()), request)
            except Exception as exc:
                warnings.append(f"pilot_failed:{type(exc).__name__}")
                emit("pilot_failed", {"campaign": item.candidate.campaign.to_dict(), "error_type": type(exc).__name__})
                continue
            item.observations.append(observation)
            pilots.append(observation)
            emit("pilot_observed", asdict(observation))
            emit("evidence_updated", {"campaign": item.candidate.campaign.campaign_name,
                 "replicates": len(item.observations), "mean_ratio": item.mean,
                 "uncertainty": item.uncertainty, "conservative_net": item.lower_net(),
                 "confirmed": item.confirmed()})

        after_pilots = ResourceState.from_env(env)
        eligible = [item for item in evidence if item.confirmed()]
        # The existing advisor may reorder eligible conservative estimates only.
        # It cannot override the repeated-pilot gate or supply arbitrary campaigns.
        summaries = [(item.candidate, replace(item.observations[-1], observed_lift_ratio=item.lower_ratio()))
                     for item in eligible]
        try:
            order = self.advisor.rank(summaries.copy())
            if not permutation(order, len(summaries)):
                raise ValueError("Advisor must return a permutation")
        except Exception as exc:
            warnings.append(f"advisor_fallback:{type(exc).__name__}")
            order = DeterministicAdvisor().rank(summaries)
        remaining, selected, audiences = after_pilots, [], set()
        for index in order:
            c = eligible[index].candidate
            key = audience_key(c)
            if key not in audiences and fits(c, remaining):
                selected.append(c.campaign)
                audiences.add(key)
                remaining = reserve(c, remaining)
            if len(selected) == 10:
                break
        if not selected:
            warnings.append("fallback_used:no_confirmed_affordable_observation")
            candidate = choose_fallback(safety_candidates, remaining)
            selected = [candidate.campaign]
            remaining = reserve(candidate, remaining)
        emit("completed", {"campaigns": [c.to_dict() for c in selected], "resources_after_plan": asdict(remaining)})
        return StrategyRun(selected, pilots, before, after_pilots, remaining, warnings, recorder.events,
                           (perf_counter() - started) * 1000)

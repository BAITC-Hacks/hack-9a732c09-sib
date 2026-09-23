"""Advisor ranks measured candidates; the engine validates all suggestions."""

from typing import Protocol

from false_positive.domain.models import Candidate, PilotObservation


class DecisionAdvisor(Protocol):
    def rank(self, observations: list[tuple[Candidate, PilotObservation]]) -> list[int]: ...


class DeterministicAdvisor:
    def rank(self, observations: list[tuple[Candidate, PilotObservation]]) -> list[int]:
        return sorted(range(len(observations)), key=lambda i: (
            -estimated_net(*observations[i]), observations[i][0].campaign.campaign_name,
        ))


def estimated_net(candidate: Candidate, observation: PilotObservation) -> float:
    """Pilot-based estimate for selection, never an official scored KPI."""
    return observation.observed_lift_ratio * candidate.baseline_arpu - candidate.n_customers * candidate.cost_per_contact

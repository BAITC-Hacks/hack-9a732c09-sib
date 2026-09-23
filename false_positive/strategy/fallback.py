"""Select one real, affordable cell even when all observations are negative."""

from false_positive.domain.models import Candidate, ResourceState


def fits(candidate: Candidate, resources: ResourceState) -> bool:
    return (0 < candidate.n_customers <= resources.remaining_contacts
            and candidate.n_customers * candidate.cost_per_contact <= resources.remaining_budget)


def reserve(candidate: Candidate, resources: ResourceState) -> ResourceState:
    return ResourceState(
        resources.remaining_budget - candidate.n_customers * candidate.cost_per_contact,
        resources.remaining_contacts - candidate.n_customers, resources.pilots_left,
    )


def choose_fallback(candidates: list[Candidate], resources: ResourceState) -> Candidate:
    for candidate in candidates:
        if fits(candidate, resources):
            return candidate
    raise ValueError("No non-empty campaign fits the environment's remaining resources")

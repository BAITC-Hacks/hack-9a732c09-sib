"""Repeat-pilot evidence, not a calibrated confidence interval or scored KPI."""

from dataclasses import dataclass, field
from math import sqrt

from false_positive.domain.models import Candidate, PilotObservation


@dataclass
class Evidence:
    candidate: Candidate
    observations: list[PilotObservation] = field(default_factory=list)
    attempts: int = 0

    @property
    def mean(self):
        total = sum(p.n_customers for p in self.observations)
        return sum(p.n_customers * p.observed_lift_ratio for p in self.observations) / total if total else 0.0

    @property
    def uncertainty(self):
        if not self.observations:
            return 1.0
        weights = [p.n_customers for p in self.observations]
        total = sum(weights)
        # A unit-scale floor prevents identical or single noisy reports from
        # claiming certainty. It is an explicit risk assumption, not env knowledge.
        floor = 1.0 / sqrt(total)
        if len(weights) == 1:
            return floor
        variance = sum(w * (p.observed_lift_ratio - self.mean) ** 2
                       for w, p in zip(weights, self.observations)) / total
        effective = total ** 2 / sum(w * w for w in weights)
        return max(floor, sqrt(variance / max(effective - 1, 1)))

    def lower_ratio(self, penalty=2.0):
        return self.mean - penalty * self.uncertainty

    def upper_net(self, penalty=2.0):
        c = self.candidate
        return (self.mean + penalty * self.uncertainty) * c.baseline_arpu - c.n_customers * c.cost_per_contact

    def lower_net(self, penalty=2.0):
        c = self.candidate
        return self.lower_ratio(penalty) * c.baseline_arpu - c.n_customers * c.cost_per_contact

    def confirmed(self):
        c = self.candidate
        positives = sum(p.observed_lift_ratio * c.baseline_arpu > c.n_customers * c.cost_per_contact
                        for p in self.observations)
        # A third independent call is a confirmation stage after exploratory
        # selection. Two favorable measurements alone cannot deploy a large cell.
        return len(self.observations) >= 3 and positives >= 3 and self.lower_net() > 0

"""JSON-friendly core values. No HTTP schemas or scoring internals."""

from dataclasses import asdict, dataclass, field
from math import isfinite

from .constraints import CHANNELS, FILTER_VALUES, MAX_PILOT_CUSTOMERS, MIN_PILOT_CUSTOMERS


@dataclass(frozen=True)
class Campaign:
    target_tariff: str
    channel: str
    campaign_name: str = "baseline"
    filter_arpu_segment: str | None = None
    filter_data_segment: str | None = None
    filter_call_segment: str | None = None
    filter_current_tariff: str | None = None

    def __post_init__(self):
        if not self.target_tariff or self.channel not in CHANNELS:
            raise ValueError("Campaign requires a tariff and supported channel")
        for key, allowed in FILTER_VALUES.items():
            if getattr(self, key) is not None and getattr(self, key) not in allowed:
                raise ValueError(f"Invalid {key}")
        if self.filter_current_tariff is not None:
            if not all(part.strip() for part in self.filter_current_tariff.split(";")):
                raise ValueError("Empty tariff in filter_current_tariff")

    def to_dict(self) -> dict:
        return asdict(self)

    def pilot_kwargs(self) -> dict:
        return {key: value for key, value in asdict(self).items() if key != "campaign_name"}


@dataclass(frozen=True)
class PilotRequest:
    campaign: Campaign
    n_customers: int = 100

    def __post_init__(self):
        if not MIN_PILOT_CUSTOMERS <= self.n_customers <= MAX_PILOT_CUSTOMERS:
            raise ValueError("Pilot request must contain 10..200 customers")

    def to_kwargs(self) -> dict:
        return dict(self.campaign.pilot_kwargs(), n_customers=self.n_customers)


@dataclass(frozen=True)
class PilotObservation:
    pilot: str
    target_tariff: str
    channel: str
    n_customers: int
    cost: float
    observed_lift_ratio: float
    observed_lift_total: float
    remaining_budget: float
    remaining_contacts: int
    filters: dict[str, str | None] = field(default_factory=dict)

    @classmethod
    def from_result(cls, result: dict, request: PilotRequest):
        numeric = ("cost", "observed_lift_ratio", "observed_lift_total", "remaining_budget")
        values = {key: float(result[key]) for key in numeric}
        if not all(isfinite(value) for value in values.values()):
            raise ValueError("Non-finite pilot observation")
        count, contacts = int(result["n_customers"]), int(result["remaining_contacts"])
        if not 1 <= count <= request.n_customers or contacts < 0:
            raise ValueError("Invalid pilot resource counters")
        if values["cost"] < 0 or values["remaining_budget"] < 0:
            raise ValueError("Negative pilot resources")
        if result["target_tariff"] != request.campaign.target_tariff or result["channel"] != request.campaign.channel:
            raise ValueError("Pilot response does not match request")
        return cls(
            pilot=str(result["pilot"]), target_tariff=str(result["target_tariff"]),
            channel=str(result["channel"]), n_customers=count, remaining_contacts=contacts,
            filters={k: v for k, v in request.campaign.to_dict().items() if k.startswith("filter_")},
            **values,
        )


@dataclass(frozen=True)
class ResourceState:
    remaining_budget: float
    remaining_contacts: int
    pilots_left: int

    @classmethod
    def from_env(cls, env):
        return cls(float(env.remaining_budget), int(env.remaining_contacts), int(env.pilots_left))


@dataclass(frozen=True)
class Candidate:
    campaign: Campaign
    n_customers: int
    baseline_arpu: float
    cost_per_contact: float


@dataclass
class StrategyRun:
    campaigns: list[Campaign]
    pilots: list[PilotObservation]
    resources_before: ResourceState
    resources_after_pilots: ResourceState
    resources_after_plan: ResourceState
    warnings: list[str] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)
